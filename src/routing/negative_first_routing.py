"""
Negative-First Routing Algorithm

A partially adaptive, turn-model routing algorithm that provides deadlock freedom
by prioritizing negative direction movements.

Key Concept:
- Movements in "negative" directions (WEST or NORTH) must be taken FIRST
- After completing all negative movements, can freely move in positive directions
- Negative directions: WEST (decreasing column), NORTH (decreasing row)
- Positive directions: EAST (increasing column), SOUTH (increasing row)

Routing Phases:
1. Phase 1: Complete all WEST and/or NORTH movements
2. Phase 2: Complete all EAST and/or SOUTH movements (fully adaptive)

Benefits:
- Deadlock-free
- More adaptive than XY routing
- Good balance between adaptivity and simplicity
- Works well for distributed traffic patterns

Drawbacks:
- May cause longer paths in some cases
- Two distinct phases may limit flexibility
"""

from typing import Optional, Tuple, List
from ..core.node import Node, Direction
from ..core.packet import Packet
from .base_routing import BaseRouting


class NegativeFirstRouting(BaseRouting):
    """
    Negative-First Routing Algorithm
    
    Ensures deadlock freedom by handling negative direction movements first.
    Provides adaptivity in the positive direction phase.
    
    Routing Rules:
    1. Phase 1 (Negative): Handle WEST and/or NORTH first (in any order)
    2. Phase 2 (Positive): Handle EAST and/or SOUTH (in any order)
    3. Never return to negative directions after starting positive phase
    """
    
    def __init__(self):
        """Initialize Negative-First routing algorithm"""
        super().__init__(name="Negative-First")
    
    def get_next_direction(
        self,
        current_node: Node,
        packet: Packet
    ) -> Optional[Direction]:
        """
        Determine next direction using Negative-First routing
        
        Args:
            current_node: Current node holding the packet
            packet: Packet to route
            
        Returns:
            Direction to forward packet, or None if at destination
        """
        current_pos = current_node.position
        dest_pos = packet.destination
        
        # Check if at destination
        if self.is_at_destination(current_pos, dest_pos):
            return None
        
        current_row, current_col = current_pos
        dest_row, dest_col = dest_pos
        
        # Calculate what movements are needed
        needs_west = current_col > dest_col  # Negative X
        needs_north = current_row > dest_row  # Negative Y
        needs_east = current_col < dest_col   # Positive X
        needs_south = current_row < dest_row  # Positive Y
        
        # Phase 1: Handle negative directions first (WEST or NORTH)
        if needs_west or needs_north:
            # Adaptively choose between West and North if both needed
            if needs_west and needs_north:
                return self._choose_negative_direction(current_node, needs_west, needs_north)
            elif needs_west:
                if current_node.has_neighbor(Direction.WEST):
                    return Direction.WEST
            elif needs_north:
                if current_node.has_neighbor(Direction.NORTH):
                    return Direction.NORTH
        
        # Phase 2: Handle positive directions (EAST or SOUTH)
        # Can adaptively choose between them
        if needs_east and needs_south:
            return self._choose_positive_direction(current_node, needs_east, needs_south)
        elif needs_east:
            if current_node.has_neighbor(Direction.EAST):
                return Direction.EAST
        elif needs_south:
            if current_node.has_neighbor(Direction.SOUTH):
                return Direction.SOUTH
        
        return None
    
    def _choose_negative_direction(
        self,
        current_node: Node,
        needs_west: bool,
        needs_north: bool
    ) -> Optional[Direction]:
        """
        Adaptively choose between WEST and NORTH based on buffer availability
        
        Args:
            current_node: Current node
            needs_west: Whether westward movement is needed
            needs_north: Whether northward movement is needed
            
        Returns:
            WEST or NORTH based on buffer occupancy
        """
        directions = []
        if needs_west and current_node.has_neighbor(Direction.WEST):
            directions.append(Direction.WEST)
        if needs_north and current_node.has_neighbor(Direction.NORTH):
            directions.append(Direction.NORTH)
        
        return self._select_by_buffer_occupancy(current_node, directions)
    
    def _choose_positive_direction(
        self,
        current_node: Node,
        needs_east: bool,
        needs_south: bool
    ) -> Optional[Direction]:
        """
        Adaptively choose between EAST and SOUTH based on buffer availability
        
        Args:
            current_node: Current node
            needs_east: Whether eastward movement is needed
            needs_south: Whether southward movement is needed
            
        Returns:
            EAST or SOUTH based on buffer occupancy
        """
        directions = []
        if needs_east and current_node.has_neighbor(Direction.EAST):
            directions.append(Direction.EAST)
        if needs_south and current_node.has_neighbor(Direction.SOUTH):
            directions.append(Direction.SOUTH)
        
        return self._select_by_buffer_occupancy(current_node, directions)
    
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
            source: Source position (row, col)
            destination: Destination position (row, col)
            
        Returns:
            Minimum number of hops
        """
        return self.calculate_manhattan_distance(source, destination)
    
    def is_in_negative_phase(
        self,
        current_pos: Tuple[int, int],
        dest_pos: Tuple[int, int]
    ) -> bool:
        """
        Check if still in negative direction phase
        
        Args:
            current_pos: Current position (row, col)
            dest_pos: Destination position (row, col)
            
        Returns:
            True if negative movements still needed
        """
        current_row, current_col = current_pos
        dest_row, dest_col = dest_pos
        
        needs_west = current_col > dest_col
        needs_north = current_row > dest_row
        
        return needs_west or needs_north
