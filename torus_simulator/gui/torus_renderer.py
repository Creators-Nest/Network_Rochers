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
    
    def draw_routing_path(self, path, node_positions, transform_coords, zoom_level):
        """Draw highlighted routing path for torus."""
        if not path or len(path) < 2:
            return
        
        # Draw path segments
        for i in range(len(path) - 1):
            start_addr = path[i]
            end_addr = path[i + 1]
            
            if start_addr in node_positions and end_addr in node_positions:
                x1, y1 = node_positions[start_addr]
                x2, y2 = node_positions[end_addr]
                
                cx1, cy1 = transform_coords(x1, y1)
                cx2, cy2 = transform_coords(x2, y2)
                
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