import tkinter as tk
from tkinter import ttk, messagebox
import math
import time
from ..core.packet import Packet

class RicoBitVisualizer:
    """
    Enhanced Tkinter-based GUI for visualizing RicoBit topology and packet transfers.
    Matches the enhanced reference image design exactly.
    """
    
    def __init__(self, topology, simulator, packet_generator):
        self.topology = topology
        self.simulator = simulator
        self.packet_generator = packet_generator
        
        # GUI State
        self.is_running = False
        self.is_paused = False
        self.step_mode = False
        self.speed = 1000
        self.num_levels = topology.num_levels
        
        # Enhanced features
        self.zoom_level = 1.0
        self.canvas_offset_x = 0
        self.canvas_offset_y = 0
        self.show_grid = False
        self.highlighted_path = []
        self.selected_node = None
        self.animating = False
        self.animation_step = 0
        self.pan_start_x = 0
        self.pan_start_y = 0
        
        # Packet tracking
        self.current_packets = []
        self.delivered_packets = []
        self.packet_positions = {}
        self.routing_path = []
        
        # Color scheme - Dark theme with light elements
        self.colors = {
            'bg_dark': '#2b2b2b',
            'bg_medium': '#3a3a3a',
            'bg_light': '#4a4a4a',
            'panel_bg': '#2e2e2e',
            'text': '#ffffff',
            'accent': '#5a9fd4',
            'node': '#5a9fd4',
            'node_highlight': '#ff6b6b',
            'path': '#4ecdc4',
            'packet': '#ff4444',
            'connection': '#555555',
            'canvas_bg': '#1e1e1e',
            'button': '#404040',
            'button_hover': '#505050'
        }
        
        # Create main window
        self.root = tk.Tk()
        self.root.title("Enhanced RiCoBiT Simulator")
        self.root.geometry("1600x900")
        self.root.configure(bg=self.colors['bg_dark'])
        
        self._create_ui()
        self._calculate_node_positions()
        self._draw_topology()
        
    def _create_ui(self):
        """Creates the enhanced UI layout."""
        # Title Bar
        title_frame = tk.Frame(self.root, bg=self.colors['bg_dark'], height=50)
        title_frame.pack(side=tk.TOP, fill=tk.X)
        title_frame.pack_propagate(False)
        
        tk.Label(title_frame, text="Enhanced RiCoBiT Simulator", 
                font=("Arial", 20, "bold"), bg=self.colors['bg_dark'], fg=self.colors['text']
               ).pack(side=tk.LEFT, padx=20, pady=10)
        
        # Main content
        content_frame = tk.Frame(self.root, bg=self.colors['bg_dark'])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self._create_control_panel(content_frame)
        self._create_visualization_panel(content_frame)
        
    def _create_control_panel(self, parent):
        """Creates the enhanced left control panel."""
        control_frame = tk.Frame(parent, bg=self.colors['panel_bg'], width=350)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        control_frame.pack_propagate(False)
        
        # Scrollable container
        canvas = tk.Canvas(control_frame, bg=self.colors['panel_bg'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(control_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.colors['panel_bg'])
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # TOPOLOGY CONFIGURATION
        self._create_section(scrollable_frame, "Topology Configuration")
        topo_frame = self._create_topology_config(scrollable_frame)
        
        # PACKET ROUTING
        self._create_section(scrollable_frame, "Packet Routing")
        routing_frame = self._create_routing_config(scrollable_frame)
        
        # VIEW CONTROLS
        self._create_section(scrollable_frame, "View Controls")
        view_frame = self._create_view_controls(scrollable_frame)
        
        # STATISTICS & HELP
        self._create_section(scrollable_frame, "Statistics & Help")
        stats_frame = self._create_stats_panel(scrollable_frame)
        
    def _create_topology_config(self, parent):
        """Creates topology configuration section."""
        frame = tk.Frame(parent, bg=self.colors['panel_bg'])
        frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(frame, text="Number of Rings:", 
                font=("Arial", 10), bg=self.colors['panel_bg'], fg=self.colors['text']
               ).pack(anchor=tk.W, pady=(5, 0))
        
        rings_control = tk.Frame(frame, bg=self.colors['panel_bg'])
        rings_control.pack(fill=tk.X, pady=5)
        
        self.rings_var = tk.IntVar(value=self.num_levels)
        self.rings_label = tk.Label(rings_control, text=str(self.num_levels), 
                                    font=("Arial", 12, "bold"), 
                                    bg=self.colors['bg_light'], fg=self.colors['text'],
                                    width=3, relief=tk.SUNKEN)
        self.rings_label.pack(side=tk.LEFT, padx=(0, 5))
        
        self.rings_slider = tk.Scale(rings_control, from_=2, to=5, 
                                     orient=tk.HORIZONTAL, variable=self.rings_var,
                                     bg=self.colors['bg_medium'], fg=self.colors['text'],
                                     highlightthickness=0, troughcolor=self.colors['bg_light'],
                                     command=self.on_rings_change)
        self.rings_slider.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        tk.Button(frame, text="Create Topology", command=self.recreate_topology,
                 bg=self.colors['button'], fg=self.colors['text'],
                 font=("Arial", 10, "bold"), relief=tk.RAISED,
                 cursor="hand2").pack(fill=tk.X, pady=5)
        
        self.topo_info_label = tk.Label(frame, 
                                        text=f"Current: {len(self.topology.nodes)} nodes",
                                        font=("Arial", 9), bg=self.colors['panel_bg'], 
                                        fg=self.colors['accent'])
        self.topo_info_label.pack(anchor=tk.W)
        
        return frame
    
    def _create_routing_config(self, parent):
        """Creates packet routing configuration section."""
        frame = tk.Frame(parent, bg=self.colors['panel_bg'])
        frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Source Node
        src_frame = tk.Frame(frame, bg=self.colors['panel_bg'])
        src_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(src_frame, text="Source Node:", 
                font=("Arial", 10), bg=self.colors['panel_bg'], fg=self.colors['text']
               ).pack(side=tk.LEFT)
        
        src_controls = tk.Frame(src_frame, bg=self.colors['panel_bg'])
        src_controls.pack(side=tk.RIGHT)
        
        tk.Label(src_controls, text="Ring:", 
                font=("Arial", 9), bg=self.colors['panel_bg'], fg=self.colors['text']
               ).pack(side=tk.LEFT, padx=(0, 2))
        
        self.src_ring_var = tk.IntVar(value=1)
        tk.Spinbox(src_controls, from_=0, to=self.num_levels-1,
                  width=3, textvariable=self.src_ring_var,
                  bg=self.colors['bg_light'], fg=self.colors['text']).pack(side=tk.LEFT, padx=2)
        
        tk.Label(src_controls, text="Node:", 
                font=("Arial", 9), bg=self.colors['panel_bg'], fg=self.colors['text']
               ).pack(side=tk.LEFT, padx=(5, 2))
        
        self.src_node_var = tk.IntVar(value=0)
        tk.Spinbox(src_controls, from_=0, to=15,
                  width=3, textvariable=self.src_node_var,
                  bg=self.colors['bg_light'], fg=self.colors['text']).pack(side=tk.LEFT, padx=2)
        
        # Destination Node
        dst_frame = tk.Frame(frame, bg=self.colors['panel_bg'])
        dst_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(dst_frame, text="Destination Node:", 
                font=("Arial", 10), bg=self.colors['panel_bg'], fg=self.colors['text']
               ).pack(side=tk.LEFT)
        
        dst_controls = tk.Frame(dst_frame, bg=self.colors['panel_bg'])
        dst_controls.pack(side=tk.RIGHT)
        
        tk.Label(dst_controls, text="Ring:", 
                font=("Arial", 9), bg=self.colors['panel_bg'], fg=self.colors['text']
               ).pack(side=tk.LEFT, padx=(0, 2))
        
        self.dst_ring_var = tk.IntVar(value=2)
        tk.Spinbox(dst_controls, from_=0, to=self.num_levels-1,
                  width=3, textvariable=self.dst_ring_var,
                  bg=self.colors['bg_light'], fg=self.colors['text']).pack(side=tk.LEFT, padx=2)
        
        tk.Label(dst_controls, text="Node:", 
                font=("Arial", 9), bg=self.colors['panel_bg'], fg=self.colors['text']
               ).pack(side=tk.LEFT, padx=(5, 2))
        
        self.dst_node_var = tk.IntVar(value=3)
        tk.Spinbox(dst_controls, from_=0, to=15,
                  width=3, textvariable=self.dst_node_var,
                  bg=self.colors['bg_light'], fg=self.colors['text']).pack(side=tk.LEFT, padx=2)
        
        # Buttons
        btn_frame = tk.Frame(frame, bg=self.colors['panel_bg'])
        btn_frame.pack(fill=tk.X, pady=5)
        
        tk.Button(btn_frame, text="Simulate Routing", command=self.simulate_routing,
                 bg=self.colors['button'], fg=self.colors['text'],
                 font=("Arial", 9, "bold"), relief=tk.RAISED,
                 cursor="hand2").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))
        
        tk.Button(btn_frame, text="▶ Animate", command=self.animate_routing,
                 bg=self.colors['button'], fg=self.colors['text'],
                 font=("Arial", 9, "bold"), relief=tk.RAISED,
                 cursor="hand2").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        
        tk.Button(btn_frame, text="Clear", command=self.clear_routing,
                 bg=self.colors['button'], fg=self.colors['text'],
                 font=("Arial", 9, "bold"), relief=tk.RAISED,
                 cursor="hand2").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 0))
        
        return frame
    
    def _create_view_controls(self, parent):
        """Creates view control section."""
        frame = tk.Frame(parent, bg=self.colors['panel_bg'])
        frame.pack(fill=tk.X, padx=10, pady=5)
        
        btn_frame1 = tk.Frame(frame, bg=self.colors['panel_bg'])
        btn_frame1.pack(fill=tk.X, pady=2)
        
        tk.Button(btn_frame1, text="Reset View", command=self.reset_view,
                 bg=self.colors['button'], fg=self.colors['text'],
                 font=("Arial", 9), relief=tk.RAISED,
                 cursor="hand2").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))
        
        tk.Button(btn_frame1, text="Clear Highlights", command=self.clear_highlights,
                 bg=self.colors['button'], fg=self.colors['text'],
                 font=("Arial", 9), relief=tk.RAISED,
                 cursor="hand2").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 0))
        
        btn_frame2 = tk.Frame(frame, bg=self.colors['panel_bg'])
        btn_frame2.pack(fill=tk.X, pady=2)
        
        tk.Button(btn_frame2, text="Zoom In", command=self.zoom_in,
                 bg=self.colors['button'], fg=self.colors['text'],
                 font=("Arial", 9), relief=tk.RAISED,
                 cursor="hand2").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))
        
        tk.Button(btn_frame2, text="Zoom Out", command=self.zoom_out,
                 bg=self.colors['button'], fg=self.colors['text'],
                 font=("Arial", 9), relief=tk.RAISED,
                 cursor="hand2").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        
        self.grid_var = tk.BooleanVar(value=False)
        tk.Checkbutton(btn_frame2, text="Grid", variable=self.grid_var,
                      command=self.toggle_grid,
                      bg=self.colors['panel_bg'], fg=self.colors['text'],
                      selectcolor=self.colors['bg_light'],
                      activebackground=self.colors['panel_bg'],
                      font=("Arial", 9)).pack(side=tk.LEFT, padx=(2, 0))
        
        return frame
    
    def _create_stats_panel(self, parent):
        """Creates statistics and help panel."""
        frame = tk.Frame(parent, bg=self.colors['panel_bg'])
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        help_text = """Enhanced Controls:
🖱️ Click nodes to see details
🖱️ Mouse wheel to zoom
🖱️ Pinch/trackpad gestures (macOS)
🖱️ Drag to pan view
⌨️ Ctrl+Plus/Minus for zoom
⌨️ Ctrl+0 to reset view
⌨️ ESC to clear highlights
📊 View topology statistics
🔵 All ring connections fixed
🎯 Persistent path highlighting"""
        
        self.help_text_widget = tk.Text(frame, height=15, width=35,
                                        bg=self.colors['bg_dark'], fg=self.colors['text'],
                                        font=("Courier", 9), wrap=tk.WORD,
                                        relief=tk.SUNKEN, bd=2)
        self.help_text_widget.pack(fill=tk.BOTH, expand=True)
        self.help_text_widget.insert("1.0", help_text)
        self.help_text_widget.config(state=tk.DISABLED)
        
        self.stats_label = tk.Label(frame, text="", 
                                    bg=self.colors['panel_bg'], fg=self.colors['accent'],
                                    font=("Courier", 9), justify=tk.LEFT)
        self.stats_label.pack(fill=tk.X, pady=(5, 0))
        self._update_statistics()
        
        return frame
    
    def _create_section(self, parent, title):
        """Creates a section header."""
        frame = tk.Frame(parent, bg=self.colors['bg_medium'], height=30)
        frame.pack(fill=tk.X, padx=5, pady=(10, 5))
        frame.pack_propagate(False)
        
        tk.Label(frame, text=title, 
                font=("Arial", 11, "bold"), bg=self.colors['bg_medium'], fg=self.colors['text']
               ).pack(side=tk.LEFT, padx=10, pady=5)
    
    def _create_visualization_panel(self, parent):
        """Creates the enhanced visualization panel."""
        viz_frame = tk.Frame(parent, bg=self.colors['bg_dark'])
        viz_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Title
        title_frame = tk.Frame(viz_frame, bg=self.colors['bg_medium'], height=40)
        title_frame.pack(side=tk.TOP, fill=tk.X)
        title_frame.pack_propagate(False)
        
        tk.Label(title_frame, text="Enhanced RiCoBiT Topology Visualization", 
                font=("Arial", 14, "bold"), bg=self.colors['bg_medium'], fg=self.colors['text']
               ).pack(pady=10)
        
        # Status bar
        status_frame = tk.Frame(viz_frame, bg="#e0e0e0", height=40)
        status_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 5))
        status_frame.pack_propagate(False)
        
        self.status_label = tk.Label(status_frame, 
                                     text="Ready - Click on nodes to see details | Use mouse wheel to zoom",
                                     font=("Arial", 10), bg="#e0e0e0", fg="black",
                                     anchor=tk.W)
        self.status_label.pack(side=tk.LEFT, padx=10, pady=5, fill=tk.X, expand=True)
        
        # Canvas
        canvas_frame = tk.Frame(viz_frame, bg=self.colors['canvas_bg'], relief=tk.SUNKEN, bd=2)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(canvas_frame, bg=self.colors['canvas_bg'], 
                               highlightthickness=0, cursor="crosshair")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Bind events
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)
        self.canvas.bind("<Button-4>", self.on_mouse_wheel)
        self.canvas.bind("<Button-5>", self.on_mouse_wheel)
        
        self.root.bind("<Control-plus>", lambda e: self.zoom_in())
        self.root.bind("<Control-minus>", lambda e: self.zoom_out())
        self.root.bind("<Control-0>", lambda e: self.reset_view())
        self.root.bind("<Escape>", lambda e: self.clear_highlights())
    
    def _calculate_node_positions(self):
        """Calculates node positions in circular rings."""
        self.node_positions = {}
        self.canvas.update_idletasks()
        canvas_width = self.canvas.winfo_width() or 1000
        canvas_height = self.canvas.winfo_height() or 700
        
        self.center_x = canvas_width / 2
        self.center_y = canvas_height / 2
        max_radius = min(canvas_width, canvas_height) / 2 - 100
        
        for R in range(self.num_levels):
            num_nodes = 2**R
            radius = ((R + 1) / self.num_levels) * max_radius
            
            for Nr in range(num_nodes):
                angle = 2 * math.pi * Nr / num_nodes - math.pi / 2
                x = self.center_x + radius * math.cos(angle)
                y = self.center_y + radius * math.sin(angle)
                self.node_positions[(R, Nr)] = (x, y)
    
    def _draw_topology(self):
        """Draws the topology with all enhancements."""
        self.canvas.delete("all")
        
        if self.show_grid:
            self._draw_grid()
        
        # Draw ring circles
        for R in range(self.num_levels):
            radius = ((R + 1) / self.num_levels) * (min(
                self.canvas.winfo_width() or 1000,
                self.canvas.winfo_height() or 700) / 2 - 100) * self.zoom_level
            
            self.canvas.create_oval(
                self.center_x - radius + self.canvas_offset_x,
                self.center_y - radius + self.canvas_offset_y,
                self.center_x + radius + self.canvas_offset_x,
                self.center_y + radius + self.canvas_offset_y,
                outline=self.colors['connection'], width=1, dash=(5, 5), tags="ring"
            )
        
        # Draw connections
        for addr, node in self.topology.nodes.items():
            x1, y1 = self._transform_coords(*self.node_positions[addr])
            
            for neighbor_addr in node.interfaces.keys():
                x2, y2 = self._transform_coords(*self.node_positions[neighbor_addr])
                
                is_highlighted = False
                if self.highlighted_path:
                    for i in range(len(self.highlighted_path) - 1):
                        if ((addr == self.highlighted_path[i] and neighbor_addr == self.highlighted_path[i+1]) or
                            (addr == self.highlighted_path[i+1] and neighbor_addr == self.highlighted_path[i])):
                            is_highlighted = True
                            break
                
                color = self.colors['path'] if is_highlighted else self.colors['connection']
                width = 3 if is_highlighted else 1
                
                self.canvas.create_line(x1, y1, x2, y2, 
                                       fill=color, width=width, tags="connection")
        
        # Draw nodes
        self.node_circles = {}
        self.node_labels = {}
        
        for addr in self.topology.nodes.keys():
            x, y = self._transform_coords(*self.node_positions[addr])
            R, Nr = addr
            
            if addr == self.selected_node:
                color = self.colors['node_highlight']
            elif addr in self.highlighted_path:
                color = self.colors['path']
            else:
                color = self.colors['node']
            
            radius = 12 * self.zoom_level
            circle = self.canvas.create_oval(x - radius, y - radius,
                                            x + radius, y + radius,
                                            fill=color, outline="white",
                                            width=2, tags=("node", f"node_{R}_{Nr}"))
            self.node_circles[addr] = circle
            
            label_offset = 25 * self.zoom_level
            label = self.canvas.create_text(x, y + label_offset, 
                                           text=f"({R},{Nr})",
                                           font=("Arial", int(9 * self.zoom_level)), 
                                           fill="white", tags=("label", f"label_{R}_{Nr}"))
            self.node_labels[addr] = label
        
        self._draw_packets()
    
    def _transform_coords(self, x, y):
        """Applies zoom and pan."""
        x = (x - self.center_x) * self.zoom_level + self.center_x + self.canvas_offset_x
        y = (y - self.center_y) * self.zoom_level + self.center_y + self.canvas_offset_y
        return x, y
    
    def _draw_grid(self):
        """Draws grid."""
        width = self.canvas.winfo_width() or 1000
        height = self.canvas.winfo_height() or 700
        spacing = 50
        
        for x in range(0, width, spacing):
            self.canvas.create_line(x, 0, x, height, fill="#333333", tags="grid")
        for y in range(0, height, spacing):
            self.canvas.create_line(0, y, width, y, fill="#333333", tags="grid")
    
    def _draw_packets(self):
        """Draws packets."""
        self.canvas.delete("packet")
        for packet, node_addr in self.packet_positions.items():
            if node_addr in self.node_positions:
                x, y = self._transform_coords(*self.node_positions[node_addr])
                self.canvas.create_oval(x - 5, y - 5, x + 5, y + 5,
                                       fill=self.colors['packet'], outline="white", tags="packet")
    
    def _update_status(self, message):
        """Updates status bar."""
        self.status_label.config(text=message)
        self.root.update()
    
    def _update_statistics(self):
        """Updates statistics display."""
        stats = f"""Clock: {self.simulator.global_clock}
Nodes: {len(self.topology.nodes)}
Packets: {len(self.current_packets)}
Delivered: {len(self.delivered_packets)}"""
        
        self.stats_label.config(text=stats)
    
    # Interactive Methods
    def on_canvas_click(self, event):
        """Handles canvas clicks to select nodes."""
        x, y = event.x, event.y
        
        # Find clicked node
        for addr, pos in self.node_positions.items():
            tx, ty = self._transform_coords(*pos)
            dist = math.sqrt((x - tx)**2 + (y - ty)**2)
            
            if dist <= 12 * self.zoom_level:
                self.selected_node = addr
                self._show_node_details(addr)
                self._draw_topology()
                return
        
        self.selected_node = None
        self._draw_topology()
    
    def _show_node_details(self, addr):
        """Shows detailed information about a node."""
        node = self.topology.nodes[addr]
        R, Nr = addr
        
        details = f"""Node ({R},{Nr}) Details:
━━━━━━━━━━━━━━━━━━━
Address: Ring {R}, Node {Nr}
Neighbors: {len(node.interfaces)}
Routing Table Entries: {len(node.routing_table)}

Connections:
"""
        for neighbor_addr in node.interfaces.keys():
            details += f"  → ({neighbor_addr[0]},{neighbor_addr[1]})\n"
        
        details += f"\nPackets in Application Buffer: {len(node.application_logic_buffer)}"
        
        # Show in messagebox
        messagebox.showinfo(f"Node ({R},{Nr})", details)
        self._update_status(f"Selected Node ({R},{Nr}) - {len(node.interfaces)} connections")
    
    def on_mouse_wheel(self, event):
        """Handles mouse wheel zoom."""
        if event.delta > 0 or event.num == 4:
            self.zoom_in()
        elif event.delta < 0 or event.num == 5:
            self.zoom_out()
    
    def on_rings_change(self, value):
        """Updates ring count label."""
        self.rings_label.config(text=value)
    
    def zoom_in(self):
        """Zooms in."""
        self.zoom_level = min(self.zoom_level * 1.2, 3.0)
        self._draw_topology()
        self._update_status(f"Zoom: {int(self.zoom_level * 100)}%")
    
    def zoom_out(self):
        """Zooms out."""
        self.zoom_level = max(self.zoom_level / 1.2, 0.3)
        self._draw_topology()
        self._update_status(f"Zoom: {int(self.zoom_level * 100)}%")
    
    def reset_view(self):
        """Resets view."""
        self.zoom_level = 1.0
        self.canvas_offset_x = 0
        self.canvas_offset_y = 0
        self._draw_topology()
        self._update_status("View reset")
    
    def toggle_grid(self):
        """Toggles grid display."""
        self.show_grid = self.grid_var.get()
        self._draw_topology()
    
    def clear_highlights(self):
        """Clears all highlights."""
        self.highlighted_path = []
        self.selected_node = None
        self._draw_topology()
        self._update_status("Highlights cleared")
    
    def simulate_routing(self):
        """Simulates routing and highlights path."""
        src_addr = (self.src_ring_var.get(), self.src_node_var.get())
        dst_addr = (self.dst_ring_var.get(), self.dst_node_var.get())
        
        if src_addr not in self.topology.nodes or dst_addr not in self.topology.nodes:
            messagebox.showerror("Error", "Invalid source or destination node!")
            return
        
        # Compute path using BFS
        path = self._compute_path(src_addr, dst_addr)
        
        if path:
            self.highlighted_path = path
            self.routing_path = path
            self._draw_topology()
            self._update_status(f"Route: {' → '.join([f'({r},{n})' for r, n in path])} ({len(path)-1} hops)")
        else:
            messagebox.showwarning("No Path", "No route found!")
    
    def _compute_path(self, src, dst):
        """Computes shortest path using BFS."""
        from collections import deque
        
        queue = deque([(src, [src])])
        visited = {src}
        
        while queue:
            current, path = queue.popleft()
            
            if current == dst:
                return path
            
            node = self.topology.nodes[current]
            for neighbor in node.interfaces.keys():
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        
        return None
    
    def animate_routing(self):
        """Animates the routing path."""
        if not self.routing_path:
            messagebox.showinfo("Info", "Please simulate routing first!")
            return
        
        self.animating = True
        self.animation_step = 0
        self._animate_step()
    
    def _animate_step(self):
        """Performs one animation step."""
        if not self.animating or self.animation_step >= len(self.routing_path):
            self.animating = False
            return
        
        # Highlight up to current step
        self.highlighted_path = self.routing_path[:self.animation_step + 1]
        self._draw_topology()
        
        current_node = self.routing_path[self.animation_step]
        self._update_status(f"Animation: Step {self.animation_step + 1}/{len(self.routing_path)} - At node {current_node}")
        
        self.animation_step += 1
        self.root.after(500, self._animate_step)
    
    def clear_routing(self):
        """Clears routing."""
        self.highlighted_path = []
        self.routing_path = []
        self.animating = False
        self._draw_topology()
        self._update_status("Routing cleared")
    
    def recreate_topology(self):
        """Recreates topology with new ring count."""
        from topology.ricobit_topology import RiCoBiT_Topology
        from simulation.simulator import Simulator
        from simulation.packet_generator import PacketGenerator
        
        new_levels = self.rings_var.get()
        
        # Recreate topology
        self.topology = RiCoBiT_Topology(num_levels=new_levels)
        self.simulator = Simulator(self.topology)
        self.packet_generator = PacketGenerator(self.topology)
        self.num_levels = new_levels
        
        # Reset state
        self.current_packets = []
        self.delivered_packets = []
        self.packet_positions = {}
        self.highlighted_path = []
        self.selected_node = None
        
        # Update spinbox ranges
        max_nodes = 2**(new_levels - 1) - 1
        
        # Redraw
        self._calculate_node_positions()
        self._draw_topology()
        self.topo_info_label.config(text=f"Current: {len(self.topology.nodes)} nodes")
        self._update_statistics()
        self._update_status(f"Topology recreated with {new_levels} rings ({len(self.topology.nodes)} nodes)")
    
    def run(self):
        """Starts the Tkinter main loop."""
        self.root.mainloop()
