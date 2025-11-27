# Enhanced Mesh Topology NoC Simulator - Flask Web Application

## Overview

This is a comprehensive web-based Network-on-Chip (NoC) simulator implementing a **Mesh Topology** with enhanced interface design. The simulator provides real-time visualization of packet transfers, interface states, and routing operations.

## Key Features

### 🌐 **Enhanced Interface Architecture**
Each node has **n interfaces** where n = number of adjacent nodes

**Pins (Boolean signals):**
- `REQ`: Request signal
- `ACK`: Acknowledgment signal  
- `DATA`: Data signal (packet content)
- `CLK`: Clock signal
- `CHOKE`: Flow control/congestion signal

**Registers (packet-sized bit arrays):**
- `Send_Register`: Holds packet being sent
- `Receive_Register`: Holds packet being received

**Buffers (circular buffers with n slots):**
- `Send_Buffer`: Queue of packets to send
- `Receive_Buffer`: Queue of received packets

**Status Bits:**
- `Busy_Bit`: Interface is busy
- `Receive_Bit`: Currently receiving data
- `Transfer_Bit`: Currently transferring data

**Control Methods:**
- `Routing_Algorithm(packet)`: XY routing for next hop determination
- `Control_Logic()`: REQ-ACK-DATA handshake management
- `Buffer_Operations()`: Buffer management and flow control

### 📡 **Transfer Modes**

1. **1:1 (One-to-One)**
   - Single source to single destination
   - Direct packet transfer with path visualization

2. **1:M (One-to-Many Multicast)**
   - Single source to multiple destinations
   - Sequential delivery to all destinations
   - ACK signals return through reverse path
   - Comprehensive results display

### 🎨 **Interactive Visualization**

- **Canvas-based mesh rendering** with zoom and pan
- **Node highlighting**: Source (red), Destinations (green), Completed (blue)
- **Real-time packet animation** with hexagonal packets
- **Interface info popups** on edge hover
- **Path visualization** showing completed transfers
- **Smooth animations** with configurable speed

### 🔧 **Packet Flow Logic**

- **Source nodes**: Inject packets into the network
- **Intermediate nodes**: 
  - Receive packets into `receive_buffer`
  - Forward to `send_buffer` for next hop
- **Destination nodes**: Consume packets (not forwarded)

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Setup

1. **Navigate to webapp directory:**
   ```powershell
   cd "c:\Users\girio\OneDrive - REVA University\Sem 5\Network on chips\project\Network_Rochers\Mesh_topology\webapp"
   ```

2. **Install dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

3. **Run the Flask application:**
   ```powershell
   python enhanced_app.py
   ```

4. **Open browser:**
   Navigate to `http://localhost:5000`

## Usage Guide

### 1. Initialize Topology

- Set grid dimensions (width × height)
- Click "Initialize Topology" button
- Default: 6×6 mesh with 36 nodes

### 2. Select Transfer Type

**1:1 Mode:**
- Click to select source node (turns red)
- Click to select destination node (turns green)
- Click "Start Simulation"

**1:M Mode:**
- Click to select source node (turns red)
- Click multiple nodes for destinations (turn green)
- Remove destinations using "Remove" button
- Click "Start Simulation"

### 3. View Results

- Packet animations show real-time transfer
- Results modal displays:
  - Packet ID and data
  - Source and destination(s)
  - Path taken (hop-by-hop)
  - Total hops count
  - Transfer statistics

### 4. Monitor Interfaces

- Hover over edges to see interface details:
  - Pin states (REQ, ACK, DATA, CLK, CHOKE)
  - Register contents
  - Buffer status (size, capacity)
  - Status bits (Busy, Receive, Transfer)

## API Endpoints

### `POST /api/init`
Initialize topology with dimensions
```json
{
  "width": 6,
  "height": 6
}
```

### `GET /api/topology`
Get current topology structure

### `GET /api/node/<x>/<y>`
Get detailed node information including all interfaces

### `POST /api/route`
Find route between two nodes
```json
{
  "source": [0, 0],
  "destination": [5, 5]
}
```

### `POST /api/simulate`
Simulate single packet transfer (1:1)
```json
{
  "source": [0, 0],
  "destination": [5, 5],
  "data": "Test Data"
}
```

### `POST /api/multicast`
Simulate multicast transfer (1:M)
```json
{
  "source": [0, 0],
  "destinations": [[3, 3], [5, 5], [2, 4]],
  "data": "Multicast Data"
}
```

## Architecture

### Backend (Python/Flask)

```
webapp/
├── enhanced_app.py          # Main Flask application
├── requirements.txt         # Python dependencies
├── templates/
│   └── enhanced_simulator.html  # HTML interface
└── static/
    └── js/
        └── enhanced_simulator.js  # Frontend logic
```

### Core Components

```
core/
├── enhanced_interface.py    # Enhanced Interface class
├── enhanced_node.py         # Node with packet consumption
├── packet.py               # Packet data structure
└── buffers.py              # Buffer implementations

topology/
└── enhanced_mesh_topology.py  # Mesh topology builder

routing/
└── xy_router.py            # XY routing algorithm
```

## Technical Details

### XY Routing Algorithm

1. Route along **X-axis first** (horizontal movement)
2. Then route along **Y-axis** (vertical movement)
3. Deterministic and deadlock-free
4. Minimal path routing

### Handshake Protocol

```
1. IDLE        → Wait for packet in send_buffer
2. REQ_SENT    → Assert REQ signal
3. ACK_WAIT    → Wait for ACK from receiver
4. DATA_TRANSFER → Transfer data when ACK received
5. COMPLETE    → Clear signals, return to IDLE
```

### Buffer Management

- **Circular buffers** with configurable capacity (default: 4 slots)
- **Flow control** via CHOKE signal when buffers full
- **Automatic forwarding** at intermediate nodes
- **Packet consumption** at destination nodes

## Statistics Tracked

- Total nodes in topology
- Packets sent/received
- Average hop count
- Transfer success rate
- Interface utilization

## Troubleshooting

### Port Already in Use
If port 5000 is occupied, modify `enhanced_app.py`:
```python
app.run(debug=True, host='0.0.0.0', port=5001)  # Change port
```

### Canvas Not Rendering
- Clear browser cache
- Check browser console for JavaScript errors
- Ensure static files are being served correctly

### Slow Animation
- Reduce `ANIMATION_SPEED` in `enhanced_simulator.js`
- Decrease grid size for better performance

## Future Enhancements

- [ ] Additional routing algorithms (Shortest Path, Adaptive)
- [ ] Network congestion visualization
- [ ] Packet priority queuing
- [ ] Real-time throughput graphs
- [ ] Export simulation results to CSV/JSON
- [ ] Custom topology editor
- [ ] Fault injection and recovery testing

## Credits

Based on the ricobit_simulator_web architecture with enhanced NoC interface design for academic research in Network-on-Chip systems.

## License

See LICENSE file in the root directory.
