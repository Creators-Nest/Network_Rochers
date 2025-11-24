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
        self.arrow_items = {}
        
    def clear_animations(self):
        """Clear all animation items from canvas"""
        for item in self.animation_items:
            try:
                self.canvas.delete(item)
            except:
                pass
        self.animation_items.clear()

        for items in self.arrow_items.values():
            for item in items:
                try:
                    self.canvas.delete(item)
                except:
                    pass
        self.arrow_items.clear()

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
    
    def draw_transfer_arrow(self, x1, y1, x2, y2, phase="handshake", arc_points=None, identifier=None):
        """Draw animated arrow showing data transfer direction with NS3-like moving animation
        
        Phases:
        - 'handshake': Dotted line (REQ/ACK phase)
        - 'req': REQ arrow (source to dest) - ANIMATED
        - 'ack': ACK arrow (dest to source) - ANIMATED
        - 'data': Solid arrow (data transfer) - ANIMATED
        - 'complete': Green arrow (transfer complete)
        
        Args:
            x1, y1: Start coordinates
            x2, y2: End coordinates
            phase: Transfer phase
            arc_points: Optional list of (x,y) tuples for curved path
        """
        items_for_identifier = []

        if identifier is None:
            for item in self.current_arrow_items:
                try:
                    self.canvas.delete(item)
                except:
                    pass
            self.current_arrow_items.clear()
            self.arrow_items.clear()
        else:
            existing_items = self.arrow_items.pop(identifier, [])
            for item in existing_items:
                try:
                    self.canvas.delete(item)
                except:
                    pass
        
        # Use arc points if provided, otherwise straight line
        if arc_points and len(arc_points) > 2:
            path_points = arc_points
        else:
            path_points = [(x1, y1), (x2, y2)]
        
        # Arrow styling based on phase
        if phase == 'handshake':
            color = '#3498db'
            width = 2
            dash = (5, 5)
            animate = False
        elif phase == 'req':
            # REQ: Blue arrow from source to destination
            color = '#2196F3'
            width = 3
            dash = None
            animate = True
        elif phase == 'ack':
            # ACK: Green arrow from destination to source (reverse direction)
            color = '#4CAF50'
            width = 3
            dash = None
            animate = True
            # Reverse the path for ACK
            path_points = list(reversed(path_points))
        elif phase == 'data':
            color = '#f39c12'
            width = 4
            dash = None
            animate = True
        elif phase == 'complete':
            color = '#27ae60'
            width = 3
            dash = None
            animate = False
        else:
            color = '#95a5a6'
            width = 2
            dash = None
            animate = False
        
        # Draw the path (static background)
        if len(path_points) == 2:
            # Straight line
            line_id = self.canvas.create_line(
                path_points[0][0], path_points[0][1],
                path_points[1][0], path_points[1][1],
                fill='#d0d0d0',  # Light gray background
                width=width,
                dash=dash if not animate else None,
                tags='transfer_arrow'
            )
            items_for_identifier.append(line_id)
            self.current_arrow_items.append(line_id)
            self.animation_items.append(line_id)
        else:
            # Curved path - flatten points for create_line
            flat_points = []
            for px, py in path_points:
                flat_points.extend([px, py])
            
            line_id = self.canvas.create_line(
                *flat_points,
                fill='#d0d0d0',  # Light gray background
                width=width,
                smooth=True,
                tags='transfer_arrow'
            )
            items_for_identifier.append(line_id)
            self.current_arrow_items.append(line_id)
            self.animation_items.append(line_id)
        
        # Phase labels - Position in the MIDDLE between nodes, away from path
        phase_labels = {
            'handshake': 'REQ/ACK',
            'req': 'REQ',
            'ack': 'ACK',
            'data': 'DATA',
            'complete': 'DONE'
        }
        label_text = phase_labels.get(phase, '')
        
        if label_text:
            # Calculate midpoint between start and end nodes (not on path curve)
            if len(path_points) >= 2:
                # Use straight line midpoint between first and last point
                start_x, start_y = path_points[0]
                end_x, end_y = path_points[-1]
                
                # Direct midpoint (not following the curve)
                mid_x = (start_x + end_x) / 2
                mid_y = (start_y + end_y) / 2
                
                # Calculate direction vector from start to end
                dx = end_x - start_x
                dy = end_y - start_y
                length = math.sqrt(dx*dx + dy*dy)
                
                if length > 0:
                    # Normalize direction
                    dx /= length
                    dy /= length
                    
                    # Perpendicular vector (rotated 90 degrees counter-clockwise)
                    perp_x = -dy
                    perp_y = dx
                    
                    # Offset to position label to the side of the straight line between nodes
                    offset = 35
                    
                    # Position label away from the direct line between nodes
                    label_x = mid_x + perp_x * offset
                    label_y = mid_y + perp_y * offset
                else:
                    label_x = mid_x
                    label_y = mid_y
                
                # No arrow marks - just plain text
                display_text = label_text
                
                text_width = len(display_text) * 8 + 12
                
                # Create background for text
                bg_id = self.canvas.create_rectangle(
                    label_x - text_width//2, label_y - 11,
                    label_x + text_width//2, label_y + 11,
                    fill='white',
                    outline=color,
                    width=2,
                    tags='transfer_arrow'
                )
                
                text_id = self.canvas.create_text(
                    label_x, label_y,
                    text=display_text,
                    font=('Arial', 10, 'bold'),
                    fill=color,
                    tags='transfer_arrow'
                )
                
                items_for_identifier.extend([bg_id, text_id])
                self.current_arrow_items.extend([bg_id, text_id])
                self.animation_items.extend([bg_id, text_id])
        
        # Animate moving arrow if needed (NS3-style)
        if animate:
            self._animate_moving_arrow(path_points, color, width, tracked_items=items_for_identifier)

        if identifier is not None:
            self.arrow_items[identifier] = items_for_identifier
        
        return line_id
    
    def _animate_moving_arrow(self, path_points, color, width, duration=800, tracked_items=None):
        """Animate a moving arrow along the path (NS3-style)
        
        Args:
            path_points: List of (x, y) tuples defining the path
            color: Arrow color
            width: Arrow width
            duration: Animation duration in milliseconds
        """
        # Number of animation steps
        steps = 25
        step_duration = duration // steps
        
        # Create the moving arrow
        arrow_id = None
        trail_id = None
        step = [0]  # Use list to allow modification in nested function
        
        def animate_step():
            nonlocal arrow_id, trail_id
            
            if step[0] >= steps:
                # Animation complete, remove arrow
                if arrow_id:
                    try:
                        self.canvas.delete(arrow_id)
                    except:
                        pass
                if trail_id:
                    try:
                        self.canvas.delete(trail_id)
                    except:
                        pass
                return
            
            # Calculate position along path
            t = step[0] / (steps - 1)
            
            # Find position on path
            if len(path_points) == 2:
                # Straight line interpolation
                x1, y1 = path_points[0]
                x2, y2 = path_points[1]
                current_x = x1 + (x2 - x1) * t
                current_y = y1 + (y2 - y1) * t
                
                # Next point for arrow direction
                if t < 1.0:
                    next_t = min(1.0, t + 0.05)
                    next_x = x1 + (x2 - x1) * next_t
                    next_y = y1 + (y2 - y1) * next_t
                else:
                    next_x, next_y = x2, y2
                    
                # Previous point for trail
                if t > 0:
                    prev_t = max(0.0, t - 0.15)
                    prev_x = x1 + (x2 - x1) * prev_t
                    prev_y = y1 + (y2 - y1) * prev_t
                else:
                    prev_x, prev_y = x1, y1
            else:
                # Curved path interpolation
                total_length = 0
                segment_lengths = []
                for i in range(len(path_points) - 1):
                    dx = path_points[i+1][0] - path_points[i][0]
                    dy = path_points[i+1][1] - path_points[i][1]
                    seg_len = math.sqrt(dx*dx + dy*dy)
                    segment_lengths.append(seg_len)
                    total_length += seg_len
                
                # Find segment at current t
                target_dist = t * total_length
                cumulative = 0
                current_x, current_y = path_points[0]
                next_x, next_y = path_points[1] if len(path_points) > 1 else path_points[0]
                prev_x, prev_y = path_points[0]
                
                for i, seg_len in enumerate(segment_lengths):
                    if cumulative + seg_len >= target_dist:
                        # Interpolate within this segment
                        seg_t = (target_dist - cumulative) / seg_len if seg_len > 0 else 0
                        x1, y1 = path_points[i]
                        x2, y2 = path_points[i+1]
                        current_x = x1 + (x2 - x1) * seg_t
                        current_y = y1 + (y2 - y1) * seg_t
                        
                        # Next point
                        if i + 1 < len(path_points) - 1:
                            next_x, next_y = path_points[i+2]
                        else:
                            next_x, next_y = x2, y2
                        
                        # Previous point for trail
                        if i > 0:
                            prev_x, prev_y = path_points[i-1]
                        else:
                            prev_x, prev_y = x1, y1
                        break
                    cumulative += seg_len
            
            # Delete previous arrow and trail
            if arrow_id:
                try:
                    self.canvas.delete(arrow_id)
                except:
                    pass
            if trail_id:
                try:
                    self.canvas.delete(trail_id)
                except:
                    pass
            
            # Draw trail line (fade effect)
            if step[0] > 2:
                trail_id = self.canvas.create_line(
                    prev_x, prev_y,
                    current_x, current_y,
                    fill=color,
                    width=width + 2,
                    tags='moving_arrow_trail'
                )
                self.current_arrow_items.append(trail_id)
                if tracked_items is not None:
                    tracked_items.append(trail_id)
            
            # Draw new arrow at current position
            arrow_length = 30
            dx = next_x - current_x
            dy = next_y - current_y
            length = math.sqrt(dx*dx + dy*dy)
            
            if length > 0:
                dx /= length
                dy /= length
                
                arrow_start_x = current_x - dx * arrow_length * 0.2
                arrow_start_y = current_y - dy * arrow_length * 0.2
                arrow_end_x = current_x + dx * arrow_length * 0.8
                arrow_end_y = current_y + dy * arrow_length * 0.8
                
                arrow_id = self.canvas.create_line(
                    arrow_start_x, arrow_start_y,
                    arrow_end_x, arrow_end_y,
                    arrow=tk.LAST,
                    fill=color,
                    width=width + 1,
                    arrowshape=(14, 18, 6),
                    tags='moving_arrow'
                )
                
                self.current_arrow_items.append(arrow_id)
                if tracked_items is not None:
                    tracked_items.append(arrow_id)
            
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
