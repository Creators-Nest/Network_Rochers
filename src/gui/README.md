# Mesh Topology GUI - User Guide

## 🚀 Quick Start

### Running the Simulator

```bash
python run_simulator.py
```

Or directly:

```bash
python -m src.gui.main_window
```

## 📐 GUI Layout

The GUI is divided into two main sections:

### ⬅️ Left Side: Control Panel (Fixed 350px width)
Scrollable panel containing all configuration and control sections

### ➡️ Right Side: Visualization Area
Dynamic canvas displaying the mesh network with real-time packet routing

---

## 🎛️ Control Panel Sections

### 1. 📐 Topology Configuration

**Purpose**: Create and configure the mesh network

**Controls**:
- **Rows**: Set number of rows (2-10)
- **Columns**: Set number of columns (2-10)
- **Apply Configuration**: Create new network with specified dimensions

**Usage**:
1. Set desired rows and columns
2. Click "Apply Configuration"
3. Network will be redrawn with new dimensions

---

### 2. 📦 Packet Routing

**Purpose**: Select source and destination for packet routing

**Controls**:
- **Source Node**: Displays selected source (Green)
- **Destination Node**: Displays selected destination (Red)
- **Clear Selection**: Reset source and destination

**Usage**:
1. Click any node in the visualization to set as **Source** (turns green)
2. Click another node to set as **Destination** (turns red)
3. Click "Clear Selection" to reset and start over

**Node Selection Logic**:
- First click → Source node (green)
- Second click → Destination node (red)
- Third click → Clears and starts over

---

### 3. 🔍 View Controls

**Purpose**: Navigate and zoom the visualization

**Controls**:
- **Zoom In (+)**: Increase visualization scale
- **Zoom Out (-)**: Decrease visualization scale
- **Reset View**: Return to default zoom and position

**Keyboard Shortcuts** (coming soon):
- `+` or `=` → Zoom in
- `-` or `_` → Zoom out
- `R` → Reset view

---

### 4. ▶️ Simulation Controls

**Purpose**: Control packet routing simulation

**Controls**:
- **Start Simulation**: Begin automatic packet routing
- **Step Forward**: Manually advance one simulation step
- **Reset Simulation**: Clear current simulation and buffers
- **Speed (ms)**: Adjust animation speed (100-2000ms)

**Workflow**:
1. Select source and destination nodes
2. Click "Start Simulation" for automatic routing
3. Watch packet traverse the network following XY routing
4. Or use "Step Forward" for manual step-by-step control

**Simulation States**:
- ✅ **Ready**: Source and destination selected
- ▶️ **Running**: Packet is routing through network
- ✓ **Completed**: Packet delivered to destination
- ⏸️ **Paused**: Use step-forward for manual control

---

### 5. 📊 Statistics

**Purpose**: Display real-time network and routing statistics

**Information Displayed**:

```
Network Statistics:
━━━━━━━━━━━━━━━━━━━━━━━━━
Topology: Mesh 4×4
Total Nodes: 16
Routing: XY Algorithm

Routing Info:
Source: (0, 0)
Destination: (3, 3)
Expected Hops: 6

Current Packet:
ID: 1
Status: in_transit
Current Hops: 3
Latency: 3 cycles (when delivered)

Packet Statistics:
Generated: 1
Received: 0
```

**Key Metrics**:
- **Network Size**: Current mesh dimensions
- **Routing Algorithm**: XY (dimension-ordered)
- **Expected Hops**: Manhattan distance calculation
- **Current Hops**: Actual hops taken so far
- **Latency**: Time from creation to delivery
- **Buffer Status**: Input/Output buffer occupancy

---

### 6. ❓ Help & Guide

**Purpose**: Quick reference guide for using the simulator

**Contents**:
- 🖱️ **Mouse Controls**: Node selection and interaction
- ⌨️ **Simulation Steps**: Complete workflow
- 📐 **Topology Info**: Network characteristics
- 🎨 **Color Legend**: Node and packet colors

---

## 🎨 Visualization Area

### Node Representation

**Node Colors**:
- 🔵 **Blue**: Normal/idle nodes
- 🟢 **Green**: Source node (packet origin)
- 🔴 **Red**: Destination node (packet target)
- 🟠 **Orange**: Selected/highlighted node
- 🟣 **Purple**: Active routing node

**Node Display**:
```
    ┌─────────┐
    │ (row,col)│  ← Node coordinates
    └─────────┘
      I:2 O:1    ← Buffer status
                   (Input: 2, Output: 1)
```

### Network Connections

- **Gray Lines**: Physical links between adjacent nodes
- **Mesh Topology**: 
  - Each node connects to 2-4 neighbors
  - Corner nodes: 2 connections
  - Edge nodes: 3 connections  
  - Internal nodes: 4 connections

### Packet Visualization

- 🟠 **Orange Arrow Path**: Packet's routing path
- 🟠 **Orange Dot**: Current packet position
- **Animated Movement**: Watch packet hop between nodes

---

## 🎯 Complete Usage Workflow

### Basic Simulation

1. **Configure Network**:
   ```
   Rows: 4
   Columns: 4
   Click "Apply Configuration"
   ```

2. **Select Routing**:
   ```
   Click node (0,0) → Source (Green)
   Click node (3,3) → Destination (Red)
   ```

3. **Run Simulation**:
   ```
   Click "Start Simulation"
   Watch packet route: EAST → EAST → EAST → SOUTH → SOUTH → SOUTH
   ```

