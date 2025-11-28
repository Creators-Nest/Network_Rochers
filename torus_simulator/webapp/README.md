# Torus Topology NoC Simulator - Web Application

Web-based interface for simulating packet routing on a torus Network-on-Chip (NoC) topology with wraparound connections.

## Features

- **Interactive Visualization**: Drag, zoom, and pan torus topology
- **Torus Wraparound**: Full support for torus wraparound edges visualization
- **Enhanced Architecture**: 
  - Pin-level simulation (REQ, ACK, DATA, CLK, CHOKE)
  - Register tracking (Send/Receive registers)
  - Buffer management (Send/Receive buffers)
  - Handshake protocol visualization
- **Multiple Simulation Modes**:
  - 1:1 unicast routing
  - 1:n multicast routing
  - n:m parallel routing
- **Real-time Monitoring**:
  - Node interface states
  - Buffer occupancy
  - Signal states (REQ/ACK/DATA)
  - Packet flow animation

## Installation

1. Install required packages:
```bash
pip install -r requirements.txt
```

## Running the Simulator

### Option 1: Using run script
```bash
python run_webapp.py
```

### Option 2: Direct Flask execution
```bash
cd webapp
python enhanced_app.py
```

The server will start on `http://localhost:5000`

## Default Configuration

- **Topology**: 4×4 torus with wraparound
- **Total Nodes**: 16
- **Connections per Node**: 4 (North, South, East, West)
- **Buffer Capacity**: 4 packets per interface
- **Routing Algorithm**: XY routing with wraparound consideration

## Usage

1. **Initialize Topology**:
   - Set grid width and height
   - Click "Apply topology"

2. **Select Nodes**:
   - Choose source and destination from dropdowns
   - Or click "Pick" to select from canvas

3. **Simulate**:
   - Click "Simulate route" to compute path
   - Click "Animate path" to visualize packet transfer
   - Watch handshake phases (REQ → ACK → DATA → Release)

4. **View Details**:
   - Click nodes to see interface details
   - Monitor buffers, pins, and registers
   - View routing tables and packet flow

## API Endpoints

- `POST /api/init` - Initialize topology with dimensions
- `GET /api/topology` - Get topology structure
- `GET /api/node/<x>/<y>` - Get node details
- `POST /api/route` - Find route between nodes
- `POST /api/simulate` - Simulate packet transfer
- `POST /api/multicast` - Simulate 1:M transfer
- `POST /api/node-state` - Get real-time node state

## Architecture

### Torus Topology
- **Wraparound Connections**: All edge nodes connect to opposite edge
- **XY Routing**: Deterministic routing with shortest path selection
- **Manhattan Distance**: Considers wraparound for distance calculation

### Node Components
Each node has 4 interfaces (one per neighbor):

**Interface Structure**:
- **Pins**: REQ, ACK, DATA, CLK, CHOKE
- **Registers**: Send_Register, Receive_Register
- **Buffers**: Send_Buffer (4 slots), Receive_Buffer (4 slots)
- **Control Bits**: Busy, Transfer, Receive

### Packet Flow
1. **Source**: Packet → Send_Buffer → Send_Register → REQ signal
2. **Handshake**: REQ → ACK → DATA transfer
3. **Intermediate**: Receive_Buffer → Routing → Send_Buffer (next hop)
4. **Destination**: Receive_Buffer → Consumed (application layer)

## Key Differences from Mesh Topology

1. **Wraparound Edges**: Torus has additional wraparound connections
2. **Routing Logic**: XY routing considers both direct and wraparound paths
3. **Shorter Paths**: Average hop count is lower due to wraparound
4. **Visualization**: Wraparound edges shown with special styling

## Technologies

- **Backend**: Python Flask
- **Frontend**: HTML5 Canvas, JavaScript (ES6+)
- **Routing**: XY routing algorithm with torus wraparound
- **Visualization**: Custom canvas rendering with animation

## Development

Built by extending the Mesh topology simulator with torus-specific features:
- Enhanced routing for wraparound
- Modified visualization for torus edges  
- Same frontend design and UI/UX
- Compatible with existing simulation logic

## License

Part of the Network-on-Chip Simulator project.
