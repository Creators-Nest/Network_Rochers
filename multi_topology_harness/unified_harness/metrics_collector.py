"""
Unified Metrics Collection System
Collects and standardizes metrics across all topology types
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple, Any
from statistics import mean, stdev, median
from datetime import datetime
import json


@dataclass
class PacketMetric:
    """Metrics for a single packet"""
    packet_id: str
    source: Tuple[int, int]
    destination: Tuple[int, int]
    injection_time: int
    delivery_time: Optional[int]
    latency: Optional[int]
    hop_count: int
    delivered: bool
    
    def to_dict(self) -> Dict:
        return {
            'packet_id': self.packet_id,
            'source': self.source,
            'destination': self.destination,
            'injection_time': self.injection_time,
            'delivery_time': self.delivery_time,
            'latency': self.latency,
            'hop_count': self.hop_count,
            'delivered': self.delivered
        }


@dataclass
class TopologyMetrics:
    """Aggregated metrics for a single topology"""
    topology_type: str
    total_nodes: int
    total_packets_injected: int = 0
    total_packets_delivered: int = 0
    total_packets_in_flight: int = 0
    total_simulation_cycles: int = 0
    
    # Latency metrics
    min_latency: Optional[int] = None
    max_latency: Optional[int] = None
    avg_latency: Optional[float] = None
    median_latency: Optional[float] = None
    latency_std_dev: Optional[float] = None
    
    # Hop count metrics
    min_hops: Optional[int] = None
    max_hops: Optional[int] = None
    avg_hops: Optional[float] = None
    
    # Throughput metrics
    packets_per_cycle: Optional[float] = None
    
    # Time metrics
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    execution_time_seconds: Optional[float] = None
    
    # Raw data for detailed analysis
    packet_metrics: List[PacketMetric] = field(default_factory=list)
    latencies: List[int] = field(default_factory=list)
    hop_counts: List[int] = field(default_factory=list)
    
    def calculate_aggregates(self):
        """Calculate aggregate statistics from raw data"""
        # Only recalculate from packet_metrics if we have that data
        # If values were already set (e.g., by from_consumed_packets), preserve them
        if self.packet_metrics:
            delivered_packets = [p for p in self.packet_metrics if p.delivered]
            
            self.total_packets_delivered = len(delivered_packets)
            self.total_packets_in_flight = self.total_packets_injected - self.total_packets_delivered
            
            if delivered_packets:
                self.latencies = [p.latency for p in delivered_packets if p.latency is not None]
                self.hop_counts = [p.hop_count for p in delivered_packets]
                
                if self.latencies:
                    self.min_latency = min(self.latencies)
                    self.max_latency = max(self.latencies)
                    self.avg_latency = mean(self.latencies)
                    self.median_latency = median(self.latencies)
                    if len(self.latencies) > 1:
                        self.latency_std_dev = stdev(self.latencies)
                
                if self.hop_counts:
                    self.min_hops = min(self.hop_counts)
                    self.max_hops = max(self.hop_counts)
                    self.avg_hops = mean(self.hop_counts)
        
        # Calculate throughput (always update this)
        if self.total_simulation_cycles > 0 and self.total_packets_delivered > 0:
            self.packets_per_cycle = self.total_packets_delivered / self.total_simulation_cycles
        
        # Calculate execution time
        if self.start_time and self.end_time:
            self.execution_time_seconds = (self.end_time - self.start_time).total_seconds()
    
    def delivery_rate(self) -> float:
        """Calculate packet delivery rate as percentage"""
        if self.total_packets_injected == 0:
            return 0.0
        return (self.total_packets_delivered / self.total_packets_injected) * 100
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            'topology_type': self.topology_type,
            'total_nodes': self.total_nodes,
            'packets': {
                'injected': self.total_packets_injected,
                'delivered': self.total_packets_delivered,
                'in_flight': self.total_packets_in_flight,
                'delivery_rate_percent': round(self.delivery_rate(), 2)
            },
            'latency': {
                'min': self.min_latency,
                'max': self.max_latency,
                'avg': round(self.avg_latency, 2) if self.avg_latency else None,
                'median': round(self.median_latency, 2) if self.median_latency else None,
                'std_dev': round(self.latency_std_dev, 2) if self.latency_std_dev else None
            },
            'hops': {
                'min': self.min_hops,
                'max': self.max_hops,
                'avg': round(self.avg_hops, 2) if self.avg_hops else None
            },
            'throughput': {
                'packets_per_cycle': round(self.packets_per_cycle, 4) if self.packets_per_cycle else None
            },
            'simulation': {
                'total_cycles': self.total_simulation_cycles,
                'execution_time_seconds': round(self.execution_time_seconds, 3) if self.execution_time_seconds else None
            }
        }
    
    def summary_string(self) -> str:
        """Generate a human-readable summary"""
        lines = [
            f"=== {self.topology_type.upper()} Topology Metrics ===",
            f"Nodes: {self.total_nodes}",
            f"Packets: {self.total_packets_delivered}/{self.total_packets_injected} delivered ({self.delivery_rate():.1f}%)",
            f"Simulation Cycles: {self.total_simulation_cycles}",
            "",
            "Latency (cycles):",
            f"  Min: {self.min_latency}, Max: {self.max_latency}",
            f"  Avg: {self.avg_latency:.2f}" if self.avg_latency else "  Avg: N/A",
            f"  Median: {self.median_latency:.2f}" if self.median_latency else "  Median: N/A",
            "",
            "Hop Count:",
            f"  Min: {self.min_hops}, Max: {self.max_hops}",
            f"  Avg: {self.avg_hops:.2f}" if self.avg_hops else "  Avg: N/A",
            "",
            f"Throughput: {self.packets_per_cycle:.4f} packets/cycle" if self.packets_per_cycle else "Throughput: N/A",
            f"Execution Time: {self.execution_time_seconds:.3f} seconds" if self.execution_time_seconds else ""
        ]
        return "\n".join(lines)


class UnifiedMetricsCollector:
    """
    Collects and manages metrics for all topologies
    Provides standardized interface regardless of underlying topology implementation
    """
    
    def __init__(self):
        self.metrics: Dict[str, TopologyMetrics] = {}
        self.collection_start_time: Optional[datetime] = None
        self.collection_end_time: Optional[datetime] = None
        
    def initialize_topology(self, topology_type: str, total_nodes: int):
        """Initialize metrics collection for a topology"""
        self.metrics[topology_type] = TopologyMetrics(
            topology_type=topology_type,
            total_nodes=total_nodes
        )
        
    def start_collection(self):
        """Mark the start of metric collection"""
        self.collection_start_time = datetime.now()
        for metrics in self.metrics.values():
            metrics.start_time = self.collection_start_time
    
    def end_collection(self):
        """Mark the end of metric collection"""
        self.collection_end_time = datetime.now()
        for metrics in self.metrics.values():
            metrics.end_time = self.collection_end_time
            metrics.calculate_aggregates()
    
    def record_injection(self, topology_type: str, packet_id: str, 
                         source: Tuple[int, int], destination: Tuple[int, int],
                         injection_time: int):
        """Record a packet injection"""
        if topology_type not in self.metrics:
            return
        
        metric = PacketMetric(
            packet_id=packet_id,
            source=source,
            destination=destination,
            injection_time=injection_time,
            delivery_time=None,
            latency=None,
            hop_count=0,
            delivered=False
        )
        
        self.metrics[topology_type].packet_metrics.append(metric)
        self.metrics[topology_type].total_packets_injected += 1
    
    def record_delivery(self, topology_type: str, packet_id: str,
                        delivery_time: int, hop_count: int = 0):
        """Record a packet delivery"""
        if topology_type not in self.metrics:
            return
        
        # Find the packet metric and update it
        for packet_metric in self.metrics[topology_type].packet_metrics:
            if packet_metric.packet_id == packet_id:
                packet_metric.delivery_time = delivery_time
                packet_metric.latency = delivery_time - packet_metric.injection_time
                packet_metric.hop_count = hop_count
                packet_metric.delivered = True
                break
    
    def update_cycle_count(self, topology_type: str, cycle_count: int):
        """Update the total simulation cycles for a topology"""
        if topology_type in self.metrics:
            self.metrics[topology_type].total_simulation_cycles = cycle_count
    
    def get_metrics(self, topology_type: str) -> Optional[TopologyMetrics]:
        """Get metrics for a specific topology"""
        return self.metrics.get(topology_type)
    
    def get_all_metrics(self) -> Dict[str, TopologyMetrics]:
        """Get metrics for all topologies"""
        return self.metrics
    
    def to_json(self) -> str:
        """Export all metrics as JSON"""
        data = {
            'collection_start': self.collection_start_time.isoformat() if self.collection_start_time else None,
            'collection_end': self.collection_end_time.isoformat() if self.collection_end_time else None,
            'topologies': {
                topo_type: metrics.to_dict() 
                for topo_type, metrics in self.metrics.items()
            }
        }
        return json.dumps(data, indent=2)
    
    def summary(self) -> str:
        """Generate a summary of all collected metrics"""
        lines = ["=" * 60, "UNIFIED METRICS SUMMARY", "=" * 60, ""]
        
        for topology_type, metrics in self.metrics.items():
            lines.append(metrics.summary_string())
            lines.append("")
        
        return "\n".join(lines)


class TopologyMetricsAdapter:
    """
    Adapter to convert topology-specific metrics to unified format
    """
    
    @staticmethod
    def from_ricobit_metrics(simulation_metrics, topology_type: str = "ricobit") -> TopologyMetrics:
        """Convert RiCoBiT SimulationMetrics to TopologyMetrics"""
        metrics = TopologyMetrics(
            topology_type=topology_type,
            total_nodes=0  # Will be set separately
        )
        
        # Extract from SimulationMetrics
        metrics.total_packets_injected = simulation_metrics.total_injections
        metrics.total_packets_delivered = simulation_metrics.delivered_count
        metrics.total_packets_in_flight = simulation_metrics.in_flight_count
        
        metrics.avg_latency = simulation_metrics.average_latency()
        metrics.min_latency = simulation_metrics.min_latency()
        metrics.max_latency = simulation_metrics.max_latency()
        
        metrics.avg_hops = simulation_metrics.average_hop_count()
        metrics.max_hops = simulation_metrics.max_hop_count()
        
        metrics.packets_per_cycle = simulation_metrics.throughput()
        
        # Get raw data
        metrics.latencies = simulation_metrics._latencies
        metrics.hop_counts = simulation_metrics._hop_counts
        
        if metrics.latencies and len(metrics.latencies) > 0:
            metrics.median_latency = median(metrics.latencies)
            if len(metrics.latencies) > 1:
                metrics.latency_std_dev = stdev(metrics.latencies)
        
        return metrics
    
    @staticmethod
    def from_consumed_packets(consumed_packets: List, topology_type: str, 
                              total_injected: int, total_cycles: int) -> TopologyMetrics:
        """
        Create metrics from a list of consumed packets
        Used for Mesh and Torus topologies
        """
        metrics = TopologyMetrics(
            topology_type=topology_type,
            total_nodes=0  # Will be set separately
        )
        
        metrics.total_packets_injected = total_injected
        metrics.total_simulation_cycles = total_cycles
        
        latencies = []
        hop_counts = []
        
        for packet in consumed_packets:
            if hasattr(packet, 'start_timer') and hasattr(packet, 'end_timer'):
                if packet.end_timer >= 0:
                    latency = packet.end_timer - packet.start_timer
                    latencies.append(latency)
            
            if hasattr(packet, 'hops_traversed'):
                hop_counts.append(packet.hops_traversed)
        
        metrics.total_packets_delivered = len(latencies)
        metrics.total_packets_in_flight = total_injected - len(latencies)
        
        if latencies:
            metrics.min_latency = min(latencies)
            metrics.max_latency = max(latencies)
            metrics.avg_latency = mean(latencies)
            metrics.median_latency = median(latencies)
            if len(latencies) > 1:
                metrics.latency_std_dev = stdev(latencies)
            metrics.latencies = latencies
        
        if hop_counts:
            metrics.min_hops = min(hop_counts)
            metrics.max_hops = max(hop_counts)
            metrics.avg_hops = mean(hop_counts)
            metrics.hop_counts = hop_counts
        
        if total_cycles > 0:
            metrics.packets_per_cycle = len(latencies) / total_cycles
        
        return metrics
