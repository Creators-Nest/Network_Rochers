"""
Base Node class for NoC simulation
Compatible with Mesh, Torus, and RiCoBiT topologies
"""

from typing import Dict, List, Tuple, Optional
from enum import Enum
from .buffer import Buffer
from .packet import Packet, PacketStatus


class NodeStatus(Enum):
    """Node status enumeration"""
    IDLE = "idle"
    BUSY = "busy"
    SENDING = "sending"
    RECEIVING = "receiving"
    PROCESSING = "processing"


class Direction(Enum):
    """Direction enumeration for node connections"""
    NORTH = "north"
    SOUTH = "south"
    EAST = "east"
    WEST = "west"
    NORTHEAST = "northeast"  # For RiCoBiT
    NORTHWEST = "northwest"  # For RiCoBiT
    SOUTHEAST = "southeast"  # For RiCoBiT
    SOUTHWEST = "southwest"  # For RiCoBiT
    LOCAL = "local"  # For local injection/ejection


class Node:
    """
    Universal Node class for all NoC topologies
    
    Attributes:
        position: Node coordinates (row, col)
        input_buffer: Buffer for incoming packets
        output_buffer: Buffer for outgoing packets
        neighbors: Dictionary mapping Direction to neighbor nodes
        routing_table: Optional routing table for the node
        status: Current node status
    """
    
    def __init__(
        self,
        position: Tuple[int, int],
        buffer_capacity: int = 10
    ):
        """
        Initialize a node
        
        Args:
            position: Node position (row, col)
            buffer_capacity: Size of input/output buffers
        """
        self.position = position
        self.row, self.col = position
        
        # Buffers
        self.input_buffer = Buffer(
            capacity=buffer_capacity,
            name=f"Node{position}_input"
        )
        self.output_buffer = Buffer(
            capacity=buffer_capacity,
            name=f"Node{position}_output"
        )
        
        # Directional buffers for more sophisticated routing
        self.direction_buffers: Dict[Direction, Buffer] = {}
        
        # Neighbors (populated by topology)
        self.neighbors: Dict[Direction, Optional['Node']] = {
            Direction.NORTH: None,
            Direction.SOUTH: None,
            Direction.EAST: None,
            Direction.WEST: None,
            Direction.NORTHEAST: None,
            Direction.NORTHWEST: None,
            Direction.SOUTHEAST: None,
            Direction.SOUTHWEST: None,
            Direction.LOCAL: None,
        }
        
        # Routing table (direction to next hop)
        self.routing_table: Dict[Tuple[int, int], Direction] = {}
        
        # Status and state
        self.status = NodeStatus.IDLE
        self.current_packet: Optional[Packet] = None
        
        # Statistics
        self.packets_generated = 0
        self.packets_forwarded = 0
        self.packets_received = 0
        self.packets_dropped = 0
        
        # Communication signals (per Figure 4 - Unidirectional mode)
        self.signals = {
            Direction.NORTH: {'REQ': False, 'ACK': False, 'DATA': None, 'CLK': False, 'Choke': False},
            Direction.SOUTH: {'REQ': False, 'ACK': False, 'DATA': None, 'CLK': False, 'Choke': False},
            Direction.EAST: {'REQ': False, 'ACK': False, 'DATA': None, 'CLK': False, 'Choke': False},
            Direction.WEST: {'REQ': False, 'ACK': False, 'DATA': None, 'CLK': False, 'Choke': False},
        }
        
        # Transfer state machine
        self.transfer_state = "IDLE"  # IDLE, REQUESTING, TRANSFERRING, RECEIVING
        self.current_transfer_direction: Optional[Direction] = None
        
        # Clock cycle tracking
        self.last_activity_time = 0
    
    def add_neighbor(self, direction: Direction, neighbor: 'Node'):
        """
        Add a neighbor node in specified direction
        
        Args:
            direction: Direction to neighbor
            neighbor: Neighbor node
        """
        self.neighbors[direction] = neighbor
    
    def get_neighbor(self, direction: Direction) -> Optional['Node']:
        """
        Get neighbor in specified direction
        
        Args:
            direction: Direction to query
            
        Returns:
            Neighbor node or None
        """
        return self.neighbors.get(direction)
    
    def has_neighbor(self, direction: Direction) -> bool:
        """Check if neighbor exists in direction"""
        return self.neighbors.get(direction) is not None
    
    def get_neighbor_position(self, direction: Direction) -> Optional[Tuple[int, int]]:
        """
        Get the position of neighbor in given direction
        
        Args:
            direction: Direction to check
            
        Returns:
            Position tuple (row, col) of neighbor, or None if no neighbor
        """
        neighbor = self.neighbors.get(direction)
        if neighbor:
            return neighbor.position
        return None
    
    def get_available_directions(self) -> List[Direction]:
        """Get list of directions with valid neighbors"""
        return [d for d, n in self.neighbors.items() if n is not None]
    
    def inject_packet(self, packet: Packet) -> bool:
        """
        Inject a new packet into the network at this node
        
        Args:
            packet: Packet to inject
            
        Returns:
            True if successful, False if buffer full
        """
        if self.output_buffer.enqueue(packet):
            self.packets_generated += 1
            packet.add_hop(self.position, packet.creation_time)
            return True
        return False
    
    def receive_packet(self, packet: Packet, current_time: int) -> bool:
        """
        Receive packet from another node
        
        Args:
            packet: Incoming packet
            current_time: Current simulation time
            
        Returns:
            True if successful, False if buffer full
        """
        if self.input_buffer.enqueue(packet):
            packet.add_hop(self.position, current_time)
            self.last_activity_time = current_time
            
            # Check if this is the destination
            if packet.is_at_destination():
                packet.deliver(current_time)
                self.packets_received += 1
                self.status = NodeStatus.RECEIVING
            else:
                self.status = NodeStatus.PROCESSING
            
            return True
        else:
            packet.drop(current_time)
            self.packets_dropped += 1
            return False
    
    def process_packet(self, packet: Packet, next_direction: Direction) -> bool:
        """
        Process packet and move to output buffer
        
        Args:
            packet: Packet to process
            next_direction: Direction to forward packet
            
        Returns:
            True if successful
        """
        # Store routing information with packet
        packet.next_node = self.get_next_hop_position(next_direction)
        
        if self.output_buffer.enqueue(packet):
            self.packets_forwarded += 1
            return True
        return False
    
    def get_next_hop_position(self, direction: Direction) -> Optional[Tuple[int, int]]:
        """
        Get position of next hop node in given direction
        
        Args:
            direction: Direction to check
            
        Returns:
            Position tuple or None
        """
        neighbor = self.get_neighbor(direction)
        return neighbor.position if neighbor else None
    
    def can_send(self) -> bool:
        """Check if node can send a packet"""
        return not self.output_buffer.is_empty()
    
    def can_receive(self) -> bool:
        """Check if node can receive a packet"""
        return not self.input_buffer.is_full()
    
    def get_buffer_status(self) -> Dict[str, any]:
        """Get current buffer status for monitoring"""
        return {
            'position': self.position,
            'input_buffer_size': self.input_buffer.size(),
            'output_buffer_size': self.output_buffer.size(),
            'input_buffer_util': self.input_buffer.utilization(),
            'output_buffer_util': self.output_buffer.utilization(),
            'status': self.status.value
        }
    
    def reset_statistics(self):
        """Reset node statistics"""
        self.packets_generated = 0
        self.packets_forwarded = 0
        self.packets_received = 0
        self.packets_dropped = 0
        self.last_activity_time = 0
    
    def initiate_transfer(self, direction: Direction, packet: Packet) -> bool:
        """
        Initiate packet transfer to neighbor (REQ signal)
        Following Figure 4 - Unidirectional mode protocol
        
        Args:
            direction: Direction to send packet
            packet: Packet to transfer
            
        Returns:
            True if transfer initiated
        """
        neighbor = self.get_neighbor(direction)
        if not neighbor or not neighbor.can_receive():
            return False
        
        # Check choke signal - if neighbor's send buffer is full, wait
        if neighbor.signals[self._opposite_direction(direction)]['Choke']:
            return False  # Fairness: let neighbor send first
        
        # Raise REQ signal
        self.signals[direction]['REQ'] = True
        self.signals[direction]['DATA'] = packet
        self.transfer_state = "REQUESTING"
        self.current_transfer_direction = direction
        
        return True
    
    def acknowledge_transfer(self, direction: Direction) -> bool:
        """
        Acknowledge incoming transfer request (ACK signal)
        
        Args:
            direction: Direction of incoming request
            
        Returns:
            True if acknowledged
        """
        opposite_dir = self._opposite_direction(direction)
        neighbor = self.get_neighbor(direction)
        
        if not neighbor or not neighbor.signals[opposite_dir]['REQ']:
            return False
        
        if not self.can_receive():
            return False  # Buffer full
        
        # Raise ACK signal
        self.signals[direction]['ACK'] = True
        
        # Set choke bit if our send buffer has packets (fairness)
        if not self.output_buffer.is_empty():
            self.signals[direction]['Choke'] = True
        else:
            self.signals[direction]['Choke'] = False
        
        return True
    
    def complete_transfer(self, direction: Direction) -> Optional[Packet]:
        """
        Complete packet transfer with CLK synchronization
        
        Args:
            direction: Transfer direction
            
        Returns:
            Transferred packet or None
        """
        neighbor = self.get_neighbor(direction)
        opposite_dir = self._opposite_direction(direction)
        
        if not neighbor:
            return None
        
        # Check for REQ-ACK handshake
        if neighbor.signals[opposite_dir]['REQ'] and self.signals[direction]['ACK']:
            # CLK pulse - transfer data
            self.signals[direction]['CLK'] = True
            packet = neighbor.signals[opposite_dir]['DATA']
            
            if packet and self.input_buffer.enqueue(packet):
                # Clear signals
                neighbor.signals[opposite_dir]['REQ'] = False
                neighbor.signals[opposite_dir]['DATA'] = None
                self.signals[direction]['ACK'] = False
                self.signals[direction]['CLK'] = False
                
                # Update packet position
                packet.current_node = self.position
                packet.hops += 1
                self.packets_received += 1
                
                # Clear neighbor's transfer state
                if neighbor.current_transfer_direction == opposite_dir:
                    neighbor.transfer_state = "IDLE"
                    neighbor.current_transfer_direction = None
                
                return packet
        
        return None
    
    def _opposite_direction(self, direction: Direction) -> Direction:
        """Get opposite direction for bidirectional communication"""
        opposites = {
            Direction.NORTH: Direction.SOUTH,
            Direction.SOUTH: Direction.NORTH,
            Direction.EAST: Direction.WEST,
            Direction.WEST: Direction.EAST,
        }
        return opposites.get(direction, direction)
    
    def get_signal_state(self, direction: Direction) -> Dict:
        """Get current signal state for a direction"""
        if direction in self.signals:
            return self.signals[direction].copy()
        return {'REQ': False, 'ACK': False, 'DATA': None, 'CLK': False, 'Choke': False}
    
    def __repr__(self) -> str:
        """String representation"""
        return f"Node(pos={self.position}, status={self.status.value})"
    
    def __str__(self) -> str:
        """Human-readable representation"""
        return f"Node{self.position}"
    
    def __eq__(self, other) -> bool:
        """Check equality based on position"""
        if isinstance(other, Node):
            return self.position == other.position
        return False
    
    def __hash__(self) -> int:
        """Hash based on position"""
        return hash(self.position)
