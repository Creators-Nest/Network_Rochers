"""
Odd-Even Routing Algorithm

An adaptive routing algorithm that provides deadlock freedom by restricting
certain turns based on the column parity (odd or even).

Key Concept:
- Divides mesh columns into ODD and EVEN columns
- Different turn restrictions apply based on current column parity
- Allows more adaptivity than turn models while maintaining deadlock freedom

Turn Restrictions:
At EVEN columns:
- Cannot turn from East to North (EN turn prohibited)
- Cannot turn from East to South (ES turn prohibited)

At ODD columns:
- Cannot turn from North to West (NW turn prohibited)
- Cannot turn from South to West (SW turn prohibited)

Benefits:
- Deadlock-free
- Highly adaptive (more than turn models)
- Better load balancing than XY routing
- Can achieve near-optimal paths
- Works well with irregular traffic

Drawbacks:
- More complex turn logic
- Column-dependent restrictions
- Requires tracking current column parity
"""

from typing import Optional, Tuple, List
from ..core.node import Node, Direction
from ..core.packet import Packet
from .base_routing import BaseRouting


class OddEvenRouting(BaseRouting):
    """
    Odd-Even Routing Algorithm
    
    Provides high adaptivity while maintaining deadlock freedom through
    column-parity-based turn restrictions.
    
    Routing Rules:
    - At EVEN columns: No EN, ES turns
    - At ODD columns: No NW, SW turns
    - All other turns allowed adaptively
    """
    
    def __init__(self):
        """Initialize Odd-Even routing algorithm"""
        super().__init__(name="Odd-Even")
    
    def get_next_direction(
        self,
        current_node: Node,
        packet: Packet
    ) -> Optional[Direction]:
        """
        Determine next direction using Odd-Even routing
        
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
        
        # Calculate needed movements
        needs_east = current_col < dest_col
        needs_west = current_col > dest_col
        needs_north = current_row > dest_row
        needs_south = current_row < dest_row
        
        # Get valid directions based on odd-even restrictions
        valid_directions = self._get_valid_directions(
            current_col, needs_east, needs_west, needs_north, needs_south
        )
        
        # Filter by neighbor availability
        available_directions = [
            d for d in valid_directions 
            if current_node.has_neighbor(d)
        ]
        
        if not available_directions:
            return None
        
        # Choose adaptively based on buffer occupancy
        return self._select_by_buffer_occupancy(current_node, available_directions)
    
    def _get_valid_directions(
        self,
        current_col: int,
        needs_east: bool,
        needs_west: bool,
        needs_north: bool,
        needs_south: bool
    ) -> List[Direction]:
        """
        Get valid directions based on odd-even restrictions
        
        Args:
            current_col: Current column index
            needs_east: Whether eastward movement needed
            needs_west: Whether westward movement needed
            needs_north: Whether northward movement needed
            needs_south: Whether southward movement needed
            
        Returns:
            List of valid directions under odd-even rules
        """
        valid = []
        is_even_col = (current_col % 2 == 0)
        
        # At EVEN columns: No EN, ES turns (East to North/South)
        # At ODD columns: No NW, SW turns (North/South to West)
        
        if is_even_col:
            # Even column restrictions
            if needs_east:
                valid.append(Direction.EAST)
            if needs_west:
                valid.append(Direction.WEST)
            # Can go North/South only if not coming from East
            # (but we don't track previous direction, so allow if needed for progress)
            if needs_north and not needs_east:
                valid.append(Direction.NORTH)
            if needs_south and not needs_east:
                valid.append(Direction.SOUTH)
            # If needs East and North/South, prioritize East
            if needs_east and (needs_north or needs_south):
                # Must go East first at even column
                return [Direction.EAST]
        else:
            # Odd column restrictions
            if needs_east:
                valid.append(Direction.EAST)
            if needs_north:
                valid.append(Direction.NORTH)
            if needs_south:
                valid.append(Direction.SOUTH)
            # Can go West only if not coming from North/South
            if needs_west and not (needs_north or needs_south):
                valid.append(Direction.WEST)
            # If needs West and North/South, must resolve North/South first
            if needs_west and (needs_north or needs_south):
                # Handle North/South first at odd column
                if needs_north:
                    valid.append(Direction.NORTH)
                if needs_south:
                    valid.append(Direction.SOUTH)
                # Remove West if added
                if Direction.WEST in valid:
                    valid.remove(Direction.WEST)
        
        # If no valid directions yet, allow any needed direction (fallback)
        if not valid:
            if needs_east:
                valid.append(Direction.EAST)
            if needs_west:
                valid.append(Direction.WEST)
            if needs_north:
                valid.append(Direction.NORTH)
            if needs_south:
                valid.append(Direction.SOUTH)
        
        return valid
    
    def _select_by_buffer_occupancy(
        self,
        current_node: Node,
        directions: List[Direction]
    ) -> Optional[Direction]:
        """
        Select direction with least buffer occupancy (adaptive choice)
        
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
        
        Odd-Even can achieve minimal or near-minimal paths
        
        Args:
            source: Source position (row, col)
            destination: Destination position (row, col)
            
        Returns:
            Minimum number of hops
        """
        return self.calculate_manhattan_distance(source, destination)
    
    def is_valid_turn(
        self,
        current_col: int,
        from_direction: Direction,
        to_direction: Direction
    ) -> bool:
        """
        Check if a turn is valid under odd-even restrictions
        
        Args:
            current_col: Current column index
            from_direction: Direction coming from
            to_direction: Direction going to
            
        Returns:
            True if turn is allowed
        """
        is_even_col = (current_col % 2 == 0)
        
        if is_even_col:
            # Even column: No EN (East→North) or ES (East→South) turns
            if from_direction == Direction.EAST:
                if to_direction in [Direction.NORTH, Direction.SOUTH]:
                    return False
        else:
            # Odd column: No NW (North→West) or SW (South→West) turns
            if from_direction in [Direction.NORTH, Direction.SOUTH]:
                if to_direction == Direction.WEST:
                    return False
        
        return True
    
    def is_even_column(self, col: int) -> bool:
        """Check if column is even"""
        return col % 2 == 0
    
    def is_odd_column(self, col: int) -> bool:
        """Check if column is odd"""
        return col % 2 == 1
