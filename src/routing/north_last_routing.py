"""
North-Last Routing Algorithm

A partially adaptive, turn-model routing algorithm that provides deadlock freedom
by restricting turns. North-Last is one of the Glass & Ni turn model algorithms.

Key Concept:
- All northward (NORTH) movements must be taken LAST
- Once a packet moves in any direction other than North, it can still turn North
- But once it turns North, it cannot turn to any other direction

Prohibited Turns FROM North:
- North → East ✗
- North → West ✗
- North → South ✗

Allowed Turns TO North:
- East → North ✓
- West → North ✓
- South → North ✓

Benefits:
- Deadlock-free
- More adaptive than XY routing
- Good for traffic patterns with northern destinations
- Multiple routing options before final northward phase

Drawbacks:
- May increase latency for northbound traffic
- Suboptimal for some source-destination pairs
"""

from typing import Optional, Tuple, List
from ..core.node import Node, Direction
from ..core.packet import Packet
from .base_routing import BaseRouting


class NorthLastRouting(BaseRouting):
    """
    North-Last Routing Algorithm
    
    Ensures deadlock freedom by deferring all northward movements to last.
    Provides partial adaptivity for better load balancing.
    
    Routing Rules:
    1. If not aligned in X-dimension: Can go EAST or WEST
    2. If not aligned in Y-dimension: Can go SOUTH (but save NORTH for last)
    3. Once aligned in X and only North remains: Go NORTH
    4. Once going NORTH: Cannot turn away
    """
    
    def __init__(self):
        """Initialize North-Last routing algorithm"""
        super().__init__(name="North-Last")
    
    def get_next_direction(
        self,
        current_node: Node,
        packet: Packet
    ) -> Optional[Direction]:
        """
        Determine next direction using North-Last routing
        
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
        needs_east = current_col < dest_col
        needs_west = current_col > dest_col
        needs_north = current_row > dest_row
        needs_south = current_row < dest_row
        
        # Phase 1: Handle East/West movements (X-dimension)
        if needs_east:
            if current_node.has_neighbor(Direction.EAST):
                return Direction.EAST
        
        if needs_west:
            if current_node.has_neighbor(Direction.WEST):
                return Direction.WEST
        
        # Phase 2: Handle South movements (but defer North)
        if needs_south:
            if current_node.has_neighbor(Direction.SOUTH):
                return Direction.SOUTH
        
        # Phase 3: Finally, handle North movements (last resort)
        if needs_north:
            if current_node.has_neighbor(Direction.NORTH):
                return Direction.NORTH
        
        return None
    
    def get_adaptive_direction(
        self,
        current_node: Node,
        packet: Packet,
        available_directions: List[Direction]
    ) -> Optional[Direction]:
        """
        Choose adaptively among available directions
        Avoids North unless it's the only option
        
        Args:
            current_node: Current node
            packet: Packet to route
            available_directions: List of valid directions
            
        Returns:
            Best direction based on North-Last policy and buffer availability
        """
        if not available_directions:
            return None
        
        # Filter out North if other options exist
        non_north_directions = [d for d in available_directions if d != Direction.NORTH]
        
        if non_north_directions:
            # Choose among non-North directions based on buffer occupancy
            return self._select_by_buffer_occupancy(current_node, non_north_directions)
        
        # If only North is available, take it
        return Direction.NORTH
    
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
    
    def is_valid_turn(
        self,
        from_direction: Direction,
        to_direction: Direction
    ) -> bool:
        """
        Check if a turn is allowed under North-Last rules
        
        Args:
            from_direction: Direction came from
            to_direction: Direction want to go
            
        Returns:
            True if turn is allowed
        """
        # Once going North, cannot turn away
        if from_direction == Direction.NORTH and to_direction != Direction.NORTH:
            return False
        
        # All other turns are allowed
        return True
