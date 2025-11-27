"""Flask application that exposes a web-based Mesh topology visualizer."""

from __future__ import annotations

import sys
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from flask import Flask, jsonify, render_template, request

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from simulation.simulator import Simulator
from topology.enhanced_mesh_topology import EnhancedMeshTopology

NodeAddress = Tuple[int, int]


@dataclass
class HopSegment:
    """Represents one hop in the routing path."""

    start: NodeAddress
    end: NodeAddress

    @property
    def kind(self) -> str:
        """Return the hop type for front-end rendering."""
        start_x, start_y = self.start
        end_x, end_y = self.end
        
        # Determine direction
        if start_x == end_x:
            return "vertical"  # North-South
        elif start_y == end_y:
            return "horizontal"  # East-West
        return "diagonal"

    def to_payload(self) -> Dict[str, Dict[str, int]]:
        """Serialize hop information for JSON responses."""
        start_x, start_y = self.start
        end_x, end_y = self.end
        return {
            "from": {"x": start_x, "y": start_y},
            "to": {"x": end_x, "y": end_y},
            "type": self.kind,
        }


class AppState:
    """Holds topology, simulator, and routing state for the web app."""

    def __init__(self, width: int = 6, height: int = 6) -> None:
        self._lock = threading.Lock()
        self.initialize(width, height)

    def initialize(self, width: int, height: int) -> None:
        if width < 2 or height < 2:
            raise ValueError("Mesh must be at least 2x2 for visualization")

        with self._lock:
            self.width = width
            self.height = height
            self.topology = EnhancedMeshTopology(width, height)
            self.simulator = Simulator(self.topology)
            self.router = self.topology.router if hasattr(self.topology, 'router') else None

    @staticmethod
    def _serialize_packet(packet) -> Dict[str, object] | None:
        """Convert a packet into a JSON-serializable structure."""
        if packet is None:
            return None

        source_x, source_y = packet.source_address
        dest_x, dest_y = packet.dest_address
        return {
            "source": {"x": source_x, "y": source_y},
            "destination": {"x": dest_x, "y": dest_y},
            "data": getattr(packet, "data", getattr(packet, "payload", None)),
            "startTimer": getattr(packet, "start_timer", None),
            "endTimer": getattr(packet, "end_timer", None),
        }

    def _build_node_payload(self, node) -> Dict[str, object]:
        x, y = node.address
        neighbors_payload: List[Dict[str, object]] = []
        interfaces_payload: List[Dict[str, object]] = []

        def _buffer_snapshot(buffer) -> Dict[str, object]:
            if buffer is None or not hasattr(buffer, 'buffer'):
                return {
                    "used": 0,
                    "capacity": 0,
                    "head": None,
                    "pendingDestinations": [],
                }

            store = buffer.buffer
            used = len(store)
            capacity = getattr(buffer, "capacity", getattr(store, "maxlen", 0) or 0)
            head_packet = next(iter(store), None)
            destination_counts: Dict[Tuple[int, int], int] = {}
            
            for packet in store:
                dest_address = getattr(packet, "dest_address", None)
                if isinstance(dest_address, tuple) and len(dest_address) == 2:
                    if isinstance(dest_address[0], int) and isinstance(dest_address[1], int):
                        destination_counts[dest_address] = destination_counts.get(dest_address, 0) + 1

            pending_destinations = [
                {
                    "destination": {"x": dx, "y": dy},
                    "count": count,
                }
                for (dx, dy), count in sorted(
                    destination_counts.items(), key=lambda item: (-item[1], item[0])
                )
            ]
            
            return {
                "used": used,
                "capacity": capacity,
                "head": self._serialize_packet(head_packet),
                "pendingDestinations": pending_destinations,
            }

        busy_interface_count = 0

        for neighbor_address, interface in sorted(node.interfaces.items()):
            neighbor_x, neighbor_y = neighbor_address
            send_snapshot = _buffer_snapshot(interface.send_buffer)
            receive_snapshot = _buffer_snapshot(interface.receive_buffer)
            
            # Determine direction
            direction = "unknown"
            if neighbor_y < y:
                direction = "north"
            elif neighbor_y > y:
                direction = "south"
            elif neighbor_x < x:
                direction = "west"
            elif neighbor_x > x:
                direction = "east"

            neighbors_payload.append(
                {
                    "x": neighbor_x,
                    "y": neighbor_y,
                    "direction": direction,
                    "sendCapacity": send_snapshot["capacity"],
                    "receiveCapacity": receive_snapshot["capacity"],
                    "sendUsage": send_snapshot["used"],
                    "receiveUsage": receive_snapshot["used"],
                }
            )

            status_bits = {
                "busy": bool(interface.bit_Busy),
                "transfer": bool(interface.bit_Transfer),
                "receive": bool(interface.bit_Receive),
            }
            if status_bits["busy"]:
                busy_interface_count += 1

            interfaces_payload.append(
                {
                    "neighbor": {"x": neighbor_x, "y": neighbor_y},
                    "direction": direction,
                    "sendBuffer": send_snapshot,
                    "receiveBuffer": receive_snapshot,
                    "sendRegister": self._serialize_packet(interface.send_register),
                    "receiveRegister": self._serialize_packet(interface.receive_register),
                    "statusBits": status_bits,
                    "handshakePins": {
                        "req": bool(interface.pin_REQ),
                        "ack": bool(interface.pin_ACK),
                        "data": interface.pin_DATA is not None,
                        "choke": bool(interface.pin_CHOKE),
                    },
                    "dataLine": self._serialize_packet(interface.pin_DATA),
                    "timeout": {
                        "value": getattr(interface, "timeout_counter", 0),
                        "limit": getattr(interface, "TIMEOUT_LIMIT", 0),
                    },
                }
            )

        routing_entries: List[Dict[str, object]] = []
        if hasattr(node, 'routing_table') and node.routing_table:
            for destination, next_hop in sorted(node.routing_table.items()):
                if isinstance(next_hop, tuple):
                    dest_x, dest_y = destination
                    next_x, next_y = next_hop
                    routing_entries.append(
                        {
                            "destination": {"x": dest_x, "y": dest_y},
                            "nextHop": {"x": next_x, "y": next_y},
                        }
                    )

        application_packets = list(getattr(node, 'application_buffer', []))
        application_buffer_payload = {
            "count": len(application_packets),
            "packets": [self._serialize_packet(packet) for packet in application_packets],
        }

        logic_payload = {
            "routing": {
                "entryCount": len(routing_entries),
                "description": f"{len(routing_entries)} destination entries",
            },
            "application": {
                "bufferedPackets": application_buffer_payload["count"],
                "description": (
                    "Application buffer empty"
                    if application_buffer_payload["count"] == 0
                    else f"{application_buffer_payload['count']} packet(s) staged for delivery"
                ),
            },
            "control": {
                "busyInterfaces": busy_interface_count,
                "totalInterfaces": len(node.interfaces),
                "description": (
                    "All interfaces idle"
                    if busy_interface_count == 0
                    else f"{busy_interface_count} of {len(node.interfaces)} interfaces active"
                ),
            },
        }

        return {
            "id": f"{x}-{y}",
            "x": x,
            "y": y,
            "degree": len(node.interfaces),
            "neighbors": neighbors_payload,
            "routingTable": routing_entries,
            "interfaces": interfaces_payload,
            "applicationBuffer": application_buffer_payload,
            "logic": logic_payload,
        }

    def node_payload(self, address: NodeAddress) -> Dict[str, object]:
        with self._lock:
            node = self.topology.nodes.get(address)
            if node is None:
                raise KeyError(address)
            return self._build_node_payload(node)

    def topology_payload(self) -> Dict[str, object]:
        nodes_payload: List[Dict[str, int]] = []
        horizontal_edges: List[Dict[str, Dict[str, int]]] = []
        vertical_edges: List[Dict[str, Dict[str, int]]] = []
        seen_edges: set[Tuple[NodeAddress, NodeAddress]] = set()

        with self._lock:
            for (x, y), node in sorted(self.topology.nodes.items()):
                nodes_payload.append(self._build_node_payload(node))

                for neighbor in node.interfaces.keys():
                    edge = tuple(sorted((node.address, neighbor)))
                    if edge in seen_edges:
                        continue

                    seen_edges.add(edge)
                    edge_payload = {
                        "source": {"x": x, "y": y},
                        "target": {"x": neighbor[0], "y": neighbor[1]},
                    }
                    
                    # Determine if edge is horizontal or vertical
                    if x == neighbor[0]:
                        vertical_edges.append(edge_payload)
                    else:
                        horizontal_edges.append(edge_payload)

        return {
            "width": self.width,
            "height": self.height,
            "nodes": nodes_payload,
            "horizontalEdges": horizontal_edges,
            "verticalEdges": vertical_edges,
        }

    def resolve_path(self, source: NodeAddress, destination: NodeAddress) -> List[NodeAddress]:
        with self._lock:
            # Use XY routing to compute path
            path = []
            current = source
            path.append(current)
            
            # X-direction first (horizontal)
            while current[0] != destination[0]:
                if current[0] < destination[0]:
                    current = (current[0] + 1, current[1])
                else:
                    current = (current[0] - 1, current[1])
                path.append(current)
            
            # Y-direction second (vertical)
            while current[1] != destination[1]:
                if current[1] < destination[1]:
                    current = (current[0], current[1] + 1)
                else:
                    current = (current[0], current[1] - 1)
                path.append(current)
        
        if not path:
            raise ValueError(f"No path found between {source} and {destination}")
        return path


