#!/usr/bin/env python3
"""
Standalone Mesh Topology Simulation Runner
Runs mesh simulation and outputs results to a JSON file

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

from topology.mesh.enhanced_mesh_topology import EnhancedMeshTopology
from simulation.mesh.simulator import Simulator
from core.mesh.packet import Packet

# Import comprehensive metrics
from unified_harness.network_metrics import (
    NetworkMetrics, PacketData, calculate_manhattan_distance
)


def run_mesh_simulation(config: dict) -> dict:
    """Run mesh topology simulation with comprehensive metrics"""
    
    print("=" * 60)
    print("MESH TOPOLOGY SIMULATION")
    print("=" * 60)
    
    result = {
        "topology": "mesh",
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
        
        width = config.get("width", 4)
        height = config.get("height", 4)
        buffer_capacity = config.get("buffer_capacity", 4)
        num_packets = config.get("num_packets", 100)
        max_cycles = config.get("max_cycles", 10000)
        
        print(f"Configuration:")
        print(f"  Grid Size: {width}x{height} ({width * height} nodes)")
        print(f"  Buffer Capacity: {buffer_capacity}")
        print(f"  Packets: {num_packets}")
        print(f"  Max Cycles: {max_cycles}")
        print()
        
        # Initialize comprehensive metrics
        metrics = NetworkMetrics(
            topology_type="mesh",
            total_nodes=width * height,
            grid_width=width,
            grid_height=height,
            buffer_capacity=buffer_capacity,
            max_cycles=max_cycles
        )
        
        # Create topology
        print("Creating Mesh topology...")
        topology = EnhancedMeshTopology(
            width=width,
            height=height,
            buffer_capacity=buffer_capacity
        )
        
        node_addresses = list(topology.nodes.keys())
        
        # Create simulator
        simulator = Simulator(topology)
        
        # Generate packets with tracking data
        print(f"\n--- Packet Source -> Destination Log (MESH) ---")
        packets = []
        packet_map = {}  # Map packet_id to PacketData
        
        for i in range(num_packets):
            src = random.choice(node_addresses)
            dst = random.choice([addr for addr in node_addresses if addr != src])
            
            packet = Packet(
                source_address=src,
                dest_address=dst,
                data=f"pkt_{i}",
                sim_clock=0
            )
            packets.append(packet)
            
            # Track packet for metrics
            manhattan_dist = calculate_manhattan_distance(src, dst)
            packet_data = PacketData(
                packet_id=f"pkt_{i}",
                source=src,
                destination=dst,
                injection_cycle=0,
                manhattan_distance=manhattan_dist
            )
            metrics.packets.append(packet_data)
            packet_map[f"pkt_{i}"] = packet_data
            
            log_entry = {"packet_id": f"pkt_{i}", "src": str(src), "dst": str(dst)}
            result["packet_log"].append(log_entry)
            print(f"  Packet {i+1}: SRC={src} -> DST={dst} (Manhattan={manhattan_dist})")
        
        print(f"--- End of Packet Log (MESH) - Total: {len(packets)} packets ---\n")
        
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
            
            # Count delivered packets
            delivered = sum(
                len(node.consumed_packets) 
                for node in topology.nodes.values() 
                if hasattr(node, 'consumed_packets')
            )
            
            # Check if all delivered
            if delivered >= len(packets):
                metrics.simulation_completed = True
                break
            
            # Progress logging
            if cycles % 1000 == 0:
                print(f"  Cycle {cycles}: Delivered {delivered}/{len(packets)}")
        
        # Collect results and update metrics
        all_consumed = simulator.get_all_consumed_packets()
        
        # Update packet metrics with delivery information
        for pkt in all_consumed:
            pkt_id = getattr(pkt, 'data', None) or getattr(pkt, 'packet_id', None)
            if pkt_id in packet_map:
                packet_data = packet_map[pkt_id]
                packet_data.delivered = True
                
                # Get timing information
                if hasattr(pkt, 'start_timer') and hasattr(pkt, 'end_timer'):
                    if pkt.start_timer is not None and pkt.end_timer is not None:
                        packet_data.delivery_cycle = pkt.end_timer
                        packet_data.injection_cycle = pkt.start_timer
                
                # Get hop count if available
                if hasattr(pkt, 'hop_count'):
                    packet_data.hop_count = pkt.hop_count
                else:
                    # Estimate hop count from latency if not tracked
                    packet_data.hop_count = packet_data.manhattan_distance
        
        # Finalize metrics
        metrics.total_simulation_cycles = cycles
        metrics.execution_time_seconds = time.time() - start_time
        
        result["total_cycles"] = cycles
        result["packets_delivered"] = len(all_consumed)
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
        print(f"MESH SIMULATION COMPLETE")
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
    parser = argparse.ArgumentParser(description="Run Mesh Topology Simulation")
    parser.add_argument("--width", type=int, default=4, help="Grid width")
    parser.add_argument("--height", type=int, default=4, help="Grid height")
    parser.add_argument("--packets", type=int, default=100, help="Number of packets")
    parser.add_argument("--max-cycles", type=int, default=10000, help="Max simulation cycles")
    parser.add_argument("--buffer", type=int, default=4, help="Buffer capacity")
    parser.add_argument("--seed", type=int, help="Random seed")
    parser.add_argument("--output", type=str, default="mesh_results.json", help="Output file")
    
    args = parser.parse_args()
    
    config = {
        "width": args.width,
        "height": args.height,
        "num_packets": args.packets,
        "max_cycles": args.max_cycles,
        "buffer_capacity": args.buffer,
        "seed": args.seed
    }
    
    result = run_mesh_simulation(config)
    
    # Save results to file
    output_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results", args.output)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"\nResults saved to: {output_path}")
    
    return 0 if result["success"] else 1


if __name__ == "__main__":
    sys.exit(main())
