<<<<<<< HEAD
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
=======
Repository contianing intial working prototypes of the 4 Network On Chip Topologies:
* Mesh (Handeled by Giridharan and Akarsh)
* Torus (Handeled by David and Darshan)
* RiCoBiT (Handeled By Akarsh and Darshan)
* Adaptive -RiCoBiT (Joint Contribution)
>>>>>>> 48be702f2bf683c3cde44e9ada36cc1a40d43dc6



scripts : 
1.python topology_metrics.py 


TABLE I.     MAX HOP VS NUMBER OF NODES

    Number |              Max Hop Count              
  of Nodes |         Mesh        Torus      RiCoBiT
-------------------------------------------------------
         4 |         2.00         2.00         1.17
         8 |         3.66         2.83         2.64
        16 |         6.00         4.00         4.34
        32 |         9.31         5.66         6.17
        64 |        14.00         8.00         8.09
       128 |        20.63        11.31        10.04
       256 |        30.00        16.00        12.02
       512 |        43.25        22.63        14.01
      1024 |        62.00        32.00        16.01
      2048 |        88.51        45.25        18.00

TABLE II.    AVERAGE HOP VS NUMBER OF NODES

    Number |            Average Hop Count            
  of Nodes |         Mesh        Torus      RiCoBiT
-------------------------------------------------------
         4 |         1.00         1.00         1.01
         8 |         1.75         1.50         1.29
        16 |         2.50         2.00         2.01
        32 |         3.88         3.00         3.00
        64 |         5.25         4.00         4.27
       128 |         7.94         6.00         5.78
       256 |        10.62         8.00         7.46
       512 |        15.97        12.00         9.27
      1024 |        21.31        16.00        11.15
      2048 |        31.98        24.00        13.09


2. Python run_all_simulations.sh

═══════════════════════════════════════════════════════════════════════
                      METRICS COMPARISON
═══════════════════════════════════════════════════════════════════════

------------------------------------------------------------------------
Metric                               MESH      RICOBIT        TORUS
------------------------------------------------------------------------
Nodes                                  64          126           64
Packets Injected                      100          100          100
Packets Delivered                     100          100          100
Delivery Rate (%)                   100.0        100.0        100.0
Total Cycles                           35           44           29
Avg Latency (cycles)                35.00        18.24        29.00
Min Latency                            35            1           29
Max Latency                            35           43           29
Throughput (pkt/cycle)             2.8571       2.2727       3.4483
Avg Hops (RiCoBiT only)              5.73         5.81         0.00
Packet Speed (1/latency)           0.0286       0.0548       0.0345
------------------------------------------------------------------------