4. **View Results**:
   ```
   Check Statistics panel:
   - Total Hops: 6
   - Latency: 6 cycles
   - Status: Delivered ✓
   ```

### Advanced Usage

**Manual Step-Through**:
1. Select source and destination
2. Click "Start Simulation"
3. Immediately click "Step Forward" for manual control
4. Observe each hop individually

**Different Network Sizes**:
- **Small** (2×2, 3×3): Quick testing
- **Medium** (4×4, 5×5): Standard demonstrations
- **Large** (8×8, 10×10): Complex routing scenarios

**Routing Scenarios**:
- **Horizontal**: (0,0) → (0,3) - East only
- **Vertical**: (0,0) → (3,0) - South only
- **Diagonal**: (0,0) → (3,3) - East then South
- **Reverse**: (3,3) → (0,0) - West then North

---

## 🔬 Buffer System Implementation

Based on the attached NoC router specification:

### Reception & Input
1. **Receive Bit**: Asserted when flit arrives
2. **Receive Buffer**: FIFO queue stores incoming packets
3. **Buffer Capacity**: Configurable (default: 10 packets)

### Routing & Decision  
1. **Routing Logic**: XY algorithm determines output port
2. **Control Logic**: Sends REQ signal to downstream router
3. **Address Lookup**: Header flit contains destination

### Transmission & Flow Control
1. **Acknowledge (ACK)**: Downstream confirms buffer space
2. **Arbitration**: Multiple inputs compete for output
3. **Transfer Bit**: Asserted during data movement
4. **CLK Signal**: Synchronizes data transfer

### Congestion Management
1. **Choke Signal**: Back-pressure when buffer nearly full
2. **Buffer Monitoring**: Displayed in real-time (I:x O:y)
3. **Overflow Prevention**: REQ/ACK handshaking

**Visual Buffer Display**:
```
Node (1,2)
  I:3 O:1    ← Input buffer: 3 packets
             ← Output buffer: 1 packet
             ← Capacity: 10 each
```

---

## 🎨 Color Scheme

### Node States
| Color | RGB | Hex | Meaning |
|-------|-----|-----|---------|
| Blue | (52, 152, 219) | #3498db | Normal node |
| Green | (46, 204, 113) | #2ecc71 | Source node |
| Red | (231, 76, 60) | #e74c3c | Destination node |
| Orange | (243, 156, 18) | #f39c12 | Selected node |
| Purple | (155, 89, 182) | #9b59b6 | Active routing |

### UI Elements
| Element | Color | Hex | Purpose |
|---------|-------|-----|---------|
| Background | Light Gray | #ecf0f1 | Canvas |
| Panel | Dark Blue | #34495e | Control panel |
| Header | Darker Blue | #2c3e50 | Section headers |
| Connections | Gray | #95a5a6 | Network links |
| Packet | Orange | #e67e22 | Packet path |

---

## ⚡ Performance Tips

### Smooth Animation
- **Small networks** (2×2 to 5×5): Speed 100-300ms
- **Medium networks** (6×6 to 8×8): Speed 300-500ms  
- **Large networks** (9×9 to 10×10): Speed 500-1000ms

### Best Viewing
- **Zoom In**: Better detail for large networks
- **Reset View**: Optimal automatic centering
- **Manual Step**: Detailed observation mode

---

## 🐛 Troubleshooting

### Issue: Nodes not clickable
**Solution**: Ensure network is created (Apply Configuration)

### Issue: Simulation won't start
**Solution**: Select both source and destination nodes

### Issue: Visualization too small/large
**Solution**: Use Zoom In/Out or Reset View

### Issue: Buffer overflow warnings
**Solution**: This is expected behavior demonstrating congestion

---

## 🔮 Coming Soon

- [ ] Torus topology support
- [ ] RiCoBiT topology support
- [ ] Multiple packet simulation
- [ ] Custom routing algorithms
- [ ] Traffic pattern generation
- [ ] Performance graphs
- [ ] Export simulation data
- [ ] Save/Load configurations
- [ ] Animation replay

---

## 📚 Technical Details

### XY Routing Algorithm
- **Phase 1**: Route in X-dimension (East/West) first
- **Phase 2**: Route in Y-dimension (North/South) second
- **Properties**: Deadlock-free, deterministic, minimal path
- **Complexity**: O(1) per routing decision

### Buffer Implementation
- **Type**: FIFO (First-In-First-Out)
- **Structure**: Python deque with maxlen
- **Operations**: O(1) enqueue/dequeue
- **Statistics**: Real-time utilization tracking

### GUI Framework
- **Toolkit**: Tkinter (Python standard library)
- **Canvas**: Hardware-accelerated drawing
- **Updates**: Event-driven architecture
- **Responsive**: Automatic layout adjustment

---

## 💡 Tips & Tricks

1. **Quick Test**: Use 3×3 mesh with (0,0)→(2,2) for fast demo
2. **Path Comparison**: Try same source/dest on different sizes
3. **Buffer Observation**: Watch I/O counts during routing
4. **Step Mode**: Best for understanding XY routing logic
5. **Statistics**: Monitor latency vs expected hops match

---

## 📖 References

- XY Routing: Dimension-ordered routing for mesh networks
- NoC Architecture: Based on standard mesh-based NoC design
- Buffer Management: FIFO queues with back-pressure control
- Flow Control: REQ/ACK handshaking protocol

---

**Version**: 1.0.0  
**Framework**: Network_Rochers NoC Simulator  
**Topology**: Mesh (2D Grid)  
**Routing**: XY Algorithm (Deadlock-free)
