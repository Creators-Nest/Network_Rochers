"""
Shortest Path Routing Algorithm for RiCoBiT Topology

This module implements a routing algorithm that finds the true shortest path
in the RiCoBiT topology by considering both ring connections and tree connections.

According to the routing logic document:
1. For nodes on the same ring: Use the shortest ring path (clockwise or counter-clockwise)
2. For nodes on different rings: Navigate via the binary tree structure, finding the
   optimal path through common ancestors

The algorithm uses BFS (Breadth-First Search) to guarantee the shortest path.
"""

from collections import deque
from typing import Dict, Tuple, List, Optional


class ShortestPathRouter:
    """
    Implements shortest-path routing for RiCoBiT topology using BFS.
    
    Key principles:
    - Ring connections provide shortest paths within a ring
    - Tree connections (parent-child) allow movement between rings
    - The shortest path may involve going up the tree to a common ancestor,
      then down to the destination ring, then along the ring to the destination node
    """
    
    def __init__(self, topology):
        """
        Initialize the router with a RiCoBiT topology.
        
        Args:
            topology: RiCoBiT_Topology instance with nodes and connections
        """
        self.topology = topology
        self.routing_tables = {}  # Key: source_addr, Value: {dest_addr: next_hop}
        self.distance_tables = {}  # Key: source_addr, Value: {dest_addr: distance}
        
    def build_routing_tables(self):
        """
        Build routing tables for all nodes using BFS to find shortest paths.
        This ensures optimal routing decisions at each hop.
        """
        print("Building shortest-path routing tables using BFS...")
        
        for source_addr in self.topology.nodes.keys():
            self.routing_tables[source_addr] = {}
            self.distance_tables[source_addr] = {}
            
            # Run BFS from this source to all destinations
            self._bfs_from_source(source_addr)
        
        print(f"Routing tables built for {len(self.routing_tables)} nodes.")
        self._validate_routing_tables()
    
    def _bfs_from_source(self, source: Tuple[int, int]):
        """
        Run BFS from source to build routing table and distance table.
        
        Args:
            source: Source node address (R, Nr)
        """
        queue = deque([(source, None, 0)])  # (current_node, came_from, distance)
        visited = {source}
        parent_map = {}  # Maps each node to the node we came from
        distance_map = {source: 0}
        
        while queue:
            current, came_from, dist = queue.popleft()
            
            if came_from is not None:
                parent_map[current] = came_from
                distance_map[current] = dist
            
            # Explore neighbors
            current_node = self.topology.nodes[current]
            for neighbor_addr in current_node.interfaces.keys():
                if neighbor_addr not in visited:
                    visited.add(neighbor_addr)
                    queue.append((neighbor_addr, current, dist + 1))
        
        # Build routing table: for each destination, find the first hop
        for dest_addr in self.topology.nodes.keys():
            if dest_addr == source:
                continue
            
            # Trace back from destination to source to find first hop
            path = self._reconstruct_path(source, dest_addr, parent_map)
            
            if len(path) >= 2:
                next_hop = path[1]  # The first hop after source
                self.routing_tables[source][dest_addr] = next_hop
                self.distance_tables[source][dest_addr] = distance_map.get(dest_addr, float('inf'))
    
    def _reconstruct_path(self, source: Tuple[int, int], dest: Tuple[int, int], 
                         parent_map: Dict[Tuple[int, int], Tuple[int, int]]) -> List[Tuple[int, int]]:
        """
        Reconstruct the path from source to dest using parent_map.
        
        Args:
            source: Source node address
            dest: Destination node address
            parent_map: Maps each node to its parent in the BFS tree
            
        Returns:
            List of node addresses from source to dest
        """
        if dest not in parent_map and dest != source:
            return []
        
        path = []
        current = dest
        
        while current != source:
            path.append(current)
            if current not in parent_map:
                return []  # No path found
            current = parent_map[current]
        
        path.append(source)
        path.reverse()
        return path
    
    def _validate_routing_tables(self):
        """
        Validate that routing tables are complete and correct.
        Checks that all source-destination pairs have a valid next hop.
        """
        errors = []
        
        for source_addr in self.topology.nodes.keys():
            for dest_addr in self.topology.nodes.keys():
                if source_addr == dest_addr:
                    continue
                
                # Check if next hop exists
                next_hop = self.routing_tables[source_addr].get(dest_addr)
                
                if next_hop is None:
                    errors.append(f"No route from {source_addr} to {dest_addr}")
                    continue
                
                # Check if next hop is actually a neighbor
                source_node = self.topology.nodes[source_addr]
                if next_hop not in source_node.interfaces:
                    errors.append(f"Invalid next hop {next_hop} from {source_addr} to {dest_addr}")
        
        if errors:
            print(f"WARNING: Found {len(errors)} routing table errors:")
            for error in errors[:10]:  # Print first 10 errors
                print(f"  - {error}")
        else:
            print("✓ Routing tables validated successfully")
    
    def get_next_hop(self, source: Tuple[int, int], dest: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        """
        Get the next hop for a packet going from source to dest.
        
        Args:
            source: Current node address
            dest: Destination node address
            
        Returns:
            Next hop address, or None if no route exists
        """
        if source == dest:
            return None
        
        return self.routing_tables.get(source, {}).get(dest)
    
    def get_full_path(self, source: Tuple[int, int], dest: Tuple[int, int]) -> List[Tuple[int, int]]:
        """
        Get the complete path from source to dest.
        
        Args:
            source: Source node address
            dest: Destination node address
            
        Returns:
            List of node addresses forming the path, or empty list if no path exists
        """
        if source == dest:
            return [source]
        
        path = [source]
        current = source
        visited = set([source])
        
        while current != dest:
            next_hop = self.get_next_hop(current, dest)
            
            if next_hop is None:
                print(f"ERROR: No route from {current} to {dest}")
                return []
            
            if next_hop in visited:
                print(f"ERROR: Loop detected at {next_hop}")
                return []
            
            path.append(next_hop)
            visited.add(next_hop)
            current = next_hop
            
            # Safety check
            if len(path) > 1000:
                print(f"ERROR: Path too long (possible infinite loop)")
                return []
        
        return path
    
    def get_distance(self, source: Tuple[int, int], dest: Tuple[int, int]) -> int:
        """
        Get the shortest distance (number of hops) from source to dest.
        
        Args:
            source: Source node address
            dest: Destination node address
            
        Returns:
            Number of hops, or infinity if no path exists
        """
        if source == dest:
            return 0
        
        return self.distance_tables.get(source, {}).get(dest, float('inf'))
    
    def print_routing_statistics(self):
        """Print statistics about the routing tables."""
        total_routes = sum(len(routes) for routes in self.routing_tables.values())
        
        print(f"\n{'='*60}")
        print("ROUTING STATISTICS")
        print(f"{'='*60}")
        print(f"Total nodes: {len(self.topology.nodes)}")
        print(f"Total routes: {total_routes}")
        print(f"Average routes per node: {total_routes / len(self.topology.nodes):.1f}")
        
        # Find longest shortest path
        max_distance = 0
        max_pair = None
        
        for source, distances in self.distance_tables.items():
            for dest, dist in distances.items():
                if dist != float('inf') and dist > max_distance:
                    max_distance = dist
                    max_pair = (source, dest)
        
        if max_pair:
            print(f"Longest shortest path: {max_distance} hops")
            print(f"  From {max_pair[0]} to {max_pair[1]}")
            path = self.get_full_path(max_pair[0], max_pair[1])
            print(f"  Path: {' -> '.join(str(p) for p in path)}")
        
        print(f"{'='*60}\n")
    
    def apply_to_nodes(self):
        """
        Apply the computed routing tables to the actual node objects in the topology.
        This updates each node's routing_table attribute.
        """
        for node_addr, routing_table in self.routing_tables.items():
            node = self.topology.nodes[node_addr]
            node.routing_table = routing_table.copy()
        
        print("✓ Routing tables applied to all nodes")
