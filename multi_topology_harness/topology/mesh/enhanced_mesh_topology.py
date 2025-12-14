"""
Enhanced Mesh Topology with improved node and interface handling
Based on RiCoBiT simulator architecture patterns
Supports adaptive XY routing for congestion avoidance (Intel Mesh style)
"""

from typing import Dict, Tuple, List, Optional
import sys
import os

# Add parent directory to path for standalone execution
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.mesh.enhanced_node import EnhancedNode
from routing.mesh.xy_router import XYRouter

# Try to import adaptive router, fallback to standard XY
try:
    from routing.mesh.adaptive_xy_router import AdaptiveXYRouter
    ADAPTIVE_ROUTING_AVAILABLE = True
except ImportError:
    ADAPTIVE_ROUTING_AVAILABLE = False


class EnhancedMeshTopology:
    """
    Enhanced Mesh Topology for Network-on-Chip
    
    Architecture improvements based on RiCoBiT simulator:
    - Proper node-interface-buffer hierarchy
    - Bidirectional interface connections
    - Comprehensive routing table management
    - Advanced packet flow control
    - Node update stepping for simulation
    - Adaptive XY/YX routing for congestion avoidance (Intel Mesh style)
    
    Creates a 2D mesh grid where each node has n interfaces (n = adjacent nodes)
    Each interface manages its own buffers and handshake protocol
    """
    
    def __init__(self, width: int = 6, height: int = 6, buffer_capacity: int = 4, 
                 use_adaptive_routing: bool = True):
        """
        Initialize mesh topology
        
        Args:
            width: Number of nodes in X direction
            height: Number of nodes in Y direction
            buffer_capacity: Buffer size for each interface
            use_adaptive_routing: If True, use adaptive XY/YX routing (Intel style)
        """
        self.width = width
        self.height = height
        self.buffer_capacity = buffer_capacity
        self.nodes: Dict[Tuple[int, int], EnhancedNode] = {}
        self.use_adaptive_routing = use_adaptive_routing and ADAPTIVE_ROUTING_AVAILABLE
        
        # Build topology
        self._create_nodes()
        self._create_connections()
        self._build_routing_tables()
    
    def _create_nodes(self):
        """Create all nodes in the mesh"""
        for y in range(self.height):
            for x in range(self.width):
                address = (x, y)
                self.nodes[address] = EnhancedNode(address)
    
    def _create_connections(self):
        """Create bidirectional connections between adjacent nodes"""
        for y in range(self.height):
            for x in range(self.width):
                current_addr = (x, y)
                current_node = self.nodes[current_addr]
                
                # Connect to North (y-1)
                if y > 0:
                    neighbor_addr = (x, y - 1)
                    current_node.add_interface(neighbor_addr, self.buffer_capacity)
                
                # Connect to South (y+1)
                if y < self.height - 1:
                    neighbor_addr = (x, y + 1)
                    current_node.add_interface(neighbor_addr, self.buffer_capacity)
                
                # Connect to West (x-1)
                if x > 0:
                    neighbor_addr = (x - 1, y)
                    current_node.add_interface(neighbor_addr, self.buffer_capacity)
                
                # Connect to East (x+1)
                if x < self.width - 1:
                    neighbor_addr = (x + 1, y)
                    current_node.add_interface(neighbor_addr, self.buffer_capacity)
        
        # Connect interfaces bidirectionally
        self._connect_interfaces()
    
    def _connect_interfaces(self):
        """Connect interfaces between neighboring nodes bidirectionally"""
        for addr, node in self.nodes.items():
            for neighbor_addr, interface in node.interfaces.items():
                neighbor_node = self.nodes.get(neighbor_addr)
                if neighbor_node:
                    neighbor_interface = neighbor_node.interfaces.get(addr)
                    if neighbor_interface and (not hasattr(interface, 'connected_interface') or interface.connected_interface is None):
                        interface.connect_to(neighbor_interface)
    
    def _build_routing_tables(self):
        """Build routing tables for all nodes using adaptive or standard XY routing"""
        
        if self.use_adaptive_routing:
            print("Using Adaptive XY/YX routing (Intel Mesh style)...")
            router = AdaptiveXYRouter(self)
            router.build_routing_tables()
            
            # Apply both primary routes and adaptive routes to nodes
            for source_addr in self.nodes:
                source_node = self.nodes[source_addr]
                
                for dest_addr in self.nodes:
                    if source_addr != dest_addr:
                        # Get all possible next hops for adaptive routing
                        next_hops = router.get_all_next_hops(source_addr, dest_addr)
                        if next_hops:
                            # Primary route
                            source_node.routing_table[dest_addr] = next_hops[0]
                            # All adaptive options
                            source_node.adaptive_routes[dest_addr] = next_hops
            
            router.print_routing_statistics()
        else:
            print("Using standard XY routing...")
            router = XYRouter(self)
            router.build_routing_tables()
            
            for source_addr in self.nodes:
                source_node = self.nodes[source_addr]
                
                for dest_addr in self.nodes:
                    if source_addr != dest_addr:
                        next_hop = router.get_next_hop(source_addr, dest_addr)
                        if next_hop:
                            source_node.routing_table[dest_addr] = next_hop
        
        print(f"✓ Routing tables built for {len(self.nodes)} nodes")
    
    def get_node(self, address: Tuple[int, int]) -> EnhancedNode:
        """Get node at given address"""
        return self.nodes.get(address)
    
    def get_neighbors(self, address: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Get list of neighbor addresses for a node"""
        node = self.nodes.get(address)
        if node:
            return list(node.interfaces.keys())
        return []
    
    def update_all_nodes(self):
        """Update all nodes (call their update methods)"""
        for node in self.nodes.values():
            node.update()
    
    def get_topology_info(self) -> dict:
        """Get comprehensive topology information"""
        return {
            'width': self.width,
            'height': self.height,
            'total_nodes': len(self.nodes),
            'buffer_capacity': self.buffer_capacity,
            'nodes': [
                {
                    'address': addr,
                    'num_interfaces': len(node.interfaces),
                    'neighbors': list(node.interfaces.keys())
                }
                for addr, node in self.nodes.items()
            ]
        }
    
    def reset(self):
        """Reset all nodes in the topology"""
        for node in self.nodes.values():
            node.reset()
    
    def step_all_nodes(self, global_clock: int):
        """
        Execute one simulation step for all nodes
        Pattern from RiCoBiT simulator node_step method
        
        Args:
            global_clock: Current global simulation clock
        """
        for node in self.nodes.values():
            node.process_packets(global_clock)
    
    def update_all_interfaces(self):
        """
        Update all node interfaces (sender and receiver logic)
        Based on RiCoBiT Interface update pattern
        """
        for node in self.nodes.values():
            for interface in node.interfaces.values():
                # Update sender side (REQ, DATA transfer)
                interface.update_sender_logic()
        
        for node in self.nodes.values():
            for interface in node.interfaces.values():
                # Update receiver side (ACK, buffer management)
                interface.update_receiver_logic()
    
    def inject_packet(self, source_addr: Tuple[int, int], dest_addr: Tuple[int, int], payload: dict) -> bool:
        """
        Inject a packet into the network at source node
        Pattern from RiCoBiT packet injection
        
        Args:
            source_addr: Source node address
            dest_addr: Destination node address
            payload: Packet payload data
            
        Returns:
            True if packet was successfully injected, False otherwise
        """
        source_node = self.nodes.get(source_addr)
        if not source_node:
            return False
        
        # Create packet
        from core.packet import Packet
        packet = Packet(
            packet_id=f"pkt_{source_addr}_{dest_addr}_{payload.get('id', 0)}",
            source_address=source_addr,
            dest_address=dest_addr,
            payload=payload
        )
        
        # Inject into source node's application buffer
        return source_node.inject_packet(packet)
    
    def get_delivered_packets(self) -> List:
        """
        Collect all delivered packets from all nodes
        Pattern from RiCoBiT application_logic_buffer collection
        
        Returns:
            List of delivered packets across all nodes
        """
        delivered = []
        for node in self.nodes.values():
            if hasattr(node, 'application_buffer'):
                delivered.extend(node.application_buffer)
        return delivered
    
    def get_network_statistics(self) -> dict:
        """
        Get comprehensive network statistics
        Enhanced version with buffer utilization and interface states
        
        Returns:
            Dictionary with network-wide statistics
        """
        total_packets_in_flight = 0
        total_buffer_usage = 0
        total_buffer_capacity = 0
        active_interfaces = 0
        total_interfaces = 0
        
        for node in self.nodes.values():
            for interface in node.interfaces.values():
                total_interfaces += 1
                total_buffer_usage += interface.send_buffer.size() + interface.receive_buffer.size()
                total_buffer_capacity += interface.send_buffer.capacity * 2
                
                # Count active interfaces (busy or transferring)
                if interface.bit_Busy or interface.bit_Transfer or interface.bit_Receive:
                    active_interfaces += 1
                
                total_packets_in_flight += interface.send_buffer.size()
        
        return {
            'total_nodes': len(self.nodes),
            'total_interfaces': total_interfaces,
            'active_interfaces': active_interfaces,
            'packets_in_flight': total_packets_in_flight,
            'buffer_utilization': (total_buffer_usage / total_buffer_capacity * 100) if total_buffer_capacity > 0 else 0,
            'network_load': (active_interfaces / total_interfaces * 100) if total_interfaces > 0 else 0
        }
    
    def get_node_state(self, address: Tuple[int, int]) -> Optional[dict]:
        """
        Get detailed state of a specific node
        Useful for visualization and debugging
        
        Args:
            address: Node address
            
        Returns:
            Dictionary with node state information
        """
        node = self.nodes.get(address)
        if not node:
            return None
        
        interface_states = {}
        for neighbor_addr, interface in node.interfaces.items():
            interface_states[neighbor_addr] = {
                'pins': {
                    'REQ': interface.pin_REQ,
                    'ACK': interface.pin_ACK,
                    'DATA': interface.pin_DATA is not None,
                    'CLK': interface.pin_CLK,
                    'CHOKE': interface.pin_CHOKE
                },
                'status_bits': {
                    'Busy': interface.bit_Busy,
                    'Transfer': interface.bit_Transfer,
                    'Receive': interface.bit_Receive
                },
                'buffers': {
                    'send': {
                        'size': interface.send_buffer.size(),
                        'capacity': interface.send_buffer.capacity,
                        'full': interface.send_buffer.is_full()
                    },
                    'receive': {
                        'size': interface.receive_buffer.size(),
                        'capacity': interface.receive_buffer.capacity,
                        'full': interface.receive_buffer.is_full()
                    }
                }
            }
        
        return {
            'address': address,
            'neighbors': list(node.interfaces.keys()),
            'interface_count': len(node.interfaces),
            'interfaces': interface_states,
            'routing_table_size': len(node.routing_table) if hasattr(node, 'routing_table') else 0
        }
    
    def validate_topology(self) -> Tuple[bool, List[str]]:
        """
        Validate topology integrity
        Pattern from RiCoBiT connection validation
        
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        
        # Check all nodes have correct connections
        for addr, node in self.nodes.items():
            x, y = addr
            
            # Expected neighbors based on mesh topology
            expected_neighbors = []
            if y > 0:
                expected_neighbors.append((x, y - 1))  # North
            if y < self.height - 1:
                expected_neighbors.append((x, y + 1))  # South
            if x > 0:
                expected_neighbors.append((x - 1, y))  # West
            if x < self.width - 1:
                expected_neighbors.append((x + 1, y))  # East
            
            # Verify interfaces exist for all expected neighbors
            actual_neighbors = set(node.interfaces.keys())
            expected_set = set(expected_neighbors)
            
            if actual_neighbors != expected_set:
                missing = expected_set - actual_neighbors
                extra = actual_neighbors - expected_set
                if missing:
                    issues.append(f"Node {addr} missing connections to: {missing}")
                if extra:
                    issues.append(f"Node {addr} has unexpected connections to: {extra}")
        
        # Validate routing tables
        for addr, node in self.nodes.items():
            if not hasattr(node, 'routing_table') or not node.routing_table:
                issues.append(f"Node {addr} has empty routing table")
        
        return (len(issues) == 0, issues)
    
    def __repr__(self):
        return f"EnhancedMeshTopology({self.width}x{self.height}, {len(self.nodes)} nodes)"
