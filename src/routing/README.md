# XY Routing Algorithm for Mesh Topology

## Overview

The XY Routing algorithm (also known as dimension-ordered routing) is a **deterministic, deadlock-free** routing algorithm designed for 2D mesh networks-on-chip (NoCs).

## Algorithm Description

### Routing Strategy

XY routing uses a simple two-phase approach:

1. **Phase 1 (X-dimension)**: Route horizontally (East/West) until the packet's column matches the destination column
2. **Phase 2 (Y-dimension)**: Route vertically (North/South) until the packet reaches the destination

### Pseudocode

```
function XY_Route(current_position, destination):
    current_row, current_col = current_position
    dest_row, dest_col = destination
    
    // Phase 1: X-dimension routing
    if current_col < dest_col:
        return EAST
    else if current_col > dest_col:
        return WEST
    
    // Phase 2: Y-dimension routing
    else if current_row < dest_row:
        return SOUTH
    else if current_row > dest_row:
        return NORTH
    
    // At destination
    else:
        return None
```

## Key Properties

### ✅ Advantages

1. **Deadlock-Free**: The dimension-ordered approach prevents circular dependencies
2. **Simple Implementation**: Easy to implement in hardware and software
3. **Deterministic**: Same path is always taken for a given source-destination pair
4. **Minimal Path**: Uses Manhattan distance (shortest path in mesh)
5. **Low Overhead**: No routing tables needed, decisions made locally

### ⚠️ Disadvantages

1. **Load Imbalance**: All packets follow the same path, which can cause congestion
2. **No Adaptivity**: Cannot avoid congested or faulty links
3. **Hot Spots**: Central nodes may experience higher traffic

## Usage Example

```python
from core.node import Node, Direction
from core.packet import Packet
from routing.xy_routing import XYRouting

# Create routing algorithm
xy_routing = XYRouting()

# Create packet
packet = Packet(source=(0, 0), destination=(3, 3))

# Get next direction at current node
current_node = mesh_nodes[(1, 1)]
next_direction = xy_routing.get_next_direction(current_node, packet)

# Calculate expected hops
hops = xy_routing.calculate_hops((0, 0), (3, 3))  # Returns 6

# Get complete routing path
path = xy_routing.get_routing_path((0, 0), (3, 3))
# Returns: [EAST, EAST, EAST, SOUTH, SOUTH, SOUTH]
```

## Routing Examples

### Example 1: Corner to Corner
```
Source: (0, 0)  →  Destination: (3, 3)
Path: EAST → EAST → EAST → SOUTH → SOUTH → SOUTH
Hops: 6
```

### Example 2: Horizontal Movement
```
Source: (1, 0)  →  Destination: (1, 3)
Path: EAST → EAST → EAST
Hops: 3
```

### Example 3: Vertical Movement
```
Source: (0, 2)  →  Destination: (3, 2)
Path: SOUTH → SOUTH → SOUTH
Hops: 3
```

### Example 4: Diagonal Movement
```
Source: (0, 0)  →  Destination: (2, 2)
Path: EAST → EAST → SOUTH → SOUTH
Hops: 4
```

## Visual Representation

```
4x4 Mesh Network - XY Routing from (0,0) to (3,3)

  0   1   2   3  (columns)
0 S → → → →     Source (S)
1     ↓   ↓
2     ↓   ↓
3     → → D     Destination (D)
(rows)

Path: (0,0) → (0,1) → (0,2) → (0,3) → (1,3) → (2,3) → (3,3)
```

## YX Routing (Alternative)

The framework also includes **YX Routing**, which reverses the order:

1. **Phase 1 (Y-dimension)**: Route vertically first (North/South)
2. **Phase 2 (X-dimension)**: Route horizontally (East/West)

### Comparison

| Feature | XY Routing | YX Routing |
|---------|-----------|------------|
| X-phase first | ✓ | ✗ |
| Y-phase first | ✗ | ✓ |
| Hops | Same (Manhattan distance) | Same |
| Path | Different | Different |
| Use case | Primary routing | Load balancing |

### Load Balancing Strategy

You can use both XY and YX routing together:
- Alternate between algorithms for different packets
- Distribute traffic across different paths
- Reduce congestion at hot spots

```python
# Alternate based on packet ID
if packet.packet_id % 2 == 0:
    routing = XYRouting()
else:
    routing = YXRouting()
```

## Deadlock-Free Proof

XY routing is deadlock-free because:

1. **Channel Dependency Graph is Acyclic**: 
   - X-channels can only depend on other X-channels in the same direction
   - Y-channels can only depend on other Y-channels in the same direction
   - Y-channels never depend on X-channels

2. **No Circular Dependencies**:
   - Packets always move in X-dimension first, then Y-dimension
   - No packet ever needs to return to X-dimension after moving in Y-dimension
   - This breaks any potential cycles in the channel dependency graph

## Performance Metrics

For a N×N mesh using XY routing:

- **Average Hops**: N/2 + N/2 = N (for uniform random traffic)
- **Maximum Hops**: 2(N-1) (corner to opposite corner)
- **Minimum Hops**: 0 (same node)
- **Hop Count**: Manhattan distance = |x₁ - x₂| + |y₁ - y₂|

## Integration with Mesh Topology

The XY routing algorithm integrates seamlessly with the Mesh topology:

1. **Node Structure**: Uses North, South, East, West directions from `Node` class
2. **Packet Tracking**: Automatically records path in `Packet.path`
3. **Buffer Management**: Works with node input/output buffers
4. **Statistics**: Tracks routing decisions and hop counts

## Testing

Run the demo to see XY routing in action:

```bash
python examples/mesh_xy_routing_demo.py
```

This will demonstrate:
- Basic routing from corner to corner
- Path visualization
- Comparison with YX routing
- Multiple routing scenarios

## References

- Dally, W. J., & Towles, B. (2004). Principles and practices of interconnection networks.
- Duato, J., Yalamanchili, S., & Ni, L. (2002). Interconnection networks: an engineering approach.
