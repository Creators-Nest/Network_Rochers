"""
Unified Simulation Runner
Runs simulations across all configured topologies and collects metrics
"""

import sys
import os
import random
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add parent path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .config import UnifiedConfig, TopologyType, TrafficPattern, TopologyConfig
from .metrics_collector import UnifiedMetricsCollector, TopologyMetrics, TopologyMetricsAdapter


class SimulationResult:
    """Container for simulation results from a single topology"""
    
    def __init__(self, topology_type: TopologyType):
        self.topology_type = topology_type
        self.success: bool = False
        self.error_message: Optional[str] = None
        self.metrics: Optional[TopologyMetrics] = None
        self.total_cycles: int = 0
        self.packets_delivered: int = 0
        self.packets_injected: int = 0


class UnifiedSimulationRunner:
    """
    Runs simulations across all three topology types with unified configuration
    and metrics collection
    """
    
    def __init__(self, config: UnifiedConfig):
        self.config = config
        self.metrics_collector = UnifiedMetricsCollector()
        self.results: Dict[TopologyType, SimulationResult] = {}
        
        # Set random seed if provided
        if config.simulation.random_seed is not None:
            random.seed(config.simulation.random_seed)
        
        self._log(f"Initialized UnifiedSimulationRunner", level=1)
        self._log(f"Configuration: {config.summary()}", level=2)
    
    def _log(self, message: str, level: int = 1):
        """Log message if verbosity allows"""
        if self.config.simulation.verbosity >= level:
            print(f"[Runner] {message}")
    
    def run_all(self) -> Dict[TopologyType, SimulationResult]:
        """
        Run simulations for all enabled topologies
        
        Returns:
            Dictionary mapping topology type to simulation results
        """
        self._log("=" * 60, level=1)
        self._log("STARTING UNIFIED SIMULATION", level=1)
        self._log("=" * 60, level=1)
        
        enabled_topologies = self.config.get_enabled_topologies()
        self._log(f"Enabled topologies: {[t.value for t in enabled_topologies]}", level=1)
        
        self.metrics_collector.start_collection()
        
        for topology_type in enabled_topologies:
            self._log(f"\n--- Running {topology_type.value.upper()} Simulation ---", level=1)
            
            try:
                result = self._run_single_topology(topology_type)
                self.results[topology_type] = result
                
                if result.success:
                    self._log(f"{topology_type.value}: SUCCESS - {result.packets_delivered}/{result.packets_injected} packets delivered in {result.total_cycles} cycles", level=1)
                else:
                    self._log(f"{topology_type.value}: FAILED - {result.error_message}", level=1)
                    
            except Exception as e:
                result = SimulationResult(topology_type)
                result.error_message = str(e)
                self.results[topology_type] = result
                self._log(f"{topology_type.value}: ERROR - {e}", level=1)
        
        self.metrics_collector.end_collection()
        
        self._log("\n" + "=" * 60, level=1)
        self._log("SIMULATION COMPLETE", level=1)
        self._log("=" * 60, level=1)
        
        return self.get_results_dict()
    
    def get_results_dict(self) -> Dict[str, Any]:
        """Get results as a dictionary suitable for JSON serialization"""
        results_dict = {}
        
        for topo_type, result in self.results.items():
            topo_name = topo_type.value if hasattr(topo_type, 'value') else str(topo_type)
            
            # Get metrics from metrics collector
            topo_metrics = self.metrics_collector.get_topology_metrics(topo_name)
            
            results_dict[topo_name] = {
                'success': result.success,
                'error_message': result.error_message,
                'metrics': {
                    'nodes': topo_metrics.nodes if topo_metrics else 0,
                    'packets_injected': result.packets_injected,
                    'packets_delivered': result.packets_delivered,
                    'delivery_rate': (result.packets_delivered / result.packets_injected * 100) if result.packets_injected > 0 else 0,
                    'total_cycles': result.total_cycles,
                    'avg_latency': topo_metrics.avg_latency if topo_metrics else 0,
                    'min_latency': topo_metrics.min_latency if topo_metrics else 0,
                    'max_latency': topo_metrics.max_latency if topo_metrics else 0,
                    'throughput': (result.packets_delivered / result.total_cycles) if result.total_cycles > 0 else 0
                }
            }
        
        return results_dict
    
    def _run_single_topology(self, topology_type: TopologyType) -> SimulationResult:
        """Run simulation for a single topology type"""
        result = SimulationResult(topology_type)
        
        if topology_type == TopologyType.MESH:
            return self._run_mesh_simulation()
        elif topology_type == TopologyType.RICOBIT:
            return self._run_ricobit_simulation()
        elif topology_type == TopologyType.TORUS:
            return self._run_torus_simulation()
        else:
            result.error_message = f"Unknown topology type: {topology_type}"
            return result
    
    def _run_mesh_simulation(self) -> SimulationResult:
        """Run Mesh topology simulation"""
        result = SimulationResult(TopologyType.MESH)
        
        try:
            # Import mesh-specific modules
            from topology.mesh.enhanced_mesh_topology import EnhancedMeshTopology
            from simulation.mesh.simulator import Simulator
            from core.mesh.packet import Packet
            
            config = self.config.mesh
            
            # Create topology
            self._log(f"Creating Mesh topology ({config.width}x{config.height})", level=2)
            topology = EnhancedMeshTopology(
                width=config.width,
                height=config.height,
                buffer_capacity=config.buffer_capacity
            )
            
            # Initialize metrics
            self.metrics_collector.initialize_topology("mesh", len(topology.nodes))
            
            # Create simulator
            simulator = Simulator(topology)
            
            # Generate packets
            packets = self._generate_packets_for_topology(
                list(topology.nodes.keys()),
                Packet,
                "mesh"
            )
            
            result.packets_injected = len(packets)
            
            # Inject all packets
            for packet in packets:
                simulator.inject_packet(packet)
                self.metrics_collector.record_injection(
                    "mesh",
                    str(id(packet)),
                    packet.source_address,
                    packet.dest_address,
                    simulator.global_clock
                )
            
            # Run simulation
            delivered = 0
            cycles = 0
            max_cycles = self.config.simulation.max_cycles
            
            while cycles < max_cycles:
                simulator.run_simulation_step()
                cycles += 1
                
                # Count delivered packets
                new_delivered = sum(
                    len(node.consumed_packets) 
                    for node in topology.nodes.values() 
                    if hasattr(node, 'consumed_packets')
                )
                
                # Check if all delivered
                if new_delivered >= len(packets):
                    break
                
                # Progress logging
                if cycles % 100 == 0:
                    self._log(f"Mesh: Cycle {cycles}, Delivered: {new_delivered}/{len(packets)}", level=3)
            
            # Collect all delivered packets (use simulator method to ensure end_timer is set)
            all_consumed = simulator.get_all_consumed_packets()
            
            # Convert to metrics
            result.metrics = TopologyMetricsAdapter.from_consumed_packets(
                all_consumed, "mesh", len(packets), cycles
            )
            result.metrics.total_nodes = len(topology.nodes)
            
            # Store metrics in collector for summary reporting
            self.metrics_collector.metrics["mesh"] = result.metrics
            
            result.total_cycles = cycles
            result.packets_delivered = len(all_consumed)
            result.success = True
            
            self.metrics_collector.update_cycle_count("mesh", cycles)
            
        except ImportError as e:
            result.error_message = f"Import error: {e}. Mesh modules may not be properly configured."
        except Exception as e:
            result.error_message = str(e)
        
        return result
    
    def _run_ricobit_simulation(self) -> SimulationResult:
        """Run RiCoBiT topology simulation"""
        result = SimulationResult(TopologyType.RICOBIT)
        
        try:
            # Import ricobit-specific modules
            from topology.ricobit.ricobit_topology import RiCoBiT_Topology
            from simulation.ricobit.simulator import Simulator
            from core.ricobit.packet import Packet
            
            config = self.config.ricobit
            
            # Create topology
            self._log(f"Creating RiCoBiT topology (levels={config.num_levels})", level=2)
            topology = RiCoBiT_Topology(num_levels=config.num_levels)
            
            # Initialize metrics
            self.metrics_collector.initialize_topology("ricobit", len(topology.nodes))
            
            # Create simulator
            simulator = Simulator(topology)
            
            # Generate packets
            packets = self._generate_packets_for_topology(
                list(topology.nodes.keys()),
                Packet,
                "ricobit"
            )
            
            result.packets_injected = len(packets)
            
            # Inject all packets
            for packet in packets:
                simulator.inject_packet(packet)
            
            # Run simulation
            cycles = 0
            max_cycles = self.config.simulation.max_cycles
            
            while cycles < max_cycles:
                simulator.run_simulation_step()
                cycles += 1
                
                # Check if all delivered
                if simulator.metrics.delivered_count >= len(packets):
                    break
                
                # Progress logging
                if cycles % 100 == 0:
                    self._log(f"RiCoBiT: Cycle {cycles}, Delivered: {simulator.metrics.delivered_count}/{len(packets)}", level=3)
            
            # Get metrics from simulator
            result.metrics = TopologyMetricsAdapter.from_ricobit_metrics(
                simulator.metrics, "ricobit"
            )
            result.metrics.total_nodes = len(topology.nodes)
            result.metrics.total_simulation_cycles = cycles
            
            # Store metrics in collector for summary reporting
            self.metrics_collector.metrics["ricobit"] = result.metrics
            
            result.total_cycles = cycles
            result.packets_delivered = simulator.metrics.delivered_count
            result.success = True
            
            self.metrics_collector.update_cycle_count("ricobit", cycles)
            
        except ImportError as e:
            result.error_message = f"Import error: {e}. RiCoBiT modules may not be properly configured."
        except Exception as e:
            result.error_message = str(e)
        
        return result
    
    def _run_torus_simulation(self) -> SimulationResult:
        """Run Torus topology simulation"""
        result = SimulationResult(TopologyType.TORUS)
        
        try:
            # Import torus-specific modules
            from topology.torus.enhanced_torus_topology import EnhancedTorusTopology
            from simulation.torus.simulator import Simulator
            from core.torus.packet import Packet
            
            config = self.config.torus
            
            # Create topology
            self._log(f"Creating Torus topology ({config.width}x{config.height})", level=2)
            topology = EnhancedTorusTopology(
                width=config.width,
                height=config.height,
                buffer_capacity=config.buffer_capacity
            )
            
            # Initialize metrics
            self.metrics_collector.initialize_topology("torus", len(topology.nodes))
            
            # Create simulator
            simulator = Simulator(topology)
            
            # Generate packets
            packets = self._generate_packets_for_topology(
                list(topology.nodes.keys()),
                Packet,
                "torus"
            )
            
            result.packets_injected = len(packets)
            
            # Inject all packets
            for packet in packets:
                simulator.inject_packet(packet)
                self.metrics_collector.record_injection(
                    "torus",
                    str(id(packet)),
                    packet.source_address,
                    packet.dest_address,
                    simulator.global_clock
                )
            
            # Run simulation
            delivered = 0
            cycles = 0
            max_cycles = self.config.simulation.max_cycles
            
            while cycles < max_cycles:
                simulator.run_simulation_step()
                cycles += 1
                
                # Count delivered packets
                new_delivered = sum(
                    len(node.consumed_packets) 
                    for node in topology.nodes.values() 
                    if hasattr(node, 'consumed_packets')
                )
                
                # Check if all delivered
                if new_delivered >= len(packets):
                    break
                
                # Progress logging
                if cycles % 100 == 0:
                    self._log(f"Torus: Cycle {cycles}, Delivered: {new_delivered}/{len(packets)}", level=3)
            
            # Collect all delivered packets (use simulator method to ensure end_timer is set)
            all_consumed = simulator.get_all_consumed_packets()
            
            # Convert to metrics
            result.metrics = TopologyMetricsAdapter.from_consumed_packets(
                all_consumed, "torus", len(packets), cycles
            )
            result.metrics.total_nodes = len(topology.nodes)
            
            # Store metrics in collector for summary reporting
            self.metrics_collector.metrics["torus"] = result.metrics
            
            result.total_cycles = cycles
            result.packets_delivered = len(all_consumed)
            result.success = True
            
            self.metrics_collector.update_cycle_count("torus", cycles)
            
        except ImportError as e:
            result.error_message = f"Import error: {e}. Torus modules may not be properly configured."
        except Exception as e:
            result.error_message = str(e)
        
        return result
    
    def _generate_packets_for_topology(self, node_addresses: List[Tuple], 
                                        packet_class, topology_name: str) -> List:
        """Generate packets based on configured traffic pattern"""
        packets = []
        num_packets = self.config.simulation.num_packets
        pattern = self.config.simulation.traffic_pattern
        
        self._log(f"Generating {num_packets} packets with pattern: {pattern.value}", level=2)
        self._log(f"--- Packet Source -> Destination Log ({topology_name.upper()}) ---", level=1)
        
        if pattern == TrafficPattern.UNIFORM_RANDOM:
            for i in range(num_packets):
                src = random.choice(node_addresses)
                dst = random.choice([addr for addr in node_addresses if addr != src])
                
                # Log source and destination
                self._log(f"  Packet {i+1}: SRC={src} -> DST={dst}", level=1)
                
                # Create packet based on topology type
                if topology_name == "ricobit":
                    packet = packet_class(
                        source_address=src,
                        dest_address=dst,
                        data=f"pkt_{i}",
                        sim_clock=0,
                        packet_id=f"pkt_{i}"
                    )
                else:
                    packet = packet_class(
                        source_address=src,
                        dest_address=dst,
                        data=f"pkt_{i}",
                        sim_clock=0
                    )
                packets.append(packet)
                
        elif pattern == TrafficPattern.NEAREST_NEIGHBOR:
            # Send packets to nearest neighbor only
            for i in range(num_packets):
                src = random.choice(node_addresses)
                # Find adjacent nodes (implementation depends on topology)
                if topology_name == "ricobit":
                    dst = random.choice([a for a in node_addresses if a != src])
                    self._log(f"  Packet {i+1}: SRC={src} -> DST={dst}", level=1)
                    packet = packet_class(
                        source_address=src,
                        dest_address=dst,
                        data=f"pkt_{i}",
                        sim_clock=0,
                        packet_id=f"pkt_{i}"
                    )
                else:
                    # For grid topologies, find adjacent
                    x, y = src
                    adjacent = []
                    for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                        adj = (x + dx, y + dy)
                        if adj in node_addresses:
                            adjacent.append(adj)
                    dst = random.choice(adjacent) if adjacent else random.choice([a for a in node_addresses if a != src])
                    self._log(f"  Packet {i+1}: SRC={src} -> DST={dst}", level=1)
                    packet = packet_class(
                        source_address=src,
                        dest_address=dst,
                        data=f"pkt_{i}",
                        sim_clock=0
                    )
                packets.append(packet)
                
        elif pattern == TrafficPattern.HOTSPOT:
            # All packets go to a single hotspot node
            hotspot = random.choice(node_addresses)
            self._log(f"Hotspot node: {hotspot}", level=2)
            self._log(f"  [HOTSPOT MODE] All packets destined to: {hotspot}", level=1)
            
            for i in range(num_packets):
                src = random.choice([addr for addr in node_addresses if addr != hotspot])
                self._log(f"  Packet {i+1}: SRC={src} -> DST={hotspot}", level=1)
                if topology_name == "ricobit":
                    packet = packet_class(
                        source_address=src,
                        dest_address=hotspot,
                        data=f"pkt_{i}",
                        sim_clock=0,
                        packet_id=f"pkt_{i}"
                    )
                else:
                    packet = packet_class(
                        source_address=src,
                        dest_address=hotspot,
                        data=f"pkt_{i}",
                        sim_clock=0
                    )
                packets.append(packet)
                
        elif pattern == TrafficPattern.LONGEST_NEIGHBOR:
            # This requires distance calculation which varies by topology
            # Fall back to uniform random for now with a note
            self._log("LONGEST_NEIGHBOR pattern requires topology-specific distance calculation. Using UNIFORM_RANDOM.", level=1)
            return self._generate_packets_for_topology(node_addresses, packet_class, topology_name)
        
        self._log(f"--- End of Packet Log ({topology_name.upper()}) - Total: {len(packets)} packets ---", level=1)
        return packets
    
    def get_metrics_collector(self) -> UnifiedMetricsCollector:
        """Get the metrics collector"""
        return self.metrics_collector
    
    def get_results_summary(self) -> Dict:
        """Get a summary of all simulation results"""
        summary = {}
        for topology_type, result in self.results.items():
            summary[topology_type.value] = {
                'success': result.success,
                'packets_injected': result.packets_injected,
                'packets_delivered': result.packets_delivered,
                'total_cycles': result.total_cycles,
                'error': result.error_message
            }
            if result.metrics:
                summary[topology_type.value]['metrics'] = result.metrics.to_dict()
        return summary
