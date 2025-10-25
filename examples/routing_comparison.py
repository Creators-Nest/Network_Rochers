"""
Routing Algorithm Comparison Demo

Demonstrates all implemented routing algorithms and compares their:
- Path selection
- Hop count
- Turn restrictions
- Adaptivity

Run this to understand the differences between algorithms.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.routing import (
    XYRouting,
    YXRouting,
    WestFirstRouting,
    NorthLastRouting,
    NegativeFirstRouting,
    OddEvenRouting,
    FullyAdaptiveRouting,
    DuatoRouting
)
from src.core.node import Node, Direction
from src.core.packet import Packet
from src.core.buffer import Buffer


def create_test_mesh(rows=6, cols=6):
    """Create a simple mesh network for testing"""
    nodes = {}
    
    # Create nodes
    for row in range(rows):
        for col in range(cols):
            pos = (row, col)
            nodes[pos] = Node(
                position=pos,
                buffer_capacity=10
            )
    
    # Connect neighbors
    for row in range(rows):
        for col in range(cols):
            pos = (row, col)
            node = nodes[pos]
            
            # North neighbor (row - 1)
            if row > 0:
                north_pos = (row - 1, col)
                node.neighbors[Direction.NORTH] = nodes[north_pos]
            
            # South neighbor (row + 1)
            if row < rows - 1:
                south_pos = (row + 1, col)
                node.neighbors[Direction.SOUTH] = nodes[south_pos]
            
            # West neighbor (col - 1)
            if col > 0:
                west_pos = (row, col - 1)
                node.neighbors[Direction.WEST] = nodes[west_pos]
            
            # East neighbor (col + 1)
            if col < cols - 1:
                east_pos = (row, col + 1)
                node.neighbors[Direction.EAST] = nodes[east_pos]
    
    return nodes


def trace_path(routing, nodes, source, destination):
    """
    Trace the complete path taken by a routing algorithm
    
    Returns:
        List of positions forming the path
    """
    path = [source]
    current_pos = source
    max_hops = 100  # Safety limit
    hops = 0
    
    while current_pos != destination and hops < max_hops:
        current_node = nodes[current_pos]
        packet = Packet(
            source=source,
            destination=destination,
            payload="test",
            priority=1
        )
        
        next_direction = routing.get_next_direction(current_node, packet)
        
        if next_direction is None:
            break
        
        # Get next position based on direction
        row, col = current_pos
        if next_direction == Direction.NORTH:
            next_pos = (row - 1, col)
        elif next_direction == Direction.SOUTH:
            next_pos = (row + 1, col)
        elif next_direction == Direction.EAST:
            next_pos = (row, col + 1)
        elif next_direction == Direction.WEST:
            next_pos = (row, col - 1)
        else:
            break
        
        if next_pos in nodes:
            path.append(next_pos)
            current_pos = next_pos
            hops += 1
        else:
            break
    
    return path


def print_path(path, algorithm_name):
    """Pretty print a path"""
    print(f"\n{algorithm_name}:")
    print(f"  Hops: {len(path) - 1}")
    print(f"  Path: {' → '.join(str(pos) for pos in path)}")


def visualize_path_on_grid(path, rows, cols, source, destination):
    """Create ASCII visualization of path on grid"""
    grid = [['·' for _ in range(cols)] for _ in range(rows)]
    
    # Mark path
    for pos in path:
        grid[pos[0]][pos[1]] = '•'
    
    # Mark source and destination
    grid[source[0]][source[1]] = 'S'
    grid[destination[0]][destination[1]] = 'D'
    
    # Print grid
    print("\n  Grid:")
    for row in grid:
        print("    " + ' '.join(row))


def compare_algorithms():
    """Compare all routing algorithms"""
    print("=" * 70)
    print("ROUTING ALGORITHM COMPARISON")
    print("=" * 70)
    
    # Create test mesh
    rows, cols = 6, 6
    nodes = create_test_mesh(rows, cols)
    
    # Test scenarios
    test_cases = [
        ((0, 0), (5, 5), "Corner to Corner (SE)"),
        ((5, 5), (0, 0), "Corner to Corner (NW)"),
        ((0, 5), (5, 0), "Corner to Corner (SW)"),
        ((2, 2), (4, 4), "Center to SE"),
        ((3, 1), (1, 4), "Complex Route"),
    ]
    
    # Algorithms to test
    algorithms = [
        XYRouting(),
        YXRouting(),
        WestFirstRouting(),
        NorthLastRouting(),
        NegativeFirstRouting(),
        OddEvenRouting(),
        FullyAdaptiveRouting(use_escape_path=True),
        DuatoRouting(adaptive_preference=0.7),
    ]
    
    # Run tests
    for source, destination, description in test_cases:
        print(f"\n{'=' * 70}")
        print(f"Test Case: {description}")
        print(f"Source: {source} → Destination: {destination}")
        print(f"Manhattan Distance: {abs(source[0] - destination[0]) + abs(source[1] - destination[1])} hops")
        print('=' * 70)
        
        for algo in algorithms:
            path = trace_path(algo, nodes, source, destination)
            print_path(path, algo.name)
        
        # Show visual for XY routing (baseline)
        xy_path = trace_path(XYRouting(), nodes, source, destination)
        visualize_path_on_grid(xy_path, rows, cols, source, destination)
    
    # Algorithm characteristics summary
    print("\n" + "=" * 70)
    print("ALGORITHM CHARACTERISTICS")
    print("=" * 70)
    
    characteristics = [
        ("XY Routing", "Deterministic", "None", "Minimal", "Low"),
        ("YX Routing", "Deterministic", "None", "Minimal", "Low"),
        ("West-First", "Turn Model", "Partial", "Minimal*", "Medium"),
        ("North-Last", "Turn Model", "Partial", "Minimal*", "Medium"),
        ("Negative-First", "Turn Model", "Partial", "Minimal*", "Medium"),
        ("Odd-Even", "Parity-Based", "High", "Near-Minimal", "Medium"),
        ("Fully-Adaptive", "Adaptive", "Maximum", "Near-Minimal", "High"),
        ("Duato", "Hybrid", "High", "Near-Minimal", "High"),
    ]
    
    print(f"\n{'Algorithm':<18} {'Type':<15} {'Adaptivity':<12} {'Path':<13} {'Complexity':<10}")
    print("-" * 70)
    for name, type_, adapt, path, complex_ in characteristics:
        print(f"{name:<18} {type_:<15} {adapt:<12} {path:<13} {complex_:<10}")
    
    print("\n* = Can achieve minimal in most cases")
    
    # Performance insights
    print("\n" + "=" * 70)
    print("PERFORMANCE INSIGHTS")
    print("=" * 70)
    
    print("""
✅ Best for Light Load:
   - XY Routing (simplest, lowest power)

✅ Best for Medium Load:
   - West-First, North-Last (good balance)
   - Odd-Even (higher performance)

✅ Best for Heavy Load:
   - Fully-Adaptive (maximum throughput)
   - Duato's Protocol (proven guarantees)

✅ Best for Fault Tolerance:
   - Fully-Adaptive (can route around failures)
   - Odd-Even (multiple path options)

✅ Best for Hardware Cost:
   - XY Routing (minimal logic gates)
   - YX Routing (same as XY)

✅ Best for Load Balancing:
   - Odd-Even (high adaptivity)
   - Alternate XY + YX (simple distribution)
    """)


if __name__ == "__main__":
    compare_algorithms()
    
    print("\n" + "=" * 70)
    print("Comparison complete! Check paths above to see algorithm differences.")
    print("=" * 70)
