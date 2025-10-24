"""
Packet class for NoC simulation
Compatible with Mesh, Torus, and RiCoBiT topologies
"""

from typing import List, Tuple, Optional
from enum import Enum


class PacketStatus(Enum):
    """Packet status enumeration"""
    CREATED = "created"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    DROPPED = "dropped"


class Packet:
    """
    Universal packet structure for all NoC topologies
    
    Attributes:
        packet_id: Unique identifier for the packet
        source: Source node coordinates (row, col)
        destination: Destination node coordinates (row, col)
        payload: Data payload (can be any serializable data)
        creation_time: Clock cycle when packet was created
        current_time: Current simulation clock cycle
        path: List of nodes the packet has traversed
        hops: Number of hops taken
        status: Current status of the packet
        priority: Packet priority (higher = more important)
    """
    
    _packet_counter = 0  # Class variable for unique packet IDs
    
    def __init__(
        self,
        source: Tuple[int, int],
        destination: Tuple[int, int],
        payload: any = None,
        creation_time: int = 0,
        priority: int = 0
    ):
        """
        Initialize a new packet
        
        Args:
            source: Source node (row, col)
            destination: Destination node (row, col)
            payload: Data payload
            creation_time: Clock cycle when created
            priority: Packet priority level
        """
        Packet._packet_counter += 1
        self.packet_id = Packet._packet_counter
        
        self.source = source
        self.destination = destination
        self.payload = payload if payload is not None else {}
        
        self.creation_time = creation_time
        self.current_time = creation_time
        self.delivery_time: Optional[int] = None
        
        self.path: List[Tuple[int, int]] = [source]
        self.hops = 0
        self.status = PacketStatus.CREATED
        self.priority = priority
        
        # For visualization and debugging
        self.current_node: Optional[Tuple[int, int]] = source
        self.next_node: Optional[Tuple[int, int]] = None
    
    def add_hop(self, node: Tuple[int, int], current_time: int):
        """
        Record a hop to a new node
        
        Args:
            node: Node coordinates (row, col)
            current_time: Current simulation time
        """
        self.path.append(node)
        self.current_node = node
        self.hops += 1
        self.current_time = current_time
        self.status = PacketStatus.IN_TRANSIT
    
    def deliver(self, current_time: int):
        """
        Mark packet as delivered
        
        Args:
            current_time: Delivery time
        """
        self.status = PacketStatus.DELIVERED
        self.delivery_time = current_time
        self.current_time = current_time
    
    def drop(self, current_time: int):
        """
        Mark packet as dropped (failed delivery)
        
        Args:
            current_time: Drop time
        """
        self.status = PacketStatus.DROPPED
        self.current_time = current_time
    
    def get_latency(self) -> Optional[int]:
        """
        Calculate packet latency (delivery_time - creation_time)
        
        Returns:
            Latency in clock cycles, or None if not delivered
        """
        if self.delivery_time is not None:
            return self.delivery_time - self.creation_time
        return None
    
    def is_at_destination(self) -> bool:
        """Check if packet has reached its destination"""
        return self.current_node == self.destination
    
    def __repr__(self) -> str:
        """String representation of packet"""
        return (f"Packet(id={self.packet_id}, "
                f"src={self.source}, dst={self.destination}, "
                f"hops={self.hops}, status={self.status.value})")
    
    def __str__(self) -> str:
        """Human-readable string representation"""
        return f"P{self.packet_id}: {self.source}→{self.destination}"
    
    @classmethod
    def reset_counter(cls):
        """Reset packet counter (useful for testing)"""
        cls._packet_counter = 0
