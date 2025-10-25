````markdown
# NoC Routing Algorithms

Comprehensive collection of routing algorithms for Network-on-Chip topologies.

---

## Overview

This module provides **8 routing algorithms** spanning from simple deterministic to advanced adaptive routing:

| Algorithm | Type | Adaptivity | Deadlock-Free | Complexity |
|-----------|------|------------|---------------|------------|
| XY Routing | Deterministic | None | ✓ | Low |
| YX Routing | Deterministic | None | ✓ | Low |
| West-First | Turn Model | Partial | ✓ | Medium |
| North-Last | Turn Model | Partial | ✓ | Medium |
| Negative-First | Turn Model | Partial | ✓ | Medium |
| Odd-Even | Parity-Based | High | ✓ | Medium |
| Fully Adaptive | Adaptive | Maximum | ✓* | High |
| Duato's Protocol | Hybrid | High | ✓ | High |

*Requires escape paths or virtual channels

---

## Quick Start

```python
from src.routing import (
    XYRouting,           # Deterministic
    WestFirstRouting,    # Turn model
    OddEvenRouting,      # Advanced adaptive
    DuatoRouting         # Duato's protocol
)

# Create routing algorithm
routing = WestFirstRouting()

# Use with packet
next_direction = routing.get_next_direction(current_node, packet)
```

---

## Algorithms

### 1. Deterministic Algorithms

#### XY Routing ⭐ Most Common

```python
routing = XYRouting()
```

- Routes X dimension first, then Y dimension
- Guaranteed minimal path (Manhattan distance)
- Simple, low hardware cost
- Best for light load, baseline performance

**Turn restrictions:** Only XY order allowed (X→X→...→Y→Y→...)

---

#### YX Routing

```python
routing = YXRouting()
```

- Routes Y dimension first, then X dimension
- Use with XY for load balancing (alternate packets)

---

### 2. Turn Model Algorithms (Partially Adaptive)

#### West-First Routing

```python
routing = WestFirstRouting()
```

**Rule:** All westward movements FIRST
- ✓ After West phase: can choose North/South/East adaptively
- ❌ Prohibited: Turning West after leaving West direction

**Best for:** Westward traffic patterns, better load distribution than XY

---

#### North-Last Routing

```python
routing = NorthLastRouting()
```

**Rule:** All northward movements LAST
- ✓ Before North: can choose East/West/South adaptively
- ❌ Prohibited: Turning away after going North

**Best for:** Northern destination traffic, flexible early routing

---

#### Negative-First Routing

```python
routing = NegativeFirstRouting()
```

**Rule:** Negative directions (West/North) before positive (East/South)
- Phase 1: Complete West and/or North (adaptive between them)
- Phase 2: Complete East and/or South (adaptive between them)

**Best for:** Balanced traffic, good adaptivity within phases

---

### 3. Advanced Adaptive Algorithms

#### Odd-Even Routing ⭐ High Performance

```python
routing = OddEvenRouting()
```

**Rule:** Turn restrictions based on column parity
- **Even columns:** No East→North, East→South turns
- **Odd columns:** No North→West, South→West turns

**Features:**
- High adaptivity (more than turn models)
- Better load balancing
- Near-optimal paths

**Best for:** High-performance systems, irregular traffic

---

#### Fully Adaptive Routing

```python
routing = FullyAdaptiveRouting(use_escape_path=True)

# Configure
routing.set_escape_threshold(0.8)  # Use XY escape when buffers > 80%
```

**Rule:** Choose ANY productive direction based on:
- Buffer availability (40% weight)
- Distance to destination (30% weight)
- Channel utilization (30% weight)

**Features:**
- Maximum adaptivity
- Real-time congestion awareness
- XY escape path for deadlock avoidance

**Best for:** Maximum performance, research, dynamic conditions

---

#### Duato's Protocol ⭐ Provably Deadlock-Free

```python
routing = DuatoRouting(adaptive_preference=0.7)

# Configure
routing.set_adaptive_preference(0.7)   # 70% prefer adaptive
routing.set_escape_threshold(0.75)     # Switch to escape at 75% full
```

**Rule:** Two channel types
- **Adaptive channels:** Any productive direction (buffer-based)
- **Escape channels:** XY routing (guaranteed deadlock-free)

**Theory:** Duato's theorem guarantees deadlock freedom with escape paths

**Best for:** Production systems, virtual channel networks, proven guarantees

---

## Usage Examples

### Basic Routing

