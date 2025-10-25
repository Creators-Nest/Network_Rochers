"""
Duato's Protocol Routing Algorithm

Implements Duato's deadlock avoidance protocol using escape channels.
This is a foundational adaptive routing technique that allows high adaptivity
while guaranteeing deadlock freedom.

Key Concept:
- Provides TWO types of routing channels:
  1. Adaptive channels: Can route adaptively using any algorithm
  2. Escape channels: Must use deadlock-free routing (e.g., XY)
- Packets can use adaptive channels when available
- When adaptive channels are full/congested, use escape channels
- Escape channels form a deadlock-free connected subnetwork

Duato's Theorem:
A routing algorithm is deadlock-free if:
1. There exists a connected escape channel subnetwork
2. The escape routing function is deadlock-free
3. Packets can always eventually access escape channels

Benefits:
- Provably deadlock-free
- High adaptivity (better than turn models)
- Flexible: can combine with any adaptive routing
- Works with virtual channels or separate physical channels

Drawbacks:
- Requires duplicate channels (virtual or physical)
- More complex buffer management
- Need to track channel types
"""

from typing import Optional, Tuple, List
from ..core.node import Node, Direction
from ..core.packet import Packet
from .base_routing import BaseRouting
from enum import Enum


class ChannelType(Enum):
    """Channel type for Duato's protocol"""
    ADAPTIVE = "adaptive"
    ESCAPE = "escape"


