"""
Unified Configuration System for Multi-Topology Simulation
Provides consistent configuration across all three topology types
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Literal
from enum import Enum


class TopologyType(Enum):
    """Enumeration of supported topology types"""
    MESH = "mesh"
    RICOBIT = "ricobit"
    TORUS = "torus"


class TrafficPattern(Enum):
    """Enumeration of supported traffic patterns"""
    UNIFORM_RANDOM = "uniform_random"
    LONGEST_NEIGHBOR = "longest_neighbor"
    HOTSPOT = "hotspot"
    NEAREST_NEIGHBOR = "nearest_neighbor"


@dataclass
class TopologyConfig:
    """Configuration for individual topology parameters"""
    
    # Common parameters
    buffer_capacity: int = 4
    enabled: bool = True
    
    # Mesh/Torus specific parameters (2D grid)
    width: int = 4
    height: int = 4
    
    # RiCoBiT specific parameters (ring-tree structure)
    num_levels: int = 5  # Creates 2^(num_levels-1) - 1 nodes approximately
    
    def get_estimated_node_count(self, topology_type: TopologyType) -> int:
        """Estimate the number of nodes for this configuration"""
        if topology_type == TopologyType.MESH or topology_type == TopologyType.TORUS:
            return self.width * self.height
        elif topology_type == TopologyType.RICOBIT:
            # RiCoBiT: Sum of 2^R for R from 1 to (num_levels-1)
            # Excludes level 0 (central controller)
            return sum(2**r for r in range(1, self.num_levels))
        return 0


@dataclass
class SimulationConfig:
    """Configuration for simulation parameters"""
    
    # Number of packets to inject
    num_packets: int = 100
    
    # Traffic pattern to use
    traffic_pattern: TrafficPattern = TrafficPattern.UNIFORM_RANDOM
    
    # Maximum simulation cycles (to prevent infinite loops)
    max_cycles: int = 10000
    
    # Random seed for reproducibility
    random_seed: Optional[int] = None
    
    # Logging verbosity (0=quiet, 1=summary, 2=verbose, 3=debug)
    verbosity: int = 1
    
    # Whether to run topologies in parallel (if supported)
    parallel_execution: bool = False


@dataclass
class OutputConfig:
    """Configuration for output and reporting"""
    
    # Directory for output files
    output_dir: str = "./logs"
    
    # Generate detailed log files
    generate_logs: bool = True
    
    # Generate comparison report
    generate_report: bool = True
    
    # Report format: 'text', 'json', 'csv', 'all'
    report_format: str = "all"
    
    # Include per-packet details in logs
    detailed_packet_logs: bool = False
    
    # Timestamp format for log files
    timestamp_format: str = "%Y%m%d_%H%M%S"


@dataclass
class UnifiedConfig:
    """
    Master configuration for unified multi-topology simulation
    
    Usage:
        config = UnifiedConfig(
            mesh=TopologyConfig(width=6, height=6),
            ricobit=TopologyConfig(num_levels=5),
            torus=TopologyConfig(width=4, height=4),
            simulation=SimulationConfig(num_packets=1000),
            output=OutputConfig(output_dir="./results")
        )
    """
    
    # Individual topology configurations
    mesh: TopologyConfig = field(default_factory=TopologyConfig)
    ricobit: TopologyConfig = field(default_factory=TopologyConfig)
    torus: TopologyConfig = field(default_factory=TopologyConfig)
    
    # Simulation parameters
    simulation: SimulationConfig = field(default_factory=SimulationConfig)
    
    # Output configuration
    output: OutputConfig = field(default_factory=OutputConfig)
    
    def get_enabled_topologies(self) -> List[TopologyType]:
        """Get list of enabled topology types"""
        enabled = []
        if self.mesh.enabled:
            enabled.append(TopologyType.MESH)
        if self.ricobit.enabled:
            enabled.append(TopologyType.RICOBIT)
        if self.torus.enabled:
            enabled.append(TopologyType.TORUS)
        return enabled
    
    def get_topology_config(self, topology_type: TopologyType) -> TopologyConfig:
        """Get configuration for specific topology type"""
        if topology_type == TopologyType.MESH:
            return self.mesh
        elif topology_type == TopologyType.RICOBIT:
            return self.ricobit
        elif topology_type == TopologyType.TORUS:
            return self.torus
        raise ValueError(f"Unknown topology type: {topology_type}")
    
    def summary(self) -> Dict:
        """Get configuration summary"""
        return {
            "enabled_topologies": [t.value for t in self.get_enabled_topologies()],
            "mesh": {
                "enabled": self.mesh.enabled,
                "grid_size": f"{self.mesh.width}x{self.mesh.height}",
                "nodes": self.mesh.get_estimated_node_count(TopologyType.MESH),
                "buffer_capacity": self.mesh.buffer_capacity
            },
            "ricobit": {
                "enabled": self.ricobit.enabled,
                "num_levels": self.ricobit.num_levels,
                "nodes": self.ricobit.get_estimated_node_count(TopologyType.RICOBIT),
                "buffer_capacity": self.ricobit.buffer_capacity
            },
            "torus": {
                "enabled": self.torus.enabled,
                "grid_size": f"{self.torus.width}x{self.torus.height}",
                "nodes": self.torus.get_estimated_node_count(TopologyType.TORUS),
                "buffer_capacity": self.torus.buffer_capacity
            },
            "simulation": {
                "num_packets": self.simulation.num_packets,
                "traffic_pattern": self.simulation.traffic_pattern.value,
                "max_cycles": self.simulation.max_cycles
            }
        }
    
    @classmethod
    def from_dict(cls, config_dict: Dict) -> 'UnifiedConfig':
        """Create configuration from dictionary"""
        mesh_config = TopologyConfig(**config_dict.get('mesh', {}))
        ricobit_config = TopologyConfig(**config_dict.get('ricobit', {}))
        torus_config = TopologyConfig(**config_dict.get('torus', {}))
        
        sim_dict = config_dict.get('simulation', {})
        if 'traffic_pattern' in sim_dict and isinstance(sim_dict['traffic_pattern'], str):
            sim_dict['traffic_pattern'] = TrafficPattern(sim_dict['traffic_pattern'])
        simulation_config = SimulationConfig(**sim_dict)
        
        output_config = OutputConfig(**config_dict.get('output', {}))
        
        return cls(
            mesh=mesh_config,
            ricobit=ricobit_config,
            torus=torus_config,
            simulation=simulation_config,
            output=output_config
        )
    
    def to_dict(self) -> Dict:
        """Convert configuration to dictionary"""
        return {
            'mesh': {
                'width': self.mesh.width,
                'height': self.mesh.height,
                'buffer_capacity': self.mesh.buffer_capacity,
                'enabled': self.mesh.enabled,
                'num_levels': self.mesh.num_levels
            },
            'ricobit': {
                'width': self.ricobit.width,
                'height': self.ricobit.height,
                'buffer_capacity': self.ricobit.buffer_capacity,
                'enabled': self.ricobit.enabled,
                'num_levels': self.ricobit.num_levels
            },
            'torus': {
                'width': self.torus.width,
                'height': self.torus.height,
                'buffer_capacity': self.torus.buffer_capacity,
                'enabled': self.torus.enabled,
                'num_levels': self.torus.num_levels
            },
            'simulation': {
                'num_packets': self.simulation.num_packets,
                'traffic_pattern': self.simulation.traffic_pattern.value,
                'max_cycles': self.simulation.max_cycles,
                'random_seed': self.simulation.random_seed,
                'verbosity': self.simulation.verbosity,
                'parallel_execution': self.simulation.parallel_execution
            },
            'output': {
                'output_dir': self.output.output_dir,
                'generate_logs': self.output.generate_logs,
                'generate_report': self.output.generate_report,
                'report_format': self.output.report_format,
                'detailed_packet_logs': self.output.detailed_packet_logs
            }
        }


# Preset configurations for common test scenarios
PRESETS = {
    "small_test": UnifiedConfig(
        mesh=TopologyConfig(width=3, height=3, buffer_capacity=4),
        ricobit=TopologyConfig(num_levels=4, buffer_capacity=4),
        torus=TopologyConfig(width=3, height=3, buffer_capacity=4),
        simulation=SimulationConfig(num_packets=50, max_cycles=1000)
    ),
    "medium_test": UnifiedConfig(
        mesh=TopologyConfig(width=4, height=4, buffer_capacity=4),
        ricobit=TopologyConfig(num_levels=5, buffer_capacity=4),
        torus=TopologyConfig(width=4, height=4, buffer_capacity=4),
        simulation=SimulationConfig(num_packets=200, max_cycles=5000)
    ),
    "large_test": UnifiedConfig(
        mesh=TopologyConfig(width=6, height=6, buffer_capacity=4),
        ricobit=TopologyConfig(num_levels=6, buffer_capacity=4),
        torus=TopologyConfig(width=6, height=6, buffer_capacity=4),
        simulation=SimulationConfig(num_packets=1000, max_cycles=20000)
    ),
    "stress_test": UnifiedConfig(
        mesh=TopologyConfig(width=8, height=8, buffer_capacity=8),
        ricobit=TopologyConfig(num_levels=7, buffer_capacity=8),
        torus=TopologyConfig(width=8, height=8, buffer_capacity=8),
        simulation=SimulationConfig(num_packets=5000, max_cycles=50000)
    )
}


def get_preset(name: str) -> UnifiedConfig:
    """Get a preset configuration by name"""
    if name not in PRESETS:
        raise ValueError(f"Unknown preset: {name}. Available: {list(PRESETS.keys())}")
    return PRESETS[name]
