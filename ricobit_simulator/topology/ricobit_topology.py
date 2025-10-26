from collections import deque
from core.node import Node

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
        """Build routing tables following RicoBit routing logic:
        - Same Ring: Use shortest ring path (clockwise or counter-clockwise)
        - Different Rings: Navigate via tree structure (up/down binary tree)
        """
        all_addresses = self.nodes.keys()
        self.all_pairs_distances = {} 

        for start_addr in all_addresses:
            start_node = self.nodes[start_addr]
            self.all_pairs_distances[start_addr] = {}
            
            for dest_addr in all_addresses:
                if start_addr == dest_addr:
                    self.all_pairs_distances[start_addr][dest_addr] = 0
                    continue
                
                # Compute next hop using RicoBit routing logic
                next_hop = self._compute_next_hop(start_addr, dest_addr)
                if next_hop:
                    start_node.routing_table[dest_addr] = next_hop
                
                # Compute distance
                distance = self._compute_distance(start_addr, dest_addr)
                self.all_pairs_distances[start_addr][dest_addr] = distance
        
        print("Routing tables and distance maps are built using RicoBit routing logic.")
    
    def _compute_next_hop(self, source, dest):
        """Compute the next hop from source to dest following RicoBit routing logic."""
        src_R, src_Nr = source
        dst_R, dst_Nr = dest
        
        # Case 1: Same ring - use ring connections
        if src_R == dst_R:
            if src_R == 0:
                # Ring 0 has only one node, shouldn't happen
                return None
            
            num_nodes = 2 ** src_R
            # Calculate shortest path on ring (circular)
            clockwise_dist = (dst_Nr - src_Nr) % num_nodes
            counter_clockwise_dist = (src_Nr - dst_Nr) % num_nodes
            
            if clockwise_dist <= counter_clockwise_dist:
                # Go clockwise (right)
                next_Nr = (src_Nr + 1) % num_nodes
            else:
                # Go counter-clockwise (left)
                next_Nr = (src_Nr - 1) % num_nodes
            
            return (src_R, next_Nr)
        
        # Case 2: Different rings - use tree navigation
        # If dest is on inner ring (dst_R < src_R), move toward parent (up the tree)
        if dst_R < src_R:
            # Move to parent ring
            parent_R = src_R - 1
            parent_Nr = src_Nr // 2
            return (parent_R, parent_Nr)
        
        # If dest is on outer ring (dst_R > src_R), move toward children (down the tree)
        else:  # dst_R > src_R
            # First, we need to navigate to the correct subtree
            # Calculate which child path leads to destination
            
            # Find the common ancestor level
            current_R = src_R
            current_Nr = src_Nr
            
            # Navigate down to next ring
            next_R = src_R + 1
            
            # Determine which child to take based on destination
            # Scale dest_Nr to current level to see which subtree it belongs to
            scale_factor = 2 ** (dst_R - next_R)
            target_at_next_level = dst_Nr // scale_factor
            
            # Our children at next level
            child1_Nr = 2 * src_Nr
            child2_Nr = 2 * src_Nr + 1
            
            # Choose child that leads toward destination
            if target_at_next_level == child1_Nr:
                return (next_R, child1_Nr)
            else:
                return (next_R, child2_Nr)
    
    def _compute_distance(self, source, dest):
        """Compute the hop distance from source to dest by actually tracing the path."""
        if source == dest:
            return 0
        
        # Trace the actual path using routing table
        current = source
        hops = 0
        visited = set()
        
        while current != dest:
            if current in visited or hops > 1000:  # Safety check
                return float('inf')  # Loop detected
            
            visited.add(current)
            next_hop = self._compute_next_hop(current, dest)
            
            if next_hop is None:
                return float('inf')  # No path
            
            current = next_hop
            hops += 1
        
        return hops

    def get_all_node_addresses(self):
        return list(self.nodes.keys())