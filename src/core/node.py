"""
Base Node class for NoC simulation
Compatible with Mesh, Torus, and RiCoBiT topologies
"""

from typing import Dict, List, Tuple, Optional, Set
from enum import Enum
from .buffer import Buffer
from .packet import Packet, PacketStatus, PacketType


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


class RouteEntry:
    """Routing table entry for AODV protocol"""
    def __init__(self, destination: Tuple[int, int], next_hop: Direction,
                 hop_count: int, sequence_num: int, timestamp: int):
        self.destination = destination
        self.next_hop = next_hop
        self.hop_count = hop_count
        self.sequence_num = sequence_num  # Freshness indicator
        self.timestamp = timestamp
        self.lifetime = 100  # Route lifetime in clock cycles
        
    def is_expired(self, current_time: int) -> bool:
        """Check if route has expired"""
        return (current_time - self.timestamp) > self.lifetime
    
    def is_fresher(self, seq_num: int, hops: int) -> bool:
        """Check if current route is fresher than given parameters"""
        if seq_num > self.sequence_num:
            return False
        if seq_num == self.sequence_num and hops < self.hop_count:
            return False
        return True


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
        
        # AODV Routing table with route entries
        self.routing_table: Dict[Tuple[int, int], RouteEntry] = {}
        
        # Reverse routing table for RREQ tracking
        self.reverse_routes: Dict[Tuple[int, int], Direction] = {}
        
        # RREQ cache to prevent duplicates
        self.rreq_cache: Set[Tuple[Tuple[int, int], int]] = set()  # (source, broadcast_id)
        
        # Sequence number for AODV freshness
        self.sequence_number = 0
        
        # Status and state
        self.status = NodeStatus.IDLE
        self.current_packet: Optional[Packet] = None
        
        # Flow control signals (Content.txt specification)
        self.req_signal = False  # Request buffer space downstream
        self.ack_signal = False  # Acknowledge buffer available
        self.choke_signal = False  # Congestion backpressure
        self.transfer_signal = False  # Data transfer in progress
        
        # Pending packets waiting for ACK
        self.pending_packets: Dict[Direction, Optional[Packet]] = {}
        
        # Statistics
        self.packets_generated = 0
        self.packets_forwarded = 0
        self.packets_received = 0
        self.packets_dropped = 0
        self.rreq_sent = 0
        self.rrep_sent = 0
        
        # Clock cycle tracking
        self.last_activity_time = 0
        self.clock_cycle = 0
    
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
        self.rreq_sent = 0
        self.rrep_sent = 0
        self.last_activity_time = 0
        self.clock_cycle = 0
    
    def tick_clock(self):
        """Advance clock cycle"""
        self.clock_cycle += 1
        
        # Reset flow control signals each cycle
        self.transfer_signal = False
        
        # Update choke signal based on buffer status
        input_util = self.input_buffer.utilization()
        self.choke_signal = input_util >= 80.0  # Choke if >80% full
    
    def has_route_to(self, destination: Tuple[int, int]) -> bool:
        """Check if node has valid route to destination"""
        if destination not in self.routing_table:
            return False
        route = self.routing_table[destination]
        return not route.is_expired(self.clock_cycle)
    
    def get_next_hop(self, destination: Tuple[int, int]) -> Optional[Direction]:
        """Get next hop direction from routing table"""
        if not self.has_route_to(destination):
            return None
        return self.routing_table[destination].next_hop
    
    def update_route(self, destination: Tuple[int, int], next_hop: Direction,
                     hop_count: int, sequence_num: int):
        """Update routing table with new or better route"""
        current_route = self.routing_table.get(destination)
        
        # Update if no route exists or new route is fresher
        if current_route is None or not current_route.is_fresher(sequence_num, hop_count):
            self.routing_table[destination] = RouteEntry(
                destination=destination,
                next_hop=next_hop,
                hop_count=hop_count,
                sequence_num=sequence_num,
                timestamp=self.clock_cycle
            )
            return True
        return False
    
    def process_rreq(self, rreq: Packet, from_direction: Direction) -> List[Packet]:
        """
        Process Route Request following AODV protocol
        Returns list of packets to send (RREP or forwarded RREQ)
        """
        packets_to_send = []
        
        # Check for duplicate RREQ
        rreq_id = (rreq.source, rreq.broadcast_id)
        if rreq_id in self.rreq_cache:
            return packets_to_send  # Discard duplicate
        
        # Cache this RREQ
        self.rreq_cache.add(rreq_id)
        
        # Create/update reverse route to source
        self.reverse_routes[rreq.source] = from_direction
        self.update_route(
            destination=rreq.source,
            next_hop=from_direction,
            hop_count=rreq.hop_count,
            sequence_num=rreq.source_sequence_num
        )
        
        # Am I the destination?
        if self.position == rreq.destination:
            # Generate RREP
            self.sequence_number = max(self.sequence_number, rreq.dest_sequence_num) + 1
            rrep = Packet.create_rrep(
                source=self.position,
                destination=rreq.source,
                dest_seq=self.sequence_number,
                hop_count=0,
                current_time=self.clock_cycle
            )
            packets_to_send.append((rrep, from_direction))
            self.rrep_sent += 1
            return packets_to_send
        
        # Do I have a fresh route to destination?
        if self.has_route_to(rreq.destination):
            route = self.routing_table[rreq.destination]
            if route.sequence_num >= rreq.dest_sequence_num:
                # Send RREP on behalf of destination
                rrep = Packet.create_rrep(
                    source=self.position,
                    destination=rreq.source,
                    dest_seq=route.sequence_num,
                    hop_count=route.hop_count,
                    current_time=self.clock_cycle
                )
                packets_to_send.append((rrep, from_direction))
                self.rrep_sent += 1
                return packets_to_send
        
        # Forward RREQ to all neighbors except source
        rreq.hop_count += 1
        for direction, neighbor in self.neighbors.items():
            if neighbor is not None and direction != from_direction:
                # Create copy of RREQ for each neighbor
                rreq_copy = Packet.create_rreq(
                    source=rreq.source,
                    destination=rreq.destination,
                    source_seq=rreq.source_sequence_num,
                    dest_seq=rreq.dest_sequence_num,
                    current_time=self.clock_cycle
                )
                rreq_copy.broadcast_id = rreq.broadcast_id
                rreq_copy.hop_count = rreq.hop_count
                packets_to_send.append((rreq_copy, direction))
        
        self.rreq_sent += len(packets_to_send)
        return packets_to_send
    
    def process_rrep(self, rrep: Packet, from_direction: Direction) -> Optional[Tuple[Packet, Direction]]:
        """
        Process Route Reply following AODV protocol
        Returns packet to forward and direction
        """
        # Update forward route to destination
        self.update_route(
            destination=rrep.source,  # RREP source is the original destination
            next_hop=from_direction,
            hop_count=rrep.hop_count + 1,
            sequence_num=rrep.dest_sequence_num
        )
        
        # Am I the final destination of RREP?
        if self.position == rrep.destination:
            return None  # Route established
        
        # Forward RREP along reverse route
        if rrep.destination in self.reverse_routes:
            reverse_dir = self.reverse_routes[rrep.destination]
            rrep.hop_count += 1
            return (rrep, reverse_dir)
        
        return None
    
    def send_rreq(self, destination: Tuple[int, int]) -> List[Tuple[Packet, Direction]]:
        """Initiate route discovery by broadcasting RREQ"""
        self.sequence_number += 1
        
        dest_seq = 0
        if destination in self.routing_table:
            dest_seq = self.routing_table[destination].sequence_num
        
        rreq = Packet.create_rreq(
            source=self.position,
            destination=destination,
            source_seq=self.sequence_number,
            dest_seq=dest_seq,
            current_time=self.clock_cycle
        )
        
        # Cache our own RREQ
        self.rreq_cache.add((rreq.source, rreq.broadcast_id))
        
        # Broadcast to all neighbors
        packets = []
        for direction, neighbor in self.neighbors.items():
            if neighbor is not None:
                # Create copy for each neighbor
                rreq_copy = Packet.create_rreq(
                    source=self.position,
                    destination=destination,
                    source_seq=self.sequence_number,
                    dest_seq=dest_seq,
                    current_time=self.clock_cycle
                )
                rreq_copy.broadcast_id = rreq.broadcast_id
                packets.append((rreq_copy, direction))
        
        self.rreq_sent += len(packets)
        return packets
    
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
