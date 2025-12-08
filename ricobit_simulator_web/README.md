# RiCoBiT Simulator Web

A web-based interactive simulator and visualizer for the RiCoBiT (Recursive Combination of Binary Trees) network topology, designed for on-chip network research and education.

## Overview

RiCoBiT Simulator Web provides a comprehensive platform to simulate, visualize, and analyze packet routing in RiCoBiT topologies. This topology combines ring connections within levels and tree connections between levels to create an efficient hierarchical network structure.

The simulator implements shortest-path routing using BFS (Breadth-First Search) to guarantee optimal routing decisions, making it suitable for studying network-on-chip (NoC) performance characteristics.

## Features

- **Interactive Web Interface**: Real-time visualization of topology and packet routing
- **Dynamic Simulation**: Step-by-step packet injection and routing simulation
- **Shortest Path Routing**: BFS-based routing algorithm ensuring optimal paths
- **Traffic Generation**: Support for uniform random and longest-neighbor-first traffic patterns
- **Topology Exploration**: Configurable RiCoBiT topology with variable levels
- **Performance Analysis**: Distance calculations and routing statistics

## Architecture

The simulator is built with a modular architecture:

- **Core**: Fundamental components (Nodes, Interfaces, Packets, Buffers)
- **Topology**: RiCoBiT topology generation and management
- **Routing**: Shortest-path routing algorithm implementation
- **Simulation**: Packet generation and simulation coordination
- **Webapp**: Flask-based web interface for visualization

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/Creators-Nest/Network_Rochers.git
   cd Network_Rochers/ricobit_simulator_web
   ```

2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install flask
   ```

## Usage

### Running the Web Application

Start the Flask development server:

```bash
python -m flask --app ricobit_simulator_web.webapp:create_app run --debug
```

The application will be available at `http://localhost:5000`

### Configuration

The topology size can be configured by modifying the `num_levels` parameter in the `AppState` class within `webapp/app.py`. Default is 5 levels.

## Project Structure

```
ricobit_simulator_web/
├── core/                    # Core network components
│   ├── buffers.py          # Circular buffer implementation
│   ├── interface.py        # Node interface with handshake logic
│   ├── node.py             # Node implementation
│   └── packet.py           # Packet data structure
├── routing/                 # Routing algorithms
│   └── shortest_path_router.py  # BFS-based shortest path routing
├── simulation/              # Simulation components
│   ├── packet_generator.py  # Traffic pattern generation
│   └── simulator.py         # Simulation coordinator
├── topology/                # Topology generation
│   └── ricobit_topology.py  # RiCoBiT topology implementation
├── webapp/                  # Web interface
│   ├── app.py              # Flask application
│   ├── static/             # CSS and JavaScript assets
│   └── templates/          # HTML templates
├── __init__.py             # Package initialization
└── README.md               # This file
```

## API Endpoints

- `GET /`: Main simulator interface
- `POST /api/initialize`: Initialize topology with specified levels
- `POST /api/simulate`: Run simulation steps
- `GET /api/state`: Get current simulation state
- `POST /api/reset`: Reset simulation

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file in the root directory for details.

## Acknowledgments

- Based on RiCoBiT topology research papers
- Built with Flask web framework
- Uses modern web technologies for interactive visualization

## Contact

For questions or support, please open an issue on the GitHub repository.