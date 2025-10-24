"""
Example demonstrating XY Routing for Mesh Topology

This example shows how to:
1. Create nodes
2. Set up XY routing
3. Route a packet through the mesh
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from core.node import Node, Direction
from core.packet import Packet
from routing.xy_routing import XYRouting


def create_simple_mesh(rows: int, cols: int) -> dict:
    """
    Create a simple mesh network
    
    Args:
        rows: Number of rows
        cols: Number of columns
        
    Returns:
        Dictionary mapping (row, col) to Node
    """
    nodes = {}
    
    # Create all nodes
    for row in range(rows):
        for col in range(cols):
            nodes[(row, col)] = Node(position=(row, col))
    
    # Connect nodes (mesh topology)
    for row in range(rows):
        for col in range(cols):
            current_node = nodes[(row, col)]
            
            # North neighbor (row - 1)
            if row > 0:
                current_node.add_neighbor(Direction.NORTH, nodes[(row - 1, col)])
            
            # South neighbor (row + 1)
            if row < rows - 1:
                current_node.add_neighbor(Direction.SOUTH, nodes[(row + 1, col)])
            
            # East neighbor (col + 1)
            if col < cols - 1:
                current_node.add_neighbor(Direction.EAST, nodes[(row, col + 1)])
            
            # West neighbor (col - 1)
            if col > 0:
                current_node.add_neighbor(Direction.WEST, nodes[(row, col - 1)])
    
    return nodes


def demonstrate_xy_routing():
    """Demonstrate XY routing algorithm"""
    
    print("=" * 60)
    print("XY Routing Algorithm Demo for Mesh Topology")
    print("=" * 60)
    
    # Create a 4x4 mesh
    mesh_size = 4
    nodes = create_simple_mesh(mesh_size, mesh_size)
    
    # Create XY routing algorithm
    xy_routing = XYRouting()
    
    # Create a packet from (0,0) to (3,3)
    source = (0, 0)
    destination = (3, 3)
    
    packet = Packet(
        source=source,
        destination=destination,
        payload={"message": "Hello from corner to corner!"},
        creation_time=0
    )
    
    print(f"\nPacket Details:")
    print(f"  ID: {packet.packet_id}")
    print(f"  Source: {source}")
    print(f"  Destination: {destination}")
    print(f"  Expected hops: {xy_routing.calculate_hops(source, destination)}")
    
    # Calculate complete path
    path_directions = xy_routing.get_routing_path(source, destination)
    print(f"\nRouting Path (Directions): {[d.value for d in path_directions]}")
    
    # Simulate packet traversal
    print(f"\n{'Step':<6} {'Current':^12} {'Direction':^12} {'Next':^12}")
    print("-" * 50)
    
    current_pos = source
    step = 0
    
    while current_pos != destination:
        current_node = nodes[current_pos]
        
        # Get next direction
        direction = xy_routing.get_next_direction(current_node, packet)
        
        if direction is None:
            break
        
        # Get next node position
        next_node = current_node.get_neighbor(direction)
        next_pos = next_node.position if next_node else None
        
        print(f"{step:<6} {str(current_pos):^12} {direction.value:^12} {str(next_pos):^12}")
        
        # Move to next position
        if next_pos:
            packet.add_hop(next_pos, step + 1)
            current_pos = next_pos
        
        step += 1
    
    print("-" * 50)
    print(f"\nFinal Path: {' → '.join([str(p) for p in packet.path])}")
    print(f"Total Hops: {packet.hops}")
    print(f"Packet Status: {packet.status.value}")
    
    # Demonstrate different source-destination pairs
    print("\n" + "=" * 60)
    print("Additional Routing Examples")
    print("=" * 60)
    
    test_cases = [
        ((0, 0), (0, 3)),  # Horizontal
        ((0, 0), (3, 0)),  # Vertical
        ((1, 1), (2, 2)),  # Diagonal
        ((3, 0), (0, 3)),  # Corner to corner
    ]
    
    for src, dst in test_cases:
        hops = xy_routing.calculate_hops(src, dst)
        path_dirs = xy_routing.get_routing_path(src, dst)
        
        print(f"\n{src} → {dst}:")
        print(f"  Hops: {hops}")
        print(f"  Path: {' → '.join([d.value for d in path_dirs])}")


def compare_xy_yx_routing():
    """Compare XY and YX routing algorithms"""
    
    print("\n" + "=" * 60)
    print("XY vs YX Routing Comparison")
    print("=" * 60)
    
    from routing.xy_routing import YXRouting
    
    xy_routing = XYRouting()
    yx_routing = YXRouting()
    
    source = (0, 0)
    destination = (2, 3)
    
    xy_path = xy_routing.get_routing_path(source, destination)
    yx_path = yx_routing.get_routing_path(source, destination)
    
    print(f"\nRouting from {source} to {destination}:")
    print(f"\nXY Routing (X first, then Y):")
    print(f"  Path: {' → '.join([d.value for d in xy_path])}")
    print(f"  Hops: {len(xy_path)}")
    
    print(f"\nYX Routing (Y first, then X):")
    print(f"  Path: {' → '.join([d.value for d in yx_path])}")
    print(f"  Hops: {len(yx_path)}")
    
    print(f"\nNote: Both have same hop count (Manhattan distance)")
    print(f"      but take different paths through the network.")


if __name__ == "__main__":
    demonstrate_xy_routing()
    compare_xy_yx_routing()
    
    print("\n" + "=" * 60)
    print("Demo Complete!")
    print("=" * 60)
