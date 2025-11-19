"""Flask application that exposes a web-based RicoBit topology visualizer."""

from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple

from flask import Flask, jsonify, render_template, request

from ..simulation.simulator import Simulator
from ..topology.ricobit_topology import RiCoBiT_Topology

NodeAddress = Tuple[int, int]


@dataclass
class HopSegment:
    """Represents one hop in the routing path."""

    start: NodeAddress
    end: NodeAddress

    @property
    def kind(self) -> str:
        """Return the hop type for front-end rendering."""
        start_ring, _ = self.start
        end_ring, _ = self.end
        if start_ring == end_ring and start_ring > 0:
            return "ring"
        return "tree"

    def to_payload(self) -> Dict[str, Dict[str, int]]:
        """Serialize hop information for JSON responses."""
        start_ring, start_idx = self.start
        end_ring, end_idx = self.end
        return {
            "from": {"ring": start_ring, "index": start_idx},
            "to": {"ring": end_ring, "index": end_idx},
            "type": self.kind,
        }


class AppState:
    """Holds topology, simulator, and routing state for the web app."""

    def __init__(self, num_levels: int = 5) -> None:
        self._lock = threading.Lock()
        self.initialize(num_levels)

    def initialize(self, num_levels: int) -> None:
        if num_levels < 2:
            raise ValueError("Topology must contain at least two levels for visualization")

        with self._lock:
            self.num_levels = num_levels
            self.topology = RiCoBiT_Topology(num_levels)
            self.simulator = Simulator(self.topology)
            self.router = self.topology.router

    def _build_node_payload(self, node) -> Dict[str, object]:
        ring, index = node.address
        neighbors_payload: List[Dict[str, object]] = []

        for neighbor_address, interface in sorted(node.interfaces.items()):
            neighbor_ring, neighbor_index = neighbor_address
            neighbors_payload.append(
                {
                    "ring": neighbor_ring,
                    "index": neighbor_index,
                    "type": "ring" if neighbor_ring == ring else "tree",
                    "sendCapacity": getattr(getattr(interface.send_buffer, "buffer", None), "maxlen", 0),
                    "receiveCapacity": getattr(getattr(interface.receive_buffer, "buffer", None), "maxlen", 0),
                }
            )

        routing_entries: List[Dict[str, object]] = []
        for destination, next_hop in sorted(node.routing_table.items()):
            dest_ring, dest_index = destination
            next_ring, next_index = next_hop
            routing_entries.append(
                {
                    "destination": {"ring": dest_ring, "index": dest_index},
                    "nextHop": {"ring": next_ring, "index": next_index},
                }
            )

        return {
            "id": f"{ring}-{index}",
            "ring": ring,
            "index": index,
            "degree": len(node.interfaces),
            "neighbors": neighbors_payload,
            "routingTable": routing_entries,
        }

    def node_payload(self, address: NodeAddress) -> Dict[str, object]:
        with self._lock:
            node = self.topology.nodes.get(address)
            if node is None:
                raise KeyError(address)
            return self._build_node_payload(node)

    def topology_payload(self) -> Dict[str, object]:
        nodes_payload: List[Dict[str, int]] = []
        tree_edges: List[Dict[str, Dict[str, int]]] = []
        ring_edges: List[Dict[str, Dict[str, int]]] = []
        seen_edges: set[Tuple[NodeAddress, NodeAddress]] = set()

        with self._lock:
            for (ring, index), node in sorted(self.topology.nodes.items()):
                nodes_payload.append(self._build_node_payload(node))

                for neighbor in node.interfaces.keys():
                    edge = tuple(sorted((node.address, neighbor)))
                    if edge in seen_edges:
                        continue

                    seen_edges.add(edge)
                    edge_payload = {
                        "source": {"ring": ring, "index": index},
                        "target": {"ring": neighbor[0], "index": neighbor[1]},
                    }
                    if neighbor[0] == ring:
                        ring_edges.append(edge_payload)
                    else:
                        tree_edges.append(edge_payload)

        return {
            "numLevels": self.num_levels,
            "nodes": nodes_payload,
            "treeEdges": tree_edges,
            "ringEdges": ring_edges,
        }

    def resolve_path(self, source: NodeAddress, destination: NodeAddress) -> List[NodeAddress]:
        with self._lock:
            path = self.router.get_full_path(source, destination)
        if not path:
            raise ValueError(f"No path found between {source} and {destination}")
        return path


