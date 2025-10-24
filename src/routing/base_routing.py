"""
Base routing algorithm interface for NoC topologies
"""

from abc import ABC, abstractmethod
from typing import Tuple, Optional
from ..core.node import Node, Direction
from ..core.packet import Packet


class BaseRouting(ABC):
    """
    Abstract base class for routing algorithms
    
    All routing algorithms should inherit from this class and implement
    the get_next_direction method.
    """
    
    def __init__(self, name: str = "BaseRouting"):
        """
        Initialize routing algorithm
        
        Args:
            name: Name of the routing algorithm
        """
        self.name = name
    
    @abstractmethod
    def get_next_direction(
        self,
        current_node: Node,
        packet: Packet
    ) -> Optional[Direction]:
        """
        Determine the next direction for a packet
        
        Args:
            current_node: Current node holding the packet
            packet: Packet to route
            
        Returns:
            Direction to forward packet, or None if at destination
        """
        pass
    
    def is_at_destination(self, current_pos: Tuple[int, int], dest_pos: Tuple[int, int]) -> bool:
        """
        Check if current position is the destination
        
        Args:
            current_pos: Current position (row, col)
            dest_pos: Destination position (row, col)
            
        Returns:
            True if at destination
        """
        return current_pos == dest_pos
    
    def calculate_manhattan_distance(
        self,
        pos1: Tuple[int, int],
        pos2: Tuple[int, int]
    ) -> int:
        """
        Calculate Manhattan distance between two positions
        
        Args:
            pos1: First position (row, col)
            pos2: Second position (row, col)
            
        Returns:
            Manhattan distance
        """
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])
    
    def __repr__(self) -> str:
        """String representation"""
        return f"{self.name}RoutingAlgorithm"
    
    def __str__(self) -> str:
        """Human-readable representation"""
        return self.name
