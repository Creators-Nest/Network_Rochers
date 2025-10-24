# NoC Simulator Framework

Network-on-Chip (NoC) Simulation Framework for visualizing and analyzing packet transfer across different topologies.

## Supported Topologies

1. **Mesh** - Grid-based topology with vertical and horizontal connections
2. **Torus** - Mesh topology with wrap-around connections
3. **RiCoBiT** - Ring-Connected Bi-directional Topology with diagonal connections

## Project Structure

```
Network_Rochers/
├── src/
│   ├── core/              # Core components (Node, Packet, Buffer, Link)
│   ├── routing/           # Routing algorithms
│   ├── topologies/        # Topology implementations
│   │   ├── mesh/
│   │   ├── torus/
│   │   └── ricobit/
│   ├── simulation/        # Simulation engine
│   ├── visualization/     # Rendering and animation
│   ├── gui/              # User interface
│   └── utils/            # Utilities
├── examples/             # Example simulations
├── data/                 # Configuration files
│   └── configs/
└── output/              # Simulation results
```

## Features

- **Visual Simulation**: Real-time visualization of packet transfer
- **Multiple Topologies**: Compare Mesh, Torus, and RiCoBiT architectures
- **Performance Metrics**: Track latency, throughput, and congestion
- **Path Tracking**: Visualize packet routes through the network
- **Interactive GUI**: Configure and control simulations

## Getting Started

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run example simulations:
   ```bash
   python examples/basic_mesh_simulation.py
   ```

## Authors

Network_Rochers Team - REVA University