def create_app(num_levels: int = 5) -> Flask:
    """Application factory for the RicoBit Flask visualizer."""

    app = Flask(__name__, template_folder="templates", static_folder="static")
    state = AppState(num_levels=num_levels)

    def parse_address(payload_key: str, payload: Dict[str, object]) -> NodeAddress:
        node_payload = payload.get(payload_key)
        if not isinstance(node_payload, dict):
            raise ValueError(f"Missing '{payload_key}' payload")

        try:
            ring = int(node_payload["ring"])
            index = int(node_payload["node"] if "node" in node_payload else node_payload["index"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"Invalid node payload for '{payload_key}'") from exc

        return (ring, index)

    @app.route("/")
    def index() -> str:
        return render_template("index.html", current_year=_current_year())

    @app.route("/simulator")
    def simulator() -> str:
        return render_template("simulator.html")

    @app.get("/api/topology")
    def get_topology():
        return jsonify(state.topology_payload())

    @app.post("/api/topology")
    def update_topology():
        payload = request.get_json(force=True, silent=True) or {}
        num_levels_payload = payload.get("numLevels")

        if not isinstance(num_levels_payload, int):
            return (jsonify({"error": "numLevels must be an integer"}), 400)

        try:
            state.initialize(num_levels_payload)
        except ValueError as exc:
            return (jsonify({"error": str(exc)}), 400)

        return jsonify(state.topology_payload())

    @app.post("/api/route")
    def compute_route():
        payload = request.get_json(force=True, silent=True) or {}

        try:
            source = parse_address("source", payload)
            destination = parse_address("destination", payload)
        except ValueError as exc:
            return (jsonify({"error": str(exc)}), 400)

        if source == destination:
            return (
                jsonify(
                    {
                        "path": [
                            {"ring": source[0], "index": source[1]},
                        ],
                        "hopCount": 0,
                        "segments": [],
                        "flow": [
                            {
                                "phase": "Complete",
                                "title": "Already at destination",
                                "details": [
                                    f"Source and destination are both {source}",
                                ],
                            }
                        ],
                    }
                ),
                200,
            )

        try:
            path = state.resolve_path(source, destination)
        except ValueError as exc:
            return (jsonify({"error": str(exc)}), 400)

        segments = [HopSegment(start, end).to_payload() for start, end in zip(path, path[1:])]
        flow = build_flow_timeline(path)

        return jsonify(
            {
                "path": [
                    {"ring": ring, "index": index}
                    for ring, index in path
                ],
                "hopCount": max(len(path) - 1, 0),
                "segments": segments,
                "flow": flow,
            }
        )

    @app.get("/api/node/<int:ring>/<int:index>")
    def get_node_details(ring: int, index: int):
        try:
            payload = state.node_payload((ring, index))
        except KeyError:
            return (jsonify({"error": "Node not found"}), 404)
        return jsonify(payload)

    return app


def _current_year() -> int:
    from datetime import datetime

    return datetime.now().year


def build_flow_timeline(path: Iterable[NodeAddress]) -> List[Dict[str, object]]:
    """Generate a step-by-step flow log for the given path."""

    path_list = list(path)
    if len(path_list) <= 1:
        return []

    flow_log: List[Dict[str, object]] = [
        {
            "phase": "Create",
            "title": "Packet instantiated",
            "details": [
                f"Source: {path_list[0]}",
                f"Destination: {path_list[-1]}",
            ],
        }
    ]

    total_hops = len(path_list) - 1
    for hop_index, (start, end) in enumerate(zip(path_list, path_list[1:]), start=1):
        hop_type = "Ring" if start[0] == end[0] and start[0] > 0 else "Tree"
        base_details = [
            f"REQ: {start} → {end}",
            f"ACK: {end} → {start}",
            "Data transfer across interface",
        ]
        if hop_index == 1:
            base_details.insert(0, "Routing decision computed at source")
        if hop_index == total_hops:
            base_details.append("Packet delivered to destination buffer")

        flow_log.append(
            {
                "phase": f"Hop {hop_index}",
                "title": f"{start} → {end} ({hop_type})",
                "details": base_details,
            }
        )

    flow_log.append(
        {
            "phase": "Complete",
            "title": "Transmission finished",
            "details": [
                f"Total hops: {total_hops}",
                "All handshake lines reset to idle",
            ],
        }
    )

    return flow_log
