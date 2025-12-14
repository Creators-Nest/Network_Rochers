#!/usr/bin/env python3
"""
Parallel Multi-Topology Simulation Orchestrator
Launches each topology simulation in a separate terminal process and collects results

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
        """Generate a comparison report from all results"""
        
        report_file = os.path.join(self.results_dir, f"comparison_{self.timestamp}.txt")
        json_file = os.path.join(self.results_dir, f"comparison_{self.timestamp}.json")
        
        # Text report
        lines = []
        lines.append("=" * 70)
        lines.append("MULTI-TOPOLOGY SIMULATION COMPARISON REPORT")
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 70)
        lines.append("")
        
        # Summary table
        lines.append("-" * 70)
        lines.append(f"{'Metric':<25} {'MESH':>12} {'RICOBIT':>12} {'TORUS':>12}")
        lines.append("-" * 70)
        
        metrics_to_compare = [
            ("Nodes", "nodes"),
            ("Packets Injected", "packets_injected"),
            ("Packets Delivered", "packets_delivered"),
            ("Delivery Rate (%)", "delivery_rate"),
            ("Total Cycles", "total_cycles"),
            ("Avg Latency", "avg_latency"),
            ("Min Latency", "min_latency"),
            ("Max Latency", "max_latency"),
            ("Throughput", "throughput"),
        ]
        
        for display_name, key in metrics_to_compare:
            values = []
            for topo in ["mesh", "ricobit", "torus"]:
                result = self.results.get(topo, {})
                if key in ["packets_injected", "packets_delivered", "total_cycles"]:
                    val = result.get(key, 0)
                else:
                    val = result.get("metrics", {}).get(key, 0)
                
                if isinstance(val, float):
                    values.append(f"{val:.2f}")
                else:
                    values.append(str(val))
            
            lines.append(f"{display_name:<25} {values[0]:>12} {values[1]:>12} {values[2]:>12}")
        
        lines.append("-" * 70)
        lines.append("")
        
        # Determine winner
        lines.append("PERFORMANCE RANKING:")
        
        # Rank by throughput
        throughputs = []
        for topo in ["mesh", "ricobit", "torus"]:
            t = self.results.get(topo, {}).get("metrics", {}).get("throughput", 0)
            throughputs.append((topo, t))
        throughputs.sort(key=lambda x: x[1], reverse=True)
        
        lines.append(f"  By Throughput: {' > '.join([f'{t[0]}({t[1]:.4f})' for t in throughputs])}")
        
        # Rank by latency (lower is better)
        latencies = []
        for topo in ["mesh", "ricobit", "torus"]:
            l = self.results.get(topo, {}).get("metrics", {}).get("avg_latency", float('inf'))
            latencies.append((topo, l))
        latencies.sort(key=lambda x: x[1])
        
        lines.append(f"  By Avg Latency: {' < '.join([f'{l[0]}({l[1]:.2f})' for l in latencies])}")
        
        lines.append("")
        lines.append("=" * 70)
        
        report_text = "\n".join(lines)
        
        # Print to console
        print()
        print(report_text)
        
        # Save text report
        with open(report_file, 'w') as f:
            f.write(report_text)
        print(f"\nText report saved to: {report_file}")
        
        # Save JSON report
        combined_results = {
            "timestamp": self.timestamp,
            "config": self.config,
            "results": self.results
        }
        with open(json_file, 'w') as f:
            json.dump(combined_results, f, indent=2)
        print(f"JSON report saved to: {json_file}")


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
