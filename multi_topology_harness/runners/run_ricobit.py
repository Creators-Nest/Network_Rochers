#!/usr/bin/env python3
"""
Standalone RiCoBiT Topology Simulation Runner
Runs RiCoBiT simulation and outputs results to a JSON file
"""

import sys
import os
import json
import random
import argparse
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from topology.ricobit.ricobit_topology import RiCoBiT_Topology
from simulation.ricobit.simulator import Simulator
from core.ricobit.packet import Packet


def run_ricobit_simulation(config: dict) -> dict:
    """Run RiCoBiT topology simulation"""
    
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
        "metrics": {}
    }
    
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
        
        print(f"  Total nodes: {len(node_addresses)}")
        
        # Create simulator
        simulator = Simulator(topology)
        
        # Generate packets
        print(f"\n--- Packet Source -> Destination Log (RICOBIT) ---")
        packets = []
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
                break
            
            # Progress logging
            if cycles % 100 == 0:
                print(f"  Cycle {cycles}: Delivered {simulator.metrics.delivered_count}/{len(packets)}")
        
        # Collect results
        metrics = simulator.metrics
        
        result["total_cycles"] = cycles
        result["packets_delivered"] = metrics.delivered_count
        result["success"] = True
        result["metrics"] = {
            "nodes": len(topology.nodes),
            "avg_latency": metrics.average_latency(),
            "min_latency": metrics.min_latency(),
            "max_latency": metrics.max_latency(),
            "throughput": metrics.delivered_count / cycles if cycles > 0 else 0,
            "delivery_rate": (metrics.delivered_count / len(packets) * 100) if packets else 0,
            "avg_hops": metrics.average_hop_count()
        }
        
        print()
        print("=" * 60)
        print(f"RICOBIT SIMULATION COMPLETE")
        print(f"  Packets Delivered: {result['packets_delivered']}/{result['packets_injected']}")
        print(f"  Total Cycles: {result['total_cycles']}")
        print(f"  Avg Latency: {result['metrics']['avg_latency']:.2f}")
        print(f"  Avg Hops: {result['metrics']['avg_hops']:.2f}")
        print(f"  Throughput: {result['metrics']['throughput']:.4f} packets/cycle")
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
