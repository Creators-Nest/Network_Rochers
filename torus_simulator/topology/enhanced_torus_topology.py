"""
Enhanced Torus Topology with improved node and interface handling
Based on Mesh topology enhanced architecture adapted for torus wraparound
"""

from typing import Dict, Tuple, List, Optional
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.enhanced_node import EnhancedNode
from routing.xy_router import XYRouter


class EnhancedTorusTopology:
    """
    Enhanced Torus Topology for Network-on-Chip
    
    Architecture improvements based on RiCoBiT and Mesh simulators:
    - Proper node-interface-buffer hierarchy
    - Bidirectional interface connections
    - Comprehensive routing table management
    - Advanced packet flow control
    - Node update stepping for simulation
    - Torus-specific wraparound connections
    
    Creates a 2D torus grid where each node has 4 interfaces (N, S, E, W)
    Each interface manages its own buffers and handshake protocol
    All edges wrap around to create torus topology
    """
    
    def __init__(self, width: int = 4, height: int = 4, buffer_capacity: int = 4):
        """
        Initialize torus topology
        
        Args:
            width: Number of nodes in X direction
            height: Number of nodes in Y direction
            buffer_capacity: Buffer size for each interface
        """
        self.width = width
        self.height = height
        self.buffer_capacity = buffer_capacity
        self.nodes: Dict[Tuple[int, int], EnhancedNode] = {}
        
        # Build topology
        self._create_nodes()
        self._create_connections()
        self._build_routing_tables()
    
    def _create_nodes(self):
        """Create all nodes in the torus"""
        for y in range(self.height):
            for x in range(self.width):
                address = (x, y)
                node = EnhancedNode(address)
                node.set_topology_dimensions(self.width, self.height)
                self.nodes[address] = node
    
    def _create_connections(self):
        """Create bidirectional connections with torus wraparound"""
        for y in range(self.height):
            for x in range(self.width):
                current_addr = (x, y)
                current_node = self.nodes[current_addr]
                
                # North neighbor (with wraparound)
                north_y = (y - 1) % self.height
                north_addr = (x, north_y)
                if north_addr not in current_node.interfaces:
                    current_node.add_interface(north_addr, self.buffer_capacity)
                
                # South neighbor (with wraparound)
                south_y = (y + 1) % self.height
                south_addr = (x, south_y)
                if south_addr not in current_node.interfaces:
                    current_node.add_interface(south_addr, self.buffer_capacity)
                
                # East neighbor (with wraparound)
                east_x = (x + 1) % self.width
                east_addr = (east_x, y)
                if east_addr not in current_node.interfaces:
                    current_node.add_interface(east_addr, self.buffer_capacity)
                
                # West neighbor (with wraparound)
                west_x = (x - 1) % self.width
                west_addr = (west_x, y)
                if west_addr not in current_node.interfaces:
                    current_node.add_interface(west_addr, self.buffer_capacity)
        
        print(f"Created {len(self.nodes)} nodes with wraparound connections")
    
    def _build_routing_tables(self):
        """Build XY routing tables for all nodes with torus wraparound"""
        router = XYRouter(self)
        router.build_routing_tables()
        
        for source_addr in self.nodes:
            source_node = self.nodes[source_addr]
            
            for dest_addr in self.nodes:
                if source_addr != dest_addr:
                    path = router.get_full_path(source_addr, dest_addr)
                    source_node.add_route(dest_addr, path)
        
        print(f"Routing tables built for {len(self.nodes)} nodes")
    
    def get_node(self, address: Tuple[int, int]) -> EnhancedNode:
        """Get node by address"""
        return self.nodes.get(address)
    
    def get_all_nodes(self) -> List[Tuple[int, int]]:
        """Get list of all node addresses"""
        return list(self.nodes.keys())
    
    def get_neighbors(self, address: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Get the 4 neighbors of a node in torus topology with wraparound"""
        x, y = address
        neighbors = []
        
        # North, South, East, West with wraparound
        neighbors.append((x, (y - 1) % self.height))  # North
        neighbors.append((x, (y + 1) % self.height))  # South
        neighbors.append(((x + 1) % self.width, y))   # East
        neighbors.append(((x - 1) % self.width, y))   # West
        
        return neighbors
    
    def manhattan_distance(self, addr1: Tuple[int, int], addr2: Tuple[int, int]) -> int:
        """
        Calculate Manhattan distance in torus (considering wraparound)
        
        For torus, we choose the shorter path in each dimension
        """
        x1, y1 = addr1
        x2, y2 = addr2
        
        # Calculate distance in X direction (considering wraparound)
        dx = min(abs(x2 - x1), self.width - abs(x2 - x1))
        
        # Calculate distance in Y direction (considering wraparound)
        dy = min(abs(y2 - y1), self.height - abs(y2 - y1))
        
        return dx + dy
    
    def update_all_nodes(self):
        """Update all nodes (one simulation step)"""
        for node in self.nodes.values():
            node.update()
    
    def get_topology_info(self) -> dict:
        """Get topology information for web interface"""
        return {
            'type': 'torus',
            'width': self.width,
            'height': self.height,
            'total_nodes': len(self.nodes),
            'buffer_capacity': self.buffer_capacity
        }
    
    def __str__(self):
        return f"Enhanced Torus Topology ({self.width}x{self.height}, {len(self.nodes)} nodes)"
