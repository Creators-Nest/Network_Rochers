#!/usr/bin/env python3
"""
Standalone Torus Topology Simulation Runner
Runs torus simulation and outputs results to a JSON file
"""

import sys
import os
import json
import random
import argparse
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from topology.torus.enhanced_torus_topology import EnhancedTorusTopology
from simulation.torus.simulator import Simulator
from core.torus.packet import Packet


def run_torus_simulation(config: dict) -> dict:
    """Run torus topology simulation"""
    
    print("=" * 60)
    print("TORUS TOPOLOGY SIMULATION")
    print("=" * 60)
    
    result = {
        "topology": "torus",
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
        
        # Create topology
        print("Creating Torus topology...")
        topology = EnhancedTorusTopology(
            width=width,
            height=height,
            buffer_capacity=buffer_capacity
        )
        
        node_addresses = list(topology.nodes.keys())
        
        # Create simulator
        simulator = Simulator(topology)
        
        # Generate packets
        print(f"\n--- Packet Source -> Destination Log (TORUS) ---")
        packets = []
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
            
            log_entry = {"packet_id": f"pkt_{i}", "src": str(src), "dst": str(dst)}
            result["packet_log"].append(log_entry)
            print(f"  Packet {i+1}: SRC={src} -> DST={dst}")
        
        print(f"--- End of Packet Log (TORUS) - Total: {len(packets)} packets ---\n")
        
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
                break
            
            # Progress logging
            if cycles % 100 == 0:
                print(f"  Cycle {cycles}: Delivered {delivered}/{len(packets)}")
        
        # Collect results
        all_consumed = simulator.get_all_consumed_packets()
        
        # Calculate latencies
        latencies = []
        for pkt in all_consumed:
            if hasattr(pkt, 'start_timer') and hasattr(pkt, 'end_timer'):
                if pkt.start_timer is not None and pkt.end_timer is not None:
                    latencies.append(pkt.end_timer - pkt.start_timer)
        
        result["total_cycles"] = cycles
        result["packets_delivered"] = len(all_consumed)
        result["success"] = True
        result["metrics"] = {
            "nodes": len(topology.nodes),
            "avg_latency": sum(latencies) / len(latencies) if latencies else 0,
            "min_latency": min(latencies) if latencies else 0,
            "max_latency": max(latencies) if latencies else 0,
            "throughput": len(all_consumed) / cycles if cycles > 0 else 0,
            "delivery_rate": (len(all_consumed) / len(packets) * 100) if packets else 0
        }
        
        print()
        print("=" * 60)
        print(f"TORUS SIMULATION COMPLETE")
        print(f"  Packets Delivered: {result['packets_delivered']}/{result['packets_injected']}")
        print(f"  Total Cycles: {result['total_cycles']}")
        print(f"  Avg Latency: {result['metrics']['avg_latency']:.2f}")
        print(f"  Throughput: {result['metrics']['throughput']:.4f} packets/cycle")
        print("=" * 60)
        
    except Exception as e:
        result["error"] = str(e)
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    return result


def main():
    parser = argparse.ArgumentParser(description="Run Torus Topology Simulation")
    parser.add_argument("--width", type=int, default=4, help="Grid width")
    parser.add_argument("--height", type=int, default=4, help="Grid height")
    parser.add_argument("--packets", type=int, default=100, help="Number of packets")
    parser.add_argument("--max-cycles", type=int, default=10000, help="Max simulation cycles")
    parser.add_argument("--buffer", type=int, default=4, help="Buffer capacity")
    parser.add_argument("--seed", type=int, help="Random seed")
    parser.add_argument("--output", type=str, default="torus_results.json", help="Output file")
    
    args = parser.parse_args()
    
    config = {
        "width": args.width,
        "height": args.height,
        "num_packets": args.packets,
        "max_cycles": args.max_cycles,
        "buffer_capacity": args.buffer,
        "seed": args.seed
    }
    
    result = run_torus_simulation(config)
    
    # Save results to file
    output_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results", args.output)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"\nResults saved to: {output_path}")
    
    return 0 if result["success"] else 1


if __name__ == "__main__":
    sys.exit(main())
