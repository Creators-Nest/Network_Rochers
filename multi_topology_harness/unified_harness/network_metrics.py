"""
Network Simulation Metrics Module
=================================
Implements standard Network-on-Chip (NoC) performance metrics with proper formulas.

Key Performance Metrics:
------------------------
1. Latency Metrics - Measure delay from injection to delivery
2. Throughput Metrics - Measure network capacity utilization
3. Network Efficiency Metrics - Overall network performance
4. Hop Count Metrics - Routing path efficiency
5. Network Saturation Metrics - Congestion indicators

Standard Formulas Reference (from RiCoBiT Paper):
-------------------------------------------------
Maximum Hop Count (RiCoBiT): H_c(Max) = 2 × log₂(N_r + 2) - 4
    where N_r = number of nodes

Latency Bounds:
    Lower: L_p ≥ 2 × p × H_c(Max) + p
    Upper: L_p ≤ {T_a(Max) + 2P} × (N_b + 2) × H_c(Max) + p

Throughput Bounds:
    Lower: τ_p ≥ 1 / [{T_a(Max) + 2P} × (N_b + 2) × H_c(Max) + p]
    Upper: τ_p ≤ 1 / [2 × p × H_c(Max) + p]

Where:
    p = packet processing time per hop
    N_b = buffer capacity
    T_a(Max) = maximum arbitration time
    P = pipeline stages
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from statistics import mean, stdev, median, variance
import math


# === RICOBIT THEORETICAL FORMULAS ===

def ricobit_max_hop_count(num_nodes: int) -> int:
    """
    Maximum Hop Count for RiCoBiT topology
    H_c(Max) = 2 × log₂(N_r + 2) - 4
    
    From the paper: In a complete binary tree, the maximum distance
    from root to leaf is log₂(N_r + 1) - 1, so the total max distance
    between any two leaf nodes is 2 × log₂(N_r + 2) - 4
    
    Args:
        num_nodes: Total number of nodes in RiCoBiT topology (N_r)
    
    Returns:
        Maximum hop count (network diameter)
    """
    if num_nodes <= 1:
        return 0
    return max(0, int(2 * math.log2(num_nodes + 2) - 4))


def ricobit_avg_hop_count(num_nodes: int) -> float:
    """
    Average Hop Count for RiCoBiT topology
    H_c(Avg) = log₂(N_r + 2) - 2 (approximately half of max)
    
    Args:
        num_nodes: Total number of nodes
    
    Returns:
        Expected average hop count
    """
    if num_nodes <= 1:
        return 0.0
    return max(0.0, math.log2(num_nodes + 2) - 2)


def ricobit_latency_lower_bound(max_hops: int, p: int = 1) -> int:
    """
    Lower bound on latency for RiCoBiT
    L_p(min) = 2 × p × H_c(Max) + p
    
    This is the best-case latency assuming no contention.
    
    Args:
        max_hops: Maximum hop count H_c(Max)
        p: Packet processing time per hop (cycles)
    
    Returns:
        Minimum expected latency
    """
    return 2 * p * max_hops + p


def ricobit_latency_upper_bound(max_hops: int, buffer_capacity: int, 
                                 p: int = 1, t_arb_max: int = 2, pipeline_stages: int = 1) -> int:
    """
    Upper bound on latency for RiCoBiT
    L_p(max) = {T_a(Max) + 2P} × (N_b + 2) × H_c(Max) + p
    
    This is the worst-case latency with maximum contention.
    
    Args:
        max_hops: Maximum hop count H_c(Max)
        buffer_capacity: Buffer size per node (N_b)
        p: Packet processing time per hop
        t_arb_max: Maximum arbitration time
        pipeline_stages: Number of pipeline stages (P)
    
    Returns:
        Maximum expected latency
    """
    return (t_arb_max + 2 * pipeline_stages) * (buffer_capacity + 2) * max_hops + p


def ricobit_throughput_lower_bound(max_hops: int, buffer_capacity: int,
                                    p: int = 1, t_arb_max: int = 2, pipeline_stages: int = 1) -> float:
    """
    Lower bound on throughput for RiCoBiT
    τ_p(min) = 1 / [{T_a(Max) + 2P} × (N_b + 2) × H_c(Max) + p]
    
    Args:
        max_hops: Maximum hop count
        buffer_capacity: Buffer size per node
        p: Packet processing time
        t_arb_max: Maximum arbitration time
        pipeline_stages: Pipeline stages
    
    Returns:
        Minimum expected throughput (packets/cycle)
    """
    denominator = ricobit_latency_upper_bound(max_hops, buffer_capacity, p, t_arb_max, pipeline_stages)
    return 1.0 / denominator if denominator > 0 else 0.0


def ricobit_throughput_upper_bound(max_hops: int, p: int = 1) -> float:
    """
    Upper bound on throughput for RiCoBiT
    τ_p(max) = 1 / [2 × p × H_c(Max) + p]
    
    This is the best-case throughput with no contention.
    
    Args:
        max_hops: Maximum hop count
        p: Packet processing time
    
    Returns:
        Maximum expected throughput (packets/cycle)
    """
    denominator = ricobit_latency_lower_bound(max_hops, p)
    return 1.0 / denominator if denominator > 0 else 0.0


def mesh_max_hop_count(width: int, height: int) -> int:
    """
    Maximum Hop Count for Mesh topology (Network Diameter)
    H_mesh(Max) = (width - 1) + (height - 1)
    
    The longest path in a mesh is from one corner to the opposite corner.
    """
    return (width - 1) + (height - 1)


def mesh_avg_hop_count(width: int, height: int) -> float:
    """
    Average Hop Count for Mesh topology
    H_mesh(Avg) = (width + height) / 3
    
    Approximate average Manhattan distance for uniform traffic.
    """
    return (width + height) / 3.0


def torus_max_hop_count(width: int, height: int) -> int:
    """
    Maximum Hop Count for Torus topology (Network Diameter)
    H_torus(Max) = floor(width/2) + floor(height/2)
    
    With wraparound links, max distance is halved.
    """
    return (width // 2) + (height // 2)


def torus_avg_hop_count(width: int, height: int) -> float:
    """
    Average Hop Count for Torus topology
    H_torus(Avg) = (width + height) / 4
    
    Approximately half of mesh average due to wraparound.
    """
    return (width + height) / 4.0


@dataclass
class PacketData:
    """Complete packet tracking data for metrics calculation"""
    packet_id: str
    source: Tuple[int, int]
    destination: Tuple[int, int]
    injection_cycle: int
    delivery_cycle: Optional[int] = None
    hop_count: int = 0
    delivered: bool = False
    
    # Manhattan distance (minimum hops for mesh/torus)
    manhattan_distance: int = 0
    
    @property
    def latency(self) -> Optional[int]:
        """Packet latency = delivery_cycle - injection_cycle"""
        if self.delivered and self.delivery_cycle is not None:
            return self.delivery_cycle - self.injection_cycle
        return None
    
    @property
    def routing_efficiency(self) -> Optional[float]:
        """
        Routing Efficiency = manhattan_distance / actual_hop_count
        Perfect routing = 1.0, higher values indicate routing overhead
        """
        if self.delivered and self.hop_count > 0 and self.manhattan_distance > 0:
            return self.manhattan_distance / self.hop_count
        return None


@dataclass  
class NetworkMetrics:
    """
    Comprehensive Network Performance Metrics
    ==========================================
    
    All formulas are based on standard NoC performance evaluation methods.
    """
    
    topology_type: str
    total_nodes: int
    grid_width: Optional[int] = None
    grid_height: Optional[int] = None
    num_levels: Optional[int] = None  # For RiCoBiT
    buffer_capacity: int = 4
    
    # Packet tracking
    packets: List[PacketData] = field(default_factory=list)
    
    # Simulation parameters
    total_simulation_cycles: int = 0
    max_cycles: int = 0
    simulation_completed: bool = False
    
    # Execution time
    execution_time_seconds: float = 0.0
    
    # === PACKET STATISTICS ===
    
    @property
    def packets_injected(self) -> int:
        """Total number of packets injected into the network"""
        return len(self.packets)
    
    @property
    def packets_delivered(self) -> int:
        """Total number of packets successfully delivered"""
        return len([p for p in self.packets if p.delivered])
    
    @property
    def packets_in_flight(self) -> int:
        """Packets currently in the network (not yet delivered)"""
        return self.packets_injected - self.packets_delivered
    
    # === DELIVERY RATE METRICS ===
    
    @property
    def delivery_rate(self) -> float:
        """
        Delivery Rate (%) = (packets_delivered / packets_injected) × 100
        
        Measures the percentage of packets that successfully reach their destination.
        100% means all packets were delivered.
        """
        if self.packets_injected == 0:
            return 0.0
        return (self.packets_delivered / self.packets_injected) * 100
    
    @property
    def packet_loss_rate(self) -> float:
        """
        Packet Loss Rate (%) = (packets_not_delivered / packets_injected) × 100
        
        Inverse of delivery rate. 0% means no packets were lost.
        """
        return 100.0 - self.delivery_rate
    
    # === LATENCY METRICS ===
    
    @property
    def latencies(self) -> List[int]:
        """List of all delivered packet latencies"""
        return [p.latency for p in self.packets if p.latency is not None]
    
    @property
    def avg_latency(self) -> float:
        """
        Average Latency = Σ(latency_i) / N
        
        Where latency_i = delivery_cycle_i - injection_cycle_i
        N = number of delivered packets
        
        This is the mean time taken for packets to travel from source to destination.
        """
        lats = self.latencies
        return mean(lats) if lats else 0.0
    
    @property
    def min_latency(self) -> int:
        """Minimum observed latency (best case)"""
        lats = self.latencies
        return min(lats) if lats else 0
    
    @property
    def max_latency(self) -> int:
        """Maximum observed latency (worst case)"""
        lats = self.latencies
        return max(lats) if lats else 0
    
    @property
    def median_latency(self) -> float:
        """
        Median Latency - Middle value when latencies are sorted
        
        More robust to outliers than mean latency.
        """
        lats = self.latencies
        return median(lats) if lats else 0.0
    
    @property
    def latency_std_dev(self) -> float:
        """
        Latency Standard Deviation = √(Σ(latency_i - avg_latency)² / N)
        
        Measures consistency of delivery times.
        Lower values indicate more predictable network behavior.
        """
        lats = self.latencies
        return stdev(lats) if len(lats) > 1 else 0.0
    
    @property
    def latency_variance(self) -> float:
        """
        Latency Variance = Σ(latency_i - avg_latency)² / N
        
        Square of standard deviation.
        """
        lats = self.latencies
        return variance(lats) if len(lats) > 1 else 0.0
    
    @property
    def latency_percentile_90(self) -> float:
        """
        90th Percentile Latency
        
        90% of packets are delivered within this latency.
        Important for quality of service (QoS) guarantees.
        """
        lats = sorted(self.latencies)
        if not lats:
            return 0.0
        idx = int(0.9 * len(lats))
        return lats[min(idx, len(lats) - 1)]
    
    @property
    def latency_percentile_95(self) -> float:
        """95th Percentile Latency"""
        lats = sorted(self.latencies)
        if not lats:
            return 0.0
        idx = int(0.95 * len(lats))
        return lats[min(idx, len(lats) - 1)]
    
    @property
    def latency_percentile_99(self) -> float:
        """99th Percentile Latency - Tail latency"""
        lats = sorted(self.latencies)
        if not lats:
            return 0.0
        idx = int(0.99 * len(lats))
        return lats[min(idx, len(lats) - 1)]
    
    @property
    def jitter(self) -> float:
        """
        Jitter = max_latency - min_latency
        
        Measures the variability in network delay.
        Lower jitter = more consistent network performance.
        Also known as "latency range".
        """
        return self.max_latency - self.min_latency if self.latencies else 0
    
    @property
    def coefficient_of_variation(self) -> float:
        """
        Coefficient of Variation (CV) = (std_dev / mean) × 100
        
        Normalized measure of latency variability.
        Allows comparison across different average latencies.
        """
        if self.avg_latency > 0:
            return (self.latency_std_dev / self.avg_latency) * 100
        return 0.0
    
    # === THROUGHPUT METRICS ===
    
    @property
    def throughput_packets_per_cycle(self) -> float:
        """
        Throughput = packets_delivered / total_simulation_cycles
        
        Number of packets delivered per simulation cycle.
        Higher values indicate better network capacity utilization.
        """
        if self.total_simulation_cycles > 0:
            return self.packets_delivered / self.total_simulation_cycles
        return 0.0
    
    @property
    def throughput_packets_per_node_per_cycle(self) -> float:
        """
        Normalized Throughput = throughput / total_nodes
        
        Throughput normalized by network size.
        Allows fair comparison between different topology sizes.
        """
        if self.total_nodes > 0:
            return self.throughput_packets_per_cycle / self.total_nodes
        return 0.0
    
    @property
    def effective_bandwidth(self) -> float:
        """
        Effective Bandwidth (packets/cycle) = packets_delivered / cycles_to_complete
        
        Where cycles_to_complete = last_delivery_cycle - first_injection_cycle
        
        Measures the actual sustained throughput during active packet delivery.
        """
        delivered = [p for p in self.packets if p.delivered]
        if not delivered:
            return 0.0
        
        first_injection = min(p.injection_cycle for p in self.packets)
        last_delivery = max(p.delivery_cycle for p in delivered)
        
        active_cycles = last_delivery - first_injection
        if active_cycles > 0:
            return len(delivered) / active_cycles
        return 0.0
    
    @property
    def injection_rate(self) -> float:
        """
        Injection Rate = packets_injected / cycles_with_injections
        
        Rate at which packets were introduced into the network.
        """
        if self.packets:
            injection_cycles = len(set(p.injection_cycle for p in self.packets))
            if injection_cycles > 0:
                return self.packets_injected / injection_cycles
        return 0.0
    
    @property
    def accepted_traffic(self) -> float:
        """
        Accepted Traffic = packets_delivered / (total_nodes × total_cycles)
        
        Normalized measure of successfully delivered traffic.
        Standard metric for NoC saturation analysis.
        """
        if self.total_nodes > 0 and self.total_simulation_cycles > 0:
            return self.packets_delivered / (self.total_nodes * self.total_simulation_cycles)
        return 0.0
    
    # === HOP COUNT METRICS ===
    
    @property
    def hop_counts(self) -> List[int]:
        """List of hop counts for delivered packets"""
        return [p.hop_count for p in self.packets if p.delivered and p.hop_count > 0]
    
    @property
    def avg_hop_count(self) -> float:
        """
        Average Hop Count = Σ(hops_i) / N
        
        Average number of router-to-router transmissions.
        Indicates routing path length efficiency.
        """
        hops = self.hop_counts
        return mean(hops) if hops else 0.0
    
    @property
    def min_hop_count(self) -> int:
        """Minimum hop count (shortest path used)"""
        hops = self.hop_counts
        return min(hops) if hops else 0
    
    @property
    def max_hop_count(self) -> int:
        """Maximum hop count (longest path used)"""
        hops = self.hop_counts
        return max(hops) if hops else 0
    
    @property
    def hop_count_std_dev(self) -> float:
        """Standard deviation of hop counts"""
        hops = self.hop_counts
        return stdev(hops) if len(hops) > 1 else 0.0
    
    # === NETWORK EFFICIENCY METRICS ===
    
    @property
    def network_diameter(self) -> int:
        """
        Network Diameter (theoretical)
        
        For Mesh: (width - 1) + (height - 1)
        For Torus: floor(width/2) + floor(height/2)
        For RiCoBiT: 2 × (num_levels - 1)
        
        The maximum shortest path between any two nodes.
        """
        if self.topology_type.lower() == "mesh":
            if self.grid_width and self.grid_height:
                return (self.grid_width - 1) + (self.grid_height - 1)
        elif self.topology_type.lower() == "torus":
            if self.grid_width and self.grid_height:
                return (self.grid_width // 2) + (self.grid_height // 2)
        elif self.topology_type.lower() == "ricobit":
            if self.num_levels:
                return 2 * (self.num_levels - 1)
        return self.max_hop_count  # Fallback to observed max
    
    @property
    def avg_routing_efficiency(self) -> float:
        """
        Average Routing Efficiency = Σ(manhattan_dist_i / hops_i) / N
        
        Measures how close actual paths are to optimal (shortest) paths.
        1.0 = perfect routing (all packets took shortest paths)
        < 1.0 = routing overhead/detours
        """
        efficiencies = [p.routing_efficiency for p in self.packets 
                       if p.routing_efficiency is not None]
        return mean(efficiencies) if efficiencies else 0.0
    
    @property
    def energy_consumption_proxy(self) -> float:
        """
        Energy Consumption Proxy = Σ(hops_i) / packets_delivered
        
        Total hops represents energy consumed for routing.
        Lower is better (less energy per delivered packet).
        Note: This is a proxy, actual energy depends on hardware.
        """
        total_hops = sum(self.hop_counts)
        if self.packets_delivered > 0:
            return total_hops / self.packets_delivered
        return 0.0
    
    @property
    def latency_per_hop(self) -> float:
        """
        Latency Per Hop = avg_latency / avg_hop_count
        
        Average time spent at each hop (router processing + link delay).
        Lower values indicate faster per-hop processing.
        """
        if self.avg_hop_count > 0:
            return self.avg_latency / self.avg_hop_count
        return 0.0
    
    @property
    def network_load(self) -> float:
        """
        Network Load = packets_in_flight / (total_nodes × buffer_capacity)
        
        Measures current network congestion level.
        0.0 = empty network, 1.0 = fully saturated
        """
        max_capacity = self.total_nodes * self.buffer_capacity
        if max_capacity > 0:
            return self.packets_in_flight / max_capacity
        return 0.0
    
    @property
    def saturation_indicator(self) -> str:
        """
        Network saturation state based on delivery rate and latency.
        
        Categories:
        - "Undersaturated": delivery_rate > 95%, low latency
        - "Near Saturation": delivery_rate 80-95%, moderate latency  
        - "Saturated": delivery_rate 50-80%, high latency
        - "Oversaturated": delivery_rate < 50%, very high latency or packet loss
        """
        if self.delivery_rate >= 95:
            return "Undersaturated"
        elif self.delivery_rate >= 80:
            return "Near Saturation"
        elif self.delivery_rate >= 50:
            return "Saturated"
        else:
            return "Oversaturated"
    
    # === SCALABILITY METRICS ===
    
    @property
    def bisection_bandwidth_utilization(self) -> float:
        """
        Bisection Bandwidth Utilization estimate
        
        For grid topologies, bisection bandwidth = min(width, height) links
        Utilization = throughput / theoretical_bisection_bandwidth
        """
        if self.grid_width and self.grid_height:
            bisection_bw = min(self.grid_width, self.grid_height)
            if bisection_bw > 0:
                return self.throughput_packets_per_cycle / bisection_bw
        return 0.0
    
    @property
    def scalability_factor(self) -> float:
        """
        Scalability Factor = throughput / sqrt(total_nodes)
        
        Normalized throughput that accounts for network size growth.
        Useful for comparing performance across different network sizes.
        """
        if self.total_nodes > 0:
            return self.throughput_packets_per_cycle / math.sqrt(self.total_nodes)
        return 0.0
    
    # === THEORETICAL BOUNDS (from RiCoBiT paper formulas) ===
    
    @property
    def theoretical_max_hops(self) -> int:
        """
        Theoretical maximum hop count (network diameter) based on topology.
        
        Mesh: (width - 1) + (height - 1)
        Torus: floor(width/2) + floor(height/2)
        RiCoBiT: 2 × log₂(N_r + 2) - 4
        """
        if self.topology_type.lower() == "mesh":
            if self.grid_width and self.grid_height:
                return mesh_max_hop_count(self.grid_width, self.grid_height)
        elif self.topology_type.lower() == "torus":
            if self.grid_width and self.grid_height:
                return torus_max_hop_count(self.grid_width, self.grid_height)
        elif self.topology_type.lower() == "ricobit":
            return ricobit_max_hop_count(self.total_nodes)
        return 0
    
    @property
    def theoretical_avg_hops(self) -> float:
        """
        Theoretical average hop count based on topology.
        
        Mesh: (width + height) / 3
        Torus: (width + height) / 4
        RiCoBiT: log₂(N_r + 2) - 2
        """
        if self.topology_type.lower() == "mesh":
            if self.grid_width and self.grid_height:
                return mesh_avg_hop_count(self.grid_width, self.grid_height)
        elif self.topology_type.lower() == "torus":
            if self.grid_width and self.grid_height:
                return torus_avg_hop_count(self.grid_width, self.grid_height)
        elif self.topology_type.lower() == "ricobit":
            return ricobit_avg_hop_count(self.total_nodes)
        return 0.0
    
    @property
    def latency_lower_bound(self) -> int:
        """
        Theoretical lower bound on latency (best case, no contention).
        
        Based on: L_p(min) = 2 × p × H_c(Max) + p
        where p = 1 (single cycle per hop)
        """
        max_hops = self.theoretical_max_hops
        p = 1  # Processing time per hop
        return 2 * p * max_hops + p
    
    @property
    def latency_upper_bound(self) -> int:
        """
        Theoretical upper bound on latency (worst case, max contention).
        
        Based on: L_p(max) = {T_a(Max) + 2P} × (N_b + 2) × H_c(Max) + p
        """
        max_hops = self.theoretical_max_hops
        p = 1  # Processing time
        t_arb = 2  # Arbitration time
        pipeline = 1  # Pipeline stages
        return (t_arb + 2 * pipeline) * (self.buffer_capacity + 2) * max_hops + p
    
    @property
    def throughput_lower_bound(self) -> float:
        """
        Theoretical lower bound on throughput (worst case).
        
        τ_p(min) = 1 / L_p(max)
        """
        return 1.0 / self.latency_upper_bound if self.latency_upper_bound > 0 else 0.0
    
    @property
    def throughput_upper_bound(self) -> float:
        """
        Theoretical upper bound on throughput (best case).
        
        τ_p(max) = 1 / L_p(min)
        """
        return 1.0 / self.latency_lower_bound if self.latency_lower_bound > 0 else 0.0
    
    @property
    def overall_absorption_time(self) -> int:
        """
        Overall Absorption Time = sum of all packet latencies
        
        Total time for all packets to be absorbed (delivered).
        As defined in Table 3 of the RiCoBiT paper.
        """
        return sum(self.latencies)
    
    @property
    def absorption_efficiency(self) -> float:
        """
        Absorption Efficiency = theoretical_min_absorption / actual_absorption
        
        How close the absorption time is to theoretical minimum.
        1.0 = perfect, < 1.0 = overhead due to contention
        """
        if self.overall_absorption_time > 0:
            # Theoretical minimum = packets × (avg_hops × processing_time)
            min_absorption = self.packets_delivered * max(1, int(self.theoretical_avg_hops))
            return min_absorption / self.overall_absorption_time
        return 0.0
    
    # === TIMING METRICS ===
    
    @property
    def simulation_efficiency(self) -> float:
        """
        Simulation Efficiency = packets_delivered / execution_time_seconds
        
        Packets processed per wall-clock second.
        Higher = faster simulation (implementation efficiency).
        """
        if self.execution_time_seconds > 0:
            return self.packets_delivered / self.execution_time_seconds
        return 0.0
    
    @property
    def cycles_per_second(self) -> float:
        """Simulation cycles per wall-clock second"""
        if self.execution_time_seconds > 0:
            return self.total_simulation_cycles / self.execution_time_seconds
        return 0.0
    
    # === SUMMARY METHODS ===
    
    def to_dict(self) -> Dict[str, Any]:
        """Export all metrics as a dictionary"""
        return {
            "topology_info": {
                "type": self.topology_type,
                "total_nodes": self.total_nodes,
                "grid_width": self.grid_width,
                "grid_height": self.grid_height,
                "num_levels": self.num_levels,
                "buffer_capacity": self.buffer_capacity,
                "network_diameter": self.network_diameter,
            },
            "packet_statistics": {
                "packets_injected": self.packets_injected,
                "packets_delivered": self.packets_delivered,
                "packets_in_flight": self.packets_in_flight,
                "delivery_rate_percent": round(self.delivery_rate, 4),
                "packet_loss_rate_percent": round(self.packet_loss_rate, 4),
            },
            "latency_metrics": {
                "avg_latency": round(self.avg_latency, 4),
                "min_latency": self.min_latency,
                "max_latency": self.max_latency,
                "median_latency": round(self.median_latency, 4),
                "std_dev": round(self.latency_std_dev, 4),
                "variance": round(self.latency_variance, 4),
                "jitter": self.jitter,
                "coefficient_of_variation": round(self.coefficient_of_variation, 4),
                "percentile_90": round(self.latency_percentile_90, 4),
                "percentile_95": round(self.latency_percentile_95, 4),
                "percentile_99": round(self.latency_percentile_99, 4),
            },
            "throughput_metrics": {
                "throughput_packets_per_cycle": round(self.throughput_packets_per_cycle, 6),
                "throughput_normalized": round(self.throughput_packets_per_node_per_cycle, 8),
                "effective_bandwidth": round(self.effective_bandwidth, 6),
                "injection_rate": round(self.injection_rate, 4),
                "accepted_traffic": round(self.accepted_traffic, 8),
            },
            "hop_count_metrics": {
                "avg_hops": round(self.avg_hop_count, 4),
                "min_hops": self.min_hop_count,
                "max_hops": self.max_hop_count,
                "hop_std_dev": round(self.hop_count_std_dev, 4),
            },
            "efficiency_metrics": {
                "routing_efficiency": round(self.avg_routing_efficiency, 4),
                "latency_per_hop": round(self.latency_per_hop, 4),
                "energy_proxy": round(self.energy_consumption_proxy, 4),
                "network_load": round(self.network_load, 4),
                "saturation_state": self.saturation_indicator,
            },
            "scalability_metrics": {
                "bisection_utilization": round(self.bisection_bandwidth_utilization, 6),
                "scalability_factor": round(self.scalability_factor, 6),
            },
            "theoretical_bounds": {
                "max_hop_count": self.theoretical_max_hops,
                "avg_hop_count": round(self.theoretical_avg_hops, 4),
                "latency_lower_bound": self.latency_lower_bound,
                "latency_upper_bound": self.latency_upper_bound,
                "throughput_lower_bound": round(self.throughput_lower_bound, 8),
                "throughput_upper_bound": round(self.throughput_upper_bound, 8),
            },
            "absorption_metrics": {
                "overall_absorption_time": self.overall_absorption_time,
                "max_absorption_time": self.max_latency,
                "avg_absorption_time": round(self.avg_latency, 4),
                "absorption_efficiency": round(self.absorption_efficiency, 4),
            },
            "simulation_info": {
                "total_cycles": self.total_simulation_cycles,
                "max_cycles": self.max_cycles,
                "completed": self.simulation_completed,
                "execution_time_seconds": round(self.execution_time_seconds, 3),
                "simulation_efficiency": round(self.simulation_efficiency, 2),
                "cycles_per_second": round(self.cycles_per_second, 2),
            }
        }
    
    def summary_text(self) -> str:
        """Generate a human-readable summary report"""
        lines = [
            "=" * 70,
            f"NETWORK METRICS SUMMARY - {self.topology_type.upper()}",
            "=" * 70,
            "",
            "TOPOLOGY CONFIGURATION",
            "-" * 40,
            f"  Total Nodes: {self.total_nodes}",
        ]
        
        if self.grid_width and self.grid_height:
            lines.append(f"  Grid Size: {self.grid_width}×{self.grid_height}")
        if self.num_levels:
            lines.append(f"  Levels: {self.num_levels}")
        lines.append(f"  Buffer Capacity: {self.buffer_capacity}")
        lines.append(f"  Network Diameter: {self.network_diameter}")
        
        lines.extend([
            "",
            "PACKET DELIVERY",
            "-" * 40,
            f"  Injected:  {self.packets_injected}",
            f"  Delivered: {self.packets_delivered}",
            f"  In Flight: {self.packets_in_flight}",
            f"  Delivery Rate: {self.delivery_rate:.2f}%",
            f"  Network State: {self.saturation_indicator}",
            "",
            "LATENCY (cycles)",
            "-" * 40,
            f"  Average:    {self.avg_latency:.2f}",
            f"  Minimum:    {self.min_latency}",
            f"  Maximum:    {self.max_latency}",
            f"  Median:     {self.median_latency:.2f}",
            f"  Std Dev:    {self.latency_std_dev:.2f}",
            f"  Jitter:     {self.jitter}",
            f"  90th %ile:  {self.latency_percentile_90:.2f}",
            f"  95th %ile:  {self.latency_percentile_95:.2f}",
            f"  99th %ile:  {self.latency_percentile_99:.2f}",
            "",
            "THROUGHPUT",
            "-" * 40,
            f"  Packets/Cycle:           {self.throughput_packets_per_cycle:.6f}",
            f"  Packets/Node/Cycle:      {self.throughput_packets_per_node_per_cycle:.8f}",
            f"  Effective Bandwidth:     {self.effective_bandwidth:.6f}",
            f"  Accepted Traffic:        {self.accepted_traffic:.8f}",
            "",
            "HOP COUNT",
            "-" * 40,
            f"  Average: {self.avg_hop_count:.2f}",
            f"  Min/Max: {self.min_hop_count}/{self.max_hop_count}",
            f"  Std Dev: {self.hop_count_std_dev:.2f}",
            "",
            "EFFICIENCY",
            "-" * 40,
            f"  Routing Efficiency: {self.avg_routing_efficiency:.4f}",
            f"  Latency per Hop:    {self.latency_per_hop:.2f} cycles",
            f"  Energy Proxy:       {self.energy_consumption_proxy:.2f} hops/pkt",
            "",
            "SIMULATION",
            "-" * 40,
            f"  Total Cycles:     {self.total_simulation_cycles}",
            f"  Execution Time:   {self.execution_time_seconds:.3f} seconds",
            f"  Cycles/Second:    {self.cycles_per_second:.0f}",
            "",
            "=" * 70,
        ])
        
        return "\n".join(lines)


def calculate_manhattan_distance(src: Tuple[int, int], dst: Tuple[int, int]) -> int:
    """Calculate Manhattan distance between two points"""
    return abs(dst[0] - src[0]) + abs(dst[1] - src[1])


def calculate_torus_distance(src: Tuple[int, int], dst: Tuple[int, int], 
                            width: int, height: int) -> int:
    """
    Calculate minimum distance on a torus topology.
    Accounts for wraparound links.
    """
    dx = abs(dst[0] - src[0])
    dy = abs(dst[1] - src[1])
    
    # Consider wraparound
    dx = min(dx, width - dx)
    dy = min(dy, height - dy)
    
    return dx + dy


def create_comparison_table(metrics_list: List[NetworkMetrics]) -> Dict[str, Dict]:
    """
    Create a comparison table of key metrics across topologies.
    
    Returns a dictionary where:
    - keys are metric names
    - values are dicts mapping topology name -> value
    """
    if not metrics_list:
        return {}
    
    # Key metrics to compare (metric_name, property_name, better_direction)
    comparison_metrics = [
        ("Delivery Rate (%)", "delivery_rate", "higher"),
        ("Avg Latency (cycles)", "avg_latency", "lower"),
        ("Min Latency (cycles)", "min_latency", "lower"),
        ("Max Latency (cycles)", "max_latency", "lower"),
        ("Median Latency (cycles)", "median_latency", "lower"),
        ("Latency Std Dev", "latency_std_dev", "lower"),
        ("Jitter (cycles)", "jitter", "lower"),
        ("90th Percentile Latency", "latency_percentile_90", "lower"),
        ("Throughput (pkts/cycle)", "throughput_packets_per_cycle", "higher"),
        ("Normalized Throughput", "throughput_packets_per_node_per_cycle", "higher"),
        ("Effective Bandwidth", "effective_bandwidth", "higher"),
        ("Accepted Traffic", "accepted_traffic", "higher"),
        ("Avg Hop Count", "avg_hop_count", "lower"),
        ("Max Hop Count", "max_hop_count", "lower"),
        ("Routing Efficiency", "avg_routing_efficiency", "higher"),
        ("Latency per Hop", "latency_per_hop", "lower"),
        ("Energy Proxy (hops/pkt)", "energy_consumption_proxy", "lower"),
        ("Network Load", "network_load", "lower"),
        ("Scalability Factor", "scalability_factor", "higher"),
        ("Total Nodes", "total_nodes", "info"),
        ("Total Cycles", "total_simulation_cycles", "lower"),
    ]
    
    comparison = {}
    
    for metric_name, prop_name, direction in comparison_metrics:
        values = {}
        for m in metrics_list:
            try:
                value = getattr(m, prop_name)
                values[m.topology_type] = value
            except:
                values[m.topology_type] = None
        
        # Determine winner
        valid_values = {k: v for k, v in values.items() if v is not None and v != 0}
        winner = None
        
        if valid_values and direction != "info":
            if direction == "lower":
                winner = min(valid_values, key=valid_values.get)
            else:
                winner = max(valid_values, key=valid_values.get)
        
        comparison[metric_name] = {
            "values": values,
            "winner": winner,
            "better": direction
        }
    
    return comparison


def generate_comparison_report(metrics_list: List[NetworkMetrics], 
                               output_format: str = "text") -> str:
    """
    Generate a comprehensive comparison report.
    
    Args:
        metrics_list: List of NetworkMetrics objects to compare
        output_format: "text" or "markdown"
    
    Returns:
        Formatted comparison report string
    """
    if not metrics_list:
        return "No metrics to compare"
    
    comparison = create_comparison_table(metrics_list)
    topology_names = [m.topology_type for m in metrics_list]
    
    lines = []
    
    if output_format == "markdown":
        lines.append("# Network Topology Comparison Report\n")
        lines.append("## Overview\n")
        for m in metrics_list:
            lines.append(f"- **{m.topology_type}**: {m.total_nodes} nodes, "
                        f"{m.packets_delivered}/{m.packets_injected} delivered")
        lines.append("\n## Detailed Metrics Comparison\n")
        
        # Header
        header = "| Metric | " + " | ".join(topology_names) + " | Winner |"
        separator = "|" + "---|" * (len(topology_names) + 2)
        lines.append(header)
        lines.append(separator)
        
        for metric_name, data in comparison.items():
            row = f"| {metric_name} | "
            for topo in topology_names:
                val = data["values"].get(topo)
                if val is None:
                    row += "N/A | "
                elif isinstance(val, float):
                    row += f"{val:.4f} | "
                else:
                    row += f"{val} | "
            
            winner = data["winner"] or "N/A"
            row += f"{winner} |"
            lines.append(row)
    
    else:  # text format
        lines.append("=" * 90)
        lines.append("NETWORK TOPOLOGY COMPARISON REPORT")
        lines.append("=" * 90)
        lines.append("")
        
        # Overview
        lines.append("TOPOLOGY OVERVIEW")
        lines.append("-" * 90)
        for m in metrics_list:
            lines.append(f"  {m.topology_type:12}: {m.total_nodes:4} nodes, "
                        f"{m.packets_delivered:5}/{m.packets_injected:5} delivered "
                        f"({m.delivery_rate:.1f}%)")
        lines.append("")
        
        # Comparison table
        lines.append("METRICS COMPARISON")
        lines.append("-" * 90)
        
        # Calculate column widths
        col_width = 14
        metric_col = 30
        
        # Header
        header = f"{'Metric':<{metric_col}}"
        for topo in topology_names:
            header += f"{topo:>{col_width}}"
        header += f"{'Winner':>{col_width}}"
        lines.append(header)
        lines.append("-" * 90)
        
        for metric_name, data in comparison.items():
            row = f"{metric_name:<{metric_col}}"
            for topo in topology_names:
                val = data["values"].get(topo)
                if val is None:
                    row += f"{'N/A':>{col_width}}"
                elif isinstance(val, float):
                    if val >= 1000:
                        row += f"{val:>{col_width}.2f}"
                    elif val >= 1:
                        row += f"{val:>{col_width}.4f}"
                    else:
                        row += f"{val:>{col_width}.6f}"
                else:
                    row += f"{val:>{col_width}}"
            
            winner = data["winner"] or "N/A"
            row += f"{winner:>{col_width}}"
            lines.append(row)
        
        lines.append("-" * 90)
        lines.append("")
        
        # Winner summary
        lines.append("WINNER SUMMARY")
        lines.append("-" * 90)
        win_counts = {t: 0 for t in topology_names}
        for data in comparison.values():
            if data["winner"] and data["better"] != "info":
                win_counts[data["winner"]] = win_counts.get(data["winner"], 0) + 1
        
        total_metrics = len([d for d in comparison.values() if d["better"] != "info"])
        for topo, count in sorted(win_counts.items(), key=lambda x: x[1], reverse=True):
            pct = (count / total_metrics * 100) if total_metrics > 0 else 0
            bar = "█" * int(pct / 5)
            lines.append(f"  {topo:12}: {count:2}/{total_metrics} wins ({pct:5.1f}%) {bar}")
        
        lines.append("")
        lines.append("=" * 90)
    
    return "\n".join(lines)
