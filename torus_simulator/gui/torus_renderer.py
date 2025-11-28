import tkinter as tk
import math

class TorusRenderer:
    """
    Handles rendering of torus-specific visual elements like grid lines and paths.
    """
    
    def __init__(self, canvas, colors):
        self.canvas = canvas
        self.colors = colors
        self.grid_items = []
        self.path_items = []
    
    def clear_grid(self):
        """Clear grid lines from canvas."""
        for item in self.grid_items:
            try:
                self.canvas.delete(item)
            except:
                pass
        self.grid_items.clear()
    
    def clear_paths(self):
        """Clear path highlights from canvas."""
        for item in self.path_items:
            try:
                self.canvas.delete(item)
            except:
                pass
        self.path_items.clear()
    
    def draw_grid_lines(self, width, height, node_positions, transform_coords, zoom_level):
        """Draw grid lines to show torus structure."""
        if not node_positions:
            return
        
        # Get canvas dimensions
        canvas_width = self.canvas.winfo_width() or 800
        canvas_height = self.canvas.winfo_height() or 600
        
        # Calculate grid spacing
        if width > 1 and height > 1:
            # Find spacing between adjacent nodes
            pos_00 = node_positions.get((0, 0))
            pos_10 = node_positions.get((1, 0))
            pos_01 = node_positions.get((0, 1))
            
            if pos_00 and pos_10 and pos_01:
                x_spacing = abs(pos_10[0] - pos_00[0])
                y_spacing = abs(pos_01[1] - pos_00[1])
                
                # Draw vertical grid lines
                for x in range(width + 1):
                    if (0, 0) in node_positions:
                        start_x = node_positions[(0, 0)][0] + x * x_spacing - x_spacing/2
                        start_y = node_positions[(0, 0)][1] - y_spacing/2
                        end_y = start_y + (height) * y_spacing
                        
                        # Transform coordinates
                        cx1, cy1 = transform_coords(start_x, start_y)
                        cx2, cy2 = transform_coords(start_x, end_y)
                        
                        line_item = self.canvas.create_line(
                            cx1, cy1, cx2, cy2,
                            fill=self.colors['connection'], width=1, dash=(2, 2)
                        )
                        self.grid_items.append(line_item)
                
                # Draw horizontal grid lines
                for y in range(height + 1):
                    if (0, 0) in node_positions:
                        start_x = node_positions[(0, 0)][0] - x_spacing/2
                        start_y = node_positions[(0, 0)][1] + y * y_spacing - y_spacing/2
                        end_x = start_x + (width) * x_spacing
                        
                        # Transform coordinates
                        cx1, cy1 = transform_coords(start_x, start_y)
                        cx2, cy2 = transform_coords(end_x, start_y)
                        
                        line_item = self.canvas.create_line(
                            cx1, cy1, cx2, cy2,
                            fill=self.colors['connection'], width=1, dash=(2, 2)
                        )
                        self.grid_items.append(line_item)
                
                # Draw torus wraparound connections - offset above and below existing connections
                offset = 15  # Offset distance for wraparound lines
                
                # Horizontal wraparound (left-right edges) - above and below
                for y in range(height):
                    left_pos = node_positions.get((0, y))
                    right_pos = node_positions.get((width-1, y))
                    if left_pos and right_pos:
                        cx1, cy1 = transform_coords(left_pos[0], left_pos[1])
                        cx2, cy2 = transform_coords(right_pos[0], right_pos[1])
                        
                        # Upper wraparound line
                        line_item = self.canvas.create_line(
                            cx1, cy1 - offset, cx2, cy2 - offset,
                            fill='#FF6B6B', width=2, dash=(8, 4)
                        )
                        self.grid_items.append(line_item)
                        
                        # Lower wraparound line
                        line_item = self.canvas.create_line(
                            cx1, cy1 + offset, cx2, cy2 + offset,
                            fill='#FF6B6B', width=2, dash=(8, 4)
                        )
                        self.grid_items.append(line_item)
                
                # Vertical wraparound (top-bottom edges) - left and right
                for x in range(width):
                    top_pos = node_positions.get((x, 0))
                    bottom_pos = node_positions.get((x, height-1))
                    if top_pos and bottom_pos:
                        cx1, cy1 = transform_coords(top_pos[0], top_pos[1])
                        cx2, cy2 = transform_coords(bottom_pos[0], bottom_pos[1])
                        
                        # Left wraparound line
                        line_item = self.canvas.create_line(
                            cx1 - offset, cy1, cx2 - offset, cy2,
                            fill='#FF6B6B', width=2, dash=(8, 4)
                        )
                        self.grid_items.append(line_item)
                        
                        # Right wraparound line
                        line_item = self.canvas.create_line(
                            cx1 + offset, cy1, cx2 + offset, cy2,
                            fill='#FF6B6B', width=2, dash=(8, 4)
                        )
                        self.grid_items.append(line_item)
    
    def draw_routing_path(self, path, node_positions, transform_coords, zoom_level):
        """Draw highlighted routing path for torus."""
        if not path or len(path) < 2:
            return
        
        offset = 15  # Same offset as wraparound lines
        
        # Draw path segments
        for i in range(len(path) - 1):
            start_addr = path[i]
            end_addr = path[i + 1]
            
            if start_addr in node_positions and end_addr in node_positions:
                x1, y1 = node_positions[start_addr]
                x2, y2 = node_positions[end_addr]
                
                cx1, cy1 = transform_coords(x1, y1)
                cx2, cy2 = transform_coords(x2, y2)
                
                # Check if this is a wraparound connection
                sx, sy = start_addr
                ex, ey = end_addr
                is_horizontal_wrap = (abs(sx - ex) > 1) and (sy == ey)
                is_vertical_wrap = (abs(sy - ey) > 1) and (sx == ex)
                
                # Adjust coordinates for wraparound paths
                if is_horizontal_wrap:
                    # Use upper wraparound line for horizontal wrap
                    cy1 -= offset
                    cy2 -= offset
                elif is_vertical_wrap:
                    # Use left wraparound line for vertical wrap
                    cx1 -= offset
                    cx2 -= offset
                
                # Draw path segment
                path_item = self.canvas.create_line(
                    cx1, cy1, cx2, cy2,
                    fill=self.colors['path'], width=4,
                    arrow=tk.LAST, arrowshape=(10, 12, 5)
                )
                self.path_items.append(path_item)
                
                # Add hop number with background
                mid_x = (cx1 + cx2) / 2
                mid_y = (cy1 + cy2) / 2
                
                # Create background circle for hop number
                bg_radius = 12
                bg_circle = self.canvas.create_oval(
                    mid_x - bg_radius, mid_y - 15 - bg_radius,
                    mid_x + bg_radius, mid_y - 15 + bg_radius,
                    fill='white', outline=self.colors['path'], width=2
                )
                self.path_items.append(bg_circle)
                
                # Create hop number text
                hop_label = self.canvas.create_text(
                    mid_x, mid_y - 15, text=f"{i+1}",
                    fill=self.colors['path'], font=('Arial', 10, 'bold')
                )
                self.path_items.append(hop_label)