class DuatoRouting(BaseRouting):
    """
    Duato's Protocol Routing Algorithm
    
    Uses escape channels with deterministic routing alongside
    adaptive channels for high performance with deadlock freedom.
    
    Escape routing: XY routing (deadlock-free)
    Adaptive routing: Any productive direction based on buffer availability
    """
    
    def __init__(self, adaptive_preference: float = 0.7):
        """
        Initialize Duato routing algorithm
        
        Args:
            adaptive_preference: Probability of choosing adaptive over escape (0.0-1.0)
        """
        super().__init__(name="Duato")
        self.adaptive_preference = adaptive_preference
        self.escape_threshold = 0.75  # Use escape if adaptive buffers > 75% full
    
    def get_next_direction(
        self,
        current_node: Node,
        packet: Packet,
        prefer_adaptive: bool = True
    ) -> Optional[Direction]:
        """
        Determine next direction using Duato's protocol
        
        Args:
            current_node: Current node holding the packet
            packet: Packet to route
            prefer_adaptive: Whether to prefer adaptive channels
            
        Returns:
            Direction to forward packet, or None if at destination
        """
        current_pos = current_node.position
        dest_pos = packet.destination
        
        # Check if at destination
        if self.is_at_destination(current_pos, dest_pos):
            return None
        
        # Try adaptive routing first if preferred and available
        if prefer_adaptive and self._should_use_adaptive(current_node, packet):
            adaptive_dir = self._get_adaptive_direction(current_node, dest_pos)
            if adaptive_dir:
                return adaptive_dir
        
        # Fall back to escape routing (XY routing)
        return self._get_escape_direction(current_pos, dest_pos, current_node)
    
    def _should_use_adaptive(self, current_node: Node, packet: Packet) -> bool:
        """
        Decide whether to use adaptive routing
        
        Args:
            current_node: Current node
            packet: Packet to route
            
        Returns:
            True if should try adaptive routing
        """
        # Check if adaptive channels have reasonable availability
        dest_pos = packet.destination
        productive_dirs = self._get_productive_directions(current_node.position, dest_pos)
        
        available_count = 0
        low_occupancy_count = 0
        
        for direction in productive_dirs:
            if current_node.has_neighbor(direction):
                available_count += 1
                neighbor_pos = current_node.get_neighbor_position(direction)
                if neighbor_pos and neighbor_pos in current_node.neighbors:
                    neighbor = current_node.neighbors[neighbor_pos]
                    occupancy = len(neighbor.input_buffer.packets) / neighbor.input_buffer.capacity
                    
                    if occupancy < self.escape_threshold:
                        low_occupancy_count += 1
        
        # Use adaptive if at least one channel has low occupancy
        return low_occupancy_count > 0 if available_count > 0 else False
    
    def _get_adaptive_direction(
        self,
        current_node: Node,
        dest_pos: Tuple[int, int]
    ) -> Optional[Direction]:
        """
        Get direction using adaptive routing
        
        Chooses among all productive directions based on buffer availability
        
        Args:
            current_node: Current node
            dest_pos: Destination position
            
        Returns:
            Adaptive routing direction
        """
        productive_dirs = self._get_productive_directions(current_node.position, dest_pos)
        
        # Filter by availability
        available = [d for d in productive_dirs if current_node.has_neighbor(d)]
        
        if not available:
            return None
        
        # Choose direction with minimum buffer occupancy
        return self._select_by_buffer_occupancy(current_node, available)
    
    def _get_escape_direction(
        self,
        current_pos: Tuple[int, int],
        dest_pos: Tuple[int, int],
        current_node: Node
    ) -> Optional[Direction]:
        """
        Get direction using escape routing (XY routing)
        
        This ensures deadlock-free routing
        
        Args:
            current_pos: Current position
            dest_pos: Destination position
            current_node: Current node
            
        Returns:
            XY routing direction
        """
        current_row, current_col = current_pos
        dest_row, dest_col = dest_pos
        
        # XY routing: X dimension first, then Y dimension
        if current_col != dest_col:
            if current_col < dest_col and current_node.has_neighbor(Direction.EAST):
                return Direction.EAST
            elif current_col > dest_col and current_node.has_neighbor(Direction.WEST):
                return Direction.WEST
        
        if current_row != dest_row:
            if current_row < dest_row and current_node.has_neighbor(Direction.SOUTH):
                return Direction.SOUTH
            elif current_row > dest_row and current_node.has_neighbor(Direction.NORTH):
                return Direction.NORTH
        
        return None
    
    def _get_productive_directions(
        self,
        current_pos: Tuple[int, int],
        dest_pos: Tuple[int, int]
    ) -> List[Direction]:
        """
        Get all directions that make progress toward destination
        
        Args:
            current_pos: Current position
            dest_pos: Destination position
            
        Returns:
            List of productive directions
        """
        current_row, current_col = current_pos
        dest_row, dest_col = dest_pos
        
        productive = []
        
        if current_col < dest_col:
            productive.append(Direction.EAST)
        if current_col > dest_col:
            productive.append(Direction.WEST)
        if current_row > dest_row:
            productive.append(Direction.NORTH)
        if current_row < dest_row:
            productive.append(Direction.SOUTH)
        
        return productive
    
    def _select_by_buffer_occupancy(
        self,
        current_node: Node,
        directions: List[Direction]
    ) -> Optional[Direction]:
        """
        Select direction with least buffer occupancy
        
        Args:
            current_node: Current node
            directions: Available directions
            
        Returns:
            Direction with minimum buffer occupancy
        """
        if not directions:
            return None
        
        best_direction = None
        min_occupancy = float('inf')
        
        for direction in directions:
            neighbor_pos = current_node.get_neighbor_position(direction)
            if neighbor_pos and neighbor_pos in current_node.neighbors:
                neighbor = current_node.neighbors[neighbor_pos]
                occupancy = len(neighbor.input_buffer.packets) / neighbor.input_buffer.capacity
                
                if occupancy < min_occupancy:
                    min_occupancy = occupancy
                    best_direction = direction
        
        return best_direction if best_direction else directions[0]
    
    def calculate_hops(
        self,
        source: Tuple[int, int],
        destination: Tuple[int, int]
    ) -> int:
        """
        Calculate minimum number of hops (Manhattan distance)
        
        Args:
            source: Source position
            destination: Destination position
            
        Returns:
            Minimum number of hops
        """
        return self.calculate_manhattan_distance(source, destination)
    
    def set_adaptive_preference(self, preference: float):
        """
        Set preference for using adaptive channels
        
        Args:
            preference: Probability 0.0 (always escape) to 1.0 (always adaptive)
        """
        self.adaptive_preference = max(0.0, min(1.0, preference))
    
    def set_escape_threshold(self, threshold: float):
        """
        Set buffer occupancy threshold for switching to escape
        
        Args:
            threshold: Occupancy threshold 0.0 to 1.0
        """
        self.escape_threshold = max(0.0, min(1.0, threshold))
