#!/usr/bin/env python3
"""
Network Scalability Study
=========================
Compares network topologies across different sizes, similar to academic paper format.

This script generates results like Table 1 from NoC analysis papers:
- Starting with small networks (2x2 = 4 nodes)
- Scaling up to larger networks (8x8 = 64 nodes, 16x16 = 256 nodes)
- Comparing theoretical vs actual metrics

Output Tables (like the PDF paper):
- Table 1: Network Parameters for Different Sizes
- Table 2: Theoretical Hop Count Comparison
- Table 3: Latency Scaling Analysis  
- Table 4: Throughput Scaling Analysis
- Table 5: Overall Performance Summary

Reference Formulas:
- Mesh Max Hops: (W-1) + (H-1)
- Torus Max Hops: floor(W/2) + floor(H/2)
- RiCoBiT Max Hops: 2 × log₂(N+2) - 4 where N = number of nodes

Usage:
    python run_scalability_study.py                    # Run with defaults
    python run_scalability_study.py --min-size 2      # Start from 2x2
    python run_scalability_study.py --max-size 16     # Go up to 16x16
    python run_scalability_study.py --packets 100     # Packets per simulation
"""

import sys
import os
import json
import subprocess
import time
import argparse
import math
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class ScalabilityStudy:
    """
    Runs scalability analysis across different network sizes.
    
    This mimics the analysis done in NoC research papers comparing
    different topologies at various scales.
    """
    
    def __init__(self, config: dict):
        self.config = config
        self.results_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.all_results: Dict[str, Dict[int, dict]] = {
            "mesh": {},
            "torus": {},
            "ricobit": {}
        }
        
        # Create results directory
        os.makedirs(self.results_dir, exist_ok=True)
        
        # Network sizes to test: 2x2, 4x4, 8x8, 16x16 (optionally)
        self.sizes = self._generate_sizes()
    
    def _generate_sizes(self) -> List[int]:
        """Generate list of network sizes to test"""
        min_size = self.config.get("min_size", 2)
        max_size = self.config.get("max_size", 8)
        
        sizes = []
        size = min_size
        while size <= max_size:
            sizes.append(size)
            size *= 2  # Double each time: 2, 4, 8, 16
        
        return sizes
    
    def _get_ricobit_levels(self, grid_size: int) -> int:
        """
        Calculate RiCoBiT levels to match grid node count.
        RiCoBiT has 2^L - 1 nodes at level L
        """
        nodes = grid_size * grid_size
        # Find L such that 2^L - 1 >= nodes
        levels = max(2, int(math.ceil(math.log2(nodes + 1))))
        return levels
    
    # =====================================================================
    # THEORETICAL CALCULATIONS (from papers)
    # =====================================================================
    
    def _calc_theoretical_metrics(self, topology: str, grid_size: int) -> dict:
        """
        Calculate theoretical metrics based on formulas from NoC papers.
        
        These are the EXPECTED values based on network structure.
        """
        num_nodes = grid_size * grid_size
        
        if topology == "mesh":
            # Mesh: rectangular grid with no wraparound
            max_hops = (grid_size - 1) + (grid_size - 1)  # Corner to corner
            avg_hops = (grid_size + grid_size) / 3.0  # Average Manhattan distance
            
            # Bisection bandwidth (links crossing middle)
            bisection_bw = grid_size
            
            # Total links in mesh
            total_links = 2 * grid_size * (grid_size - 1)
            
        elif topology == "torus":
            # Torus: mesh with wraparound links
            max_hops = (grid_size // 2) + (grid_size // 2)  # Half due to wraparound
            avg_hops = (grid_size + grid_size) / 4.0  # Approximately
            
            # Bisection bandwidth (doubled due to wraparound)
            bisection_bw = 2 * grid_size
            
            # Total links in torus
            total_links = 2 * grid_size * grid_size
            
        elif topology == "ricobit":
            # RiCoBiT: Binary tree-based interconnect
            levels = self._get_ricobit_levels(grid_size)
            ricobit_nodes = (2 ** levels) - 1
            
            # H_c(Max) = 2 × log₂(N+2) - 4
            max_hops = max(0, int(2 * math.log2(ricobit_nodes + 2) - 4))
            
            # Average is approximately half of max
            avg_hops = max_hops / 2.0
            
            # Bisection bandwidth for tree
            bisection_bw = 1  # Single link at root
            
            # Total links = N - 1 for tree
            total_links = ricobit_nodes - 1
            num_nodes = ricobit_nodes  # Override
            
        else:
            return {}
        
        # Latency bounds (from RiCoBiT paper formula)
        p = 1  # Processing time
        buffer_cap = self.config.get("buffer", 4)
        t_arb = 2  # Arbitration time
        pipeline = 1  # Pipeline stages
        
        # L_p(min) = 2 × p × H_c(Max) + p
        latency_lower = 2 * p * max_hops + p
        
        # L_p(max) = {T_a + 2P} × (N_b + 2) × H_c(Max) + p
        latency_upper = (t_arb + 2 * pipeline) * (buffer_cap + 2) * max_hops + p
        
        # Throughput bounds (inverse of latency)
        throughput_lower = 1.0 / latency_upper if latency_upper > 0 else 0
        throughput_upper = 1.0 / latency_lower if latency_lower > 0 else 0
        
        return {
            "nodes": num_nodes,
            "max_hop_count": max_hops,
            "avg_hop_count": round(avg_hops, 2),
            "bisection_bandwidth": bisection_bw,
            "total_links": total_links,
            "latency_lower_bound": latency_lower,
            "latency_upper_bound": latency_upper,
            "throughput_lower_bound": round(throughput_lower, 6),
            "throughput_upper_bound": round(throughput_upper, 6),
            "degree": 4 if topology != "ricobit" else 3,  # Node degree
        }
    
    # =====================================================================
    # RUN SIMULATIONS
    # =====================================================================
    
    def _run_single_simulation(self, topology: str, grid_size: int) -> Optional[dict]:
        """Run a single simulation for given topology and size"""
        python_exe = sys.executable
        runner_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "runners")
        
        output_file = f"{topology}_scale_{grid_size}x{grid_size}_{self.timestamp}.json"
        output_path = os.path.join(self.results_dir, output_file)
        
        num_packets = self.config.get("num_packets", 100)
        max_cycles = self.config.get("max_cycles", 10000)
        buffer_cap = self.config.get("buffer", 4)
        seed = self.config.get("seed", 42)
        
        # Build command based on topology
        if topology == "mesh":
            script = os.path.join(runner_dir, "run_mesh.py")
            cmd = [
                python_exe, script,
                "--width", str(grid_size),
                "--height", str(grid_size),
                "--packets", str(num_packets),
                "--max-cycles", str(max_cycles),
                "--buffer", str(buffer_cap),
                "--seed", str(seed),
                "--output", output_file
            ]
        elif topology == "torus":
            script = os.path.join(runner_dir, "run_torus.py")
            cmd = [
                python_exe, script,
                "--width", str(grid_size),
                "--height", str(grid_size),
                "--packets", str(num_packets),
                "--max-cycles", str(max_cycles),
                "--buffer", str(buffer_cap),
                "--seed", str(seed),
                "--output", output_file
            ]
        elif topology == "ricobit":
            levels = self._get_ricobit_levels(grid_size)
            script = os.path.join(runner_dir, "run_ricobit.py")
            cmd = [
                python_exe, script,
                "--levels", str(levels),
                "--packets", str(num_packets),
                "--max-cycles", str(max_cycles),
                "--buffer", str(buffer_cap),
                "--seed", str(seed),
                "--output", output_file
            ]
        else:
            return None
        
        print(f"  Running {topology.upper()} at {grid_size}x{grid_size}...", end=" ", flush=True)
        start_time = time.time()
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                cwd=os.path.dirname(os.path.abspath(__file__))
            )
            
            elapsed = time.time() - start_time
            
            if result.returncode == 0 and os.path.exists(output_path):
                with open(output_path, 'r') as f:
                    data = json.load(f)
                print(f"✓ ({elapsed:.1f}s)")
                return data
            else:
                print(f"✗ (failed)")
                if result.stderr:
                    print(f"    Error: {result.stderr[:200]}")
                return None
                
        except subprocess.TimeoutExpired:
            print(f"✗ (timeout)")
            return None
        except Exception as e:
            print(f"✗ ({str(e)[:50]})")
            return None
    
    def run_all_simulations(self):
        """Run simulations for all topologies and sizes"""
        print("\n" + "=" * 80)
        print("NETWORK SCALABILITY STUDY")
        print("=" * 80)
        print(f"Sizes to test: {[f'{s}x{s}' for s in self.sizes]}")
        print(f"Packets per test: {self.config.get('num_packets', 100)}")
        print(f"Random seed: {self.config.get('seed', 42)}")
        print("=" * 80 + "\n")
        
        topologies = ["mesh", "torus", "ricobit"]
        
        for size in self.sizes:
            print(f"\n{'='*40}")
            print(f"Network Size: {size}x{size} ({size*size} nodes)")
            print(f"{'='*40}")
            
            for topo in topologies:
                result = self._run_single_simulation(topo, size)
                if result:
                    # Store result with theoretical calculations
                    theoretical = self._calc_theoretical_metrics(topo, size)
                    result["theoretical"] = theoretical
                    self.all_results[topo][size] = result
    
    # =====================================================================
    # REPORT GENERATION (Paper-style tables)
    # =====================================================================
    
    def generate_report(self) -> str:
        """Generate comprehensive scalability report in paper format"""
        lines = []
        
        # Header
        lines.append("\n" + "=" * 80)
        lines.append("         NETWORK TOPOLOGY SCALABILITY ANALYSIS")
        lines.append(f"                  Generated: {self.timestamp}")
        lines.append("=" * 80)
        
        # ===================================================================
        # TABLE 1: Network Parameters - Separate sub-table for each size
        # ===================================================================
        lines.append("\n\nTABLE 1: NETWORK PARAMETERS AT DIFFERENT SCALES")
        lines.append("=" * 80)
        lines.append("(Similar to Table 1 from NoC analysis papers)\n")
        
        for size in self.sizes:
            lines.append(f"  Network Size: {size}x{size} ({size*size} nodes for Mesh/Torus)")
            lines.append("  " + "-" * 60)
            lines.append(f"  {'Parameter':<18} {'MESH':>12} {'TORUS':>12} {'RICOBIT':>12}")
            lines.append("  " + "-" * 60)
            
            params = ["Nodes", "Max Hops", "Avg Hops", "Total Links", "Bisection BW"]
            
            for param in params:
                mesh_data = self.all_results.get("mesh", {}).get(size, {}).get("theoretical", self._calc_theoretical_metrics("mesh", size))
                torus_data = self.all_results.get("torus", {}).get(size, {}).get("theoretical", self._calc_theoretical_metrics("torus", size))
                ricobit_data = self.all_results.get("ricobit", {}).get(size, {}).get("theoretical", self._calc_theoretical_metrics("ricobit", size))
                
                key_map = {"Nodes": "nodes", "Max Hops": "max_hop_count", "Avg Hops": "avg_hop_count", 
                           "Total Links": "total_links", "Bisection BW": "bisection_bandwidth"}
                key = key_map.get(param, "")
                
                mesh_val = mesh_data.get(key, 0)
                torus_val = torus_data.get(key, 0)
                ricobit_val = ricobit_data.get(key, 0)
                
                if isinstance(mesh_val, float):
                    lines.append(f"  {param:<18} {mesh_val:>12.2f} {torus_val:>12.2f} {ricobit_val:>12.2f}")
                else:
                    lines.append(f"  {param:<18} {mesh_val:>12} {torus_val:>12} {ricobit_val:>12}")
            
            lines.append("")
        
        # ===================================================================
        # TABLE 2: Theoretical vs Actual Hop Counts
        # ===================================================================
        lines.append("\nTABLE 2: HOP COUNT ANALYSIS (Theoretical vs Actual)")
        lines.append("=" * 80)
        lines.append("Shows how routing efficiency scales with network size\n")
        
        for size in self.sizes:
            lines.append(f"  Network Size: {size}x{size}")
            lines.append("  " + "-" * 60)
            lines.append(f"  {'Metric':<20} {'MESH':>12} {'TORUS':>12} {'RICOBIT':>12}")
            lines.append("  " + "-" * 60)
            
            hop_metrics = [
                ("Theoretical Max", "max_hop_count", "theoretical"),
                ("Actual Max Hops", "max_hops", "metrics"),
                ("Theoretical Avg", "avg_hop_count", "theoretical"),
                ("Actual Avg Hops", "avg_hops", "metrics"),
            ]
            
            for display, key, source in hop_metrics:
                row_vals = []
                for topo in ["mesh", "torus", "ricobit"]:
                    data = self.all_results.get(topo, {}).get(size, {})
                    if source == "theoretical":
                        val = data.get("theoretical", {}).get(key, 0)
                    else:
                        val = data.get("metrics", {}).get(key, 0)
                    row_vals.append(val)
                
                if any(isinstance(v, float) for v in row_vals):
                    lines.append(f"  {display:<20} {row_vals[0]:>12.2f} {row_vals[1]:>12.2f} {row_vals[2]:>12.2f}")
                else:
                    lines.append(f"  {display:<20} {row_vals[0]:>12} {row_vals[1]:>12} {row_vals[2]:>12}")
            
            lines.append("")
        
        # ===================================================================
        # TABLE 3: Latency Scaling
        # ===================================================================
        lines.append("\nTABLE 3: LATENCY SCALING ANALYSIS (cycles)")
        lines.append("=" * 80)
        lines.append("Lower bound: L_p(min) = 2×p×H_c(Max) + p")
        lines.append("Upper bound: L_p(max) = {T_a+2P}×(N_b+2)×H_c(Max) + p\n")
        
        for size in self.sizes:
            lines.append(f"  Network Size: {size}x{size}")
            lines.append("  " + "-" * 60)
            lines.append(f"  {'Metric':<20} {'MESH':>12} {'TORUS':>12} {'RICOBIT':>12}")
            lines.append("  " + "-" * 60)
            
            latency_metrics = [
                ("Latency Lower Bound", "latency_lower_bound", "theoretical"),
                ("Actual Min Latency", "min_latency", "metrics"),
                ("Latency Upper Bound", "latency_upper_bound", "theoretical"),
                ("Actual Max Latency", "max_latency", "metrics"),
                ("Actual Avg Latency", "avg_latency", "metrics"),
            ]
            
            for display, key, source in latency_metrics:
                row_vals = []
                for topo in ["mesh", "torus", "ricobit"]:
                    data = self.all_results.get(topo, {}).get(size, {})
                    if source == "theoretical":
                        val = data.get("theoretical", {}).get(key, 0)
                    else:
                        val = data.get("metrics", {}).get(key, 0)
                    row_vals.append(val if val else 0)
                
                lines.append(f"  {display:<20} {row_vals[0]:>12.1f} {row_vals[1]:>12.1f} {row_vals[2]:>12.1f}")
            
            lines.append("")
        
        # ===================================================================
        # TABLE 4: Throughput Scaling
        # ===================================================================
        lines.append("\nTABLE 4: THROUGHPUT SCALING ANALYSIS (packets/cycle)")
        lines.append("=" * 80)
        lines.append("τ_p(max) = 1/L_p(min), τ_p(min) = 1/L_p(max)\n")
        
        for size in self.sizes:
            lines.append(f"  Network Size: {size}x{size}")
            lines.append("  " + "-" * 60)
            lines.append(f"  {'Metric':<20} {'MESH':>12} {'TORUS':>12} {'RICOBIT':>12}")
            lines.append("  " + "-" * 60)
            
            throughput_metrics = [
                ("Throughput Upper", "throughput_upper_bound", "theoretical"),
                ("Throughput Lower", "throughput_lower_bound", "theoretical"),
                ("Actual Throughput", "throughput", "metrics"),
                ("Delivery Rate %", "delivery_rate", "metrics"),
            ]
            
            for display, key, source in throughput_metrics:
                row_vals = []
                for topo in ["mesh", "torus", "ricobit"]:
                    data = self.all_results.get(topo, {}).get(size, {})
                    if source == "theoretical":
                        val = data.get("theoretical", {}).get(key, 0)
                    else:
                        val = data.get("metrics", {}).get(key, 0)
                    row_vals.append(val if val else 0)
                
                # Format based on value magnitude
                if "Delivery" in display:
                    lines.append(f"  {display:<20} {row_vals[0]:>12.2f} {row_vals[1]:>12.2f} {row_vals[2]:>12.2f}")
                else:
                    lines.append(f"  {display:<20} {row_vals[0]:>12.4f} {row_vals[1]:>12.4f} {row_vals[2]:>12.4f}")
            
            lines.append("")
        
        lines.append("-" * 80)
        
        # ===================================================================
        # TABLE 5: Performance Summary (Winners at each scale)
        # ===================================================================
        lines.append("\nTABLE 5: PERFORMANCE WINNERS AT EACH SCALE")
        lines.append("=" * 80)
        lines.append("Best topology for each metric at each scale\n")
        
        header = f"  {'Metric':<22}"
        for size in self.sizes:
            header += f"   {size}x{size}"
        lines.append(header)
        lines.append("  " + "-" * 56)
        
        comparison_metrics = [
            ("Lowest Latency", "avg_latency", "lower"),
            ("Highest Throughput", "throughput", "higher"),
            ("Best Delivery Rate", "delivery_rate", "higher"),
            ("Fewest Hops", "avg_hops", "lower"),
            ("Best Efficiency", "routing_efficiency", "higher"),
        ]
        
        for display, key, direction in comparison_metrics:
            row = f"  {display:<22}"
            
            for size in self.sizes:
                values = {}
                for topo in ["mesh", "torus", "ricobit"]:
                    data = self.all_results.get(topo, {}).get(size, {})
                    val = data.get("metrics", {}).get(key, 0)
                    if val and val > 0:
                        values[topo] = val
                
                if values:
                    if direction == "lower":
                        sorted_vals = sorted(values.items(), key=lambda x: x[1])
                    else:
                        sorted_vals = sorted(values.items(), key=lambda x: x[1], reverse=True)
                    
                    winner = sorted_vals[0][0] if sorted_vals else "-"
                    row += f"  {winner.upper():>8}"
                else:
                    row += f"  {'-':>8}"
            
            lines.append(row)
        
        lines.append("")
        
        # ===================================================================
        # Overall Scalability Summary
        # ===================================================================
        lines.append("\n")
        lines.append("=" * 100)
        lines.append("SCALABILITY SUMMARY")
        lines.append("=" * 100)
        
        # Count wins at each scale
        wins = {topo: 0 for topo in ["mesh", "torus", "ricobit"]}
        
        for size in self.sizes:
            for _, key, direction in comparison_metrics:
                values = {}
                for topo in ["mesh", "torus", "ricobit"]:
                    data = self.all_results.get(topo, {}).get(size, {})
                    val = data.get("metrics", {}).get(key, 0)
                    if val and val > 0:
                        values[topo] = val
                
                if values:
                    if direction == "lower":
                        winner = min(values.items(), key=lambda x: x[1])[0]
                    else:
                        winner = max(values.items(), key=lambda x: x[1])[0]
                    wins[winner] += 1
        
        lines.append(f"\n  Total wins across all scales and metrics:")
        sorted_wins = sorted(wins.items(), key=lambda x: x[1], reverse=True)
        medals = ["🥇", "🥈", "🥉"]
        
        for i, (topo, count) in enumerate(sorted_wins):
            medal = medals[i] if i < 3 else "  "
            bar = "█" * count + "░" * (max(wins.values()) - count)
            lines.append(f"    {medal} {topo.upper():12}: {bar} {count} wins")
        
        lines.append(f"\n  🏆 BEST OVERALL SCALABILITY: {sorted_wins[0][0].upper()}")
        
        # Add key observations
        lines.append("\n" + "-" * 100)
        lines.append("KEY OBSERVATIONS:")
        lines.append("-" * 100)
        
        # Compare how latency scales
        lines.append("\n  Latency Scaling (small → large network):")
        for topo in ["mesh", "torus", "ricobit"]:
            small_lat = self.all_results.get(topo, {}).get(self.sizes[0], {}).get("metrics", {}).get("avg_latency", 0)
            large_lat = self.all_results.get(topo, {}).get(self.sizes[-1], {}).get("metrics", {}).get("avg_latency", 0)
            if small_lat and large_lat:
                ratio = large_lat / small_lat if small_lat > 0 else 0
                lines.append(f"    {topo.upper():12}: {small_lat:.1f} → {large_lat:.1f} cycles ({ratio:.1f}x increase)")
        
        # Compare how throughput scales
        lines.append("\n  Throughput Scaling (small → large network):")
        for topo in ["mesh", "torus", "ricobit"]:
            small_tp = self.all_results.get(topo, {}).get(self.sizes[0], {}).get("metrics", {}).get("throughput", 0)
            large_tp = self.all_results.get(topo, {}).get(self.sizes[-1], {}).get("metrics", {}).get("throughput", 0)
            if small_tp and large_tp:
                ratio = large_tp / small_tp if small_tp > 0 else 0
                lines.append(f"    {topo.upper():12}: {small_tp:.4f} → {large_tp:.4f} pkt/cycle ({ratio:.2f}x)")
        
        lines.append("\n" + "=" * 100)
        lines.append("THEORETICAL FORMULAS REFERENCE")
        lines.append("=" * 100)
        lines.append("""
  Network Diameter (Maximum Hop Count):
    • Mesh:    H_c(Max) = (width - 1) + (height - 1) = 2(n-1) for n×n grid
    • Torus:   H_c(Max) = floor(width/2) + floor(height/2) = n for n×n grid  
    • RiCoBiT: H_c(Max) = 2 × log₂(N + 2) - 4 where N = number of nodes

  Latency Bounds (from RiCoBiT paper):
    • Lower: L_p(min) = 2 × p × H_c(Max) + p
    • Upper: L_p(max) = {T_a(Max) + 2P} × (N_b + 2) × H_c(Max) + p

  Throughput Bounds:
    • Upper: τ_p(max) = 1 / L_p(min)
    • Lower: τ_p(min) = 1 / L_p(max)

  Parameters:
    p = packet processing time per hop (cycles)
    N_b = buffer capacity per node
    T_a(Max) = maximum arbitration time
    P = pipeline stages
""")
        lines.append("=" * 100)
        
        return "\n".join(lines)
    
    def save_results(self):
        """Save all results to JSON file"""
        output_data = {
            "timestamp": self.timestamp,
            "config": self.config,
            "sizes": self.sizes,
            "results": self.all_results
        }
        
        output_file = os.path.join(self.results_dir, f"scalability_study_{self.timestamp}.json")
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2, default=str)
        
        print(f"\n  JSON results saved to: {output_file}")
        
        # Save report
        report = self.generate_report()
        report_file = os.path.join(self.results_dir, f"scalability_report_{self.timestamp}.txt")
        with open(report_file, 'w') as f:
            f.write(report)
        
        print(f"  Report saved to: {report_file}")
        
        return report


