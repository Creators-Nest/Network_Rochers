# Torus Topology Simulator

A 2D Torus network topology simulator with XY routing, based on the same core architecture as the RicoBit simulator.

## Features

- **2D Torus Topology**: Configurable width x height mesh with wraparound connections
- **XY Routing**: Deterministic dimension-order routing (X first, then Y)
- **Real Packet Transfer**: Detailed handshake protocol simulation with REQ/ACK signals
- **Interactive GUI**: White theme matching RicoBit visualizer
- **Packet Animation**: Step-by-step visualization of packet flow
- **Node Details**: Hover over nodes to see buffer status and interface states

## Architecture

### Core Components
- **Node**: Same interface and buffer structure as RicoBit
- **Interface**: REQ/ACK handshake protocol with circular buffers
- **Packet**: Standard packet structure with timing information
- **Buffers**: Circular send/receive buffers with congestion handling

### Topology
- **2D Torus**: Each node connects to 4 neighbors (North, South, East, West)
- **Wraparound**: Edge nodes connect to opposite edge (torus property)
- **Coordinates**: Nodes addressed as (x, y) where 0 ≤ x < width, 0 ≤ y < height

### Routing
- **XY Routing**: Route in X dimension first, then Y dimension
- **Shortest Path**: Considers wraparound for minimum distance
- **Deadlock-Free**: Deterministic routing prevents cycles

## Usage

### Running the Simulator
```bash
cd torus_simulator
python main.py
```

### GUI Controls
1. **Topology Configuration**: Adjust torus width and height (3-8 nodes)
2. **Node Selection**: Click nodes or use spinboxes to set source/destination
3. **Simulation**: 
   - "Simulate" - Compute and highlight XY routing path
   - "Animate" - Step-by-step packet transfer animation
   - "Clear" - Reset visualization
4. **View Controls**: Zoom, pan, and reset view

### XY Routing Example
For a 4x4 torus, routing from (0,0) to (3,2):
1. X-phase: (0,0) → (1,0) → (2,0) → (3,0)
2. Y-phase: (3,0) → (3,1) → (3,2)

With wraparound optimization, (0,0) to (3,0) might go:
(0,0) → (3,0) [wraparound is shorter than 3 hops]

## File Structure

```
torus_simulator/
├── core/                   # Core components (same as RicoBit)
│   ├── node.py            # Node with interfaces and routing
│   ├── interface.py       # REQ/ACK handshake protocol
│   ├── packet.py          # Packet structure
│   └── buffers.py         # Circular buffers
├── topology/
│   └── torus_topology.py  # 2D torus with wraparound
├── routing/
│   └── xy_router.py       # XY routing algorithm
├── simulation/
│   ├── simulator.py       # Simulation engine
│   └── packet_generator.py # Packet generation
├── gui/
│   ├── visualizer_complete.py # Main GUI
│   ├── packet_animator.py     # Packet animations
│   └── torus_renderer.py      # Grid and path rendering
├── main.py                # Entry point
└── README.md
```

## Comparison with RicoBit

| Feature | RicoBit | Torus |
|---------|---------|-------|
| Topology | Hierarchical rings + tree | 2D mesh with wraparound |
| Addressing | (Ring, Position) | (X, Y) coordinates |
| Routing | Shortest path (BFS) | XY routing (deterministic) |
| Connections | Ring + parent-child | 4-neighbor grid |
| Scalability | Exponential (2^R nodes) | Linear (W×H nodes) |
| Deadlock | BFS prevents loops | XY routing prevents cycles |

## Key Advantages of Torus + XY Routing

1. **Predictable Performance**: XY routing has deterministic latency
2. **Simple Implementation**: No complex routing tables needed
3. **Scalable**: Linear growth vs exponential in RicoBit
4. **Fault Tolerance**: Multiple paths available with wraparound
5. **Load Distribution**: XY routing spreads traffic evenly

## Technical Details

### XY Routing Algorithm
```python
def xy_route(source, dest, torus_width, torus_height):
    src_x, src_y = source
    dst_x, dst_y = dest
    
    # Phase 1: Route in X dimension
    if src_x != dst_x:
        # Choose shortest X direction (considering wraparound)
        direct_dist = abs(dst_x - src_x)
        wrap_dist = torus_width - direct_dist
        
        if direct_dist <= wrap_dist:
            next_x = src_x + (1 if dst_x > src_x else -1)
        else:
            next_x = src_x + (-1 if dst_x > src_x else 1)
        
        return (next_x % torus_width, src_y)
    
    # Phase 2: Route in Y dimension
    elif src_y != dst_y:
        # Similar logic for Y direction
        # ...
```

### Handshake Protocol
Same as RicoBit:
1. **REQ**: Sender sets pin_REQ=1
2. **ACK**: Receiver sets pin_ACK=1 if buffer available
3. **DATA**: Sender transfers packet via pin_DATA
4. **RESET**: Both sides reset pins after transfer

This maintains the same detailed simulation fidelity as RicoBit while providing a different topology and routing approach.