from __future__ import annotations

from dataclasses import asdict, dataclass
from statistics import mean
from typing import Dict, List, Optional, Tuple

NodeAddress = Tuple[int, int]


@dataclass
class PacketLifecycle:
    packet_id: str
    source: NodeAddress
    destination: NodeAddress
    start_clock: int
    payload_size: int
    metadata: Optional[dict] = None


@dataclass
class PacketDelivery:
    packet_id: str
    delivered_clock: int
    latency: int
    hop_count: int
    payload_size: int
    metadata: Optional[dict] = None


class SimulationMetrics:
    """Collects latency, throughput, and hop-count metrics for simulations."""

    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self._injections: Dict[str, PacketLifecycle] = {}
        self._deliveries: Dict[str, PacketDelivery] = {}
        self._latencies: List[int] = []
        self._hop_counts: List[int] = []
        self._total_payload: int = 0
        self._first_injection_clock: Optional[int] = None
        self._last_delivery_clock: Optional[int] = None

    @staticmethod
    def _packet_id(packet) -> str:
        packet_id = getattr(packet, "packet_id", None)
        if packet_id is None:
            packet_id = f"pkt-{id(packet)}"
        return str(packet_id)

    def record_injection(self, packet, clock: int) -> None:
        """Track when a packet enters the network."""
        packet_id = self._packet_id(packet)
        payload_size = max(int(getattr(packet, "payload_size", 1)) or 1, 1)
        lifecycle = PacketLifecycle(
            packet_id=packet_id,
            source=getattr(packet, "source_address", (None, None)),
            destination=getattr(packet, "dest_address", (None, None)),
            start_clock=clock,
            payload_size=payload_size,
            metadata=getattr(packet, "metrics_metadata", None),
        )

        existing = self._injections.get(packet_id)
        if existing is None or clock < existing.start_clock:
            self._injections[packet_id] = lifecycle

        if self._first_injection_clock is None or clock < self._first_injection_clock:
            self._first_injection_clock = clock

    def record_delivery(self, packet, clock: int) -> None:
        """Track when a packet reaches its destination."""
        packet_id = self._packet_id(packet)
        payload_size = max(int(getattr(packet, "payload_size", 1)) or 1, 1)
        injection = self._injections.get(packet_id)
        start_clock = injection.start_clock if injection else getattr(packet, "start_timer", clock)
        latency = clock - start_clock
        if latency < 0:
            latency = 0

        hop_count = int(getattr(packet, "hops_traversed", 0))
        delivery = PacketDelivery(
            packet_id=packet_id,
            delivered_clock=clock,
            latency=latency,
            hop_count=hop_count,
            payload_size=payload_size,
            metadata=getattr(packet, "metrics_metadata", None),
        )

        self._deliveries[packet_id] = delivery
        self._total_payload += payload_size
        self._latencies.append(latency)
        self._hop_counts.append(hop_count)
        self._last_delivery_clock = clock

    @property
    def total_injections(self) -> int:
        return len(self._injections)

    @property
    def delivered_count(self) -> int:
        return len(self._deliveries)

    @property
    def in_flight_count(self) -> int:
        return max(self.total_injections - self.delivered_count, 0)

    def elapsed_cycles(self) -> int:
        if self._first_injection_clock is None or self._last_delivery_clock is None:
            return 0
        return (self._last_delivery_clock - self._first_injection_clock) + 1

    def average_latency(self) -> float:
        return float(mean(self._latencies)) if self._latencies else 0.0

    def min_latency(self) -> int:
        return min(self._latencies) if self._latencies else 0

    def max_latency(self) -> int:
        return max(self._latencies) if self._latencies else 0

    def average_hop_count(self) -> float:
        return float(mean(self._hop_counts)) if self._hop_counts else 0.0

    def max_hop_count(self) -> int:
        return max(self._hop_counts) if self._hop_counts else 0

    def throughput(self) -> float:
        elapsed = self.elapsed_cycles()
        if elapsed <= 0:
            return 0.0
        return self.delivered_count / elapsed

    def payload_throughput(self) -> float:
        elapsed = self.elapsed_cycles()
        if elapsed <= 0:
            return 0.0
        return self._total_payload / elapsed

    def deliveries(self) -> List[dict]:
        return [asdict(delivery) for delivery in self._deliveries.values()]

    def summary(self) -> dict:
        return {
            "packetsInjected": self.total_injections,
            "packetsDelivered": self.delivered_count,
            "packetsInFlight": self.in_flight_count,
            "latency": {
                "average": self.average_latency(),
                "min": self.min_latency(),
                "max": self.max_latency(),
            },
            "throughput": {
                "average": self.throughput(),
                "payloadPerCycle": self.payload_throughput(),
            },
            "hopCount": {
                "average": self.average_hop_count(),
                "max": self.max_hop_count(),
            },
            "window": {
                "firstInjectionClock": self._first_injection_clock,
                "lastDeliveryClock": self._last_delivery_clock,
                "elapsedCycles": self.elapsed_cycles(),
            },
            "deliveries": self.deliveries(),
        }
