#!/usr/bin/env python3
"""
Multi-Topology Network Simulation Harness
Main entry point for running unified simulations

Usage:
    python run_comparison.py                    # Run with default settings
    python run_comparison.py --preset small     # Run small test
    python run_comparison.py --packets 500      # Custom packet count
    python run_comparison.py --help             # Show help
"""

import sys
import os
import argparse
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from unified_harness.config import (
    UnifiedConfig, TopologyConfig, SimulationConfig, 
    OutputConfig, TrafficPattern, get_preset, PRESETS
)
from unified_harness.runner import UnifiedSimulationRunner
from unified_harness.comparison_report import ComparisonReportGenerator


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Multi-Topology Network Simulation Comparison Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_comparison.py --preset small_test
  python run_comparison.py --packets 1000 --pattern uniform_random
  python run_comparison.py --mesh-size 6 --torus-size 6 --ricobit-levels 5
  python run_comparison.py --disable-mesh --packets 500
        """
    )
    
    # Preset selection
    parser.add_argument(
        '--preset', '-p',
        choices=list(PRESETS.keys()),
        help=f"Use a preset configuration: {list(PRESETS.keys())}"
    )
    
    # Simulation parameters
    parser.add_argument(
        '--packets', '-n',
        type=int,
        default=100,
        help="Number of packets to inject (default: 100)"
    )
    
    parser.add_argument(
        '--pattern',
        choices=['uniform_random', 'hotspot', 'nearest_neighbor'],
        default='uniform_random',
        help="Traffic pattern to use (default: uniform_random)"
    )
    
    parser.add_argument(
        '--max-cycles',
        type=int,
        default=10000,
        help="Maximum simulation cycles (default: 10000)"
    )
    
    parser.add_argument(
        '--seed',
        type=int,
        help="Random seed for reproducibility"
    )
    
    # Mesh parameters
    parser.add_argument(
        '--mesh-size',
        type=int,
        default=4,
        help="Mesh topology grid size NxN (default: 4)"
    )
    
    parser.add_argument(
        '--mesh-width',
        type=int,
        help="Mesh topology width (overrides --mesh-size)"
    )
    
    parser.add_argument(
        '--mesh-height',
        type=int,
        help="Mesh topology height (overrides --mesh-size)"
    )
    
    # Torus parameters
    parser.add_argument(
        '--torus-size',
        type=int,
        default=4,
        help="Torus topology grid size NxN (default: 4)"
    )
    
    parser.add_argument(
        '--torus-width',
        type=int,
        help="Torus topology width (overrides --torus-size)"
    )
    
    parser.add_argument(
        '--torus-height',
        type=int,
        help="Torus topology height (overrides --torus-size)"
    )
    
    # RiCoBiT parameters
    parser.add_argument(
        '--ricobit-levels',
        type=int,
        default=5,
        help="RiCoBiT topology number of levels (default: 5)"
    )
    
    # Buffer capacity
    parser.add_argument(
        '--buffer',
        type=int,
        default=4,
        help="Buffer capacity for all topologies (default: 4)"
    )
    
    # Enable/disable topologies
    parser.add_argument(
        '--disable-mesh',
        action='store_true',
        help="Disable Mesh topology simulation"
    )
    
    parser.add_argument(
        '--disable-ricobit',
        action='store_true',
        help="Disable RiCoBiT topology simulation"
    )
    
    parser.add_argument(
        '--disable-torus',
        action='store_true',
        help="Disable Torus topology simulation"
    )
    
    parser.add_argument(
        '--only',
        choices=['mesh', 'ricobit', 'torus'],
        help="Run only specified topology"
    )
    
    # Output options
    parser.add_argument(
        '--output-dir', '-o',
        default='./logs',
        help="Output directory for reports (default: ./logs)"
    )
    
    parser.add_argument(
        '--format',
        choices=['text', 'json', 'csv', 'all'],
        default='all',
        help="Report output format (default: all)"
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='count',
        default=1,
        help="Increase verbosity (can be repeated: -v, -vv, -vvv)"
    )
    
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help="Suppress output (equivalent to verbosity=0)"
    )
    
    return parser.parse_args()


def create_config_from_args(args) -> UnifiedConfig:
    """Create UnifiedConfig from command line arguments"""
    
    # Start with preset if specified
    if args.preset:
        config = get_preset(args.preset)
    else:
        config = UnifiedConfig()
    
    # Override with command line arguments
    
    # Simulation config
    config.simulation.num_packets = args.packets
    config.simulation.max_cycles = args.max_cycles
    config.simulation.random_seed = args.seed
    
    pattern_map = {
        'uniform_random': TrafficPattern.UNIFORM_RANDOM,
        'hotspot': TrafficPattern.HOTSPOT,
        'nearest_neighbor': TrafficPattern.NEAREST_NEIGHBOR
    }
    config.simulation.traffic_pattern = pattern_map.get(args.pattern, TrafficPattern.UNIFORM_RANDOM)
    
    # Verbosity
    if args.quiet:
        config.simulation.verbosity = 0
    else:
        config.simulation.verbosity = args.verbose
    
    # Mesh config
    mesh_width = args.mesh_width or args.mesh_size
    mesh_height = args.mesh_height or args.mesh_size
    config.mesh.width = mesh_width
    config.mesh.height = mesh_height
    config.mesh.buffer_capacity = args.buffer
    config.mesh.enabled = not args.disable_mesh
    
    # Torus config
    torus_width = args.torus_width or args.torus_size
    torus_height = args.torus_height or args.torus_size
    config.torus.width = torus_width
    config.torus.height = torus_height
    config.torus.buffer_capacity = args.buffer
    config.torus.enabled = not args.disable_torus
    
    # RiCoBiT config
    config.ricobit.num_levels = args.ricobit_levels
    config.ricobit.buffer_capacity = args.buffer
    config.ricobit.enabled = not args.disable_ricobit
    
    # Handle --only flag
    if args.only:
        config.mesh.enabled = (args.only == 'mesh')
        config.ricobit.enabled = (args.only == 'ricobit')
        config.torus.enabled = (args.only == 'torus')
    
    # Output config
    config.output.output_dir = args.output_dir
    config.output.report_format = args.format
    
    return config


def print_banner():
    """Print a startup banner"""
    banner = """
