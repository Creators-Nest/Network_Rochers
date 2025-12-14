"""
Enhanced Node Class for Torus Topology with packet consumption logic
Implements destination packet consumption and intermediate node forwarding
Adapted from Mesh topology but with torus-specific routing
"""

from typing import Dict, Tuple, Optional, List
from .enhanced_interface import EnhancedInterface
from .packet import Packet


class EnhancedNode:
    """
    Enhanced Node for Torus Topology with proper packet handling:
    - Destination nodes: Consume packets
    - Intermediate nodes: Forward packets (receive_buffer -> send_buffer)
    - Torus-specific wraparound routing support
    """
    
    def __init__(self, address: Tuple[int, int]):
        self.address = address
        self.interfaces: Dict[Tuple[int, int], EnhancedInterface] = {}
        self.routing_table: Dict[Tuple[int, int], List[Tuple[int, int]]] = {}
        
        # Packet consumption tracking
        self.consumed_packets: List[Packet] = []
        self.is_processing = False
        
        # Topology dimensions (will be set when topology is created)
        self.topology_width = None
        self.topology_height = None
    
    def set_topology_dimensions(self, width: int, height: int):
        """Set topology dimensions for wraparound routing"""
        self.topology_width = width
        self.topology_height = height
    
    def add_interface(self, neighbor_address: Tuple[int, int], buffer_capacity: int = 4):
        """Add interface to neighbor node"""
        if neighbor_address not in self.interfaces:
            self.interfaces[neighbor_address] = EnhancedInterface(
                self.address,
                neighbor_address,
                buffer_capacity
            )
    
    def add_route(self, destination: Tuple[int, int], path: List[Tuple[int, int]]):
        """Add route to routing table"""
        self.routing_table[destination] = path
    
    def get_route(self, destination: Tuple[int, int]) -> Optional[List[Tuple[int, int]]]:
        """Get route to destination from routing table"""
        return self.routing_table.get(destination)
    
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
        Forward packet at intermediate node
        Transfers packet from receive_buffer to send_buffer of appropriate interface
        
        Args:
            packet: Packet to forward
            
        Returns:
            True if packet forwarded successfully
        """
        if packet.dest_address == self.address:
            # This is destination, don't forward
            return self.consume_packet(packet)
        
        # Determine next hop using routing algorithm
        route = self.get_route(packet.dest_address)
        if not route or len(route) < 2:
            print(f"[Node {self.address}] No route to {packet.dest_address}")
            return False
        
        # Find this node in the route
        try:
            current_index = route.index(self.address)
            next_hop = route[current_index + 1]
        except (ValueError, IndexError):
            print(f"[Node {self.address}] Cannot determine next hop")
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
        else:
            print(f"[Node {self.address}] Send buffer to {next_hop} is full")
            return False
    
    def process_received_packets(self):
        """
        Process packets in receive buffers of all interfaces
        - If destination: consume packet
        - If intermediate: forward to appropriate send buffer
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
        
        Args:
            packet: Packet to inject
            
        Returns:
            True if packet injected successfully
        """
        if packet.source_address != self.address:
            print(f"[Node {self.address}] Cannot inject packet from different source {packet.source_address}")
            return False
        
        # Get route to destination
        route = self.get_route(packet.dest_address)
        if not route or len(route) < 2:
            print(f"[Node {self.address}] No route to {packet.dest_address}")
            return False
        
        # Get first hop (next node in route)
        next_hop = route[1]
        
        # Get interface to next hop
        if next_hop not in self.interfaces:
            print(f"[Node {self.address}] No interface to {next_hop}")
            return False
        
        interface = self.interfaces[next_hop]
        
        # Add packet to send buffer
        if interface.send_buffer.push(packet):
            print(f"[Node {self.address}] Injected packet to {packet.dest_address} via {next_hop}")
            return True
        else:
            print(f"[Node {self.address}] Send buffer full, cannot inject packet")
            return False
    
    def get_status(self) -> dict:
        """Get current node status for monitoring"""
        interfaces_status = {}
        for neighbor_addr, interface in self.interfaces.items():
            interfaces_status[str(neighbor_addr)] = interface.get_status()
        
        return {
            'address': self.address,
            'consumed_packets': len(self.consumed_packets),
            'num_interfaces': len(self.interfaces),
            'interfaces': interfaces_status,
            'routing_table_size': len(self.routing_table)
        }
