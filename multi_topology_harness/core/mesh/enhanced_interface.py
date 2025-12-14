"""
Enhanced Interface Class for Network-on-Chip Communication
Implements full specification with pins, registers, buffers, and control logic
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
    Enhanced Interface Class for NoC Communication
    
    Each node has n interfaces where n = number of adjacent nodes
    
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
    
    Methods:
        - Routing_Algorithm(packet): Determine next hop
        - Control_Logic(): Manage handshake protocol
        - Buffer_Operations(): Handle buffer management
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
    
    def routing_algorithm(self, packet: Packet) -> tuple:
        """
        Routing_Algorithm(packet): Determine next hop for packet
        
        For Mesh topology, uses XY routing:
        1. Route along X-axis first (horizontal)
        2. Then route along Y-axis (vertical)
        
        Args:
            packet: The packet to route
            
        Returns:
            Next hop address (x, y)
        """
        current = self.node_address
        destination = packet.dest_address
        
        # XY Routing Logic
        if current[0] < destination[0]:
            # Move East
            return (current[0] + 1, current[1])
        elif current[0] > destination[0]:
            # Move West
            return (current[0] - 1, current[1])
        elif current[1] < destination[1]:
            # Move South
            return (current[0], current[1] + 1)
        elif current[1] > destination[1]:
            # Move North
            return (current[0], current[1] - 1)
        else:
            # Already at destination
            return destination
    
    def control_logic(self):
        """
        Control_Logic(): Manage handshake protocol and data transfer
        
        Implements REQ-ACK-DATA handshake:
        1. IDLE: Wait for packet in send_buffer
        2. REQ_SENT: Assert REQ, wait for ACK
        3. ACK_WAIT: Wait for ACK from receiver
        4. DATA_TRANSFER: Transfer data when ACK received
        5. COMPLETE: Clear signals, return to IDLE
        """
        # Sender Logic
        if self.handshake_state == 'IDLE':
            if not self.send_buffer.is_empty() and not self.bit_Busy:
                # Start transfer
                packet = self.send_buffer.peek()
                self.send_register = packet
                self.pin_REQ = True
                self.bit_Busy = True
                self.bit_Transfer = True
                self.handshake_state = 'REQ_SENT'
        
        elif self.handshake_state == 'REQ_SENT':
            if self.pin_ACK:
                # ACK received, start data transfer
                self.pin_DATA = self.send_register
                self.handshake_state = 'DATA_TRANSFER'
        
        elif self.handshake_state == 'DATA_TRANSFER':
            # Wait for receiver to process
            if self.transfer_delay >= 2:  # Simulate transfer time
                self.handshake_state = 'COMPLETE'
                self.transfer_delay = 0
            else:
                self.transfer_delay += 1
        
        elif self.handshake_state == 'COMPLETE':
            # Clear signals and complete transfer
            self.send_buffer.pop()  # Remove sent packet
            self.pin_REQ = False
            self.pin_DATA = None
            self.send_register = None
            self.bit_Busy = False
            self.bit_Transfer = False
            self.handshake_state = 'IDLE'
        
        # Receiver Logic
        if self.pin_REQ and not self.bit_Receive:
            # Incoming request detected
            if not self.receive_buffer.is_full():
                # Send ACK if buffer has space
                self.pin_ACK = True
                self.bit_Receive = True
            else:
                # Buffer full, assert CHOKE
                self.pin_CHOKE = True
        
        if self.bit_Receive and self.pin_DATA is not None:
            # Data received, store in receive register
            self.receive_register = self.pin_DATA
            # Move to receive buffer
            self.receive_buffer.push(self.receive_register)
            self.pin_ACK = False
            self.bit_Receive = False
    
    def buffer_operations(self):
        """
        Buffer_Operations(): Handle buffer management
        
        Operations:
        1. Check buffer status (full/empty)
        2. Manage flow control (CHOKE signal)
        
        NOTE: Packet forwarding is handled by the Node's process_received_packets method,
        NOT by the interface. The interface only handles the handshake protocol.
        """
        # Check for buffer congestion
        if self.send_buffer.is_full():
            self.pin_CHOKE = True
        else:
            self.pin_CHOKE = False
        
        # NOTE: Packet forwarding from receive_buffer to send_buffer is done
        # by the Node's process_received_packets() method, not here.
        # The interface only manages the handshake and buffer status.
    
    def clock_tick(self):
        """
        Simulate one clock cycle
        Update pins and manage buffers.
        NOTE: control_logic is NOT called here because the handshake state machine
        is managed by update_sender_logic/update_receiver_logic called from the simulator.
        Having both would cause double-popping from buffers.
        """
        self.pin_CLK = not self.pin_CLK  # Toggle clock
        self.clock_cycle += 1
        
        # Only buffer operations - handshake is managed by update_sender/receiver_logic
        self.buffer_operations()
    
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
    
    def get_status(self) -> dict:
        """Get current interface status for monitoring/debugging"""
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
        """
        Implements sender side handshake protocol
        Based on RiCoBiT Interface pattern (Figure 6 LEFT side)
        
        Optimized state machine for REQ-ACK-DATA transfer
        """
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
            if self.timeout_counter >= self.TIMEOUT_LIMIT:
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
        """
        Implements receiver side handshake protocol
        Based on RiCoBiT Interface pattern (Figure 6 RIGHT side)
        
        Handles ACK generation and CHOKE flow control
        """
        if not hasattr(self, 'connected_interface') or not self.connected_interface:
            return
        
        # Clear CHOKE when buffer space available
        if self.pin_CHOKE and not self.receive_buffer.is_full():
            self.pin_CHOKE = False
        
        # State: Idle - Check for incoming REQ
        if not self.bit_Busy and not self.bit_Receive:
            if self.connected_interface.pin_REQ:
                if not self.receive_buffer.is_full():
                    # Accept transfer
                    self.pin_ACK = True
                    self.bit_Busy = True
                    self.bit_Receive = True
                else:
                    # Buffer full - send CHOKE signal
                    self.pin_CHOKE = True
        
        # State: Receiving Data
        elif self.bit_Receive:
            # Get data from sender
            if self.connected_interface.pin_DATA:
                packet = self.connected_interface.pin_DATA
                self.receive_register = packet
                
                # Move to receive buffer
                self.receive_buffer.push(packet)
                self.receive_register = None
                
                # Reset state
                self.pin_ACK = False
                self.bit_Receive = False
                self.bit_Busy = False
                self.pin_CHOKE = False
    
    def connect_to(self, other_interface):
        """Create bidirectional connection (RiCoBiT pattern)"""
        self.connected_interface = other_interface
        other_interface.connected_interface = self
    
    def __repr__(self):
        return f"EnhancedInterface({self.node_address} <-> {self.neighbor_address})"
