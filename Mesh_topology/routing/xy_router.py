"""
XY Routing Algorithm for Mesh Topology

XY routing is a dimension-ordered routing algorithm that:
1. First routes along the X dimension (horizontal) until X coordinates match
2. Then routes along the Y dimension (vertical) until Y coordinates match

This guarantees deadlock-free routing in a mesh network.
"""

from typing import Dict, Tuple, List


class XYRouter:
    """
    Implements XY (dimension-ordered) routing for 2D Mesh topology.
    
    Routing rules:
    - Always route in X direction first (change x-coordinate)
    - Then route in Y direction (change y-coordinate)
    - This creates deterministic paths and prevents deadlocks
    """
    
    def __init__(self, topology):
        """
        Initialize the XY router with a Mesh topology.
        
        Args:
            topology: MeshTopology instance with nodes and connections
        """
        self.topology = topology
        self.routing_tables = {}  # Key: source_addr, Value: {dest_addr: next_hop}
        self.distance_tables = {}  # Key: source_addr, Value: {dest_addr: distance}
        
    def build_routing_tables(self):
        """
        Build routing tables for all nodes using XY routing algorithm.
        """
        print("Building XY routing tables for mesh topology...")
        
        for source_addr in self.topology.nodes.keys():
            self.routing_tables[source_addr] = {}
            self.distance_tables[source_addr] = {}
            
            # Compute routes from this source to all destinations
            for dest_addr in self.topology.nodes.keys():
                if dest_addr == source_addr:
                    continue
                
                next_hop = self._compute_xy_next_hop(source_addr, dest_addr)
                if next_hop:
                    self.routing_tables[source_addr][dest_addr] = next_hop
                    # Manhattan distance
                    distance = abs(dest_addr[0] - source_addr[0]) + abs(dest_addr[1] - source_addr[1])
                    self.distance_tables[source_addr][dest_addr] = distance
        
        print(f"XY routing tables built for {len(self.routing_tables)} nodes.")
        self._validate_routing_tables()
    
    def _compute_xy_next_hop(self, source: Tuple[int, int], dest: Tuple[int, int]) -> Tuple[int, int]:
        """
        Compute the next hop using XY routing algorithm.
        
        XY Routing Rules:
        1. If source.x != dest.x, move in X direction (horizontal)
        2. Else if source.y != dest.y, move in Y direction (vertical)
        
        Args:
            source: Source node address (x, y)
            dest: Destination node address (x, y)
            
        Returns:
            Next hop address (x, y) or None if source == dest
        """
        src_x, src_y = source
        dst_x, dst_y = dest
        
        # Step 1: Route in X dimension first
        if src_x < dst_x:
            # Move East (increase x)
            next_hop = (src_x + 1, src_y)
        elif src_x > dst_x:
            # Move West (decrease x)
            next_hop = (src_x - 1, src_y)
        # Step 2: If X matches, route in Y dimension
        elif src_y < dst_y:
            # Move North (increase y)
            next_hop = (src_x, src_y + 1)
        elif src_y > dst_y:
            # Move South (decrease y)
            next_hop = (src_x, src_y - 1)
        else:
            # Source == Destination
            return None
        
        # Verify next_hop is a valid neighbor
        source_node = self.topology.nodes.get(source)
        if source_node and next_hop in source_node.interfaces:
            return next_hop
        else:
            return None
    
    def get_next_hop(self, current: Tuple[int, int], destination: Tuple[int, int]) -> Tuple[int, int]:
        """
        Get the next hop from current node to destination using routing table.
        
        Args:
            current: Current node address (x, y)
            destination: Destination node address (x, y)
            
        Returns:
            Next hop address (x, y)
        """
        if current == destination:
            return current
        
        return self.routing_tables.get(current, {}).get(destination)
    
    def get_full_path(self, source: Tuple[int, int], destination: Tuple[int, int]) -> List[Tuple[int, int]]:
        """
        Get the complete path from source to destination using XY routing.
        
        Args:
            source: Source node address (x, y)
            destination: Destination node address (x, y)
            
        Returns:
            List of node addresses forming the path
        """
        if source == destination:
            return [source]
        
        path = [source]
        current = source
        max_hops = self.topology.width * self.topology.height  # Prevent infinite loops
        
        for _ in range(max_hops):
            if current == destination:
                break
            
            next_hop = self.get_next_hop(current, destination)
            if next_hop is None or next_hop == current:
                # No valid next hop found
                break
            
            path.append(next_hop)
            current = next_hop
        
        return path
    
    def _validate_routing_tables(self):
        """
        Validate that routing tables are consistent and complete.
        """
        issues = []
        
        for source in self.topology.nodes.keys():
            for dest in self.topology.nodes.keys():
                if source == dest:
                    continue
                
                if dest not in self.routing_tables[source]:
                    issues.append(f"No route from {source} to {dest}")
                    continue
                
                next_hop = self.routing_tables[source][dest]
                source_node = self.topology.nodes[source]
                
                if next_hop not in source_node.interfaces:
                    issues.append(f"Invalid next hop {next_hop} from {source} to {dest}")
        
        if issues:
            print(f"⚠ Routing table validation found {len(issues)} issues:")
            for issue in issues[:10]:  # Show first 10 issues
                print(f"  - {issue}")
        else:
            print("✓ Routing tables validated successfully")
    
    def apply_to_nodes(self):
        """
        Apply computed routing tables to all nodes in the topology.
        """
        for node_addr, node in self.topology.nodes.items():
            if node_addr in self.routing_tables:
                node.routing_table = self.routing_tables[node_addr].copy()
        
        print("✓ Routing tables applied to all nodes")
    
    def print_routing_statistics(self):
        """
        Print statistics about the routing configuration.
        """
        if not self.distance_tables:
            print("No routing tables built yet.")
            return
        
        total_routes = sum(len(routes) for routes in self.routing_tables.values())
        avg_routes = total_routes / len(self.routing_tables) if self.routing_tables else 0
        
        # Find longest path
        max_distance = 0
        longest_path_pair = None
        
        for source, distances in self.distance_tables.items():
            for dest, dist in distances.items():
                if dist > max_distance:
                    max_distance = dist
                    longest_path_pair = (source, dest)
        
        print("\n" + "="*60)
        print("XY ROUTING STATISTICS")
        print("="*60)
        print(f"Total nodes: {len(self.topology.nodes)}")
        print(f"Total routes: {total_routes}")
        print(f"Average routes per node: {avg_routes:.1f}")
        print(f"Longest shortest path: {max_distance} hops")
        
        if longest_path_pair:
            src, dst = longest_path_pair
            path = self.get_full_path(src, dst)
            print(f"  From {src} to {dst}")
            path_str = " -> ".join([str(node) for node in path])
            print(f"  Path: {path_str}")
        
        print("="*60)
        print()
