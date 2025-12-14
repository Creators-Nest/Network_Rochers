from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Sequence, Tuple

from ..core.packet import Packet
from .simulator import Simulator

NodeAddress = Tuple[int, int]


def multiply_matrices(matrix_a: Sequence[Sequence[float]], matrix_b: Sequence[Sequence[float]]) -> List[List[float]]:
    """Classic matrix multiplication implemented with pure Python loops."""
    if not matrix_a or not matrix_b:
        raise ValueError("Input matrices must not be empty")

    common = len(matrix_a[0])
    if any(len(row) != common for row in matrix_a):
        raise ValueError("Matrix A has inconsistent row lengths")
    if any(len(row) != len(matrix_b[0]) for row in matrix_b):
        raise ValueError("Matrix B has inconsistent row lengths")
    if common != len(matrix_b):
        raise ValueError("Matrix dimensions incompatible for multiplication")

    rows = len(matrix_a)
    cols = len(matrix_b[0])
    result = [[0 for _ in range(cols)] for _ in range(rows)]

    for i in range(rows):
        for j in range(cols):
            cell_sum = 0
            for k in range(common):
                cell_sum += matrix_a[i][k] * matrix_b[k][j]
            result[i][j] = cell_sum

    return result


def run_matrix_multiplication_experiment(
    simulator: Simulator,
    matrix_a: Sequence[Sequence[float]],
    matrix_b: Sequence[Sequence[float]],
    *,
    aggregator: NodeAddress | None = None,
    worker_nodes: Sequence[NodeAddress] | None = None,
    max_cycles: int = 10_000,
) -> Dict[str, object]:
    """Drive a communication-heavy matrix multiplication workload through the simulator."""

    if not isinstance(simulator, Simulator):
        raise TypeError("simulator must be an instance of Simulator")

    addresses = sorted(simulator.topology.nodes.keys())
    if not addresses:
        raise ValueError("Topology must contain at least one node")

    if aggregator is None:
        aggregator = addresses[0]
    if worker_nodes is None:
        worker_nodes = [addr for addr in addresses if addr != aggregator]
    if not worker_nodes:
        raise ValueError("Matrix experiment requires at least one worker node")
    if aggregator in worker_nodes:
        raise ValueError("Aggregator node must be distinct from worker nodes")

    rows = len(matrix_a)
    cols = len(matrix_b[0]) if matrix_b else 0
    common = len(matrix_a[0]) if matrix_a else 0

    row_workers: Dict[int, NodeAddress] = {
        row_index: worker_nodes[row_index % len(worker_nodes)]
        for row_index in range(rows)
    }

    _reset_network_state(simulator)
    simulator.reset_metrics()

    expected_result = multiply_matrices(matrix_a, matrix_b)

    partial_packets: List[Packet] = []
    for i in range(rows):
        source_node = row_workers[i]
        for j in range(cols):
            for k in range(common):
                value = matrix_a[i][k] * matrix_b[k][j]
                payload = {
                    "stage": "partial",
                    "row": i,
                    "col": j,
                    "factor": k,
                    "value": value,
                }
                packet = Packet(
                    source_node,
                    aggregator,
                    data=payload,
                    packet_id=f"partial-{i}-{j}-{k}",
                    metadata={"phase": "partial", "row": i, "col": j, "factor": k},
                )
                partial_packets.append(packet)

    for packet in partial_packets:
        simulator.inject_packet(packet)

    total_packets = len(partial_packets)
    cycles_elapsed = _run_until_deliveries(simulator, total_packets, max_cycles, 0)

    aggregator_node = simulator.topology.nodes[aggregator]
    partial_contributions: Dict[Tuple[int, int], List[float]] = defaultdict(list)
    for delivered_packet in aggregator_node.application_logic_buffer:
        payload = getattr(delivered_packet, "data", None)
        if isinstance(payload, dict) and payload.get("stage") == "partial":
            partial_contributions[(payload["row"], payload["col"])].append(payload["value"])

    result_packets: List[Packet] = []
    for i in range(rows):
        destination_node = row_workers[i]
        for j in range(cols):
            value = expected_result[i][j]
            payload = {
                "stage": "result",
                "row": i,
                "col": j,
                "value": value,
            }
            packet = Packet(
                aggregator,
                destination_node,
                data=payload,
                packet_id=f"result-{i}-{j}",
                metadata={"phase": "result", "row": i, "col": j},
            )
            result_packets.append(packet)

    for packet in result_packets:
        simulator.inject_packet(packet)

    total_packets += len(result_packets)
    cycles_elapsed = _run_until_deliveries(simulator, total_packets, max_cycles, cycles_elapsed)

    received_result = [[0 for _ in range(cols)] for _ in range(rows)]
    for row_index, node_addr in row_workers.items():
        node = simulator.topology.nodes[node_addr]
        for delivered_packet in node.application_logic_buffer:
            payload = getattr(delivered_packet, "data", None)
            if isinstance(payload, dict) and payload.get("stage") == "result":
                received_result[row_index][payload["col"]] = payload["value"]

    partial_reduced = {
        key: sum(values)
        for key, values in partial_contributions.items()
    }
    partial_match = _matrices_close(
        _contribution_to_matrix(partial_reduced, rows, cols),
        expected_result,
    )
    result_match = _matrices_close(received_result, expected_result)

    return {
        "aggregator": aggregator,
        "rowWorkerMap": row_workers,
        "cyclesExecuted": cycles_elapsed,
        "packets": {
            "partial": len(partial_packets),
            "result": len(result_packets),
            "total": total_packets,
        },
        "expectedResult": expected_result,
        "receivedResult": received_result,
        "partialAggregationMatches": partial_match,
        "resultMatches": result_match,
        "metrics": simulator.metrics.summary(),
    }


