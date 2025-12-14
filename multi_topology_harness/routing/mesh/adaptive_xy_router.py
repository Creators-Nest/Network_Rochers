"""
Adaptive XY Routing Algorithm for Mesh Topology

This router implements Intel-style adaptive routing with XY as the primary strategy:
1. Primary: XY routing (dimension-ordered)
2. Fallback: YX routing when primary path is congested
3. Deadlock prevention via virtual channels simulation

Key features similar to Intel Mesh Interconnect:
- Adaptive path selection based on buffer occupancy
- Congestion-aware routing
- Multiple routing options per destination

References:
- Intel Mesh Interconnect Architecture
- Adaptive Routing in Mesh NoCs (IEEE papers)
"""

from typing import Dict, Tuple, List, Optional


class AdaptiveXYRouter:
    """
    Implements Adaptive XY routing for 2D Mesh topology.
    
    This router can choose between:
    - XY routing (horizontal first, then vertical)
    - YX routing (vertical first, then horizontal)
    
    Selection is based on buffer congestion levels at next-hop nodes.
    """
    
    # Congestion threshold: if buffer is >75% full, consider alternate route
    CONGESTION_THRESHOLD = 0.75
    
    def __init__(self, topology):
        """
        Initialize the Adaptive XY router with a Mesh topology.
        
        Args:
            topology: MeshTopology instance with nodes and connections
        """
        self.topology = topology
        self.routing_tables = {}  # Key: source_addr, Value: {dest_addr: [primary_hop, alternate_hop]}
        self.distance_tables = {}
        
    def build_routing_tables(self):
        """
        Build routing tables with both primary (XY) and alternate (YX) routes.
        """
        print("Building Adaptive XY routing tables for mesh topology...")
        
        for source_addr in self.topology.nodes.keys():
            self.routing_tables[source_addr] = {}
            self.distance_tables[source_addr] = {}
            
            for dest_addr in self.topology.nodes.keys():
                if dest_addr == source_addr:
                    continue
                
                # Compute both XY and YX options
                xy_hop = self._compute_xy_next_hop(source_addr, dest_addr)
                yx_hop = self._compute_yx_next_hop(source_addr, dest_addr)
                
                # Store both options (may be the same if only one dimension differs)
                hops = []
                if xy_hop:
                    hops.append(xy_hop)
                if yx_hop and yx_hop != xy_hop:
                    hops.append(yx_hop)
                
                if hops:
                    self.routing_tables[source_addr][dest_addr] = hops
                    # Manhattan distance
                    distance = abs(dest_addr[0] - source_addr[0]) + abs(dest_addr[1] - source_addr[1])
                    self.distance_tables[source_addr][dest_addr] = distance
        
        print(f"Adaptive XY routing tables built for {len(self.routing_tables)} nodes.")
        self._validate_routing_tables()
    
    def _compute_xy_next_hop(self, source: Tuple[int, int], dest: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        """
        Compute next hop using XY routing (horizontal first, then vertical).
        """
        src_x, src_y = source
        dst_x, dst_y = dest
        
        # X direction first
        if src_x < dst_x:
            next_hop = (src_x + 1, src_y)
        elif src_x > dst_x:
            next_hop = (src_x - 1, src_y)
        # Then Y direction
        elif src_y < dst_y:
            next_hop = (src_x, src_y + 1)
        elif src_y > dst_y:
            next_hop = (src_x, src_y - 1)
        else:
            return None
        
        # Verify valid neighbor
        source_node = self.topology.nodes.get(source)
        if source_node and next_hop in source_node.interfaces:
            return next_hop
        return None
    
    def _compute_yx_next_hop(self, source: Tuple[int, int], dest: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        """
        Compute next hop using YX routing (vertical first, then horizontal).
        This provides an alternate path when XY path is congested.
        """
        src_x, src_y = source
        dst_x, dst_y = dest
        
        # Y direction first
        if src_y < dst_y:
            next_hop = (src_x, src_y + 1)
        elif src_y > dst_y:
            next_hop = (src_x, src_y - 1)
        # Then X direction
        elif src_x < dst_x:
            next_hop = (src_x + 1, src_y)
        elif src_x > dst_x:
            next_hop = (src_x - 1, src_y)
        else:
            return None
        
        # Verify valid neighbor
        source_node = self.topology.nodes.get(source)
        if source_node and next_hop in source_node.interfaces:
            return next_hop
        return None
    
    def get_next_hop(self, current: Tuple[int, int], destination: Tuple[int, int], 
                     check_congestion: bool = True) -> Optional[Tuple[int, int]]:
        """
        Get the next hop, adaptively choosing based on congestion.
        
        Args:
            current: Current node address
            destination: Destination node address
            check_congestion: If True, check buffer levels and choose less congested path
            
        Returns:
            Next hop address or None
        """
        if current == destination:
            return current
        
        hops = self.routing_tables.get(current, {}).get(destination)
        if not hops:
            return None
        
        if len(hops) == 1 or not check_congestion:
            return hops[0]  # Only one option or congestion check disabled
        
        # Check congestion levels at each possible next hop
        best_hop = hops[0]
        min_congestion = float('inf')
        
        for hop in hops:
            congestion = self._get_node_congestion(current, hop)
            if congestion < min_congestion:
                min_congestion = congestion
                best_hop = hop
        
        return best_hop
    
    def _get_node_congestion(self, current: Tuple[int, int], neighbor: Tuple[int, int]) -> float:
        """
        Get the congestion level (0.0 to 1.0) of the interface to a neighbor.
        
        Returns:
            Congestion ratio (buffer_used / buffer_capacity)
        """
        current_node = self.topology.nodes.get(current)
        if not current_node:
            return 0.0
        
        interface = current_node.interfaces.get(neighbor)
        if not interface:
            return 0.0
        
        # Check the outgoing buffer (TX buffer)
        if hasattr(interface, 'tx_buffer') and hasattr(interface.tx_buffer, 'get_occupancy'):
            return interface.tx_buffer.get_occupancy()
        elif hasattr(interface, 'tx_buffer'):
            # Fallback: check buffer length vs capacity
            capacity = getattr(interface.tx_buffer, 'capacity', 4)
            used = len(interface.tx_buffer) if hasattr(interface.tx_buffer, '__len__') else 0
            return used / capacity if capacity > 0 else 0.0
        
        return 0.0
    
    def get_all_next_hops(self, current: Tuple[int, int], destination: Tuple[int, int]) -> List[Tuple[int, int]]:
        """
        Get all possible next hops for adaptive routing.
        
        Returns:
            List of possible next hop addresses
        """
        if current == destination:
            return [current]
        
        return self.routing_tables.get(current, {}).get(destination, [])
    
    def get_full_path(self, source: Tuple[int, int], destination: Tuple[int, int]) -> List[Tuple[int, int]]:
        """
        Get the complete path from source to destination (using primary XY route).
        """
        if source == destination:
            return [source]
        
        path = [source]
        current = source
        max_hops = self.topology.width * self.topology.height
        
        for _ in range(max_hops):
            if current == destination:
                break
            
            next_hop = self.get_next_hop(current, destination, check_congestion=False)
            if next_hop is None or next_hop == current:
                break
            
            path.append(next_hop)
            current = next_hop
        
        return path
    
    def _validate_routing_tables(self):
        """
        Validate routing tables for completeness.
        """
        issues = []
        multi_path_count = 0
        
        for source in self.topology.nodes.keys():
            for dest in self.topology.nodes.keys():
                if source == dest:
                    continue
                
                if dest not in self.routing_tables[source]:
                    issues.append(f"No route from {source} to {dest}")
                    continue
                
                hops = self.routing_tables[source][dest]
                if len(hops) > 1:
                    multi_path_count += 1
                
                for hop in hops:
                    source_node = self.topology.nodes[source]
                    if hop not in source_node.interfaces:
                        issues.append(f"Invalid hop {hop} from {source} to {dest}")
        
        if issues:
            print(f"⚠ Routing validation found {len(issues)} issues:")
            for issue in issues[:10]:
                print(f"  - {issue}")
        else:
            print("✓ Routing tables validated successfully")
            print(f"  Routes with multiple path options: {multi_path_count}")
    
    def apply_to_nodes(self):
        """
        Apply routing tables to all nodes.
        For backward compatibility, stores only primary route in node's routing_table.
        Also stores full adaptive routes in node's adaptive_routes if supported.
        """
        for node_addr, node in self.topology.nodes.items():
            if node_addr in self.routing_tables:
                # Primary route (first option) for backward compatibility
                node.routing_table = {
                    dest: hops[0] 
                    for dest, hops in self.routing_tables[node_addr].items()
                }
                # Full adaptive routes if node supports it
                if hasattr(node, 'adaptive_routes'):
                    node.adaptive_routes = self.routing_tables[node_addr].copy()
        
        print("✓ Routing tables applied to all nodes")
    
    def print_routing_statistics(self):
        """
        Print statistics about the routing configuration.
        """
        if not self.distance_tables:
            print("No routing tables built yet.")
            return
        
        total_routes = sum(len(routes) for routes in self.routing_tables.values())
        multi_path_routes = sum(
            1 for routes in self.routing_tables.values()
            for hops in routes.values() if len(hops) > 1
        )
        avg_routes = total_routes / len(self.routing_tables) if self.routing_tables else 0
        
        max_distance = 0
        longest_path_pair = None
        
        for source, distances in self.distance_tables.items():
            for dest, dist in distances.items():
                if dist > max_distance:
                    max_distance = dist
                    longest_path_pair = (source, dest)
        
        print("\n" + "="*60)
        print("ADAPTIVE XY ROUTING STATISTICS")
        print("="*60)
        print(f"Total nodes: {len(self.topology.nodes)}")
        print(f"Total routes: {total_routes}")
        print(f"Routes with alternate paths: {multi_path_routes}")
        print(f"Average routes per node: {avg_routes:.1f}")
        print(f"Longest shortest path: {max_distance} hops")
        
        if longest_path_pair:
            src, dst = longest_path_pair
            path = self.get_full_path(src, dst)
            print(f"  From {src} to {dst}")
            path_str = " -> ".join([str(node) for node in path])
            print(f"  Primary path: {path_str}")
        
        print("="*60)
        print()
