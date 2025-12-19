#!/usr/bin/env python3
"""
Standalone RiCoBiT Topology Simulation Runner
Runs RiCoBiT simulation and outputs results to a JSON file

Uses comprehensive network metrics with standard NoC formulas.
"""

import sys
import os
import json
import random
import argparse
import time
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from topology.ricobit.ricobit_topology import RiCoBiT_Topology
from simulation.ricobit.simulator import Simulator
from core.ricobit.packet import Packet

# Import comprehensive metrics
from unified_harness.network_metrics import (
    NetworkMetrics, PacketData
)


def run_ricobit_simulation(config: dict) -> dict:
    """Run RiCoBiT topology simulation with comprehensive metrics"""
    
    print("=" * 60)
    print("RiCoBiT TOPOLOGY SIMULATION")
    print("=" * 60)
    
    result = {
        "topology": "ricobit",
        "success": False,
        "error": None,
        "packets_injected": 0,
        "packets_delivered": 0,
        "total_cycles": 0,
        "packet_log": [],
        "metrics": {},
        "detailed_metrics": {}
    }
    
    start_time = time.time()
    
    try:
        # Set random seed if provided
        if config.get("seed") is not None:
            random.seed(config["seed"])
        
        num_levels = config.get("num_levels", 5)
        buffer_capacity = config.get("buffer_capacity", 4)
        num_packets = config.get("num_packets", 100)
        max_cycles = config.get("max_cycles", 10000)
        
        print(f"Configuration:")
        print(f"  Levels: {num_levels}")
        print(f"  Buffer Capacity: {buffer_capacity}")
        print(f"  Packets: {num_packets}")
        print(f"  Max Cycles: {max_cycles}")
        print()
        
        # Create topology
        print("Creating RiCoBiT topology...")
        topology = RiCoBiT_Topology(num_levels=num_levels)
        
        node_addresses = list(topology.nodes.keys())
        total_nodes = len(node_addresses)
        
        print(f"  Total nodes: {total_nodes}")
        
        # Initialize comprehensive metrics
        metrics = NetworkMetrics(
            topology_type="ricobit",
            total_nodes=total_nodes,
            num_levels=num_levels,
            buffer_capacity=buffer_capacity,
            max_cycles=max_cycles
        )
        
        # Create simulator
        simulator = Simulator(topology)
        
        # Generate packets with tracking data
        print(f"\n--- Packet Source -> Destination Log (RICOBIT) ---")
        packets = []
        packet_map = {}  # Map packet_id to PacketData
        
        for i in range(num_packets):
            src = random.choice(node_addresses)
            dst = random.choice([addr for addr in node_addresses if addr != src])
            
            packet = Packet(
                source_address=src,
                dest_address=dst,
                data=f"pkt_{i}",
                sim_clock=0,
                packet_id=f"pkt_{i}"
            )
            packets.append(packet)
            
            # For RiCoBiT, estimate distance based on tree structure
            # Maximum distance is 2 * (num_levels - 1)
            estimated_dist = 2 * (num_levels - 1)
            
            packet_data = PacketData(
                packet_id=f"pkt_{i}",
                source=src,
                destination=dst,
                injection_cycle=0,
                manhattan_distance=estimated_dist  # Approximate for tree topology
            )
            metrics.packets.append(packet_data)
            packet_map[f"pkt_{i}"] = packet_data
            
            log_entry = {"packet_id": f"pkt_{i}", "src": str(src), "dst": str(dst)}
            result["packet_log"].append(log_entry)
            print(f"  Packet {i+1}: SRC={src} -> DST={dst}")
        
        print(f"--- End of Packet Log (RICOBIT) - Total: {len(packets)} packets ---\n")
        
        result["packets_injected"] = len(packets)
        
        # Inject all packets
        print("Injecting packets...")
        for packet in packets:
            simulator.inject_packet(packet)
        
        # Run simulation
        print("Running simulation...")
        cycles = 0
        
        while cycles < max_cycles:
            simulator.run_simulation_step()
            cycles += 1
            
            # Check if all delivered
            if simulator.metrics.delivered_count >= len(packets):
                metrics.simulation_completed = True
                break
            
            # Progress logging
            if cycles % 1000 == 0:
                print(f"  Cycle {cycles}: Delivered {simulator.metrics.delivered_count}/{len(packets)}")
        
        # Collect results from simulator metrics
        sim_metrics = simulator.metrics
        
        # Update packet metrics with delivery information from simulator
        # RiCoBiT uses _deliveries dict containing PacketDelivery objects
        for pkt_id, delivery in sim_metrics._deliveries.items():
            if pkt_id in packet_map:
                packet_data = packet_map[pkt_id]
                packet_data.delivered = True
                
                # Get timing information from injection record
                injection = sim_metrics._injections.get(pkt_id)
                if injection:
                    packet_data.injection_cycle = injection.start_clock
                packet_data.delivery_cycle = delivery.delivered_clock
                
                # Get hop count from delivery
                packet_data.hop_count = delivery.hop_count
        
        # Finalize metrics
        metrics.total_simulation_cycles = cycles
        metrics.execution_time_seconds = time.time() - start_time
        
        result["total_cycles"] = cycles
        result["packets_delivered"] = sim_metrics.delivered_count
        result["success"] = True
        
        # Get comprehensive metrics
        detailed = metrics.to_dict()
        result["detailed_metrics"] = detailed
        
        # Also provide legacy format for backward compatibility
        result["metrics"] = {
            "nodes": metrics.total_nodes,
            "delivery_rate": metrics.delivery_rate,
            "avg_latency": metrics.avg_latency,
            "min_latency": metrics.min_latency,
            "max_latency": metrics.max_latency,
            "median_latency": metrics.median_latency,
            "latency_std_dev": metrics.latency_std_dev,
            "jitter": metrics.jitter,
            "percentile_90": metrics.latency_percentile_90,
            "percentile_95": metrics.latency_percentile_95,
            "percentile_99": metrics.latency_percentile_99,
            "throughput": metrics.throughput_packets_per_cycle,
            "throughput_normalized": metrics.throughput_packets_per_node_per_cycle,
            "effective_bandwidth": metrics.effective_bandwidth,
            "accepted_traffic": metrics.accepted_traffic,
            "avg_hops": metrics.avg_hop_count,
            "min_hops": metrics.min_hop_count,
            "max_hops": metrics.max_hop_count,
            "routing_efficiency": metrics.avg_routing_efficiency,
            "latency_per_hop": metrics.latency_per_hop,
            "energy_proxy": metrics.energy_consumption_proxy,
            "network_load": metrics.network_load,
            "saturation_state": metrics.saturation_indicator,
            "scalability_factor": metrics.scalability_factor,
            "network_diameter": metrics.network_diameter,
        }
        
        print()
        print("=" * 60)
        print(f"RICOBIT SIMULATION COMPLETE")
        print(f"  Packets Delivered: {result['packets_delivered']}/{result['packets_injected']} ({metrics.delivery_rate:.1f}%)")
        print(f"  Total Cycles: {result['total_cycles']}")
        print(f"  Network State: {metrics.saturation_indicator}")
        print(f"  Avg Latency: {metrics.avg_latency:.2f} cycles")
        print(f"  Median Latency: {metrics.median_latency:.2f} cycles")
        print(f"  Latency Jitter: {metrics.jitter} cycles")
        print(f"  Throughput: {metrics.throughput_packets_per_cycle:.6f} packets/cycle")
        print(f"  Avg Hops: {metrics.avg_hop_count:.2f}")
        print(f"  Execution Time: {metrics.execution_time_seconds:.3f}s")
        print("=" * 60)
        
    except Exception as e:
        result["error"] = str(e)
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    return result


def main():
    parser = argparse.ArgumentParser(description="Run RiCoBiT Topology Simulation")
    parser.add_argument("--levels", type=int, default=5, help="Number of levels")
    parser.add_argument("--packets", type=int, default=100, help="Number of packets")
    parser.add_argument("--max-cycles", type=int, default=10000, help="Max simulation cycles")
    parser.add_argument("--buffer", type=int, default=4, help="Buffer capacity")
    parser.add_argument("--seed", type=int, help="Random seed")
    parser.add_argument("--output", type=str, default="ricobit_results.json", help="Output file")
    
    args = parser.parse_args()
    
    config = {
        "num_levels": args.levels,
        "num_packets": args.packets,
        "max_cycles": args.max_cycles,
        "buffer_capacity": args.buffer,
        "seed": args.seed
    }
    
    result = run_ricobit_simulation(config)
    
    # Save results to file
    output_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results", args.output)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"\nResults saved to: {output_path}")
    
    return 0 if result["success"] else 1


if __name__ == "__main__":
    sys.exit(main())