def _run_until_deliveries(
    simulator: Simulator,
    target_deliveries: int,
    max_cycles: int,
    cycles_elapsed: int,
) -> int:
    while simulator.metrics.delivered_count < target_deliveries:
        if cycles_elapsed >= max_cycles:
            raise RuntimeError(
                f"Simulation exceeded {max_cycles} cycles without delivering {target_deliveries} packets"
            )
        simulator.run_simulation_step()
        cycles_elapsed += 1
    return cycles_elapsed


def _matrices_close(matrix_a: Sequence[Sequence[float]], matrix_b: Sequence[Sequence[float]], tol: float = 1e-9) -> bool:
    if len(matrix_a) != len(matrix_b):
        return False
    for row_a, row_b in zip(matrix_a, matrix_b):
        if len(row_a) != len(row_b):
            return False
        for value_a, value_b in zip(row_a, row_b):
            if abs(value_a - value_b) > tol:
                return False
    return True


def _contribution_to_matrix(
    contributions: Dict[Tuple[int, int], float],
    rows: int,
    cols: int,
) -> List[List[float]]:
    matrix = [[0 for _ in range(cols)] for _ in range(rows)]
    for (row, col), value in contributions.items():
        matrix[row][col] = value
    return matrix


def _reset_network_state(simulator: Simulator) -> None:
    simulator.global_clock = 0
    if hasattr(simulator, "_pending_injections"):
        simulator._pending_injections.clear()

    for node in simulator.topology.nodes.values():
        node.application_logic_buffer.clear()
        for iface in node.interfaces.values():
            iface.send_buffer.buffer.clear()
            iface.receive_buffer.buffer.clear()
            iface.send_register = None
            iface.receive_register = None
            iface.pin_REQ = False
            iface.pin_ACK = False
            iface.pin_DATA = None
            iface.pin_CHOKE = False
            iface.bit_Busy = False
            iface.bit_Transfer = False
            iface.bit_Receive = False
            iface.timeout_counter = 0