"""
Enhanced Node Class with packet consumption logic
Implements destination packet consumption and intermediate node forwarding
Supports adaptive routing for congestion avoidance (Intel Mesh style)
"""

from typing import Dict, Tuple, Optional, List
from .enhanced_interface import EnhancedInterface
from .packet import Packet


class EnhancedNode:
    """
    Enhanced Node with proper packet handling:
    - Destination nodes: Consume packets
    - Intermediate nodes: Forward packets (receive_buffer -> send_buffer)
    - Adaptive routing support for congestion avoidance
    """
    
    def __init__(self, address: Tuple[int, int]):
        self.address = address
        self.interfaces: Dict[Tuple[int, int], EnhancedInterface] = {}
        self.routing_table: Dict[Tuple[int, int], Tuple[int, int]] = {}  # dest -> next_hop
        self.adaptive_routes: Dict[Tuple[int, int], List[Tuple[int, int]]] = {}  # dest -> [next_hops]
        
        # Packet consumption tracking
        self.consumed_packets: List[Packet] = []
        self.is_processing = False
    
    def add_interface(self, neighbor_address: Tuple[int, int], buffer_capacity: int = 4):
        """Add interface to neighbor node"""
        if neighbor_address not in self.interfaces:
            self.interfaces[neighbor_address] = EnhancedInterface(
                self.address,
                neighbor_address,
                buffer_capacity
            )
    
    def add_route(self, destination: Tuple[int, int], next_hop):
        """
        Add route to routing table
        
        Args:
            destination: Destination address
            next_hop: Can be either a single next_hop tuple or a path list
        """
        if isinstance(next_hop, list):
            # Legacy: path list format - extract actual next hop
            if len(next_hop) >= 2:
                self.routing_table[destination] = next_hop[1]  # First hop after source
        else:
            # New format: direct next hop
            self.routing_table[destination] = next_hop
    
    def get_next_hop(self, destination: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        """
        Get next hop for destination, using adaptive routing if available.
        Chooses least congested path when multiple options exist.
        
        Args:
            destination: Destination address
            
        Returns:
            Next hop address or None
        """
        if destination == self.address:
            return None
        
        # Check if adaptive routes available
        if destination in self.adaptive_routes:
            next_hops = self.adaptive_routes[destination]
            if len(next_hops) == 1:
                return next_hops[0]
            
            # Choose least congested path
            best_hop = next_hops[0]
            min_congestion = float('inf')
            
            for hop in next_hops:
                if hop in self.interfaces:
                    congestion = self._get_interface_congestion(hop)
                    if congestion < min_congestion:
                        min_congestion = congestion
                        best_hop = hop
            
            return best_hop
        
        # Fallback to standard routing table
        return self.routing_table.get(destination)
    
    def _get_interface_congestion(self, neighbor: Tuple[int, int]) -> float:
        """Get congestion level (0.0-1.0) of interface to neighbor."""
        interface = self.interfaces.get(neighbor)
        if not interface:
            return 1.0
        
        # Check TX buffer occupancy
        if hasattr(interface, 'tx_buffer') and hasattr(interface.tx_buffer, 'get_occupancy'):
            return interface.tx_buffer.get_occupancy()
        elif hasattr(interface, 'send_buffer'):
            capacity = getattr(interface.send_buffer, 'capacity', 4)
            used = len(interface.send_buffer.buffer) if hasattr(interface.send_buffer, 'buffer') else 0
            return used / capacity if capacity > 0 else 0.0
        
        return 0.0
    
    def get_route(self, destination: Tuple[int, int]) -> Optional[List[Tuple[int, int]]]:
        """
        Get route to destination (legacy compatibility).
        Returns path as [source, next_hop, ...] format.
        """
        next_hop = self.get_next_hop(destination)
        if next_hop:
            return [self.address, next_hop]
        return None
    
    def consume_packet(self, packet: Packet) -> bool:
        """
        Consume packet at destination node
        
        Args:
            packet: Packet to consume
            
        Returns:
            True if packet consumed successfully
        """
        if packet.dest_address == self.address:
            # Check for duplicate consumption
            if packet not in self.consumed_packets:
                self.consumed_packets.append(packet)
                print(f"[Node {self.address}] Consumed packet from {packet.source_address}")
            return True
        return False
    
    def forward_packet(self, packet: Packet) -> bool:
        """
        Forward packet at intermediate node using adaptive routing.
        Tries primary path first, then alternate paths if available.
        
        Args:
            packet: Packet to forward
            
        Returns:
            True if packet forwarded successfully
        """
        if packet.dest_address == self.address:
            # This is destination, don't forward
            return self.consume_packet(packet)
        
        # Get next hop using adaptive routing
        next_hop = self.get_next_hop(packet.dest_address)
        if not next_hop:
            print(f"[Node {self.address}] No route to {packet.dest_address}")
            return False
        
        # Get interface to next hop
        if next_hop not in self.interfaces:
            print(f"[Node {self.address}] No interface to {next_hop}")
            return False
        
        interface = self.interfaces[next_hop]
        
        # Try to add packet to send buffer of that interface
        if interface.send_buffer.push(packet):
            print(f"[Node {self.address}] Forwarded packet to {next_hop}")
            return True
        
        # Primary path full - try alternate paths if adaptive routing enabled
        if packet.dest_address in self.adaptive_routes:
            for alt_hop in self.adaptive_routes[packet.dest_address]:
                if alt_hop != next_hop and alt_hop in self.interfaces:
                    alt_interface = self.interfaces[alt_hop]
                    if alt_interface.send_buffer.push(packet):
                        print(f"[Node {self.address}] Forwarded packet via alternate path to {alt_hop}")
                        return True
        
        print(f"[Node {self.address}] All paths to {packet.dest_address} are full")
        return False
    
    def process_received_packets(self):
        """
        Process packets in receive buffers of all interfaces
        - If destination: consume packet
        - If intermediate: forward to appropriate send buffer
        - If forwarding fails (buffer full), keep packet for retry
        """
        for neighbor_addr, interface in self.interfaces.items():
            # Process only if receive buffer has packets
            packets_to_keep = []
            while not interface.receive_buffer.is_empty():
                packet = interface.receive_buffer.pop()
                
                if packet.dest_address == self.address:
                    # Destination node - consume packet
                    self.consume_packet(packet)
                else:
                    # Intermediate node - try to forward packet
                    if not self.forward_packet(packet):
                        # Can't forward (buffer full), keep packet for retry
                        packets_to_keep.append(packet)
            
            # Put back packets that couldn't be forwarded
            for packet in packets_to_keep:
                interface.receive_buffer.push(packet)
    
    def update(self):
        """
        Update node state
        Called every simulation cycle
        """
        # Process received packets
        self.process_received_packets()
        
        # Update all interfaces (clock tick)
        for interface in self.interfaces.values():
            interface.clock_tick()
    
    def inject_packet(self, packet: Packet) -> bool:
        """
        Inject packet into network (source node operation)
        Uses adaptive routing for initial injection.
        
        Args:
            packet: Packet to inject
            
        Returns:
            True if packet injected successfully
        """
        if packet.source_address != self.address:
            print(f"[Node {self.address}] Cannot inject packet from different source {packet.source_address}")
            return False
        
        # Get next hop using adaptive routing
        next_hop = self.get_next_hop(packet.dest_address)
        if not next_hop:
            print(f"[Node {self.address}] No route to {packet.dest_address}")
            return False
        
        # Get interface to first hop
        if next_hop not in self.interfaces:
            print(f"[Node {self.address}] No interface to {next_hop}")
            return False
        
        interface = self.interfaces[next_hop]
        
        # Add to send buffer
        if interface.send_buffer.push(packet):
            print(f"[Node {self.address}] Injected packet to network via {next_hop}")
            return True
        
        # Primary path full - try alternate paths
        if packet.dest_address in self.adaptive_routes:
            for alt_hop in self.adaptive_routes[packet.dest_address]:
                if alt_hop != next_hop and alt_hop in self.interfaces:
                    alt_interface = self.interfaces[alt_hop]
                    if alt_interface.send_buffer.push(packet):
                        print(f"[Node {self.address}] Injected packet via alternate path {alt_hop}")
                        return True
        
        print(f"[Node {self.address}] All paths full, cannot inject packet")
        return False
    
    def get_status(self) -> dict:
        """Get comprehensive node status"""
        interfaces_status = {}
        for neighbor_addr, interface in self.interfaces.items():
            interfaces_status[str(neighbor_addr)] = interface.get_status()
        
        return {
            'address': self.address,
            'num_interfaces': len(self.interfaces),
            'consumed_packets': len(self.consumed_packets),
            'interfaces': interfaces_status
        }
    
    def reset(self):
        """Reset node to initial state"""
        for interface in self.interfaces.values():
            interface.reset()
        self.consumed_packets.clear()
        self.is_processing = False
    
    def __repr__(self):
        return f"EnhancedNode({self.address}, interfaces={len(self.interfaces)})"
