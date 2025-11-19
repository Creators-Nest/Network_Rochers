from collections import deque
from ..core.node import Node
from ..routing.shortest_path_router import ShortestPathRouter

class RiCoBiT_Topology:
    """
    Generates and holds the RiCoBiT topology and routing tables.
    """
    def __init__(self, num_levels):
        self.nodes = {} # Key: (R, Nr) address, Value: Node object
        self.num_levels = num_levels
        
        self._generate_nodes()
        self._connect_nodes()
        self._precompute_routing_tables()
        
        # Initialize shortest path router
        self.router = ShortestPathRouter(self)
        self.router.build_routing_tables()
        self.router.apply_to_nodes()
        self.router.print_routing_statistics()
        
        # Store distance tables for easy access
        self.all_pairs_distances = self.router.distance_tables

    def _generate_nodes(self):
        """Creates nodes based on 2^R formula."""
        for R in range(self.num_levels):
            num_nodes_in_ring = 2**R
            for Nr in range(num_nodes_in_ring):
                address = (R, Nr)
                self.nodes[address] = Node(address)
        print(f"Generated {len(self.nodes)} total nodes.")

    def _connect_nodes(self):
        """Connects nodes (Ring + Tree connections)."""
        for R in range(self.num_levels):
            num_nodes_in_ring = 2**R
            for Nr in range(num_nodes_in_ring):
                current_addr = (R, Nr)
                current_node = self.nodes[current_addr]
                
                # Ring connections (within same level)
                if num_nodes_in_ring > 1:
                    left_neighbor_addr = (R, (Nr - 1) % num_nodes_in_ring)
                    right_neighbor_addr = (R, (Nr + 1) % num_nodes_in_ring)
                    
                    if left_neighbor_addr not in current_node.interfaces:
                        current_node.add_connection(self.nodes[left_neighbor_addr])
                    if right_neighbor_addr not in current_node.interfaces:
                        current_node.add_connection(self.nodes[right_neighbor_addr])
                
                # Tree connections (to upper level)
                if R < self.num_levels - 1:
                    upper_R = R + 1
                    upper_Nr_1 = 2 * Nr
                    upper_Nr_2 = 2 * Nr + 1
                    
                    upper_addr_1 = (upper_R, upper_Nr_1)
                    upper_addr_2 = (upper_R, upper_Nr_2)
                    
                    if upper_addr_1 not in current_node.interfaces:
                        current_node.add_connection(self.nodes[upper_addr_1])
                    if upper_addr_2 not in current_node.interfaces:
                        current_node.add_connection(self.nodes[upper_addr_2])
        
        print("Finished connecting nodes.")
        
    def _precompute_routing_tables(self):
        """
        Legacy method kept for compatibility.
        The actual routing tables are now built by ShortestPathRouter
        using BFS to find true shortest paths.
        """
        # Initialize empty routing tables
        for node in self.nodes.values():
            node.routing_table = {}

    def get_all_node_addresses(self):
        return list(self.nodes.keys())