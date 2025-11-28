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
        """Clear all animation items from canvas including packet text"""
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
        
        # Also clear any items tagged as 'packet' or 'moving_packet'
        try:
            self.canvas.delete('packet')
            self.canvas.delete('moving_packet')
        except:
            pass
    
    def draw_packet_at_node(self, x, y, phase="idle"):
        """Draw packet icon at specific node position with phase indicator
        
        Phases:
        - 'idle': Gray packet (waiting)
        - 'created': Blue packet (just created)
        - 'sending': Yellow packet (sending request)
        - 'receiving': Orange packet (receiving acknowledgment)
        - 'delivered': Green packet (successfully delivered)
        - 'transferring': Blue packet (data being transferred)
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
            'delivered': '#27ae60',
            'transferring': '#0066ff'  # Blue for data transfer
        }
        color = colors.get(phase, '#808080')
        
        # Draw packet as a HEXAGON shape (6-sided) - half the size of node
        size = 8  # Half of node size (node is ~15-16 pixels)
        import math
        points = []
        for i in range(6):
            angle = math.pi / 3 * i - math.pi / 2  # Start from top
            px = x + size * math.cos(angle)
            py = y + size * math.sin(angle)
            points.extend([px, py])
        
        packet_id = self.canvas.create_polygon(
            points,
            fill=color,
            outline='#2c3e50',
            width=3,
            tags='packet'
        )
        
        # Add phase indicator text (simple letter, no emojis)
        phase_text = {
            'idle': '·',
            'created': 'P',
            'sending': 'R',
            'receiving': 'A',
            'delivered': '✓',
            'transferring': 'D'
        }
        text = phase_text.get(phase, 'P')
        
        text_id = self.canvas.create_text(
            x, y,
            text=text,
            font=('Arial', 10, 'bold'),
            fill='white',
            tags='packet'
        )
        
        self.current_packet_item = packet_id
        self.animation_items.extend([packet_id, text_id])
        
        return packet_id
    
    def draw_transfer_arrow(self, x1, y1, x2, y2, phase="handshake", arc_points=None, callback=None):
        """Draw signal indicator with single moving pointer for condition checking
        
        Phases:
        - 'check': Single blue pointer moves to check conditions (REQ)
        - 'ack': Same pointer returns green (ACK - conditions OK)
        - 'data': Blue packet transfers after ACK
        
        Args:
            x1, y1: Start coordinates
            x2, y2: End coordinates
            phase: Transfer phase
            arc_points: Optional list of (x,y) tuples for curved path
            callback: Function to call when animation completes
        """
        # Clear previous animations
        for item in self.current_arrow_items:
            try:
                self.canvas.delete(item)
            except:
                pass
        self.current_arrow_items.clear()
        
        # Use arc points if provided, otherwise straight line
        if arc_points and len(arc_points) > 2:
            path_points = arc_points
        else:
            path_points = [(x1, y1), (x2, y2)]
        
        # Single pointer for condition check (REQ)
        if phase == 'req' or phase == 'check':
            self._animate_signal_dot(path_points, color='#2196F3', label='REQ', reverse=False, callback=callback)
        # Same pointer returns as ACK
        elif phase == 'ack':
            self._animate_signal_dot(list(reversed(path_points)), color='#4CAF50', label='ACK', reverse=False, callback=callback)
        
        return None
    
    def _animate_signal_dot(self, path_points, color, label, reverse=False, callback=None):
        """Animate a small dot moving along the path for REQ/ACK signals
        
        Args:
            path_points: List of (x, y) tuples defining the path
            color: Dot color
            label: Signal label (REQ or ACK)
            reverse: If True, move in reverse direction
            callback: Function to call when animation completes
        """
        # Faster animation for realistic NoC timing
        steps = 40  # More steps for smoother animation
        step_duration = 15  # 15ms per step = 600ms total (faster, smoother)
        dot_radius = 6  # Slightly larger dot for better visibility
        
        # Create the moving dot
        dot_id = None
        label_id = None
        step = [0]
        
        def animate_step():
            nonlocal dot_id, label_id
            
            if step[0] >= steps:
                # Animation complete, remove dot
                if dot_id:
                    try:
                        self.canvas.delete(dot_id)
                        self.canvas.delete(label_id)
                    except:
                        pass
                # Call callback when animation finishes
                if callback:
                    callback()
                return
            
            # Calculate position along path
            t = step[0] / (steps - 1) if steps > 1 else 1.0
            
            # Find position on path (straight line interpolation)
            if len(path_points) == 2:
                x1, y1 = path_points[0]
                x2, y2 = path_points[1]
                current_x = x1 + (x2 - x1) * t
                current_y = y1 + (y2 - y1) * t
            else:
                # For curved paths, interpolate along segments
                total_length = 0
                segment_lengths = []
                for i in range(len(path_points) - 1):
                    dx = path_points[i+1][0] - path_points[i][0]
                    dy = path_points[i+1][1] - path_points[i][1]
                    seg_len = math.sqrt(dx*dx + dy*dy)
                    segment_lengths.append(seg_len)
                    total_length += seg_len
                
                target_dist = t * total_length
                cumulative = 0
                current_x, current_y = path_points[0]
                
                for i, seg_len in enumerate(segment_lengths):
                    if cumulative + seg_len >= target_dist:
                        seg_t = (target_dist - cumulative) / seg_len if seg_len > 0 else 0
                        x1, y1 = path_points[i]
                        x2, y2 = path_points[i+1]
                        current_x = x1 + (x2 - x1) * seg_t
                        current_y = y1 + (y2 - y1) * seg_t
                        break
                    cumulative += seg_len
            
            # Delete previous dot
            if dot_id:
                try:
                    self.canvas.delete(dot_id)
                    self.canvas.delete(label_id)
                except:
                    pass
            
            # Draw new dot at current position
            dot_id = self.canvas.create_oval(
                current_x - dot_radius, current_y - dot_radius,
                current_x + dot_radius, current_y + dot_radius,
                fill=color,
                outline='white',
                width=2,
                tags='signal_dot'
            )
            
            # Add small label above dot
            label_id = self.canvas.create_text(
                current_x, current_y - dot_radius - 10,
                text=label,
                font=('Arial', 8, 'bold'),
                fill=color,
                tags='signal_dot'
            )
            
            self.current_arrow_items.extend([dot_id, label_id])
            
            step[0] += 1
            self.canvas.after(step_duration, animate_step)
        
        # Start animation
        animate_step()
    
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
    
    def animate_packet_transfer(self, src_pos, dest_pos, callback=None, color='#0066ff'):
        """Animate hexagonal packet moving from source to destination
        
        Args:
            src_pos: (x, y) tuple for source position
            dest_pos: (x, y) tuple for destination position
            callback: Function to call when animation completes
            color: Packet color (default blue for DATA phase)
        """
        x1, y1 = src_pos
        x2, y2 = dest_pos
        
        # Clear any existing packet at source node (including 'D' text)
        if self.current_packet_item:
            try:
                self.canvas.delete(self.current_packet_item)
                self.current_packet_item = None
            except:
                pass
        
        # Create moving hexagonal packet (half the size of node)
        import math
        packet_size = 8  # Half of node size (node is ~15 pixels)
        
        def create_hexagon(cx, cy):
            points = []
            for i in range(6):
                angle = math.pi / 3 * i - math.pi / 2
                px = cx + packet_size * math.cos(angle)
                py = cy + packet_size * math.sin(angle)
                points.extend([px, py])
            return points
        
        # Create initial packet
        packet_id = self.canvas.create_polygon(
            create_hexagon(x1, y1),
            fill=color,
            outline='#2c3e50',
            width=3,
            tags='moving_packet'
        )
        
        # Add 'D' text for Data
        text_id = self.canvas.create_text(
            x1, y1,
            text='D',
            font=('Arial', 10, 'bold'),
            fill='white',
            tags='moving_packet'
        )
        
        self.animation_items.extend([packet_id, text_id])
        
        # Animation parameters for smooth, realistic movement
        steps = 50  # More steps for ultra-smooth animation
        step = 0
        
        def move_step():
            nonlocal step
            if step >= steps:
                # Delete both packet and text
                try:
                    self.canvas.delete(packet_id)
                    self.canvas.delete(text_id)
                except:
                    pass
                # Remove from animation items list
                if packet_id in self.animation_items:
                    self.animation_items.remove(packet_id)
                if text_id in self.animation_items:
                    self.animation_items.remove(text_id)
                if callback:
                    callback()
                return
            
            # Calculate current position with smooth easing
            t = step / steps
            # Apply ease-in-out for smooth acceleration/deceleration
            t_eased = t * t * (3.0 - 2.0 * t)  # Smoothstep function
            current_x = x1 + (x2 - x1) * t_eased
            current_y = y1 + (y2 - y1) * t_eased
            
            # Update packet position (hexagon)
            self.canvas.coords(packet_id, *create_hexagon(current_x, current_y))
            # Update text position
            self.canvas.coords(text_id, current_x, current_y)
            
            step += 1
            self.canvas.after(12, move_step)  # 12ms = faster, smoother (total 600ms)
        
        move_step()
