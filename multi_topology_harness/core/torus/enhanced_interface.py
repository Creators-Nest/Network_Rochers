"""
Enhanced Interface Class for Torus Topology Network-on-Chip Communication
Implements full specification with pins, registers, buffers, and control logic
Based on Mesh topology enhanced interface but adapted for torus wraparound
"""

from collections import deque
from typing import Optional, List, Any
from .packet import Packet

class CircularBuffer:
    """Circular buffer implementation for packet storage"""
    
    def __init__(self, capacity: int):
        self.buffer = deque(maxlen=capacity)
        self.capacity = capacity
    
    def push(self, item: Any) -> bool:
        """Add item to buffer, returns True if successful"""
        if len(self.buffer) < self.capacity:
            self.buffer.append(item)
            return True
        return False
    
    def pop(self) -> Optional[Any]:
        """Remove and return oldest item from buffer"""
        if self.buffer:
            return self.buffer.popleft()
        return None
    
    def peek(self) -> Optional[Any]:
        """View oldest item without removing"""
        if self.buffer:
            return self.buffer[0]
        return None
    
    def is_full(self) -> bool:
        """Check if buffer is at capacity"""
        return len(self.buffer) >= self.capacity
    
    def is_empty(self) -> bool:
        """Check if buffer is empty"""
        return len(self.buffer) == 0
    
    def size(self) -> int:
        """Get current number of items in buffer"""
        return len(self.buffer)
    
    def clear(self):
        """Clear all items from buffer"""
        self.buffer.clear()