╔══════════════════════════════════════════════════════════════════╗
║     MULTI-TOPOLOGY NETWORK SIMULATION COMPARISON HARNESS         ║
║                                                                  ║
║  Comparing: MESH  |  RiCoBiT  |  TORUS                          ║
╚══════════════════════════════════════════════════════════════════╝
    """
    print(banner)


def print_config_summary(config: UnifiedConfig):
    """Print configuration summary"""
    print("\n" + "=" * 60)
    print("CONFIGURATION")
    print("=" * 60)
    
    summary = config.summary()
    
    print(f"Enabled Topologies: {', '.join(summary['enabled_topologies'])}")
    print(f"Packets to Inject: {summary['simulation']['num_packets']}")
    print(f"Traffic Pattern: {summary['simulation']['traffic_pattern']}")
    print(f"Max Cycles: {summary['simulation']['max_cycles']}")
    print()
    
    if config.mesh.enabled:
        print(f"Mesh: {summary['mesh']['grid_size']} ({summary['mesh']['nodes']} nodes), buffer={summary['mesh']['buffer_capacity']}")
    
    if config.ricobit.enabled:
        print(f"RiCoBiT: {summary['ricobit']['num_levels']} levels (~{summary['ricobit']['nodes']} nodes), buffer={summary['ricobit']['buffer_capacity']}")
    
    if config.torus.enabled:
        print(f"Torus: {summary['torus']['grid_size']} ({summary['torus']['nodes']} nodes), buffer={summary['torus']['buffer_capacity']}")
    
    print("=" * 60)


def main():
    """Main entry point"""
    args = parse_arguments()
    config = create_config_from_args(args)
    
    if config.simulation.verbosity > 0:
        print_banner()
        print_config_summary(config)
    
    # Ensure output directory exists
    os.makedirs(config.output.output_dir, exist_ok=True)
    
    # Run simulations
    runner = UnifiedSimulationRunner(config)
    results = runner.run_all()
    
    # Generate comparison report
    report_generator = ComparisonReportGenerator(config, results)
    report_files = report_generator.generate_all_reports()
    
    # Print summary
    if config.simulation.verbosity > 0:
        report_generator.print_summary()
        
        # Print metrics summary
        print("\n" + runner.metrics_collector.summary())
    
    # Return success/failure
    successful = sum(1 for r in results.values() if r.success)
    total = len(results)
    
    if config.simulation.verbosity > 0:
        print(f"\nCompleted: {successful}/{total} topologies ran successfully")
        print(f"Reports saved to: {config.output.output_dir}/")
    
    return 0 if successful == total else 1


if __name__ == "__main__":
    sys.exit(main())
