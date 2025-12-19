#!/usr/bin/env python3
"""
Parallel Multi-Topology Simulation Orchestrator
Launches each topology simulation in a separate terminal process and collects results

Enhanced with comprehensive NoC (Network-on-Chip) metrics following standard formulas:
- Latency: Average, Min, Max, Median, Percentiles (90th, 95th, 99th), Jitter, CV
- Throughput: Packets/cycle, Normalized, Effective Bandwidth
- Hop Count: Average, Min, Max, Routing Efficiency
- Network Load: Saturation Indicators, Energy Proxy, Scalability Factor

Usage:
    python run_parallel.py                    # Run with defaults
    python run_parallel.py --packets 500      # Custom packet count
    python run_parallel.py --seed 42          # Reproducible runs
"""

import sys
import os
import json
import subprocess
import time
import argparse
from datetime import datetime
from typing import Dict, List, Optional
import threading

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class ParallelSimulationOrchestrator:
    """Orchestrates parallel simulation runs across different topologies"""
    
    def __init__(self, config: dict):
        self.config = config
        self.results_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.processes: Dict[str, subprocess.Popen] = {}
        self.results: Dict[str, dict] = {}
        
        # Ensure results directory exists
        os.makedirs(self.results_dir, exist_ok=True)
    
    def _get_python_executable(self) -> str:
        """Get the Python executable path"""
        return sys.executable
    
    def _build_runner_command(self, topology: str) -> List[str]:
        """Build command for running a topology simulation"""
        python_exe = self._get_python_executable()
        runner_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "runners")
        
        output_file = f"{topology}_results_{self.timestamp}.json"
        
        if topology == "mesh":
            script = os.path.join(runner_dir, "run_mesh.py")
            cmd = [
                python_exe, script,
                "--width", str(self.config.get("mesh_width", 4)),
                "--height", str(self.config.get("mesh_height", 4)),
                "--packets", str(self.config.get("num_packets", 100)),
                "--max-cycles", str(self.config.get("max_cycles", 10000)),
                "--buffer", str(self.config.get("buffer_capacity", 4)),
                "--output", output_file
            ]
        elif topology == "ricobit":
            script = os.path.join(runner_dir, "run_ricobit.py")
            cmd = [
                python_exe, script,
                "--levels", str(self.config.get("ricobit_levels", 5)),
                "--packets", str(self.config.get("num_packets", 100)),
                "--max-cycles", str(self.config.get("max_cycles", 10000)),
                "--buffer", str(self.config.get("buffer_capacity", 4)),
                "--output", output_file
            ]
        elif topology == "torus":
            script = os.path.join(runner_dir, "run_torus.py")
            cmd = [
                python_exe, script,
                "--width", str(self.config.get("torus_width", 4)),
                "--height", str(self.config.get("torus_height", 4)),
                "--packets", str(self.config.get("num_packets", 100)),
                "--max-cycles", str(self.config.get("max_cycles", 10000)),
                "--buffer", str(self.config.get("buffer_capacity", 4)),
                "--output", output_file
            ]
        else:
            raise ValueError(f"Unknown topology: {topology}")
        
        # Add seed if provided
        if self.config.get("seed") is not None:
            cmd.extend(["--seed", str(self.config["seed"])])
        
        return cmd
    
    def _run_topology_process(self, topology: str) -> subprocess.Popen:
        """Start a subprocess for a topology simulation"""
        cmd = self._build_runner_command(topology)
        
        print(f"[{topology.upper()}] Starting process...")
        print(f"  Command: {' '.join(cmd)}")
        
        # Create log file for this topology
        log_file = os.path.join(self.results_dir, f"{topology}_log_{self.timestamp}.txt")
        
        with open(log_file, 'w') as log:
            process = subprocess.Popen(
                cmd,
                stdout=log,
                stderr=subprocess.STDOUT,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )
        
        return process
    
    def run_all_parallel(self, topologies: List[str] = None) -> Dict[str, dict]:
        """Run all topology simulations in parallel"""
        
        if topologies is None:
            topologies = ["mesh", "ricobit", "torus"]
        
        print("=" * 70)
        print("PARALLEL MULTI-TOPOLOGY SIMULATION")
        print("=" * 70)
        print(f"Timestamp: {self.timestamp}")
        print(f"Results Directory: {self.results_dir}")
        print(f"Topologies: {', '.join(topologies)}")
        print(f"Packets per topology: {self.config.get('num_packets', 100)}")
        print()
        
        # Start all processes
        print("--- LAUNCHING SIMULATIONS ---")
        start_time = time.time()
        
        for topology in topologies:
            try:
                self.processes[topology] = self._run_topology_process(topology)
            except Exception as e:
                print(f"[{topology.upper()}] ERROR: Failed to start - {e}")
        
        print()
        print("--- WAITING FOR COMPLETION ---")
        
        # Wait for all processes to complete
        for topology, process in self.processes.items():
            print(f"[{topology.upper()}] Waiting...", end=" ", flush=True)
            return_code = process.wait()
            status = "✓ DONE" if return_code == 0 else f"✗ FAILED (code {return_code})"
            print(status)
        
        elapsed_time = time.time() - start_time
        print(f"\nAll simulations completed in {elapsed_time:.2f} seconds")
        
        # Collect results
        print()
        print("--- COLLECTING RESULTS ---")
        self._collect_results(topologies)
        
        # Generate comparison report
        self._generate_comparison_report()
        
        return self.results
    
    def run_all_sequential(self, topologies: List[str] = None) -> Dict[str, dict]:
        """Run all topology simulations sequentially (alternative mode)"""
        
        if topologies is None:
            topologies = ["mesh", "ricobit", "torus"]
        
        print("=" * 70)
        print("SEQUENTIAL MULTI-TOPOLOGY SIMULATION")
        print("=" * 70)
        print(f"Timestamp: {self.timestamp}")
        print()
        
        start_time = time.time()
        
        for topology in topologies:
            print(f"\n{'='*60}")
            print(f"Running {topology.upper()} simulation...")
            print(f"{'='*60}")
            
            cmd = self._build_runner_command(topology)
            subprocess.run(cmd, cwd=os.path.dirname(os.path.abspath(__file__)))
        
        elapsed_time = time.time() - start_time
        print(f"\nAll simulations completed in {elapsed_time:.2f} seconds")
        
        # Collect results
        self._collect_results(topologies)
        self._generate_comparison_report()
        
        return self.results
    
    def _collect_results(self, topologies: List[str]):
        """Collect results from JSON files"""
        for topology in topologies:
            result_file = os.path.join(
                self.results_dir, 
                f"{topology}_results_{self.timestamp}.json"
            )
            
            if os.path.exists(result_file):
                with open(result_file, 'r') as f:
                    self.results[topology] = json.load(f)
                print(f"[{topology.upper()}] Results loaded from {result_file}")
            else:
                print(f"[{topology.upper()}] WARNING: Result file not found")
                self.results[topology] = {"success": False, "error": "Result file not found"}
    
    def _generate_comparison_report(self):
        """Generate a comprehensive comparison report from all results using standard NoC metrics"""
        
        report_file = os.path.join(self.results_dir, f"comparison_{self.timestamp}.txt")
        json_file = os.path.join(self.results_dir, f"comparison_{self.timestamp}.json")
        
        # Generate comprehensive text report using results dict
        report_text = self._create_comprehensive_report()
        
        # Print to console
        print()
        print(report_text)
        
        # Save text report
        with open(report_file, 'w') as f:
            f.write(report_text)
        print(f"\nComprehensive report saved to: {report_file}")
        
        # Save JSON report with detailed metrics
        combined_results = {
            "timestamp": self.timestamp,
            "config": self.config,
            "results": self.results,
            "comparison_summary": self._extract_comparison_summary()
        }
        with open(json_file, 'w') as f:
            json.dump(combined_results, f, indent=2)
        print(f"JSON report saved to: {json_file}")
    
    def _create_comprehensive_report(self) -> str:
        """Create comprehensive comparison report text matching RiCoBiT paper format"""
        topologies = ["mesh", "ricobit", "torus"]
        lines = []
        
        lines.append("=" * 110)
        lines.append("COMPREHENSIVE NETWORK TOPOLOGY COMPARISON REPORT")
        lines.append("Based on RiCoBiT Paper Metrics and Formulas")
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 110)
        lines.append("")
        
        # Configuration
        lines.append("SIMULATION CONFIGURATION")
        lines.append("-" * 110)
        lines.append(f"  Packets per Topology: {self.config.get('num_packets', 'N/A')}")
        lines.append(f"  Max Cycles: {self.config.get('max_cycles', 'N/A')}")
        lines.append(f"  Buffer Capacity (N_b): {self.config.get('buffer_capacity', 'N/A')}")
        lines.append(f"  Random Seed: {self.config.get('seed', 'None')}")
        lines.append(f"  Mesh Size: {self.config.get('mesh_width', 'N/A')}×{self.config.get('mesh_height', 'N/A')}")
        lines.append(f"  Torus Size: {self.config.get('torus_width', 'N/A')}×{self.config.get('torus_height', 'N/A')}")
        lines.append(f"  RiCoBiT Levels: {self.config.get('ricobit_levels', 'N/A')}")
        lines.append("")
        
        # ============================================================
        # TABLE 1 STYLE: Performance Comparison Summary
        # ============================================================
        lines.append("TABLE 1: PERFORMANCE COMPARISON SUMMARY")
        lines.append("=" * 110)
        
        col_width = 18
        lines.append(f"{'Metric':<30} {'MESH':>{col_width}} {'TORUS':>{col_width}} {'RiCoBiT':>{col_width}}")
        lines.append("-" * 110)
        
        # Extract metrics for table
        table1_metrics = [
            ("Number of Nodes", "nodes", ""),
            ("Packets Injected", None, "packets_injected"),
            ("Packets Delivered", None, "packets_delivered"),
            ("Delivery Rate (%)", "delivery_rate", ""),
            ("Total Cycles", None, "total_cycles"),
            ("Overall Absorption Time", None, "overall_absorption"),
            ("Max Absorption Time", "max_latency", ""),
            ("Average Absorption Time", "avg_latency", ""),
        ]
        
        for display_name, metric_key, result_key in table1_metrics:
            row = f"  {display_name:<28}"
            for topo in ["mesh", "torus", "ricobit"]:
                result = self.results.get(topo, {})
                if result_key:
                    if result_key == "overall_absorption":
                        # Sum of all latencies
                        detailed = result.get("detailed_metrics", {})
                        val = detailed.get("absorption_metrics", {}).get("overall_absorption_time", 0)
                    else:
                        val = result.get(result_key, 0)
                elif metric_key:
                    val = result.get("metrics", {}).get(metric_key, 0)
                else:
                    val = 0
                
                if isinstance(val, float):
                    row += f"{val:>{col_width}.2f}"
                else:
                    row += f"{val:>{col_width}}"
            lines.append(row)
        
        lines.append("-" * 110)
        lines.append("")
        
        # ============================================================
        # TABLE 3 STYLE: Absorption Time Comparison
        # ============================================================
        lines.append("TABLE 2: ABSORPTION TIME COMPARISON (cycles)")
        lines.append("=" * 110)
        lines.append(f"{'Topology':<15} {'Overall Absorption':>{col_width}} {'Maximum Time':>{col_width}} {'Average Time':>{col_width}}")
        lines.append("-" * 110)
        
        for topo in topologies:
            result = self.results.get(topo, {})
            detailed = result.get("detailed_metrics", {})
            
            overall = detailed.get("absorption_metrics", {}).get("overall_absorption_time", 0)
            max_time = result.get("metrics", {}).get("max_latency", 0)
            avg_time = result.get("metrics", {}).get("avg_latency", 0)
            
            lines.append(f"  {topo.upper():<13} {overall:>{col_width}} {max_time:>{col_width}} {avg_time:>{col_width}.2f}")
        
        lines.append("-" * 110)
        lines.append("")
        
        # ============================================================
        # TABLE 3: THEORETICAL BOUNDS vs ACTUAL
        # ============================================================
        lines.append("TABLE 3: THEORETICAL BOUNDS vs ACTUAL PERFORMANCE")
        lines.append("=" * 110)
        lines.append(f"{'Metric':<35} {'MESH':>{col_width}} {'TORUS':>{col_width}} {'RiCoBiT':>{col_width}}")
        lines.append("-" * 110)
        
        # Get theoretical bounds from detailed_metrics
        def get_theoretical(result, key):
            return result.get("detailed_metrics", {}).get("theoretical_bounds", {}).get(key, 0)
        
        def get_absorption(result, key):
            return result.get("detailed_metrics", {}).get("absorption_metrics", {}).get(key, 0)
        
        theoretical_metrics = [
            ("Theoretical Max Hops H_c(Max)", lambda r: get_theoretical(r, "max_hop_count")),
            ("Actual Max Hops (observed)", lambda r: r.get("metrics", {}).get("max_hops", 0)),
            ("Theoretical Avg Hops H_c(Avg)", lambda r: get_theoretical(r, "avg_hop_count")),
            ("Actual Avg Hops (observed)", lambda r: r.get("metrics", {}).get("avg_hops", 0)),
            ("Latency Lower Bound L_p(min)", lambda r: get_theoretical(r, "latency_lower_bound")),
            ("Actual Min Latency", lambda r: r.get("metrics", {}).get("min_latency", 0)),
            ("Latency Upper Bound L_p(max)", lambda r: get_theoretical(r, "latency_upper_bound")),
            ("Actual Max Latency", lambda r: r.get("metrics", {}).get("max_latency", 0)),
            ("Throughput Upper τ_p(max)", lambda r: get_theoretical(r, "throughput_upper_bound")),
            ("Actual Throughput", lambda r: r.get("metrics", {}).get("throughput", 0)),
        ]
        
        for display_name, getter in theoretical_metrics:
            row = f"  {display_name:<33}"
            for topo in ["mesh", "torus", "ricobit"]:
                result = self.results.get(topo, {})
                val = getter(result)
                
                if isinstance(val, float):
                    if val < 0.01 and val > 0:
                        row += f"{val:>{col_width}.6f}"
                    else:
                        row += f"{val:>{col_width}.4f}"
                else:
                    row += f"{val:>{col_width}}"
            lines.append(row)
        
        lines.append("-" * 110)
        lines.append("")
        
        # ============================================================
        # DETAILED LATENCY METRICS
        # ============================================================
        lines.append("TABLE 4: DETAILED LATENCY METRICS (cycles)")
        lines.append("=" * 110)
        lines.append(f"{'Metric':<30} {'MESH':>{col_width}} {'TORUS':>{col_width}} {'RiCoBiT':>{col_width}} {'Winner':>{col_width}}")
        lines.append("-" * 110)
        
        latency_metrics = [
            ("Average Latency", "avg_latency", "lower"),
            ("Minimum Latency", "min_latency", "lower"),
            ("Maximum Latency", "max_latency", "lower"),
            ("Median Latency", "median_latency", "lower"),
            ("Standard Deviation", "latency_std_dev", "lower"),
            ("Jitter (Max-Min)", "jitter", "lower"),
            ("90th Percentile", "percentile_90", "lower"),
            ("95th Percentile", "percentile_95", "lower"),
            ("99th Percentile", "percentile_99", "lower"),
        ]
        
        for display_name, key, direction in latency_metrics:
            values = {}
            row = f"  {display_name:<28}"
            for topo in ["mesh", "torus", "ricobit"]:
                result = self.results.get(topo, {})
                val = result.get("metrics", {}).get(key, 0)
                values[topo] = val
                if isinstance(val, float):
                    row += f"{val:>{col_width}.2f}"
                else:
                    row += f"{val:>{col_width}}"
            
            # Determine winner
            valid = {k: v for k, v in values.items() if v and v > 0}
            if valid:
                winner = min(valid.items(), key=lambda x: x[1])[0] if direction == "lower" else max(valid.items(), key=lambda x: x[1])[0]
                row += f"{winner:>{col_width}}"
            else:
                row += f"{'-':>{col_width}}"
            lines.append(row)
        
        lines.append("-" * 110)
        lines.append("")
        
        # ============================================================
        # THROUGHPUT METRICS
        # ============================================================
        lines.append("TABLE 5: THROUGHPUT METRICS")
        lines.append("=" * 110)
        lines.append(f"{'Metric':<30} {'MESH':>{col_width}} {'TORUS':>{col_width}} {'RiCoBiT':>{col_width}} {'Winner':>{col_width}}")
        lines.append("-" * 110)
        
        throughput_metrics = [
            ("Throughput (pkt/cycle)", "throughput", "higher"),
            ("Normalized Throughput", "throughput_normalized", "higher"),
            ("Effective Bandwidth", "effective_bandwidth", "higher"),
            ("Accepted Traffic", "accepted_traffic", "higher"),
            ("Scalability Factor", "scalability_factor", "higher"),
        ]
        
        for display_name, key, direction in throughput_metrics:
            values = {}
            row = f"  {display_name:<28}"
            for topo in ["mesh", "torus", "ricobit"]:
                result = self.results.get(topo, {})
                val = result.get("metrics", {}).get(key, 0)
                values[topo] = val
                if isinstance(val, float):
                    row += f"{val:>{col_width}.6f}"
                else:
                    row += f"{val:>{col_width}}"
            
            valid = {k: v for k, v in values.items() if v and v > 0}
            if valid:
                winner = max(valid.items(), key=lambda x: x[1])[0]
                row += f"{winner:>{col_width}}"
            else:
                row += f"{'-':>{col_width}}"
            lines.append(row)
        
        lines.append("-" * 110)
        lines.append("")
        
        # ============================================================
        # HOP COUNT METRICS
        # ============================================================
        lines.append("TABLE 6: HOP COUNT AND ROUTING METRICS")
        lines.append("=" * 110)
        lines.append(f"{'Metric':<30} {'MESH':>{col_width}} {'TORUS':>{col_width}} {'RiCoBiT':>{col_width}} {'Winner':>{col_width}}")
        lines.append("-" * 110)
        
        hop_metrics = [
            ("Average Hop Count", "avg_hops", "lower"),
            ("Minimum Hop Count", "min_hops", "lower"),
            ("Maximum Hop Count", "max_hops", "lower"),
            ("Routing Efficiency", "routing_efficiency", "higher"),
            ("Latency Per Hop", "latency_per_hop", "lower"),
            ("Energy Proxy (hops/pkt)", "energy_proxy", "lower"),
        ]
        
        for display_name, key, direction in hop_metrics:
            values = {}
            row = f"  {display_name:<28}"
            for topo in ["mesh", "torus", "ricobit"]:
                result = self.results.get(topo, {})
                val = result.get("metrics", {}).get(key, 0)
                values[topo] = val
                if isinstance(val, float):
                    row += f"{val:>{col_width}.4f}"
                else:
                    row += f"{val:>{col_width}}"
            
            valid = {k: v for k, v in values.items() if v and v > 0}
            if valid:
                if direction == "lower":
                    winner = min(valid.items(), key=lambda x: x[1])[0]
                else:
                    winner = max(valid.items(), key=lambda x: x[1])[0]
                row += f"{winner:>{col_width}}"
            else:
                row += f"{'-':>{col_width}}"
            lines.append(row)
        
        lines.append("-" * 110)
        lines.append("")
        
        # ============================================================
        # OVERALL RANKING
        # ============================================================
        lines.append("=" * 110)
        lines.append("OVERALL PERFORMANCE RANKING")
        lines.append("=" * 110)
        
        # Calculate comprehensive scores
        scores = {topo: 0 for topo in topologies}
        all_metrics = [
            ("avg_latency", "lower"), ("throughput", "higher"), 
            ("delivery_rate", "higher"), ("jitter", "lower"),
            ("percentile_95", "lower"), ("avg_hops", "lower"),
            ("routing_efficiency", "higher"), ("scalability_factor", "higher"),
        ]
        
        for key, direction in all_metrics:
            values = {}
            for topo in topologies:
                val = self.results.get(topo, {}).get("metrics", {}).get(key)
                if val is not None and val > 0:
                    values[topo] = val
            
            if values:
                if direction == "lower":
                    ranked = sorted(values.items(), key=lambda x: x[1])
                else:
                    ranked = sorted(values.items(), key=lambda x: x[1], reverse=True)
                
                for i, (topo, _) in enumerate(ranked):
                    scores[topo] += (3 - i)
        
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        for i, (topo, score) in enumerate(sorted_scores):
            medal = ["🥇", "🥈", "🥉"][i] if i < 3 else "  "
            bar = "█" * (score // 2) + "░" * ((24 - score) // 2)
            lines.append(f"  {medal} {topo.upper():12}: {bar} {score:2d} points")
        
        lines.append("")
        winner = sorted_scores[0][0]
        lines.append(f"  🏆 BEST OVERALL TOPOLOGY: {winner.upper()}")
        lines.append("")
        
        # ============================================================
        # FORMULAS REFERENCE
        # ============================================================
        lines.append("=" * 110)
        lines.append("THEORETICAL FORMULAS (from RiCoBiT Paper)")
        lines.append("=" * 110)
        lines.append("")
        lines.append("  Maximum Hop Count:")
        lines.append("    Mesh:    H_c(Max) = (width - 1) + (height - 1)")
        lines.append("    Torus:   H_c(Max) = floor(width/2) + floor(height/2)")
        lines.append("    RiCoBiT: H_c(Max) = 2 × log₂(N_r + 2) - 4")
        lines.append("")
        lines.append("  Latency Bounds:")
        lines.append("    Lower: L_p(min) = 2 × p × H_c(Max) + p")
        lines.append("    Upper: L_p(max) = {T_a(Max) + 2P} × (N_b + 2) × H_c(Max) + p")
        lines.append("")
        lines.append("  Throughput Bounds:")
        lines.append("    Lower: τ_p(min) = 1 / L_p(max)")
        lines.append("    Upper: τ_p(max) = 1 / L_p(min)")
        lines.append("")
        lines.append("  Where: p = processing time, N_b = buffer capacity,")
        lines.append("         T_a = arbitration time, P = pipeline stages")
        lines.append("")
        lines.append("=" * 110)
        
        return "\n".join(lines)
    
    def _extract_comparison_summary(self) -> dict:
        """Extract comparison summary with rankings for each metric"""
        summary = {
            "rankings": {},
            "best_overall": None,
            "metric_winners": {}
        }
        
        topologies = ["mesh", "ricobit", "torus"]
        
        # Metrics where lower is better
        lower_better = ["avg_latency", "min_latency", "max_latency", "median_latency",
                       "latency_std_dev", "jitter", "percentile_90", "percentile_95", 
                       "percentile_99", "latency_per_hop", "energy_proxy", "network_load"]
        
        # Metrics where higher is better
        higher_better = ["delivery_rate", "throughput", "throughput_normalized",
                        "effective_bandwidth", "routing_efficiency", "scalability_factor"]
        
        scores = {topo: 0 for topo in topologies}
        
        for metric in lower_better + higher_better:
            values = {}
            for topo in topologies:
                result = self.results.get(topo, {})
                val = result.get("metrics", {}).get(metric, None)
                if val is not None and val != 0:
                    values[topo] = val
            
            if values:
                if metric in lower_better:
                    # Lower is better - sort ascending
                    ranked = sorted(values.items(), key=lambda x: x[1])
                else:
                    # Higher is better - sort descending
                    ranked = sorted(values.items(), key=lambda x: x[1], reverse=True)
                
                summary["rankings"][metric] = [t[0] for t in ranked]
                summary["metric_winners"][metric] = ranked[0][0] if ranked else None
                
                # Award points: 1st=3, 2nd=2, 3rd=1
                for i, (topo, _) in enumerate(ranked):
                    scores[topo] += (3 - i)
        
        # Determine overall best
        best_topo = max(scores.items(), key=lambda x: x[1])
        summary["best_overall"] = best_topo[0]
        summary["total_scores"] = scores
        
        return summary


def main():
    parser = argparse.ArgumentParser(
        description="Run Multi-Topology Simulations in Parallel",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_parallel.py --packets 100
  python run_parallel.py --packets 500 --seed 42
  python run_parallel.py --mesh-size 6 --torus-size 6 --ricobit-levels 5
  python run_parallel.py --sequential  # Run one after another instead of parallel
        """
    )
    
    # Simulation parameters
    parser.add_argument("--packets", "-n", type=int, default=100, help="Number of packets")
    parser.add_argument("--max-cycles", type=int, default=10000, help="Max cycles")
    parser.add_argument("--buffer", type=int, default=4, help="Buffer capacity")
    parser.add_argument("--seed", type=int, help="Random seed for reproducibility")
    
    # Topology sizes
    parser.add_argument("--mesh-size", type=int, default=4, help="Mesh grid size NxN")
    parser.add_argument("--mesh-width", type=int, help="Mesh width (overrides --mesh-size)")
    parser.add_argument("--mesh-height", type=int, help="Mesh height (overrides --mesh-size)")
    parser.add_argument("--torus-size", type=int, default=4, help="Torus grid size NxN")
    parser.add_argument("--torus-width", type=int, help="Torus width (overrides --torus-size)")
    parser.add_argument("--torus-height", type=int, help="Torus height (overrides --torus-size)")
    parser.add_argument("--ricobit-levels", type=int, default=5, help="RiCoBiT levels")
    
    # Topology selection
    parser.add_argument("--only", nargs="+", choices=["mesh", "ricobit", "torus"],
                       help="Run only specific topologies")
    
    # Execution mode
    parser.add_argument("--sequential", action="store_true", 
                       help="Run sequentially instead of parallel")
    
    args = parser.parse_args()
    
    config = {
        "num_packets": args.packets,
        "max_cycles": args.max_cycles,
        "buffer_capacity": args.buffer,
        "seed": args.seed,
        "mesh_width": args.mesh_width or args.mesh_size,
        "mesh_height": args.mesh_height or args.mesh_size,
        "torus_width": args.torus_width or args.torus_size,
        "torus_height": args.torus_height or args.torus_size,
        "ricobit_levels": args.ricobit_levels,
    }
    
    topologies = args.only if args.only else ["mesh", "ricobit", "torus"]
    
    orchestrator = ParallelSimulationOrchestrator(config)
    
    if args.sequential:
        orchestrator.run_all_sequential(topologies)
    else:
        orchestrator.run_all_parallel(topologies)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