class EnhancedInterface:
    """
    Enhanced Interface Class for Torus NoC Communication
    
    Each node has 4 interfaces (North, South, East, West)
    
    Pins (Boolean):
        - REQ: Request signal
        - ACK: Acknowledgment signal
        - DATA: Data signal (packet data)
        - CLK: Clock signal
        - CHOKE: Flow control signal
    
    Registers (bit arrays, size = sizeof(packet)):
        - Send_Register: Holds packet being sent
        - Receive_Register: Holds packet being received
    
    Buffers (2D arrays, size = sizeof(packet) × n):
        - Send_Buffer: Queue of packets to send
        - Receive_Buffer: Queue of received packets
    
    Status Bits:
        - Busy_Bit: Interface is busy
        - Receive_Bit: Currently receiving data
        - Transfer_Bit: Currently transferring data
    """
    
    def __init__(self, node_address: tuple, neighbor_address: tuple, buffer_capacity: int = 4):
        """
        Initialize enhanced interface between two nodes
        
        Args:
            node_address: Address of the node this interface belongs to
            neighbor_address: Address of the neighbor node
            buffer_capacity: Maximum number of packets in each buffer
        """
        self.node_address = node_address
        self.neighbor_address = neighbor_address
        
        # ============= PINS (Boolean) =============
        self.pin_REQ = False      # Request signal
        self.pin_ACK = False      # Acknowledgment signal
        self.pin_DATA = None      # Data signal (holds packet data)
        self.pin_CLK = False      # Clock signal
        self.pin_CHOKE = False    # Flow control/congestion signal
        
        # ============= REGISTERS (Packet-sized bit arrays) =============
        self.send_register = None      # Send_Register[sizeof(packet)]
        self.receive_register = None   # Receive_Register[sizeof(packet)]
        
        # ============= BUFFERS (Circular buffers with n slots) =============
        self.send_buffer = CircularBuffer(buffer_capacity)      # Send_Buffer[sizeof(packet), n]
        self.receive_buffer = CircularBuffer(buffer_capacity)   # Receive_Buffer[sizeof(packet), n]
        
        # ============= STATUS BITS =============
        self.bit_Busy = False       # Busy_Bit: Interface is busy
        self.bit_Receive = False    # Receive_Bit: Currently receiving
        self.bit_Transfer = False   # Transfer_Bit: Currently transferring
        
        # ============= INTERNAL STATE =============
        self.handshake_state = 'IDLE'  # IDLE, REQ_SENT, ACK_WAIT, DATA_TRANSFER, COMPLETE
        self.clock_cycle = 0
        self.transfer_delay = 0
        self.routing_table = {}  # For routing algorithm
        self.connected_interface = None  # Connected neighbor interface
        self.timeout_counter = 0
        self.TIMEOUT_LIMIT = 5  # Match RiCoBiT timeout behavior
    
    def routing_algorithm(self, packet: Packet, topology_width: int, topology_height: int) -> tuple:
        """
        Routing_Algorithm(packet): Determine next hop for packet in torus topology
        
        For Torus topology, uses XY routing with wraparound consideration:
        1. Route along X-axis first (horizontal) - choose shorter path (wraparound or direct)
        2. Then route along Y-axis (vertical) - choose shorter path (wraparound or direct)
        
        Args:
            packet: The packet to route
            topology_width: Width of the torus
            topology_height: Height of the torus
            
        Returns:
            Next hop address (x, y)
        """
        current = self.node_address
        destination = packet.dest_address
        
        # XY Routing with Torus Wraparound Logic
        # First, handle X-axis (horizontal)
        if current[0] != destination[0]:
            # Calculate direct distance and wraparound distance in X
            direct_x_dist = destination[0] - current[0]
            if direct_x_dist > 0:
                # Destination is to the east
                wrap_dist = direct_x_dist - topology_width
            else:
                # Destination is to the west
                wrap_dist = direct_x_dist + topology_width
            
            # Choose the shorter path
            if abs(direct_x_dist) <= abs(wrap_dist):
                # Use direct path
                if direct_x_dist > 0:
                    return ((current[0] + 1) % topology_width, current[1])  # Move East
                else:
                    return ((current[0] - 1) % topology_width, current[1])  # Move West
            else:
                # Use wraparound path
                if wrap_dist > 0:
                    return ((current[0] + 1) % topology_width, current[1])  # Move East (wraparound)
                else:
                    return ((current[0] - 1) % topology_width, current[1])  # Move West (wraparound)
        
        # X-axis aligned, now handle Y-axis (vertical)
        elif current[1] != destination[1]:
            # Calculate direct distance and wraparound distance in Y
            direct_y_dist = destination[1] - current[1]
            if direct_y_dist > 0:
                # Destination is to the south
                wrap_dist = direct_y_dist - topology_height
            else:
                # Destination is to the north
                wrap_dist = direct_y_dist + topology_height
            
            # Choose the shorter path
            if abs(direct_y_dist) <= abs(wrap_dist):
                # Use direct path
                if direct_y_dist > 0:
                    return (current[0], (current[1] + 1) % topology_height)  # Move South
                else:
                    return (current[0], (current[1] - 1) % topology_height)  # Move North
            else:
                # Use wraparound path
                if wrap_dist > 0:
                    return (current[0], (current[1] + 1) % topology_height)  # Move South (wraparound)
                else:
                    return (current[0], (current[1] - 1) % topology_height)  # Move North (wraparound)
        
        # Already at destination
        return destination
    
    def control_logic(self):
        """
        Control_Logic(): Manage REQ-ACK handshake protocol
        Implements the handshake state machine
        """
        if self.handshake_state == 'IDLE':
            # Check if there's a packet to send and interface not already busy
            # Use bit_Busy check to avoid conflict with update_sender_logic
            if not self.send_buffer.is_empty() and not self.bit_Busy:
                # Peek at packet (don't pop yet - pop only after transfer complete)
                packet = self.send_buffer.peek()
                self.send_register = packet
                self.pin_REQ = True
                self.bit_Busy = True
                self.bit_Transfer = True
                self.handshake_state = 'REQ_SENT'
        
        elif self.handshake_state == 'REQ_SENT':
            # Wait for ACK
            if self.pin_ACK:
                # ACK received, start data transfer
                self.pin_DATA = self.send_register
                self.handshake_state = 'DATA_TRANSFER'
            elif self.pin_CHOKE:
                # Receiver is congested, abort transfer
                # Packet is still in buffer (we only peeked), just clear register
                self.send_register = None
                self.pin_REQ = False
                self.bit_Busy = False
                self.bit_Transfer = False
                self.handshake_state = 'IDLE'
        
        elif self.handshake_state == 'DATA_TRANSFER':
            # Wait for receiver to process (simulate transfer time)
            if self.transfer_delay >= 2:  # Match Mesh: 2 cycle delay
                self.handshake_state = 'COMPLETE'
                self.transfer_delay = 0
            else:
                self.transfer_delay += 1
        
        elif self.handshake_state == 'COMPLETE':
            # Clear signals and complete transfer
            self.send_buffer.pop()  # Remove sent packet from buffer
            self.pin_REQ = False
            self.pin_DATA = None
            self.send_register = None
            self.bit_Transfer = False
            self.bit_Busy = False
            self.handshake_state = 'IDLE'
    
    def buffer_operations(self):
        """
        Buffer_Operations(): Handle buffer management
        - Monitor buffer levels
        - Set CHOKE signal if buffers are full
        - Transfer packets between registers and buffers
        """
        # Check receive buffer status
        if self.receive_buffer.is_full():
            self.pin_CHOKE = True
        else:
            self.pin_CHOKE = False
        
        # If receive register has data, move to receive buffer
        if self.receive_register and not self.receive_buffer.is_full():
            self.receive_buffer.push(self.receive_register)
            self.receive_register = None
            self.bit_Receive = False
    
    def clock_tick(self):
        """
        Simulate one clock cycle
        Update pins and manage buffers.
        NOTE: control_logic is NOT called here because the handshake state machine
        is managed by update_sender_logic/update_receiver_logic called from the simulator.
        Having both would cause double-popping from buffers.
        """
        self.clock_cycle += 1
        self.pin_CLK = not self.pin_CLK  # Toggle clock
        
        # Only buffer operations - handshake is managed by update_sender/receiver_logic
        self.buffer_operations()
    
    def receive_data(self, data: Any):
        """
        Receive data from connected interface
        Called when neighbor sends data
        """
        if not self.receive_buffer.is_full():
            self.receive_register = data
            self.bit_Receive = True
            self.pin_ACK = True
            return True
        else:
            self.pin_CHOKE = True
            return False
    
    def get_status(self) -> dict:
        """Get current interface status for monitoring"""
        return {
            'node': self.node_address,
            'neighbor': self.neighbor_address,
            'pins': {
                'REQ': self.pin_REQ,
                'ACK': self.pin_ACK,
                'DATA': str(self.pin_DATA) if self.pin_DATA else None,
                'CLK': self.pin_CLK,
                'CHOKE': self.pin_CHOKE
            },
            'registers': {
                'send': str(self.send_register) if self.send_register else None,
                'receive': str(self.receive_register) if self.receive_register else None
            },
            'buffers': {
                'send': {
                    'size': self.send_buffer.size(),
                    'capacity': self.send_buffer.capacity,
                    'full': self.send_buffer.is_full(),
                    'empty': self.send_buffer.is_empty()
                },
                'receive': {
                    'size': self.receive_buffer.size(),
                    'capacity': self.receive_buffer.capacity,
                    'full': self.receive_buffer.is_full(),
                    'empty': self.receive_buffer.is_empty()
                }
            },
            'status_bits': {
                'busy': self.bit_Busy,
                'receive': self.bit_Receive,
                'transfer': self.bit_Transfer
            },
            'state': self.handshake_state,
            'clock_cycle': self.clock_cycle
        }
    
    def update_sender_logic(self):
        """Implements sender side handshake protocol for torus topology"""
        if not hasattr(self, 'connected_interface') or not self.connected_interface:
            return
        
        # Release after transfer complete
        if self.bit_Transfer:
            if self.connected_interface.bit_Receive:
                return  # Receiver still processing
            
            # Clear transfer state
            self.send_register = None
            self.pin_DATA = None
            self.bit_Transfer = False
            self.bit_Busy = False
            self.pin_REQ = False
            self.timeout_counter = 0
            return
        
        # Wait for ACK
        if self.bit_Busy:
            if self.connected_interface.pin_ACK:
                packet = self.send_buffer.pop()
                if packet:
                    self.send_register = packet
                    self.pin_DATA = packet
                    self.bit_Transfer = True
                    self.timeout_counter = 0
                else:
                    self.pin_REQ = False
                    self.bit_Busy = False
                    self.timeout_counter = 0
                return
            
            self.timeout_counter += 1
            if self.timeout_counter >= getattr(self, 'TIMEOUT_LIMIT', 10):
                self.pin_REQ = False
                self.bit_Busy = False
                self.timeout_counter = 0
            return
        
        # Start new transfer
        if not self.send_buffer.is_empty():
            if not self.connected_interface.bit_Busy and not self.connected_interface.pin_CHOKE:
                self.pin_REQ = True
                self.bit_Busy = True
                self.timeout_counter = 0
    
    def update_receiver_logic(self):
        """Implements receiver side handshake protocol for torus topology"""
        if not hasattr(self, 'connected_interface') or not self.connected_interface:
            return
        
        # Clear CHOKE when buffer space available
        if self.pin_CHOKE and not self.receive_buffer.is_full():
            self.pin_CHOKE = False
        
        # Wait for REQ
        if not self.bit_Busy and not self.bit_Receive:
            if self.connected_interface.pin_REQ:
                if not self.receive_buffer.is_full():
                    self.pin_ACK = True
                    self.bit_Busy = True
                    self.bit_Receive = True
                else:
                    self.pin_CHOKE = True
            return
        
        # Receive data
        if self.bit_Receive:
            if self.connected_interface.pin_DATA:
                packet = self.connected_interface.pin_DATA
                self.receive_register = packet
                self.receive_buffer.push(packet)
                self.receive_register = None
                self.pin_ACK = False
                self.bit_Receive = False
                self.bit_Busy = False
    
    def connect_to(self, other_interface):
        """Create bidirectional connection for torus topology"""
        self.connected_interface = other_interface
        other_interface.connected_interface = self
        # Initialize timeout counter
        self.timeout_counter = 0
        other_interface.timeout_counter = 0
        self.TIMEOUT_LIMIT = 10
        other_interface.TIMEOUT_LIMIT = 10
    
    def reset(self):
        """Reset interface to initial state"""
        self.pin_REQ = False
        self.pin_ACK = False
        self.pin_DATA = None
        self.pin_CLK = False
        self.pin_CHOKE = False
        
        self.send_register = None
        self.receive_register = None
        
        self.send_buffer.clear()
        self.receive_buffer.clear()
        
        self.bit_Busy = False
        self.bit_Receive = False
        self.bit_Transfer = False
        
        self.handshake_state = 'IDLE'
        self.clock_cycle = 0
        self.transfer_delay = 0
    
    def __repr__(self):
        return f"EnhancedInterface({self.node_address} <-> {self.neighbor_address})"
