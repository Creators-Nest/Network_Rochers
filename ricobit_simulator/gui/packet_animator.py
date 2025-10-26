"""
Packet Animation Visualizer for RicoBit Simulator
Creates visual representations of packet transfer phases similar to NS3 animation
"""

import tkinter as tk
import math


class PacketAnimator:
    """Handles visual packet animation with phase indicators"""
    
    def __init__(self, canvas):
        self.canvas = canvas
        self.animation_items = []
        self.current_packet_item = None
        self.current_arrow_items = []
        
    def clear_animations(self):
        """Clear all animation items from canvas"""
        for item in self.animation_items:
            try:
                self.canvas.delete(item)
            except:
                pass
        self.animation_items.clear()
        
        for item in self.current_arrow_items:
            try:
                self.canvas.delete(item)
            except:
                pass
        self.current_arrow_items.clear()
        
        if self.current_packet_item:
            try:
                self.canvas.delete(self.current_packet_item)
            except:
                pass
            self.current_packet_item = None
    
    def draw_packet_at_node(self, x, y, phase="idle"):
        """Draw packet icon at specific node position with phase indicator
        
        Phases:
        - 'idle': Gray packet (waiting)
        - 'created': Blue packet (just created)
        - 'sending': Yellow packet with pulse (sending data)
        - 'receiving': Orange packet (receiving data)
        - 'delivered': Green packet (successfully delivered)
        """
        # Clear previous packet
        if self.current_packet_item:
            try:
                self.canvas.delete(self.current_packet_item)
            except:
                pass
        
        # Color based on phase
        colors = {
            'idle': '#808080',
            'created': '#3498db',
            'sending': '#f39c12',
            'receiving': '#e67e22',
            'delivered': '#27ae60'
        }
        color = colors.get(phase, '#808080')
        
        # Draw packet as a rectangle with rounded corners effect
        size = 18
        packet_id = self.canvas.create_rectangle(
            x - size, y - size,
            x + size, y + size,
            fill=color,
            outline='#2c3e50',
            width=3,
            tags='packet'
        )
        
        # Add phase indicator text
        phase_text = {
            'idle': '⏸',
            'created': '📦',
            'sending': '📤',
            'receiving': '📥',
            'delivered': '✓'
        }
        text = phase_text.get(phase, '📦')
        
        text_id = self.canvas.create_text(
            x, y,
            text=text,
            font=('Arial', 14, 'bold'),
            fill='white',
            tags='packet'
        )
        
        self.current_packet_item = packet_id
        self.animation_items.extend([packet_id, text_id])
        
        return packet_id
    
    def draw_transfer_arrow(self, x1, y1, x2, y2, phase="handshake"):
        """Draw animated arrow showing data transfer direction
        
        Phases:
        - 'handshake': Dotted line (REQ/ACK phase)
        - 'data': Solid arrow (data transfer)
        - 'complete': Green arrow (transfer complete)
        """
        # Clear previous arrows
        for item in self.current_arrow_items:
            try:
                self.canvas.delete(item)
            except:
                pass
        self.current_arrow_items.clear()
        
        # Calculate arrow parameters
        dx = x2 - x1
        dy = y2 - y1
        length = math.sqrt(dx*dx + dy*dy)
        
        if length < 1:
            return
        
        # Normalize direction
        dx /= length
        dy /= length
        
        # Arrow styling based on phase
        if phase == 'handshake':
            color = '#3498db'
            width = 2
            dash = (5, 5)
            arrow = None
        elif phase == 'data':
            color = '#f39c12'
            width = 4
            dash = None
            arrow = tk.LAST
        elif phase == 'complete':
            color = '#27ae60'
            width = 3
            dash = None
            arrow = tk.LAST
        else:
            color = '#95a5a6'
            width = 2
            dash = None
            arrow = None
        
        # Draw the arrow/line
        if dash:
            line_id = self.canvas.create_line(
                x1, y1, x2, y2,
                fill=color,
                width=width,
                dash=dash,
                tags='transfer_arrow'
            )
        else:
            line_id = self.canvas.create_line(
                x1, y1, x2, y2,
                fill=color,
                width=width,
                arrow=arrow,
                arrowshape=(16, 20, 6),
                tags='transfer_arrow'
            )
        
        self.current_arrow_items.append(line_id)
        self.animation_items.append(line_id)
        
        # Add phase label
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2
        
        phase_labels = {
            'handshake': 'REQ/ACK',
            'data': 'DATA',
            'complete': 'DONE'
        }
        label_text = phase_labels.get(phase, '')
        
        if label_text:
            # Create background for text
            bg_id = self.canvas.create_rectangle(
                mid_x - 30, mid_y - 12,
                mid_x + 30, mid_y + 12,
                fill='white',
                outline=color,
                width=2,
                tags='transfer_arrow'
            )
            
            text_id = self.canvas.create_text(
                mid_x, mid_y,
                text=label_text,
                font=('Arial', 9, 'bold'),
                fill=color,
                tags='transfer_arrow'
            )
            
            self.current_arrow_items.extend([bg_id, text_id])
            self.animation_items.extend([bg_id, text_id])
        
        return line_id
    
    def draw_node_activity_ring(self, x, y, activity="idle"):
        """Draw activity ring around node to show processing state
        
        Activities:
        - 'idle': No ring
        - 'processing': Blue pulsing ring
        - 'busy': Red ring
        - 'ready': Green ring
        """
        if activity == 'idle':
            return
        
        colors = {
            'processing': '#3498db',
            'busy': '#e74c3c',
            'ready': '#27ae60'
        }
        color = colors.get(activity, '#95a5a6')
        
        radius = 25
        ring_id = self.canvas.create_oval(
            x - radius, y - radius,
            x + radius, y + radius,
            outline=color,
            width=3,
            dash=(4, 4),
            tags='activity_ring'
        )
        
        self.animation_items.append(ring_id)
        return ring_id
    
    def animate_packet_transfer(self, src_pos, dest_pos, callback=None):
        """Animate packet moving from source to destination
        
        Args:
            src_pos: (x, y) tuple for source position
            dest_pos: (x, y) tuple for destination position
            callback: Function to call when animation completes
        """
        x1, y1 = src_pos
        x2, y2 = dest_pos
        
        # Create moving packet
        packet_size = 12
        packet_id = self.canvas.create_oval(
            x1 - packet_size, y1 - packet_size,
            x1 + packet_size, y1 + packet_size,
            fill='#f39c12',
            outline='#2c3e50',
            width=2,
            tags='moving_packet'
        )
        
        self.animation_items.append(packet_id)
        
        # Animation parameters
        steps = 20
        step = 0
        
        def move_step():
            nonlocal step
            if step >= steps:
                self.canvas.delete(packet_id)
                if callback:
                    callback()
                return
            
            # Calculate current position
            t = step / steps
            current_x = x1 + (x2 - x1) * t
            current_y = y1 + (y2 - y1) * t
            
            # Move packet
            self.canvas.coords(
                packet_id,
                current_x - packet_size, current_y - packet_size,
                current_x + packet_size, current_y + packet_size
            )
            
            step += 1
            self.canvas.after(30, move_step)
        
        move_step()