```python
from src.routing import OddEvenRouting
from src.core.packet import Packet

# Create algorithm
routing = OddEvenRouting()

# Create packet
packet = Packet(
    packet_id=1,
    source=(0, 0),
    destination=(4, 4),
    data="Test"
)

# Get next hop
current_node = mesh[(2, 2)]
next_dir = routing.get_next_direction(current_node, packet)
print(f"Go {next_dir}")  # Output: Direction.EAST or SOUTH, etc.
```

### Compare Algorithms

```python
algorithms = [
    XYRouting(),
    WestFirstRouting(),
    OddEvenRouting(),
    FullyAdaptiveRouting()
]

for algo in algorithms:
    hops = algo.calculate_hops((0,0), (5,5))
    print(f"{algo.name}: {hops} hops")
```

### Dynamic Selection

```python
def get_routing(traffic_load):
    if traffic_load < 0.3:
        return XYRouting()              # Light load
    elif traffic_load < 0.7:
        return WestFirstRouting()       # Medium load
    else:
        return FullyAdaptiveRouting()   # Heavy load
```

---

## Performance Comparison

### Latency (Average Hops)

```
Light Load:   All algorithms ≈ Manhattan distance
Medium Load:  Adaptive < Turn Models < XY
Heavy Load:   Fully-Adaptive < Duato < Odd-Even < Turn Models < XY
```

### Throughput (Packets/Cycle)

```
XY < YX < Turn Models < Odd-Even < Duato ≈ Fully-Adaptive
```

### Hardware Cost

```
XY = YX < Turn Models < Odd-Even < Duato < Fully-Adaptive
```

---

## Algorithm Selection Guide

| Use Case | Recommended Algorithm | Why |
|----------|----------------------|-----|
| Baseline, low cost | XY Routing | Simple, proven, minimal hardware |
| Better than XY, still simple | West-First or North-Last | Partial adaptivity, moderate cost |
| High performance | Odd-Even | Best balance of adaptivity/complexity |
| Maximum performance | Fully Adaptive | Highest adaptivity, needs escape paths |
| Production with guarantees | Duato's Protocol | Proven deadlock-free, flexible |
| Load balancing | XY + YX (alternate) | Distribute traffic across paths |

---

## Creating Custom Algorithms

```python
from src.routing import BaseRouting
from src.core.node import Direction

class MyRouting(BaseRouting):
    def __init__(self):
        super().__init__(name="My-Algorithm")
    
    def get_next_direction(self, current_node, packet):
        current_pos = current_node.position
        dest_pos = packet.destination
        
        if self.is_at_destination(current_pos, dest_pos):
            return None
        
        # Your routing logic here
        # Return Direction.NORTH/SOUTH/EAST/WEST
        
        return Direction.EAST  # Example
```

---

## Topology Compatibility

All algorithms work with:
- ✅ Mesh topology (2D grid)
- ✅ Torus topology (wraparound)
- ✅ Custom 2D grids

Algorithms use `Node` interface for neighbor queries, making them topology-agnostic.

---

## Testing

```bash
# Run routing tests
python -m pytest tests/test_routing.py

# Compare algorithms demo
python examples/routing_comparison.py

# Specific algorithm
python examples/mesh_xy_routing_demo.py
```

---

## Key Concepts

### Deadlock Freedom
All implemented algorithms are deadlock-free through:
- Dimension ordering (XY, YX)
- Turn restrictions (Turn models)
- Column parity (Odd-Even)
- Escape paths (Fully Adaptive, Duato)

### Adaptivity Levels
- **None:** XY, YX (fixed paths)
- **Partial:** Turn models (restricted choices)
- **High:** Odd-Even (column-based flexibility)
- **Maximum:** Fully Adaptive, Duato (any productive direction)

### Manhattan Distance
Minimum hops between two points:
```
distance = |x₁ - x₂| + |y₁ - y₂|
```

All algorithms achieve or approximate this optimal distance.

---

## References

1. **Glass & Ni Turn Model**: West-First, North-Last, Negative-First
2. **Chiu's Odd-Even**: Odd-Even Routing
3. **Duato's Protocol**: Escape channel methodology
4. **Dally & Towles**: Principles of interconnection networks

---

## API Reference

### BaseRouting

```python
class BaseRouting:
    def get_next_direction(node, packet) -> Optional[Direction]
    def calculate_manhattan_distance(pos1, pos2) -> int
    def is_at_destination(current, dest) -> bool
```

### All Algorithms

```python
# Create instance
routing = AlgorithmName()

# Get next hop
direction = routing.get_next_direction(current_node, packet)

# Calculate hops
hops = routing.calculate_hops(source, destination)

# Check destination
at_dest = routing.is_at_destination(current_pos, dest_pos)
```

---

## License

Part of the Network_Rochers NoC Simulator project.

````