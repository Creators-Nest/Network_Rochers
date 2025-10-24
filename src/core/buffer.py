"""
Buffer class for NoC node queues
Compatible with Mesh, Torus, and RiCoBiT topologies
"""

from collections import deque
from typing import Optional, List
from .packet import Packet


class Buffer:
    """
    FIFO buffer for packet queuing in NoC nodes
    
    Attributes:
        capacity: Maximum number of packets the buffer can hold
        queue: Deque holding the packets
        name: Buffer identifier (e.g., "input", "output", "north", "south")
    """
    
    def __init__(self, capacity: int = 10, name: str = "buffer"):
        """
        Initialize buffer
        
        Args:
            capacity: Maximum buffer size (number of packets)
            name: Buffer name for identification
        """
        self.capacity = capacity
        self.name = name
        self.queue: deque[Packet] = deque(maxlen=capacity)
        
        # Statistics
        self.packets_dropped = 0
        self.packets_received = 0
        self.packets_sent = 0
    
    def is_full(self) -> bool:
        """Check if buffer is full"""
        return len(self.queue) >= self.capacity
    
    def is_empty(self) -> bool:
        """Check if buffer is empty"""
        return len(self.queue) == 0
    
    def size(self) -> int:
        """Get current buffer occupancy"""
        return len(self.queue)
    
    def available_space(self) -> int:
        """Get available buffer space"""
        return self.capacity - len(self.queue)
    
    def enqueue(self, packet: Packet) -> bool:
        """
        Add packet to buffer
        
        Args:
            packet: Packet to add
            
        Returns:
            True if successful, False if buffer is full
        """
        if self.is_full():
            self.packets_dropped += 1
            return False
        
        self.queue.append(packet)
        self.packets_received += 1
        return True
    
    def dequeue(self) -> Optional[Packet]:
        """
        Remove and return packet from front of buffer
        
        Returns:
            Packet if available, None if buffer is empty
        """
        if self.is_empty():
            return None
        
        packet = self.queue.popleft()
        self.packets_sent += 1
        return packet
    
    def peek(self) -> Optional[Packet]:
        """
        View packet at front without removing it
        
        Returns:
            Packet if available, None if buffer is empty
        """
        if self.is_empty():
            return None
        return self.queue[0]
    
    def clear(self):
        """Clear all packets from buffer"""
        self.queue.clear()
    
    def get_all_packets(self) -> List[Packet]:
        """Get list of all packets in buffer (for visualization)"""
        return list(self.queue)
    
    def utilization(self) -> float:
        """
        Calculate buffer utilization percentage
        
        Returns:
            Utilization as percentage (0.0 to 100.0)
        """
        return (len(self.queue) / self.capacity) * 100.0
    
    def __len__(self) -> int:
        """Return current buffer size"""
        return len(self.queue)
    
    def __repr__(self) -> str:
        """String representation"""
        return f"Buffer(name={self.name}, size={len(self.queue)}/{self.capacity})"
    
    def __str__(self) -> str:
        """Human-readable representation"""
        return f"{self.name}: {len(self.queue)}/{self.capacity} packets"