def create_app(width: int = 6, height: int = 6) -> Flask:
    """Application factory for the Mesh Flask visualizer."""

    app = Flask(__name__, template_folder="templates", static_folder="static")
    state = AppState(width=width, height=height)

    def parse_address(payload_key: str, payload: Dict[str, object]) -> NodeAddress:
        node_payload = payload.get(payload_key)
        if not isinstance(node_payload, dict):
            raise ValueError(f"Missing '{payload_key}' payload")

        try:
            x = int(node_payload["x"])
            y = int(node_payload["y"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"Invalid node payload for '{payload_key}'") from exc

        return (x, y)

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
        width_payload = payload.get("width")
        height_payload = payload.get("height")

        if not isinstance(width_payload, int) or not isinstance(height_payload, int):
            return (jsonify({"error": "width and height must be integers"}), 400)

        try:
            state.initialize(width_payload, height_payload)
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
                            {"x": source[0], "y": source[1]},
                        ],
                        "hopCount": 0,
                        "segments": [],
                        "flow": [
                            {
                                "phase": "Complete",
                                "title": "Already at destination",
                                "details": [
                                    f"Source and destination are both ({source[0]}, {source[1]})",
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
                    {"x": x, "y": y}
                    for x, y in path
                ],
                "hopCount": max(len(path) - 1, 0),
                "segments": segments,
                "flow": flow,
            }
        )

    @app.get("/api/node/<int:x>/<int:y>")
    def get_node_details(x: int, y: int):
        try:
            payload = state.node_payload((x, y))
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
                f"Source: ({path_list[0][0]}, {path_list[0][1]})",
                f"Destination: ({path_list[-1][0]}, {path_list[-1][1]})",
            ],
        }
    ]

    total_hops = len(path_list) - 1
    for hop_index, (start, end) in enumerate(zip(path_list, path_list[1:]), start=1):
        # Determine direction
        direction = ""
        if end[0] > start[0]:
            direction = "East"
        elif end[0] < start[0]:
            direction = "West"
        elif end[1] > start[1]:
            direction = "South"
        elif end[1] < start[1]:
            direction = "North"
            
        base_details = [
            f"REQ: ({start[0]}, {start[1]}) → ({end[0]}, {end[1]})",
            f"ACK: ({end[0]}, {end[1]}) → ({start[0]}, {start[1]})",
            "Data transfer across interface",
        ]
        if hop_index == 1:
            base_details.insert(0, "XY routing decision computed at source")
        if hop_index == total_hops:
            base_details.append("Packet delivered to destination buffer")

        flow_log.append(
            {
                "phase": f"Hop {hop_index}",
                "title": f"({start[0]}, {start[1]}) → ({end[0]}, {end[1]}) ({direction})",
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
