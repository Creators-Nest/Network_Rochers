"""
Arc Renderer for RicoBit Topology Visualizer
Handles accurate arc and arrow rendering for routing paths

This renderer pre-computes all possible arc segments between adjacent nodes
on each ring, then uses these segments to draw the actual routing path.
"""

import math
import tkinter as tk


class ArcRenderer:
    """Handles precise arc rendering for routing paths with proper directional arrows"""
    
    def __init__(self, canvas, colors):
        self.canvas = canvas
        self.colors = colors
        self.arc_items = []
        self.arrow_items = []
        
        # Pre-computed arc segments: {(ring, start_node, end_node): [list of (x,y) points]}
        self.ring_arc_segments = {}
    
    def precompute_ring_arcs(self, num_levels, node_positions, topology):
        """Pre-compute all arc segments for all rings
        
        For each ring, compute the arc path between every pair of adjacent nodes.
        This creates a lookup table of arc segments that we can use during routing visualization.
        
        Args:
            num_levels: Number of rings in topology
            node_positions: Dictionary mapping (ring, node) to (x, y) positions
            topology: The RicoBit topology object
        """
        print(f"\n[ArcRenderer] Pre-computing arc segments for {num_levels} rings...")
        self.ring_arc_segments.clear()
        
        canvas_width = self.canvas.winfo_width() or 800
        canvas_height = self.canvas.winfo_height() or 600
        center_x = canvas_width / 2
        center_y = canvas_height / 2
        
        # Calculate ring spacing - MUST match visualizer.py for consistency
        max_radius = min(canvas_width, canvas_height) * 0.48  # Increased to 0.48 for much better spacing
        ring_spacing = max_radius / max(1, num_levels - 1) if num_levels > 1 else max_radius
        
        # For each ring (skip ring 0 - center node has no ring)
        for ring_num in range(1, num_levels):
            num_nodes_in_ring = 2 ** ring_num
            radius = ring_spacing * ring_num
            
            print(f"  Ring {ring_num}: {num_nodes_in_ring} nodes, radius={radius:.1f}")
            
            # For each node on this ring, compute arc to its neighbors
            for node_nr in range(num_nodes_in_ring):
                node_addr = (ring_num, node_nr)
                
                # Check if this node exists in topology
                if node_addr not in topology.nodes:
                    continue
                
                # Get the node's neighbors on the same ring
                node = topology.nodes[node_addr]
                ring_neighbors = []
                
                for neighbor_addr in node.interfaces.keys():
                    n_ring, n_node = neighbor_addr
                    if n_ring == ring_num:  # Same ring neighbor
                        ring_neighbors.append(n_node)
                
                # For each ring neighbor, compute the arc segment
                for neighbor_nr in ring_neighbors:
                    # Create arc segment from node_nr to neighbor_nr
                    start_angle_rad = (2 * math.pi * node_nr / num_nodes_in_ring) - (math.pi / 2)
                    end_angle_rad = (2 * math.pi * neighbor_nr / num_nodes_in_ring) - (math.pi / 2)
                    
                    # Determine if this is clockwise or counterclockwise
                    clockwise_neighbor = (node_nr + 1) % num_nodes_in_ring
                    counterclockwise_neighbor = (node_nr - 1 + num_nodes_in_ring) % num_nodes_in_ring
                    
                    if neighbor_nr == clockwise_neighbor:
                        # Clockwise arc
                        angle_diff = (2 * math.pi) / num_nodes_in_ring
                    elif neighbor_nr == counterclockwise_neighbor:
                        # Counterclockwise arc
                        angle_diff = -(2 * math.pi) / num_nodes_in_ring
                    else:
                        # Not adjacent - skip (shouldn't happen in RicoBit)
                        continue
                    
                    # Generate smooth arc points
                    num_segments = 15  # Smooth curve
                    points = []
                    
                    for i in range(num_segments + 1):
                        t = i / num_segments
                        angle = start_angle_rad + (angle_diff * t)
                        
                        x = center_x + radius * math.cos(angle)
                        y = center_y + radius * math.sin(angle)
                        
                        points.append((x, y))
                    
                    # Store the arc segment
                    key = (ring_num, node_nr, neighbor_nr)
                    self.ring_arc_segments[key] = {
                        'points': points,
                        'direction': 'clockwise' if neighbor_nr == clockwise_neighbor else 'counterclockwise',
                        'mid_angle': start_angle_rad + (angle_diff / 2),
                        'radius': radius,
                        'center': (center_x, center_y)
                    }
            
            print(f"    Created {len([k for k in self.ring_arc_segments.keys() if k[0] == ring_num])} arc segments")
        
        print(f"[ArcRenderer] Pre-computation complete: {len(self.ring_arc_segments)} total arc segments\n")
    
    def clear_arcs(self):
        """Clear all arc and arrow items"""
        for item in self.arc_items + self.arrow_items:
            try:
                self.canvas.delete(item)
            except:
                pass
        self.arc_items.clear()
        self.arrow_items.clear()
    
    def draw_routing_path(self, path, node_positions, transform_coords_func, zoom_level):
        """Draw the complete routing path with proper arcs and arrows
        
        This method draws EXACTLY what the routing table dictates:
        - For each hop from node A to node B:
          * If on SAME ring: draw arc segment from A to B
          * If on DIFFERENT rings: draw straight line from A to B
        
        Args:
            path: List of (ring, node) tuples representing the ACTUAL route from routing table
            node_positions: Dictionary mapping (ring, node) to (x, y) positions
            transform_coords_func: Function to transform coordinates
            zoom_level: Current zoom level
        """
        self.clear_arcs()
        
        if not path or len(path) < 2:
            return
        
        print(f"\n[ArcRenderer] Drawing path with {len(path)} nodes:")
        for i, node in enumerate(path):
            print(f"  Hop {i}: {node}")
        
        # Process EACH individual hop in the path (node-to-node)
        for i in range(len(path) - 1):
            current_node = path[i]
            next_node = path[i + 1]
            
            current_R, current_Nr = current_node
            next_R, next_Nr = next_node
            
            print(f"\n[ArcRenderer] Drawing hop {i}: {current_node} -> {next_node}")
            
            # Get positions
            if current_node not in node_positions or next_node not in node_positions:
                print(f"  WARNING: Node position not found!")
                continue
            
            x1, y1 = node_positions[current_node]
            x2, y2 = node_positions[next_node]
            
            cx1, cy1 = transform_coords_func(x1, y1)
            cx2, cy2 = transform_coords_func(x2, y2)
            
            # Determine if this is a ring hop or tree hop
            is_ring_hop = (current_R == next_R and current_R > 0)
            is_tree_hop = (current_R != next_R)
            
            if is_ring_hop:
                # Draw arc segment for THIS SPECIFIC ring hop (A->B on same ring)
                print(f"  -> Ring hop on ring {current_R}: node {current_Nr} to {next_Nr}")
                self._draw_ring_arc_segment(
                    current_node, next_node, 
                    transform_coords_func, zoom_level
                )
            elif is_tree_hop:
                # Draw straight arrow for tree hop (parent-child)
                print(f"  -> Tree hop: ring {current_R} to ring {next_R}")
                self._draw_tree_arrow(cx1, cy1, cx2, cy2)
    
    def _draw_ring_arc_segment(self, start_node, end_node, transform_coords_func, zoom_level):
        """Draw pre-computed arc segment on a ring with arrow in the middle
        
        Uses the pre-computed arc segment from the ring_arc_segments lookup table.
        This ensures we draw the EXACT arc that connects these two adjacent nodes.
        
        Args:
            start_node: (ring, node_nr) tuple for start
            end_node: (ring, node_nr) tuple for end (MUST be on same ring)
            transform_coords_func: Function to transform coordinates
            zoom_level: Current zoom level
        """
        start_R, start_Nr = start_node
        end_R, end_Nr = end_node
        
        # Must be same ring
        if start_R != end_R or start_R == 0:
            print(f"  ERROR: Not same ring or ring 0!")
            return
        
        ring_num = start_R
        
        # Look up the pre-computed arc segment
        key = (ring_num, start_Nr, end_Nr)
        
        if key not in self.ring_arc_segments:
            print(f"  ERROR: No pre-computed arc segment for {key}")
            print(f"  Available segments: {[k for k in self.ring_arc_segments.keys() if k[0] == ring_num]}")
            return
        
        arc_data = self.ring_arc_segments[key]
        points = arc_data['points']
        direction = arc_data['direction']
        mid_angle = arc_data['mid_angle']
        radius = arc_data['radius']
        center_x, center_y = arc_data['center']
        
        print(f"  Drawing {direction} arc on ring {ring_num}: {start_Nr} -> {end_Nr}")
        
        # Transform all points
        transformed_points = []
        for x, y in points:
            cx, cy = transform_coords_func(x, y)
            transformed_points.extend([cx, cy])
        
        # Draw the smooth arc as a polyline
        arc_id = self.canvas.create_line(
            *transformed_points,
            fill=self.colors['path'],
            width=5,
            smooth=True,
            tags='routing_arc'
        )
        self.arc_items.append(arc_id)
        
        # Draw arrow in the MIDDLE of the arc
        arrow_x = center_x + radius * math.cos(mid_angle)
        arrow_y = center_y + radius * math.sin(mid_angle)
        
        # Transform arrow position
        arrow_x, arrow_y = transform_coords_func(arrow_x, arrow_y)
        
        # Arrow direction tangent to the circle
        if direction == 'clockwise':
            tangent_dx = -math.sin(mid_angle)
            tangent_dy = math.cos(mid_angle)
        else:
            tangent_dx = math.sin(mid_angle)
            tangent_dy = -math.cos(mid_angle)
        
        # Draw arrow
        arrow_length = 20
        arrow_start_x = arrow_x - tangent_dx * arrow_length * 0.5
        arrow_start_y = arrow_y - tangent_dy * arrow_length * 0.5
        arrow_end_x = arrow_x + tangent_dx * arrow_length * 0.5
        arrow_end_y = arrow_y + tangent_dy * arrow_length * 0.5
        
        arrow_id = self.canvas.create_line(
            arrow_start_x, arrow_start_y,
            arrow_end_x, arrow_end_y,
            arrow=tk.LAST,
            fill=self.colors['path'],
            width=4,
            arrowshape=(10, 12, 4),
            tags='routing_arrow'
        )
        self.arrow_items.append(arrow_id)
        print(f"    Arc segment drawn successfully")
    
    def _draw_tree_arrow(self, x1, y1, x2, y2):
        """Draw straight arrow for tree connection (parent-child)
        
        Args:
            x1, y1: Start coordinates (transformed)
            x2, y2: End coordinates (transformed)
        """
        # Calculate midpoint for arrow
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2
        
        # Calculate direction vector
        dx = x2 - x1
        dy = y2 - y1
        length = math.sqrt(dx * dx + dy * dy)
        
        if length < 1:
            return
        
        # Normalize
        dx /= length
        dy /= length
        
        # Draw line with arrow in the middle
        # First half (no arrow)
        line1_id = self.canvas.create_line(
            x1, y1, mid_x, mid_y,
            fill=self.colors['path'],
            width=5,
            tags='routing_line'
        )
        self.arc_items.append(line1_id)
        
        # Second half with arrow at midpoint
        arrow_start_x = mid_x - dx * 15
        arrow_start_y = mid_y - dy * 15
        arrow_end_x = mid_x + dx * 15
        arrow_end_y = mid_y + dy * 15
        
        arrow_id = self.canvas.create_line(
            arrow_start_x, arrow_start_y,
            arrow_end_x, arrow_end_y,
            arrow=tk.LAST,
            fill=self.colors['path'],
            width=5,
            arrowshape=(12, 15, 5),
            tags='routing_arrow'
        )
        self.arrow_items.append(arrow_id)
        
        # Continue line to end
        line2_id = self.canvas.create_line(
            mid_x, mid_y, x2, y2,
            fill=self.colors['path'],
            width=5,
            tags='routing_line'
        )
        self.arc_items.append(line2_id)