def main():
    parser = argparse.ArgumentParser(
        description="Network Topology Scalability Study",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python run_scalability_study.py                     # Run with defaults (2x2 to 8x8)
    python run_scalability_study.py --min-size 2 --max-size 16   # Extended range
    python run_scalability_study.py --packets 200 --seed 42      # More packets
        """
    )
    
    parser.add_argument("--min-size", type=int, default=2,
                       help="Minimum grid size (default: 2 for 2x2)")
    parser.add_argument("--max-size", type=int, default=8,
                       help="Maximum grid size (default: 8 for 8x8)")
    parser.add_argument("--packets", type=int, default=100,
                       help="Number of packets per simulation (default: 100)")
    parser.add_argument("--max-cycles", type=int, default=10000,
                       help="Maximum simulation cycles (default: 10000)")
    parser.add_argument("--buffer", type=int, default=4,
                       help="Buffer capacity per node (default: 4)")
    parser.add_argument("--seed", type=int, default=42,
                       help="Random seed for reproducibility (default: 42)")
    
    args = parser.parse_args()
    
    config = {
        "min_size": args.min_size,
        "max_size": args.max_size,
        "num_packets": args.packets,
        "max_cycles": args.max_cycles,
        "buffer": args.buffer,
        "seed": args.seed
    }
    
    study = ScalabilityStudy(config)
    study.run_all_simulations()
    report = study.save_results()
    
    print(report)


if __name__ == "__main__":
    main()
