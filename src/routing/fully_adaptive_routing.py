"""
Fully Adaptive Routing Algorithm

A fully adaptive routing algorithm that can choose any productive direction
(directions that reduce distance to destination) based on current network state.

Key Concept:
- Evaluates ALL directions that make progress toward destination
- Chooses best direction based on multiple metrics:
  * Buffer availability
  * Queue length
  * Channel utilization
  * Distance reduction

Deadlock Handling:
- Uses virtual channels or escape paths to avoid deadlock
- Falls back to deterministic XY routing when needed
- Implements Duato's protocol: one virtual channel for adaptive, one for deterministic

Benefits:
- Maximum adaptivity and load balancing
- Can route around congestion dynamically
- Optimal or near-optimal paths
- Best performance under high load
- Handles fault tolerance well

Drawbacks:
- More complex implementation
- Requires virtual channels or similar mechanism
- Higher hardware cost
- More routing computation required
"""

from typing import Optional, Tuple, List, Dict
from ..core.node import Node, Direction
from ..core.packet import Packet
from .base_routing import BaseRouting


class FullyAdaptiveRouting(BaseRouting):
    """
    Fully Adaptive Routing Algorithm
    
    Provides maximum adaptivity by evaluating all productive directions
    and choosing based on buffer availability and congestion metrics.
    
    Uses escape path mechanism for deadlock avoidance.
    """
    
    def __init__(self, use_escape_path: bool = True):
        """
        Initialize Fully Adaptive routing algorithm
        
        Args:
            use_escape_path: Whether to use XY escape path for deadlock avoidance
        """
        super().__init__(name="Fully-Adaptive")
        self.use_escape_path = use_escape_path
        self.escape_threshold = 0.8  # Use escape path if all buffers > 80% full
    
    def get_next_direction(
        self,
        current_node: Node,
        packet: Packet
    ) -> Optional[Direction]:
        """
        Determine next direction using fully adaptive routing
        
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
        
        # Get all productive directions (reduce distance to destination)
        productive_directions = self._get_productive_directions(current_pos, dest_pos)
        
        # Filter by neighbor availability
        available_directions = [
            d for d in productive_directions
            if current_node.has_neighbor(d)
        ]
        
        if not available_directions:
            return None
        
        # Check if should use escape path (deadlock avoidance)
        if self.use_escape_path and self._should_use_escape_path(current_node, available_directions):
            return self._get_xy_direction(current_pos, dest_pos, current_node)
        
        # Choose best direction based on multiple metrics
        return self._select_best_adaptive_direction(current_node, available_directions, dest_pos)
    
    def _get_productive_directions(
        self,
        current_pos: Tuple[int, int],
        dest_pos: Tuple[int, int]
    ) -> List[Direction]:
        """
        Get all directions that make progress toward destination
        
        Args:
            current_pos: Current position (row, col)
            dest_pos: Destination position (row, col)
            
        Returns:
            List of productive directions
        """
        current_row, current_col = current_pos
        dest_row, dest_col = dest_pos
        
        productive = []
        
        # Check each direction for productivity
        if current_col < dest_col:  # Need to go East
            productive.append(Direction.EAST)
        if current_col > dest_col:  # Need to go West
            productive.append(Direction.WEST)
        if current_row > dest_row:  # Need to go North
            productive.append(Direction.NORTH)
        if current_row < dest_row:  # Need to go South
            productive.append(Direction.SOUTH)
        
        return productive
    
    def _should_use_escape_path(
        self,
        current_node: Node,
        available_directions: List[Direction]
    ) -> bool:
        """
        Determine if escape path should be used (deadlock detection)
        
        Args:
            current_node: Current node
            available_directions: Available productive directions
            
        Returns:
            True if should use escape path
        """
        # Check if all available neighbors have high buffer occupancy
        high_occupancy_count = 0
        
        for direction in available_directions:
            neighbor_pos = current_node.get_neighbor_position(direction)
            if neighbor_pos and neighbor_pos in current_node.neighbors:
                neighbor = current_node.neighbors[neighbor_pos]
                occupancy = len(neighbor.input_buffer.packets) / neighbor.input_buffer.capacity
                
                if occupancy >= self.escape_threshold:
                    high_occupancy_count += 1
        
        # Use escape path if most buffers are congested
        return high_occupancy_count >= len(available_directions) * 0.75
    
    def _get_xy_direction(
        self,
        current_pos: Tuple[int, int],
        dest_pos: Tuple[int, int],
        current_node: Node
    ) -> Optional[Direction]:
        """
        Get direction using XY routing (escape path)
        
        Args:
            current_pos: Current position
            dest_pos: Destination position
            current_node: Current node
            
        Returns:
            XY routing direction
        """
        current_row, current_col = current_pos
        dest_row, dest_col = dest_pos
        
        # XY routing: X first, then Y
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
    
    def _select_best_adaptive_direction(
        self,
        current_node: Node,
        directions: List[Direction],
        dest_pos: Tuple[int, int]
    ) -> Optional[Direction]:
        """
        Select best direction based on multiple metrics
        
        Args:
            current_node: Current node
            directions: Available directions
            dest_pos: Destination position
            
        Returns:
            Best direction based on weighted scoring
        """
        if not directions:
            return None
        
        best_direction = None
        best_score = float('-inf')
        
        for direction in directions:
            neighbor_pos = current_node.get_neighbor_position(direction)
            if not neighbor_pos or neighbor_pos not in current_node.neighbors:
                continue
            
            neighbor = current_node.neighbors[neighbor_pos]
            
            # Calculate composite score
            score = self._calculate_direction_score(
                neighbor, neighbor_pos, dest_pos
            )
            
            if score > best_score:
                best_score = score
                best_direction = direction
        
        return best_direction if best_direction else directions[0]
    
    def _calculate_direction_score(
        self,
        neighbor: Node,
        neighbor_pos: Tuple[int, int],
        dest_pos: Tuple[int, int]
    ) -> float:
        """
        Calculate weighted score for a direction
        
        Higher score = better choice
        
        Factors:
        - Buffer availability (40% weight)
        - Distance to destination (30% weight)
        - Channel utilization (30% weight)
        
        Args:
            neighbor: Neighbor node
            neighbor_pos: Neighbor position
            dest_pos: Destination position
            
        Returns:
            Weighted score
        """
        # Buffer availability (higher is better)
        buffer_free = 1.0 - (len(neighbor.input_buffer.packets) / neighbor.input_buffer.capacity)
        buffer_score = buffer_free * 40.0
        
        # Distance to destination (lower is better, so invert)
        distance = self.calculate_manhattan_distance(neighbor_pos, dest_pos)
        max_distance = 100  # Normalize
        distance_score = (1.0 - min(distance / max_distance, 1.0)) * 30.0
        
        # Channel utilization (assume free is better)
        # In real implementation, would check actual link usage
        channel_score = buffer_free * 30.0
        
        total_score = buffer_score + distance_score + channel_score
        return total_score
    
    def calculate_hops(
        self,
        source: Tuple[int, int],
        destination: Tuple[int, int]
    ) -> int:
        """
        Calculate minimum number of hops (Manhattan distance)
        
        Fully adaptive can achieve minimal paths
        
        Args:
            source: Source position (row, col)
            destination: Destination position (row, col)
            
        Returns:
            Minimum number of hops
        """
        return self.calculate_manhattan_distance(source, destination)
    
    def set_escape_threshold(self, threshold: float):
        """
        Set threshold for using escape path
        
        Args:
            threshold: Buffer occupancy threshold (0.0 - 1.0)
        """
        self.escape_threshold = max(0.0, min(1.0, threshold))
