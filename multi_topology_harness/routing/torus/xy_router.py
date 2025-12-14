"""
XY Routing Algorithm for 2D Torus Topology

This module implements XY routing (dimension-order routing) for torus networks.
XY routing routes packets first in the X dimension, then in the Y dimension.

Key principles:
1. Route in X dimension first until X coordinates match
2. Then route in Y dimension until Y coordinates match
3. Consider wraparound for shortest path (torus property)
4. Deterministic and deadlock-free routing
"""

from typing import Dict, Tuple, List, Optional

class XYRouter:
    """
    Implements XY routing for 2D Torus topology.
    
    XY routing is a simple, deterministic routing algorithm:
    - First route in X dimension (horizontal)
    - Then route in Y dimension (vertical)
    - Always choose shortest path considering torus wraparound
    """
    
    def __init__(self, topology):
        """
        Initialize the XY router with a torus topology.
        
        Args:
            topology: TorusTopology instance with nodes and connections
        """
        self.topology = topology
        self.routing_tables = {}  # Key: source_addr, Value: {dest_addr: next_hop}
        self.distance_tables = {}  # Key: source_addr, Value: {dest_addr: distance}
        
    def build_routing_tables(self):
        """
        Build routing tables for all nodes using XY routing algorithm.
        """
        print("Building XY routing tables for torus topology...")
        
        for source_addr in self.topology.nodes.keys():
            self.routing_tables[source_addr] = {}
            self.distance_tables[source_addr] = {}
            
            # Compute routes from this source to all destinations
            for dest_addr in self.topology.nodes.keys():
                if source_addr != dest_addr:
                    next_hop = self._compute_xy_next_hop(source_addr, dest_addr)
                    distance = self.topology.manhattan_distance(source_addr, dest_addr)
                    
                    self.routing_tables[source_addr][dest_addr] = next_hop
                    self.distance_tables[source_addr][dest_addr] = distance
        
        print(f"XY routing tables built for {len(self.routing_tables)} nodes.")
        self._validate_routing_tables()
    
    def _compute_xy_next_hop(self, source: Tuple[int, int], dest: Tuple[int, int]) -> Tuple[int, int]:
        """
        Compute next hop using XY routing algorithm.
        
        Args:
            source: Source node coordinates (x, y)
            dest: Destination node coordinates (x, y)
            
        Returns:
            Next hop coordinates (x, y)
        """
        src_x, src_y = source
        dst_x, dst_y = dest
        
        # Phase 1: Route in X dimension first
        if src_x != dst_x:
            # Determine shortest X direction considering wraparound
            direct_dist = abs(dst_x - src_x)
            wrap_dist = self.topology.width - direct_dist
            
            if direct_dist <= wrap_dist:
                # Direct path is shorter
                if dst_x > src_x:
                    # Move East
                    next_x = (src_x + 1) % self.topology.width
                else:
                    # Move West
                    next_x = (src_x - 1) % self.topology.width
            else:
                # Wraparound path is shorter
                if dst_x > src_x:
                    # Move West (wraparound)
                    next_x = (src_x - 1) % self.topology.width
                else:
                    # Move East (wraparound)
                    next_x = (src_x + 1) % self.topology.width
            
            return (next_x, src_y)
        
        # Phase 2: X coordinates match, route in Y dimension
        elif src_y != dst_y:
            # Determine shortest Y direction considering wraparound
            direct_dist = abs(dst_y - src_y)
            wrap_dist = self.topology.height - direct_dist
            
            if direct_dist <= wrap_dist:
                # Direct path is shorter
                if dst_y > src_y:
                    # Move South
                    next_y = (src_y + 1) % self.topology.height
                else:
                    # Move North
                    next_y = (src_y - 1) % self.topology.height
            else:
                # Wraparound path is shorter
                if dst_y > src_y:
                    # Move North (wraparound)
                    next_y = (src_y - 1) % self.topology.height
                else:
                    # Move South (wraparound)
                    next_y = (src_y + 1) % self.topology.height
            
            return (src_x, next_y)
        
        # Should not reach here if source != dest
        return source
    
    def _validate_routing_tables(self):
        """
        Validate that routing tables are complete and correct.
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
                
                # Check if next hop is valid neighbor in torus
                expected_neighbors = self.topology.get_neighbors(source_addr)
                if next_hop not in expected_neighbors:
                    errors.append(f"Next hop {next_hop} not a valid neighbor of {source_addr}")
        
        if errors:
            print(f"WARNING: Found {len(errors)} routing table errors:")
            for error in errors[:10]:  # Print first 10 errors
                print(f"  - {error}")
        else:
            print("XY routing tables validated successfully")
    
    def get_next_hop(self, source: Tuple[int, int], dest: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        """
        Get the next hop for a packet going from source to dest.
        
        Args:
            source: Current node coordinates
            dest: Destination node coordinates
            
        Returns:
            Next hop coordinates, or None if no route exists
        """
        if source == dest:
            return None
        
        return self.routing_tables.get(source, {}).get(dest)
    
    def get_full_path(self, source: Tuple[int, int], dest: Tuple[int, int]) -> List[Tuple[int, int]]:
        """
        Get the complete XY routing path from source to dest.
        
        Args:
            source: Source node coordinates
            dest: Destination node coordinates
            
        Returns:
            List of node coordinates forming the path
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
        Get the Manhattan distance from source to dest in torus.
        
        Args:
            source: Source node coordinates
            dest: Destination node coordinates
            
        Returns:
            Manhattan distance considering torus wraparound
        """
        if source == dest:
            return 0
        
        return self.distance_tables.get(source, {}).get(dest, float('inf'))
    
    def print_routing_statistics(self):
        """Print statistics about the XY routing tables."""
        total_routes = sum(len(routes) for routes in self.routing_tables.values())
        
        print(f"\n{'='*60}")
        print("XY ROUTING STATISTICS")
        print(f"{'='*60}")
        print(f"Torus dimensions: {self.topology.width} x {self.topology.height}")
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
        
        # Calculate average distance
        total_distance = 0
        total_pairs = 0
        for distances in self.distance_tables.values():
            for dist in distances.values():
                if dist != float('inf'):
                    total_distance += dist
                    total_pairs += 1
        
        if total_pairs > 0:
            avg_distance = total_distance / total_pairs
            print(f"Average path length: {avg_distance:.2f} hops")
        
        print(f"{'='*60}\n")
    
    def apply_to_nodes(self):
        """
        Apply the computed routing tables to the actual node objects in the topology.
        """
        for node_addr, routing_table in self.routing_tables.items():
            node = self.topology.nodes[node_addr]
            node.routing_table = routing_table.copy()
        
        print("XY routing tables applied to all nodes")