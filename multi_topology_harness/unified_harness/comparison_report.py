"""
Comparison Report Generator
Creates detailed comparison reports across all topology simulations
"""

import os
import json
import csv
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from .config import UnifiedConfig, TopologyType
from .metrics_collector import TopologyMetrics


@dataclass
class ComparisonMetric:
    """A single comparison metric across topologies"""
    metric_name: str
    mesh_value: Any
    ricobit_value: Any
    torus_value: Any
    winner: Optional[str] = None
    winner_by: str = "lower"  # "lower" or "higher" is better


class ComparisonReportGenerator:
    """
    Generates comparison reports across all topology types
    Supports multiple output formats: text, JSON, CSV
    """
    
    def __init__(self, config: UnifiedConfig, results: Dict[TopologyType, Any]):
        self.config = config
        self.results = results
        self.timestamp = datetime.now()
        self.comparisons: List[ComparisonMetric] = []
        
    def generate_all_reports(self, output_dir: Optional[str] = None) -> Dict[str, str]:
        """
        Generate all configured report formats
        
        Returns:
            Dictionary mapping format to file path
        """
        output_dir = output_dir or self.config.output.output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        report_files = {}
        timestamp_str = self.timestamp.strftime(self.config.output.timestamp_format)
        
        # Calculate comparisons
        self._calculate_comparisons()
        
        report_format = self.config.output.report_format
        
        if report_format in ['text', 'all']:
            filepath = os.path.join(output_dir, f"comparison_report_{timestamp_str}.txt")
            self._generate_text_report(filepath)
            report_files['text'] = filepath
            
        if report_format in ['json', 'all']:
            filepath = os.path.join(output_dir, f"comparison_report_{timestamp_str}.json")
            self._generate_json_report(filepath)
            report_files['json'] = filepath
            
        if report_format in ['csv', 'all']:
            filepath = os.path.join(output_dir, f"comparison_report_{timestamp_str}.csv")
            self._generate_csv_report(filepath)
            report_files['csv'] = filepath
        
        print(f"\n[Report] Generated reports in: {output_dir}")
        for fmt, path in report_files.items():
            print(f"  - {fmt.upper()}: {os.path.basename(path)}")
            
        return report_files
    
    def _calculate_comparisons(self):
        """Calculate comparison metrics across topologies"""
        self.comparisons = []
        
        # Get metrics for each topology
        mesh_metrics = self._get_metrics(TopologyType.MESH)
        ricobit_metrics = self._get_metrics(TopologyType.RICOBIT)
        torus_metrics = self._get_metrics(TopologyType.TORUS)
        
        # Node count comparison (informational)
        self._add_comparison(
            "Total Nodes",
            mesh_metrics.total_nodes if mesh_metrics else None,
            ricobit_metrics.total_nodes if ricobit_metrics else None,
            torus_metrics.total_nodes if torus_metrics else None,
            "higher"  # More nodes = more capacity
        )
        
        # Delivery rate comparison (higher is better)
        self._add_comparison(
            "Delivery Rate (%)",
            mesh_metrics.delivery_rate() if mesh_metrics else None,
            ricobit_metrics.delivery_rate() if ricobit_metrics else None,
            torus_metrics.delivery_rate() if torus_metrics else None,
            "higher"
        )
        
        # Average latency comparison (lower is better)
        self._add_comparison(
            "Average Latency (cycles)",
            mesh_metrics.avg_latency if mesh_metrics else None,
            ricobit_metrics.avg_latency if ricobit_metrics else None,
            torus_metrics.avg_latency if torus_metrics else None,
            "lower"
        )
        
        # Minimum latency comparison (lower is better)
        self._add_comparison(
            "Minimum Latency (cycles)",
            mesh_metrics.min_latency if mesh_metrics else None,
            ricobit_metrics.min_latency if ricobit_metrics else None,
            torus_metrics.min_latency if torus_metrics else None,
            "lower"
        )
        
        # Maximum latency comparison (lower is better)
        self._add_comparison(
            "Maximum Latency (cycles)",
            mesh_metrics.max_latency if mesh_metrics else None,
            ricobit_metrics.max_latency if ricobit_metrics else None,
            torus_metrics.max_latency if torus_metrics else None,
            "lower"
        )
        
        # Median latency comparison (lower is better)
        self._add_comparison(
            "Median Latency (cycles)",
            mesh_metrics.median_latency if mesh_metrics else None,
            ricobit_metrics.median_latency if ricobit_metrics else None,
            torus_metrics.median_latency if torus_metrics else None,
            "lower"
        )
        
        # Latency std dev (lower is better - more consistent)
        self._add_comparison(
            "Latency Std Dev",
            mesh_metrics.latency_std_dev if mesh_metrics else None,
            ricobit_metrics.latency_std_dev if ricobit_metrics else None,
            torus_metrics.latency_std_dev if torus_metrics else None,
            "lower"
        )
        
        # Average hop count (lower is better)
        self._add_comparison(
            "Average Hop Count",
            mesh_metrics.avg_hops if mesh_metrics else None,
            ricobit_metrics.avg_hops if ricobit_metrics else None,
            torus_metrics.avg_hops if torus_metrics else None,
            "lower"
        )
        
        # Maximum hop count (lower is better)
        self._add_comparison(
            "Maximum Hop Count",
            mesh_metrics.max_hops if mesh_metrics else None,
            ricobit_metrics.max_hops if ricobit_metrics else None,
            torus_metrics.max_hops if torus_metrics else None,
            "lower"
        )
        
        # Throughput comparison (higher is better)
        self._add_comparison(
            "Throughput (packets/cycle)",
            mesh_metrics.packets_per_cycle if mesh_metrics else None,
            ricobit_metrics.packets_per_cycle if ricobit_metrics else None,
            torus_metrics.packets_per_cycle if torus_metrics else None,
            "higher"
        )
        
        # Total simulation cycles (lower is better - faster completion)
        self._add_comparison(
            "Simulation Cycles",
            mesh_metrics.total_simulation_cycles if mesh_metrics else None,
            ricobit_metrics.total_simulation_cycles if ricobit_metrics else None,
            torus_metrics.total_simulation_cycles if torus_metrics else None,
            "lower"
        )
        
        # Execution time (lower is better)
        self._add_comparison(
            "Execution Time (seconds)",
            mesh_metrics.execution_time_seconds if mesh_metrics else None,
            ricobit_metrics.execution_time_seconds if ricobit_metrics else None,
            torus_metrics.execution_time_seconds if torus_metrics else None,
            "lower"
        )
    
    def _add_comparison(self, name: str, mesh_val: Any, ricobit_val: Any, 
                        torus_val: Any, winner_by: str):
        """Add a comparison metric and determine winner"""
        comparison = ComparisonMetric(
            metric_name=name,
            mesh_value=mesh_val,
            ricobit_value=ricobit_val,
            torus_value=torus_val,
            winner_by=winner_by
        )
        
        # Determine winner
        values = {
            "Mesh": mesh_val,
            "RiCoBiT": ricobit_val,
            "Torus": torus_val
        }
        
        valid_values = {k: v for k, v in values.items() if v is not None}
        
        if valid_values:
            if winner_by == "lower":
                comparison.winner = min(valid_values, key=valid_values.get)
            else:
                comparison.winner = max(valid_values, key=valid_values.get)
        
        self.comparisons.append(comparison)
    
    def _get_metrics(self, topology_type: TopologyType) -> Optional[TopologyMetrics]:
        """Get metrics for a topology type"""
        result = self.results.get(topology_type)
        if result and hasattr(result, 'metrics'):
            return result.metrics
        return None
    
    def _generate_text_report(self, filepath: str):
        """Generate a text-based comparison report"""
        lines = []
        
        # Header
        lines.append("=" * 80)
        lines.append("MULTI-TOPOLOGY NETWORK SIMULATION COMPARISON REPORT")
        lines.append("=" * 80)
        lines.append(f"Generated: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        # Configuration summary
        lines.append("-" * 80)
        lines.append("CONFIGURATION")
        lines.append("-" * 80)
        lines.append(f"Packets Injected: {self.config.simulation.num_packets}")
        lines.append(f"Traffic Pattern: {self.config.simulation.traffic_pattern.value}")
        lines.append(f"Max Cycles: {self.config.simulation.max_cycles}")
        lines.append("")
        
        # Topology configurations
        lines.append("Topology Configurations:")
        if self.config.mesh.enabled:
            lines.append(f"  Mesh: {self.config.mesh.width}x{self.config.mesh.height} grid, buffer={self.config.mesh.buffer_capacity}")
        if self.config.ricobit.enabled:
            lines.append(f"  RiCoBiT: {self.config.ricobit.num_levels} levels, buffer={self.config.ricobit.buffer_capacity}")
        if self.config.torus.enabled:
            lines.append(f"  Torus: {self.config.torus.width}x{self.config.torus.height} grid, buffer={self.config.torus.buffer_capacity}")
        lines.append("")
        
        # Comparison table
        lines.append("-" * 80)
        lines.append("METRIC COMPARISON")
        lines.append("-" * 80)
        
        # Table header
        header = f"{'Metric':<30} {'Mesh':>12} {'RiCoBiT':>12} {'Torus':>12} {'Winner':>12}"
        lines.append(header)
        lines.append("-" * 80)
        
        # Table rows
        for comp in self.comparisons:
            mesh_str = self._format_value(comp.mesh_value)
            ricobit_str = self._format_value(comp.ricobit_value)
            torus_str = self._format_value(comp.torus_value)
            winner_str = comp.winner or "N/A"
            
            row = f"{comp.metric_name:<30} {mesh_str:>12} {ricobit_str:>12} {torus_str:>12} {winner_str:>12}"
            lines.append(row)
        
        lines.append("-" * 80)
        lines.append("")
        
        # Summary analysis
        lines.append("-" * 80)
        lines.append("SUMMARY ANALYSIS")
        lines.append("-" * 80)
        
        # Count wins
        wins = {"Mesh": 0, "RiCoBiT": 0, "Torus": 0}
        for comp in self.comparisons:
            if comp.winner in wins:
                wins[comp.winner] += 1
        
        total_comparisons = len([c for c in self.comparisons if c.winner])
        
        lines.append("Performance Wins by Topology:")
        for topo, count in sorted(wins.items(), key=lambda x: x[1], reverse=True):
            pct = (count / total_comparisons * 100) if total_comparisons > 0 else 0
            lines.append(f"  {topo}: {count}/{total_comparisons} ({pct:.1f}%)")
        
        lines.append("")
        
        # Key insights
        lines.append("Key Insights:")
        
        # Find best for latency
        latency_comp = next((c for c in self.comparisons if c.metric_name == "Average Latency (cycles)"), None)
        if latency_comp and latency_comp.winner:
            lines.append(f"  - Lowest Average Latency: {latency_comp.winner}")
        
        # Find best for throughput
        throughput_comp = next((c for c in self.comparisons if c.metric_name == "Throughput (packets/cycle)"), None)
        if throughput_comp and throughput_comp.winner:
            lines.append(f"  - Highest Throughput: {throughput_comp.winner}")
        
        # Find best for hop count
        hop_comp = next((c for c in self.comparisons if c.metric_name == "Average Hop Count"), None)
        if hop_comp and hop_comp.winner:
            lines.append(f"  - Fewest Average Hops: {hop_comp.winner}")
        
        lines.append("")
        lines.append("=" * 80)
        lines.append("END OF REPORT")
        lines.append("=" * 80)
        
        # Write to file
        with open(filepath, 'w') as f:
            f.write('\n'.join(lines))
    
    def _generate_json_report(self, filepath: str):
        """Generate a JSON comparison report"""
        report = {
            "metadata": {
                "generated": self.timestamp.isoformat(),
                "report_type": "multi_topology_comparison"
            },
            "configuration": self.config.to_dict(),
            "comparisons": [
                {
                    "metric": comp.metric_name,
                    "mesh": comp.mesh_value,
                    "ricobit": comp.ricobit_value,
                    "torus": comp.torus_value,
                    "winner": comp.winner,
                    "optimization_direction": comp.winner_by
                }
                for comp in self.comparisons
            ],
            "results": {}
        }
        
        # Add detailed results for each topology
        for topo_type in [TopologyType.MESH, TopologyType.RICOBIT, TopologyType.TORUS]:
            result = self.results.get(topo_type)
            if result:
                report["results"][topo_type.value] = {
                    "success": result.success,
                    "packets_injected": result.packets_injected,
                    "packets_delivered": result.packets_delivered,
                    "total_cycles": result.total_cycles,
                    "error": result.error_message,
                    "metrics": result.metrics.to_dict() if result.metrics else None
                }
        
        # Summary statistics
        wins = {"mesh": 0, "ricobit": 0, "torus": 0}
        for comp in self.comparisons:
            if comp.winner:
                key = comp.winner.lower().replace("ricobit", "ricobit")
                if key in wins:
                    wins[key] += 1
        
        report["summary"] = {
            "performance_wins": wins,
            "total_metrics_compared": len(self.comparisons)
        }
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2, default=str)
    
    def _generate_csv_report(self, filepath: str):
        """Generate a CSV comparison report"""
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow(['Metric', 'Mesh', 'RiCoBiT', 'Torus', 'Winner', 'Better Is'])
            
            # Data rows
            for comp in self.comparisons:
                writer.writerow([
                    comp.metric_name,
                    self._format_value(comp.mesh_value),
                    self._format_value(comp.ricobit_value),
                    self._format_value(comp.torus_value),
                    comp.winner or 'N/A',
                    comp.winner_by
                ])
    
    def _format_value(self, value: Any) -> str:
        """Format a value for display"""
        if value is None:
            return "N/A"
        elif isinstance(value, float):
            return f"{value:.4f}"
        else:
            return str(value)
    
    def get_winner_summary(self) -> Dict[str, int]:
        """Get a summary of which topology won the most comparisons"""
        wins = {"Mesh": 0, "RiCoBiT": 0, "Torus": 0}
        for comp in self.comparisons:
            if comp.winner in wins:
                wins[comp.winner] += 1
        return wins
    
    def print_summary(self):
        """Print a quick summary to console"""
        print("\n" + "=" * 60)
        print("COMPARISON SUMMARY")
        print("=" * 60)
        
        wins = self.get_winner_summary()
        total = sum(wins.values())
        
        for topo in sorted(wins.keys(), key=lambda x: wins[x], reverse=True):
            pct = (wins[topo] / total * 100) if total > 0 else 0
            bar = "█" * int(pct / 5)
            print(f"{topo:>10}: {wins[topo]:>2} wins ({pct:>5.1f}%) {bar}")
        
        print("=" * 60)
