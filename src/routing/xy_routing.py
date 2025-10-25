"""
XY Routing Algorithm for Mesh Topology

XY routing is a deterministic, dimension-ordered routing algorithm
that is deadlock-free for mesh networks.

Algorithm:
1. First route in the X dimension (columns) until aligned with destination
2. Then route in the Y dimension (rows) to reach destination

This ensures packets follow a predictable path and avoids circular dependencies
that could cause deadlock.
"""

from typing import Optional, Tuple
from ..core.node import Node, Direction
from ..core.packet import Packet
from .base_routing import BaseRouting


class XYRouting(BaseRouting):
    """
    XY Routing Algorithm for Mesh Networks
    
    Routes packets first in X direction (East/West) then Y direction (North/South).
    This dimension-ordered approach guarantees deadlock freedom.
    
    Routing Rules:
    1. If current column != destination column:
       - Move EAST if current_col < dest_col
       - Move WEST if current_col > dest_col
    2. Else if current row != destination row:
       - Move NORTH if current_row < dest_row
       - Move SOUTH if current_row > dest_row
    3. Else: arrived at destination
    """
    
    def __init__(self):
        """Initialize XY routing algorithm"""
        super().__init__(name="XY")
    
    def get_next_direction(
        self,
        current_node: Node,
        packet: Packet
    ) -> Optional[Direction]:
        """
        Determine next direction using XY routing
        
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
        
        # Phase 1: Route in X dimension (columns) - EAST or WEST
        if current_col != dest_col:
            if current_col < dest_col:
                # Need to go right (EAST)
                if current_node.has_neighbor(Direction.EAST):
                    return Direction.EAST
            else:  # current_col > dest_col
                # Need to go left (WEST)
                if current_node.has_neighbor(Direction.WEST):
                    return Direction.WEST
        
        # Phase 2: Route in Y dimension (rows) - NORTH or SOUTH
        elif current_row != dest_row:
            if current_row < dest_row:
                # Need to go down (SOUTH)
                if current_node.has_neighbor(Direction.SOUTH):
                    return Direction.SOUTH
            else:  # current_row > dest_row
                # Need to go up (NORTH)
                if current_node.has_neighbor(Direction.NORTH):
                    return Direction.NORTH
        
        # Should not reach here if topology is properly connected
        return None
    
    def get_routing_path(
        self,
        source: Tuple[int, int],
        destination: Tuple[int, int]
    ) -> list[Direction]:
        """
        Calculate complete routing path from source to destination
        
        Args:
            source: Source position (row, col)
            destination: Destination position (row, col)
            
        Returns:
            List of directions forming the path
        """
        path = []
        current_row, current_col = source
        dest_row, dest_col = destination
        
        # X dimension movement
        while current_col != dest_col:
            if current_col < dest_col:
                path.append(Direction.EAST)
                current_col += 1
            else:
                path.append(Direction.WEST)
                current_col -= 1
        
        # Y dimension movement
        while current_row != dest_row:
            if current_row < dest_row:
                path.append(Direction.SOUTH)
                current_row += 1
            else:
                path.append(Direction.NORTH)
                current_row -= 1
        
        return path
    
    def calculate_hops(
        self,
        source: Tuple[int, int],
        destination: Tuple[int, int]
    ) -> int:
        """
        Calculate number of hops from source to destination
        
        Args:
            source: Source position (row, col)
            destination: Destination position (row, col)
            
        Returns:
            Number of hops (Manhattan distance)
        """
        return self.calculate_manhattan_distance(source, destination)
    
    def route(
        self,
        source: Tuple[int, int],
        destination: Tuple[int, int],
        rows: int,
        cols: int
    ) -> list[Tuple[int, int]]:
        """
        Calculate complete node-by-node path from source to destination
        
        Args:
            source: Source position (row, col)
            destination: Destination position (row, col)
            rows: Number of rows in mesh
            cols: Number of columns in mesh
            
        Returns:
            List of node positions forming the path
        """
        path = [source]
        current_row, current_col = source
        dest_row, dest_col = destination
        
        # X dimension movement (columns)
        while current_col != dest_col:
            if current_col < dest_col:
                current_col += 1
            else:
                current_col -= 1
            path.append((current_row, current_col))
        
        # Y dimension movement (rows)
        while current_row != dest_row:
            if current_row < dest_row:
                current_row += 1
            else:
                current_row -= 1
            path.append((current_row, current_col))
        
        return path


class YXRouting(BaseRouting):
    """
    YX Routing Algorithm for Mesh Networks
    
    Alternative to XY routing that routes first in Y direction (North/South)
    then X direction (East/West). Also deadlock-free.
    
    Can be used for load balancing with XY routing.
    """
    
    def __init__(self):
        """Initialize YX routing algorithm"""
        super().__init__(name="YX")
    
    def get_next_direction(
        self,
        current_node: Node,
        packet: Packet
    ) -> Optional[Direction]:
        """
        Determine next direction using YX routing
        
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
        
        # Phase 1: Route in Y dimension (rows) - NORTH or SOUTH
        if current_row != dest_row:
            if current_row < dest_row:
                # Need to go down (SOUTH)
                if current_node.has_neighbor(Direction.SOUTH):
                    return Direction.SOUTH
            else:  # current_row > dest_row
                # Need to go up (NORTH)
                if current_node.has_neighbor(Direction.NORTH):
                    return Direction.NORTH
        
        # Phase 2: Route in X dimension (columns) - EAST or WEST
        elif current_col != dest_col:
            if current_col < dest_col:
                # Need to go right (EAST)
                if current_node.has_neighbor(Direction.EAST):
                    return Direction.EAST
            else:  # current_col > dest_col
                # Need to go left (WEST)
                if current_node.has_neighbor(Direction.WEST):
                    return Direction.WEST
        
        return None
    
    def calculate_hops(
        self,
        source: Tuple[int, int],
        destination: Tuple[int, int]
    ) -> int:
        """
        Calculate number of hops from source to destination
        
        Args:
            source: Source position (row, col)
            destination: Destination position (row, col)
            
        Returns:
            Number of hops (Manhattan distance)
        """
        return self.calculate_manhattan_distance(source, destination)
