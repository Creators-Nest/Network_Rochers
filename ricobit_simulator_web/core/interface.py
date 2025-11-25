from .buffers import CircularBuffer

class Interface:
    """
    Implements the node interface, including pins, status bits,
    and handshake logic from Figure 6.
    """
    def __init__(self, buffer_size=4):
        # --- Internal Components ---
        self.send_buffer = CircularBuffer(buffer_size)
        self.receive_buffer = CircularBuffer(buffer_size)
        self.send_register = None
        self.receive_register = None

        # --- Pins for Handshaking ---
        self.pin_REQ = False
        self.pin_ACK = False
        self.pin_DATA = None
        self.pin_CHOKE = False

        # --- Status Bits ---
        self.bit_Busy = False
        self.bit_Transfer = False
        self.bit_Receive = False
        
        # --- Connection ---
        self.connected_interface = None
        self.timeout_counter = 0
        self.TIMEOUT_LIMIT = 5

    def connect(self, other_interface):
        self.connected_interface = other_interface
        other_interface.connected_interface = self
        
    def update_sender_logic(self):
        """Implements the LEFT side of the Figure 6 flowchart (Node 1)."""
        if not self.connected_interface:
            return

        # Fast-path: release the interface as soon as the receiver finishes.
        if self.bit_Transfer:
            if self.connected_interface.bit_Receive:
                return  # Receiver still consuming the packet this cycle.

            # Transfer completed – clear the data lines so we can reuse them.
            self.send_register = None
            self.pin_DATA = None
            self.bit_Transfer = False
            self.bit_Busy = False
            self.pin_REQ = False

        # Wait for the receiver to acknowledge the current request.
        if self.bit_Busy:
            if self.connected_interface.pin_ACK:
                packet = self.send_buffer.dequeue()
                if packet is None:
                    # Nothing left to send – drop the handshake gracefully.
                    self.pin_REQ = False
                    self.bit_Busy = False
                    return

                # Drive the shared link with the next packet immediately.
                self.send_register = packet
                self.pin_DATA = packet
                self.bit_Transfer = True
                self.timeout_counter = 0
                return

            # No ACK yet – advance the timeout watchdog.
            self.timeout_counter += 1
            if self.timeout_counter >= self.TIMEOUT_LIMIT:
                self.pin_REQ = False
                self.bit_Busy = False
                self.timeout_counter = 0
            return

        # Interface is idle: start a new transfer if data is queued and peer can accept it.
        if not self.send_buffer.is_empty():
            if not self.connected_interface.bit_Busy and not self.connected_interface.pin_CHOKE:
                self.pin_REQ = True
                self.bit_Busy = True
                self.timeout_counter = 0
            else:
                # Keep REQ low while the peer is busy or choking.
                self.pin_REQ = False

    def update_receiver_logic(self):
        """Implements the RIGHT side of the Figure 6 flowchart (Node 2)"""
        if not self.connected_interface:
            return
        
        # State: Idle - Check for incoming REQ
        if not self.bit_Busy and not self.bit_Receive:
            if self.connected_interface.pin_REQ:
                # Check if we have buffer space
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
                self.receive_buffer.enqueue(packet)
                self.receive_register = None
                
                # Reset state
                self.pin_ACK = False
                self.bit_Receive = False
                self.bit_Busy = False
                self.pin_CHOKE = False