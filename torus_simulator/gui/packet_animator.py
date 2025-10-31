import tkinter as tk
import math

class PacketAnimator:
    """
    Handles packet animation effects for the torus visualizer.
    """
    
    def __init__(self, canvas):
        self.canvas = canvas
        self.animation_items = []
        
    def clear_animations(self):
        """Clear all animation items from canvas."""
        for item in self.animation_items[:]:
            try:
                if self.canvas.winfo_exists():
                    self.canvas.delete(item)
            except (tk.TclError, AttributeError):
                pass
        self.animation_items.clear()
    
    def draw_packet_at_node(self, x, y, phase='created'):
        """Draw a packet at a specific node position."""
        try:
            colors = {
                'created': '#4CAF50',    # Green
                'sending': '#2196F3',    # Blue
                'receiving': '#FF9800',  # Orange
                'delivered': '#9C27B0'   # Purple
            }
            
            color = colors.get(phase, '#666666')
            
            # Draw packet as small square
            size = 6
            packet_item = self.canvas.create_rectangle(
                x - size, y - size, x + size, y + size,
                fill=color, outline='white', width=2
            )
            self.animation_items.append(packet_item)
            
            # Add phase label
            label_item = self.canvas.create_text(
                x, y - 20, text=phase.upper(),
                fill=color, font=('Arial', 8, 'bold')
            )
            self.animation_items.append(label_item)
            
            return packet_item
        except (tk.TclError, AttributeError):
            return None
    
    def draw_transfer_arrow(self, x1, y1, x2, y2, phase='data', arc_points=None):
        """Draw an arrow showing packet transfer between nodes."""
        try:
            colors = {
                'req': '#FF5722',     # Red-orange
                'ack': '#4CAF50',     # Green
                'data': '#2196F3'     # Blue
            }
            
            color = colors.get(phase, '#666666')
            
            # Position arrows with sufficient distance for better observability
            offset = 0
            if phase == 'req':
                offset = -20  # REQ above with more distance
            elif phase == 'ack':
                offset = 20   # ACK below with more distance
            
            # Calculate perpendicular offset for proper above/below positioning
            dx = x2 - x1
            dy = y2 - y1
            length = (dx*dx + dy*dy)**0.5
            if length > 0:
                # For ACK, reverse the perpendicular direction to ensure opposite positioning
                if phase == 'ack':
                    perp_x = dy / length * abs(offset)  # Reverse direction for ACK
                    perp_y = -dx / length * abs(offset)
                else:
                    perp_x = -dy / length * offset
                    perp_y = dx / length * offset
                x1_offset = x1 + perp_x
                y1_offset = y1 + perp_y
                x2_offset = x2 + perp_x
                y2_offset = y2 + perp_y
            else:
                # Fallback for zero-length lines
                x1_offset, y1_offset = x1, y1 + offset
                x2_offset, y2_offset = x2, y2 + offset
            
            if arc_points and len(arc_points) > 1:
                # Draw curved path using arc points
                for i in range(len(arc_points) - 1):
                    line_item = self.canvas.create_line(
                        arc_points[i][0], arc_points[i][1],
                        arc_points[i+1][0], arc_points[i+1][1],
                        fill=color, width=2, arrow=tk.LAST if i == len(arc_points) - 2 else tk.NONE,
                        arrowshape=(8, 10, 3)
                    )
                    self.animation_items.append(line_item)
            else:
                # Draw straight arrow with offset
                arrow_item = self.canvas.create_line(
                    x1_offset, y1_offset, x2_offset, y2_offset,
                    fill=color, width=2, arrow=tk.LAST,
                    arrowshape=(8, 10, 3), tags=(phase,)
                )
                self.animation_items.append(arrow_item)
            
            # Add phase label at offset midpoint
            mid_x = (x1_offset + x2_offset) / 2
            mid_y = (y1_offset + y2_offset) / 2
            label_item = self.canvas.create_text(
                mid_x, mid_y - 8, text=phase.upper(),
                fill=color, font=('Arial', 7, 'bold'), tags=(phase,)
            )
            self.animation_items.append(label_item)
        except (tk.TclError, AttributeError):
            pass
    
    def draw_node_activity_ring(self, x, y, activity='processing'):
        """Draw activity ring around node."""
        try:
            colors = {
                'processing': '#FF9800',  # Orange
                'busy': '#F44336',        # Red
                'ready': '#4CAF50'        # Green
            }
            
            color = colors.get(activity, '#666666')
            
            # Draw pulsing ring
            ring_item = self.canvas.create_oval(
                x - 20, y - 20, x + 20, y + 20,
                outline=color, width=3, fill=''
            )
            self.animation_items.append(ring_item)
            
            return ring_item
        except (tk.TclError, AttributeError):
            return None
    
    def animate_packet_movement(self, x1, y1, x2, y2, duration=500):
        """Animate packet movement from one node to another."""
        # Create moving packet
        packet_size = 8
        packet_item = self.canvas.create_rectangle(
            x1 - packet_size, y1 - packet_size, 
            x1 + packet_size, y1 + packet_size,
            fill='#2196F3', outline='white', width=2
        )
        self.animation_items.append(packet_item)
        
        # Calculate movement parameters
        dx = x2 - x1
        dy = y2 - y1
        steps = 20
        step_x = dx / steps
        step_y = dy / steps
        delay = max(10, duration // steps)  # Minimum delay of 10ms
        
        def move_step(step):
            try:
                if step >= steps:
                    # Animation complete, remove packet
                    self.canvas.delete(packet_item)
                    if packet_item in self.animation_items:
                        self.animation_items.remove(packet_item)
                    return
                
                # Move packet
                current_x = x1 + step * step_x
                current_y = y1 + step * step_y
                
                self.canvas.coords(
                    packet_item,
                    current_x - packet_size, current_y - packet_size,
                    current_x + packet_size, current_y + packet_size
                )
                
                # Schedule next step
                self.canvas.after(delay, lambda: move_step(step + 1))
            except tk.TclError:
                # Canvas was destroyed, stop animation
                return
        
        # Start animation
        move_step(0)
        return packet_item