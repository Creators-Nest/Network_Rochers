import tkinter as tk
from tkinter import ttk, messagebox
import math
import time

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
        self.speed = 1000  # milliseconds per step
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
        
        # Packet tracking
        self.current_packets = []
        self.delivered_packets = []
        self.packet_positions = {}  # packet -> current node
        self.packet_animations = {}  # packet -> animation state
        self.routing_path = []  # For animation
        
        # Color scheme - Light/White theme
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
        """Creates the enhanced UI layout matching the reference image."""
        
        # Title Bar
        title_frame = tk.Frame(self.root, bg=self.colors['bg_dark'], height=50)
        title_frame.pack(side=tk.TOP, fill=tk.X)
        title_frame.pack_propagate(False)
        
        tk.Label(title_frame, text="Enhanced RiCoBiT Simulator", 
                font=("Arial", 20, "bold"), bg=self.colors['bg_dark'], fg=self.colors['text']
               ).pack(side=tk.LEFT, padx=20, pady=10)
        
        # Main content area
        content_frame = tk.Frame(self.root, bg=self.colors['bg_dark'])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel - Control Panel
        self._create_enhanced_control_panel(content_frame)
        
        # Right panel - Visualization
        self._create_enhanced_visualization_panel(content_frame)
        
    def _create_enhanced_control_panel(self, parent):
        """Creates the enhanced left control panel with all features."""
        control_frame = tk.Frame(parent, bg=self.colors['panel_bg'], width=350)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        control_frame.pack_propagate(False)
        
        # Scrollable container
        canvas = tk.Canvas(control_frame, bg=self.colors['panel_bg'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(control_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.colors['panel_bg'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # === TOPOLOGY CONFIGURATION ===
        self._create_section(scrollable_frame, "Topology Configuration")
        
        topo_frame = tk.Frame(scrollable_frame, bg=self.colors['panel_bg'])
        topo_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(topo_frame, text="Number of Rings:", 
                font=("Arial", 10), bg=self.colors['panel_bg'], fg=self.colors['text']
               ).pack(anchor=tk.W, pady=(5, 0))
        
        rings_control = tk.Frame(topo_frame, bg=self.colors['panel_bg'])
        rings_control.pack(fill=tk.X, pady=5)
        
        self.rings_var = tk.IntVar(value=self.num_levels)
        self.rings_label = tk.Label(rings_control, text=str(self.num_levels), 
                                    font=("Arial", 12, "bold"), 
                                    bg=self.colors['bg_light'], fg=self.colors['text'],
                                    width=3, relief=tk.SUNKEN)
        self.rings_label.pack(side=tk.LEFT, padx=(0, 5))
        
        self.rings_slider = tk.Scale(rings_control, from_=2, to=5, 
                                     orient=tk.HORIZONTAL,
                                     variable=self.rings_var,
                                     bg=self.colors['bg_medium'], fg=self.colors['text'],
                                     highlightthickness=0, troughcolor=self.colors['bg_light'],
                                     command=self.on_rings_change)
        self.rings_slider.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.create_topo_btn = tk.Button(topo_frame, text="Create Topology",
                                         command=self.recreate_topology,
                                         bg=self.colors['button'], fg=self.colors['text'],
                                         font=("Arial", 10, "bold"), relief=tk.RAISED,
                                         cursor="hand2")
        self.create_topo_btn.pack(fill=tk.X, pady=5)
        
        self.topo_info_label = tk.Label(topo_frame, 
                                        text=f"Current: {len(self.topology.nodes)} nodes",
                                        font=("Arial", 9), bg=self.colors['panel_bg'], 
                                        fg=self.colors['accent'])
        self.topo_info_label.pack(anchor=tk.W)
        
        # === PACKET ROUTING ===
        self._create_section(scrollable_frame, "Packet Routing")
        
        routing_frame = tk.Frame(scrollable_frame, bg=self.colors['panel_bg'])
        routing_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Source Node
        src_frame = tk.Frame(routing_frame, bg=self.colors['panel_bg'])
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
        self.src_ring_spin = tk.Spinbox(src_controls, from_=0, to=self.num_levels-1,
                                       width=3, textvariable=self.src_ring_var,
                                       bg=self.colors['bg_light'], fg=self.colors['text'])
        self.src_ring_spin.pack(side=tk.LEFT, padx=2)
        
        tk.Label(src_controls, text="Node:", 
                font=("Arial", 9), bg=self.colors['panel_bg'], fg=self.colors['text']
               ).pack(side=tk.LEFT, padx=(5, 2))
        
        self.src_node_var = tk.IntVar(value=0)
        self.src_node_spin = tk.Spinbox(src_controls, from_=0, to=7,
                                       width=3, textvariable=self.src_node_var,
                                       bg=self.colors['bg_light'], fg=self.colors['text'])
        self.src_node_spin.pack(side=tk.LEFT, padx=2)
        
        # Destination Node
        dst_frame = tk.Frame(routing_frame, bg=self.colors['panel_bg'])
        dst_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(dst_frame, text="Destination Node:", 
                font=("Arial", 10), bg=self.colors['panel_bg'], fg=self.colors['text']
               ).pack(side=tk.LEFT)
        
        dst_controls = tk.Frame(dst_frame, bg=self.colors['panel_bg'])
        dst_controls.pack(side=tk.RIGHT)
        
        tk.Label(dst_controls, text="Ring:", 
                font=("Arial", 9), bg=self.colors['panel_bg'], fg=self.colors['text']
               ).pack(side=tk.LEFT, padx=(0, 2))
        
        self.dst_ring_var = tk.IntVar(value=3)
        self.dst_ring_spin = tk.Spinbox(dst_controls, from_=0, to=self.num_levels-1,
                                       width=3, textvariable=self.dst_ring_var,
                                       bg=self.colors['bg_light'], fg=self.colors['text'])
        self.dst_ring_spin.pack(side=tk.LEFT, padx=2)
        
        tk.Label(dst_controls, text="Node:", 
                font=("Arial", 9), bg=self.colors['panel_bg'], fg=self.colors['text']
               ).pack(side=tk.LEFT, padx=(5, 2))
        
        self.dst_node_var = tk.IntVar(value=5)
        self.dst_node_spin = tk.Spinbox(dst_controls, from_=0, to=7,
                                       width=3, textvariable=self.dst_node_var,
                                       bg=self.colors['bg_light'], fg=self.colors['text'])
        self.dst_node_spin.pack(side=tk.LEFT, padx=2)
        
        # Routing Buttons
        btn_frame = tk.Frame(routing_frame, bg=self.colors['panel_bg'])
        btn_frame.pack(fill=tk.X, pady=5)
        
        tk.Button(btn_frame, text="Simulate Routing",
                 command=self.simulate_routing,
                 bg=self.colors['button'], fg=self.colors['text'],
                 font=("Arial", 9, "bold"), relief=tk.RAISED,
                 cursor="hand2").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))
        
        tk.Button(btn_frame, text="▶ Animate",
                 command=self.animate_routing,
                 bg=self.colors['button'], fg=self.colors['text'],
                 font=("Arial", 9, "bold"), relief=tk.RAISED,
                 cursor="hand2").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        
        tk.Button(btn_frame, text="Clear",
                 command=self.clear_routing,
                 bg=self.colors['button'], fg=self.colors['text'],
                 font=("Arial", 9, "bold"), relief=tk.RAISED,
                 cursor="hand2").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 0))
        
        # === VIEW CONTROLS ===
        self._create_section(scrollable_frame, "View Controls")
        
        view_frame = tk.Frame(scrollable_frame, bg=self.colors['panel_bg'])
        view_frame.pack(fill=tk.X, padx=10, pady=5)
        
        view_btn_frame1 = tk.Frame(view_frame, bg=self.colors['panel_bg'])
        view_btn_frame1.pack(fill=tk.X, pady=2)
        
        tk.Button(view_btn_frame1, text="Reset View",
                 command=self.reset_view,
                 bg=self.colors['button'], fg=self.colors['text'],
                 font=("Arial", 9), relief=tk.RAISED,
                 cursor="hand2").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))
        
        tk.Button(view_btn_frame1, text="Clear Highlights",
                 command=self.clear_highlights,
                 bg=self.colors['button'], fg=self.colors['text'],
                 font=("Arial", 9), relief=tk.RAISED,
                 cursor="hand2").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 0))
        
        view_btn_frame2 = tk.Frame(view_frame, bg=self.colors['panel_bg'])
        view_btn_frame2.pack(fill=tk.X, pady=2)
        
        tk.Button(view_btn_frame2, text="Zoom In",
                 command=self.zoom_in,
                 bg=self.colors['button'], fg=self.colors['text'],
                 font=("Arial", 9), relief=tk.RAISED,
                 cursor="hand2").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))
        
        tk.Button(view_btn_frame2, text="Zoom Out",
                 command=self.zoom_out,
                 bg=self.colors['button'], fg=self.colors['text'],
                 font=("Arial", 9), relief=tk.RAISED,
                 cursor="hand2").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        
        self.grid_var = tk.BooleanVar(value=False)
        tk.Checkbutton(view_btn_frame2, text="Grid", variable=self.grid_var,
                      command=self.toggle_grid,
                      bg=self.colors['panel_bg'], fg=self.colors['text'],
                      selectcolor=self.colors['bg_light'],
                      activebackground=self.colors['panel_bg'],
                      font=("Arial", 9)).pack(side=tk.LEFT, padx=(2, 0))
        
        # === STATISTICS & HELP ===
        self._create_section(scrollable_frame, "Statistics & Help")
        
        stats_frame = tk.Frame(scrollable_frame, bg=self.colors['panel_bg'])
        stats_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Help text
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
        
        self.help_text_widget = tk.Text(stats_frame, height=15, width=35,
                                        bg=self.colors['bg_dark'], fg=self.colors['text'],
                                        font=("Courier", 9), wrap=tk.WORD,
                                        relief=tk.SUNKEN, bd=2)
        self.help_text_widget.pack(fill=tk.BOTH, expand=True)
        self.help_text_widget.insert("1.0", help_text)
        self.help_text_widget.config(state=tk.DISABLED)
        
        # Statistics display
        self.stats_label = tk.Label(stats_frame, text="", 
                                    bg=self.colors['panel_bg'], fg=self.colors['accent'],
                                    font=("Courier", 9), justify=tk.LEFT)
        self.stats_label.pack(fill=tk.X, pady=(5, 0))
        self._update_statistics()
        
    def _create_section(self, parent, title):
        """Creates a section header."""
        frame = tk.Frame(parent, bg=self.colors['bg_medium'], height=30)
        frame.pack(fill=tk.X, padx=5, pady=(10, 5))
        frame.pack_propagate(False)
        
        tk.Label(frame, text=title, 
                font=("Arial", 11, "bold"), bg=self.colors['bg_medium'], fg=self.colors['text']
               ).pack(side=tk.LEFT, padx=10, pady=5)
        
    def _create_enhanced_visualization_panel(self, parent):
        """Creates the enhanced right visualization panel."""
        viz_frame = tk.Frame(parent, bg=self.colors['bg_dark'])
        viz_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Title
        title_frame = tk.Frame(viz_frame, bg=self.colors['bg_medium'], height=40)
        title_frame.pack(side=tk.TOP, fill=tk.X)
        title_frame.pack_propagate(False)
        
        tk.Label(title_frame, text="Enhanced RiCoBiT Topology Visualization", 
                font=("Arial", 14, "bold"), bg=self.colors['bg_medium'], fg=self.colors['text']
               ).pack(pady=10)
        
        # Status bar (retained from original)
        status_frame = tk.Frame(viz_frame, bg="#e0e0e0", height=40)
        status_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 5))
        status_frame.pack_propagate(False)
        
        self.status_label = tk.Label(status_frame, 
                                     text="Ready - Click on nodes to see details | Use mouse wheel to zoom",
                                     font=("Arial", 10), bg="#e0e0e0", fg="black",
                                     anchor=tk.W)
        self.status_label.pack(side=tk.LEFT, padx=10, pady=5, fill=tk.X, expand=True)
        
        # Canvas for topology visualization
        canvas_frame = tk.Frame(viz_frame, bg=self.colors['canvas_bg'], relief=tk.SUNKEN, bd=2)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(canvas_frame, bg=self.colors['canvas_bg'], 
                               highlightthickness=0, cursor="crosshair")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Bind mouse events
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)
        self.canvas.bind("<Button-4>", self.on_mouse_wheel)  # Linux scroll up
        self.canvas.bind("<Button-5>", self.on_mouse_wheel)  # Linux scroll down
        self.canvas.bind("<ButtonPress-2>", self.on_pan_start)  # Middle mouse
        self.canvas.bind("<B2-Motion>", self.on_pan_move)
        
        # Keyboard shortcuts
        self.root.bind("<Control-plus>", lambda e: self.zoom_in())
        self.root.bind("<Control-minus>", lambda e: self.zoom_out())
        self.root.bind("<Control-0>", lambda e: self.reset_view())
        self.root.bind("<Escape>", lambda e: self.clear_highlights())
        
    def _old_create_control_panel(self, parent):
        """Creates the left control panel."""
        control_frame = tk.Frame(parent, bg="#2a2a2a", width=400)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        control_frame.pack_propagate(False)
        
        # Control Panel Title
        title_label = tk.Label(control_frame, text="Control Panel", 
                              font=("Arial", 16, "bold"), bg="#e0e0e0", fg="black",
                              height=2)
        title_label.pack(fill=tk.X, padx=10, pady=10)
        
        # Number of Nodes Section
        nodes_frame = tk.Frame(control_frame, bg="#2a2a2a")
        nodes_frame.pack(fill=tk.X, padx=10, pady=10)
        
        node_info_frame = tk.Frame(nodes_frame, bg="#3a3a3a", relief=tk.RIDGE, bd=2)
        node_info_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(node_info_frame, text="Number Of Nodes", 
                font=("Arial", 12), bg="#3a3a3a", fg="white"
               ).pack(side=tk.LEFT, padx=15, pady=10)
        
        total_nodes = len(self.topology.nodes)
        self.node_count_label = tk.Label(node_info_frame, 
                                         text=f"{total_nodes}", 
                                         font=("Arial", 12, "bold"), 
                                         bg="#2e2e3e", fg="white",
                                         width=4)
        self.node_count_label.pack(side=tk.RIGHT, padx=15, pady=10)
        
        # Simulation Area Section
        sim_frame = tk.Frame(control_frame, bg="#2a2a2a")
        sim_frame.pack(fill=tk.X, padx=10, pady=10)
        
        sim_header = tk.Frame(sim_frame, bg="#3a3a3a", relief=tk.RIDGE, bd=2)
        sim_header.pack(fill=tk.X, pady=5)
        
        tk.Label(sim_header, text="Simulation Area", 
                font=("Arial", 12), bg="#3a3a3a", fg="white"
               ).pack(side=tk.LEFT, padx=15, pady=10)
        
        # Control Buttons
        button_frame = tk.Frame(sim_header, bg="#3a3a3a")
        button_frame.pack(side=tk.RIGHT, padx=10)
        
        # Play button (triangle)
        self.play_btn = tk.Button(button_frame, text="▶", 
                                  font=("Arial", 16), bg="#4a4a4a", fg="white",
                                  width=3, command=self.start_simulation)
        self.play_btn.pack(side=tk.LEFT, padx=2)
        
        # Pause button (two bars)
        self.pause_btn = tk.Button(button_frame, text="❚❚", 
                                   font=("Arial", 16), bg="#4a4a4a", fg="white",
                                   width=3, command=self.pause_simulation)
        self.pause_btn.pack(side=tk.LEFT, padx=2)
        
        # More options button (three dots)
        self.more_btn = tk.Button(button_frame, text="⋮", 
                                  font=("Arial", 16), bg="#4a4a4a", fg="white",
                                  width=3, command=self.show_more_options)
        self.more_btn.pack(side=tk.LEFT, padx=2)
        
        # Add Step Control
        step_control_frame = tk.Frame(sim_frame, bg="#3a3a3a", relief=tk.RIDGE, bd=2)
        step_control_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(step_control_frame, text="• Add Step Control", 
                font=("Arial", 11), bg="#3a3a3a", fg="white"
               ).pack(side=tk.LEFT, padx=15, pady=10)
        
        self.step_var = tk.BooleanVar()
        step_toggle = tk.Checkbutton(step_control_frame, 
                                    variable=self.step_var,
                                    bg="#3a3a3a", activebackground="#3a3a3a",
                                    command=self.toggle_step_mode)
        step_toggle.pack(side=tk.RIGHT, padx=15)
        
        # Speed Control
        speed_frame = tk.Frame(sim_frame, bg="#3a3a3a", relief=tk.RIDGE, bd=2)
        speed_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(speed_frame, text="• Speed", 
                font=("Arial", 11), bg="#3a3a3a", fg="white"
               ).pack(side=tk.LEFT, padx=15, pady=10)
        
        self.speed_label = tk.Label(speed_frame, text="1x", 
                                    font=("Arial", 11, "bold"), 
                                    bg="#2e2e3e", fg="white",
                                    width=5)
        self.speed_label.pack(side=tk.RIGHT, padx=15, pady=5)
        
        # Packet Generation Section
        packet_frame = tk.Frame(control_frame, bg="#2a2a2a")
        packet_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Button(packet_frame, text="Generate Packet", 
                 font=("Arial", 11, "bold"), bg="#5a5a5a", fg="white",
                 command=self.generate_packet, height=2
                ).pack(fill=tk.X, pady=5)
        
        tk.Button(packet_frame, text="Generate Random Traffic", 
                 font=("Arial", 11, "bold"), bg="#5a5a5a", fg="white",
                 command=self.generate_random_traffic, height=2
                ).pack(fill=tk.X, pady=5)
        
        # Statistics Section
        stats_frame = tk.Frame(control_frame, bg="#3a3a3a", relief=tk.RIDGE, bd=2)
        stats_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(stats_frame, text="Statistics", 
                font=("Arial", 12, "bold"), bg="#3a3a3a", fg="white"
               ).pack(pady=5)
        
        self.stats_text = tk.Text(stats_frame, height=8, bg="#2a2a2a", fg="white",
                                 font=("Courier", 9))
        self.stats_text.pack(fill=tk.BOTH, padx=5, pady=5)
        self._update_statistics()
        
    def _create_visualization_panel(self, parent):
        """Creates the right visualization panel."""
        viz_frame = tk.Frame(parent, bg="#1a1a1a")
        viz_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Status bar
        status_frame = tk.Frame(viz_frame, bg="#e0e0e0", height=50)
        status_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 10))
        status_frame.pack_propagate(False)
        
        tk.Label(status_frame, 
                text="Status update bar of each step while packet is getting transferred.",
                font=("Arial", 11), bg="#e0e0e0", fg="black"
               ).pack(side=tk.LEFT, padx=10, pady=10)
        
        # Status text (dynamic)
        self.status_label = tk.Label(status_frame, text="", 
                                    font=("Arial", 10, "bold"), 
                                    bg="#e0e0e0", fg="black")
        self.status_label.pack(side=tk.LEFT, padx=10)
        
        # Canvas for topology visualization
        canvas_frame = tk.Frame(viz_frame, bg="white", relief=tk.SUNKEN, bd=2)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(canvas_frame, bg="white", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
    def _calculate_node_positions(self):
        """Calculates (x, y) positions for all nodes in circular rings."""
        self.node_positions = {}
        
        # Get canvas dimensions
        self.canvas.update_idletasks()
        canvas_width = self.canvas.winfo_width() or 1000
        canvas_height = self.canvas.winfo_height() or 700
        
        self.center_x = canvas_width / 2
        self.center_y = canvas_height / 2
        
        max_radius = min(canvas_width, canvas_height) / 2 - 100
        
        for R in range(self.num_levels):
            num_nodes = 2**R
            # Distribute rings evenly
            radius = ((R + 1) / self.num_levels) * max_radius
            
            for Nr in range(num_nodes):
                # Start from top and go clockwise
                angle = 2 * math.pi * Nr / num_nodes - math.pi / 2
                x = self.center_x + radius * math.cos(angle)
                y = self.center_y + radius * math.sin(angle)
                
                self.node_positions[(R, Nr)] = (x, y)
    
    def _draw_topology(self):
        """Draws the enhanced RicoBit topology on the canvas."""
        self.canvas.delete("all")
        
        # Draw grid if enabled
        if self.show_grid:
            self._draw_grid()
        
        # Draw concentric ring circles
        for R in range(self.num_levels):
            num_nodes = 2**R
            radius = ((R + 1) / self.num_levels) * (min(self.canvas.winfo_width() or 1000, 
                                                        self.canvas.winfo_height() or 700) / 2 - 100)
            radius *= self.zoom_level
            
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
                
                # Check if this connection is in highlighted path
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
            
            # Determine node color
            if addr == self.selected_node:
                color = self.colors['node_highlight']
            elif addr in self.highlighted_path:
                color = self.colors['path']
            else:
                color = self.colors['node']
            
            # Node circle
            radius = 12 * self.zoom_level
            circle = self.canvas.create_oval(x - radius, y - radius,
                                            x + radius, y + radius,
                                            fill=color, outline="white",
                                            width=2, tags=("node", f"node_{R}_{Nr}"))
            self.node_circles[addr] = circle
            
            # Node label
            label_offset = 25 * self.zoom_level
            label = self.canvas.create_text(x, y + label_offset, 
                                           text=f"({R},{Nr})",
                                           font=("Arial", int(9 * self.zoom_level)), 
                                           fill="white", tags=("label", f"label_{R}_{Nr}"))
            self.node_labels[addr] = label
        
        # Draw packets
        self._draw_packets()
        
    def _transform_coords(self, x, y):
        """Applies zoom and pan transformations to coordinates."""
        x = (x - self.center_x) * self.zoom_level + self.center_x + self.canvas_offset_x
        y = (y - self.center_y) * self.zoom_level + self.center_y + self.canvas_offset_y
        return x, y
    
    def _draw_grid(self):
        """Draws a grid on the canvas."""
        width = self.canvas.winfo_width() or 1000
        height = self.canvas.winfo_height() or 700
        spacing = 50
        
        # Vertical lines
        for x in range(0, width, spacing):
            self.canvas.create_line(x, 0, x, height, fill="#333333", tags="grid")
        
        # Horizontal lines
        for y in range(0, height, spacing):
            self.canvas.create_line(0, y, width, y, fill="#333333", tags="grid")
    
    def _update_status(self, message):
        """Updates the status bar with current packet transfer information."""
        self.status_label.config(text=message)
        self.root.update()
    
    def _update_statistics(self):
        """Updates the statistics display."""
        self.stats_text.delete("1.0", tk.END)
        
        stats = f"""Clock Cycle: {self.simulator.global_clock}
Active Packets: {len(self.current_packets)}
Delivered Packets: {len(self.delivered_packets)}
Total Nodes: {len(self.topology.nodes)}
Topology Levels: {self.num_levels}
"""
        
        if self.delivered_packets:
            avg_latency = sum(p.end_timer - p.start_timer 
                            for p in self.delivered_packets) / len(self.delivered_packets)
            stats += f"Avg Latency: {avg_latency:.1f} cycles\n"
        
        self.stats_text.insert("1.0", stats)
    
    def generate_packet(self):
        """Generates a single longest-neighbor packet."""
        packets = self.packet_generator.generate_longest_neighbor_traffic(
            num_packets=1, 
            clock=self.simulator.global_clock
        )
        
        for packet in packets:
            self.simulator.inject_packet(packet)
            self.current_packets.append(packet)
            self.packet_positions[packet] = packet.source_address
            
        self._update_status(f"Packet {packet.data} injected: {packet.source_address} → {packet.dest_address}")
        self._update_statistics()
        self._draw_packets()
    
    def generate_random_traffic(self):
        """Generates multiple random packets."""
        packets = self.packet_generator.generate_uniform_random_traffic(
            num_packets=3, 
            clock=self.simulator.global_clock
        )
        
        for packet in packets:
            self.simulator.inject_packet(packet)
            self.current_packets.append(packet)
            self.packet_positions[packet] = packet.source_address
            
        self._update_status(f"Generated {len(packets)} random packets")
        self._update_statistics()
        self._draw_packets()
    
    def _draw_packets(self):
        """Draws packets on the topology."""
        self.canvas.delete("packet")
        
        for packet, node_addr in self.packet_positions.items():
            if node_addr in self.node_positions:
                x, y = self.node_positions[node_addr]
                
                # Draw packet as small red circle
                self.canvas.create_oval(x - 5, y - 5, x + 5, y + 5,
                                       fill="red", outline="red", tags="packet")
    
    def _get_packet_location_status(self, packet):
        """Gets detailed status of where a packet is in the network."""
        if packet not in self.packet_positions:
            return f"Packet {packet.data}: Location unknown"
        
        current_node_addr = self.packet_positions[packet]
        current_node = self.topology.nodes[current_node_addr]
        
        # Check if in send buffer
        for neighbor_addr, iface in current_node.interfaces.items():
            if not iface.send_buffer.is_empty():
                for p in iface.send_buffer.buffer:
                    if p == packet:
                        return f"Packet {packet.data}: Queued at node {current_node_addr} → {neighbor_addr}"
            
            if iface.send_register == packet:
                return f"Packet {packet.data}: Transferring from {current_node_addr} → {neighbor_addr}"
            
            if not iface.receive_buffer.is_empty():
                for p in iface.receive_buffer.buffer:
                    if p == packet:
                        return f"Packet {packet.data}: Received at {current_node_addr}, routing..."
        
        return f"Packet {packet.data}: At node {current_node_addr}"
    
    def simulation_step(self):
        """Executes one simulation step and updates visualization."""
        if not self.is_running or self.is_paused:
            return
        
        # Track packets before step
        status_messages = []
        
        for packet in self.current_packets[:]:
            if packet in self.packet_positions:
                status_messages.append(self._get_packet_location_status(packet))
        
        # Execute simulation step
        self.simulator.run_simulation_step()
        
        # Update packet positions
        self._update_packet_positions()
        
        # Check for delivered packets
        for node in self.topology.nodes.values():
            for packet in node.application_logic_buffer:
                if packet in self.current_packets:
                    self.current_packets.remove(packet)
                    if packet not in self.delivered_packets:
                        self.delivered_packets.append(packet)
                        latency = packet.end_timer - packet.start_timer
                        status_messages.append(
                            f"✓ Packet {packet.data} DELIVERED at {node.address} | Latency: {latency} cycles"
                        )
        
        # Update UI
        if status_messages:
            self._update_status(" | ".join(status_messages))
        else:
            self._update_status(f"Clock: {self.simulator.global_clock} - Simulation running...")
        
        self._update_statistics()
        self._draw_packets()
        
        # Schedule next step
        if not self.step_mode:
            self.root.after(self.speed, self.simulation_step)
        else:
            self.is_paused = True
    
    def _update_packet_positions(self):
        """Updates packet positions based on current network state."""
        # Clear old positions
        old_positions = dict(self.packet_positions)
        
        for packet in self.current_packets[:]:
            found = False
            
            # Search all nodes for this packet
            for node_addr, node in self.topology.nodes.items():
                # Check all interfaces
                for neighbor_addr, iface in node.interfaces.items():
                    # Check send buffer
                    if not iface.send_buffer.is_empty():
                        if packet in iface.send_buffer.buffer:
                            self.packet_positions[packet] = node_addr
                            found = True
                            break
                    
                    # Check send register
                    if iface.send_register == packet:
                        self.packet_positions[packet] = node_addr
                        found = True
                        break
                    
                    # Check receive buffer
                    if not iface.receive_buffer.is_empty():
                        if packet in iface.receive_buffer.buffer:
                            self.packet_positions[packet] = node_addr
                            found = True
                            break
                
                if found:
                    break
    
    def start_simulation(self):
        """Starts the simulation."""
        if not self.is_running:
            self.is_running = True
            self.is_paused = False
            self._update_status("Simulation started...")
            self.simulation_step()
        elif self.is_paused:
            self.is_paused = False
            self._update_status("Simulation resumed...")
            if not self.step_mode:
                self.simulation_step()
    
    def pause_simulation(self):
        """Pauses the simulation."""
        self.is_paused = True
        self._update_status("Simulation paused")
    
    def toggle_step_mode(self):
        """Toggles step-by-step mode."""
        self.step_mode = self.step_var.get()
        if self.step_mode:
            self._update_status("Step mode enabled - Click Play for each step")
        else:
            self._update_status("Continuous mode enabled")
    
    def show_more_options(self):
        """Shows additional options menu."""
        options_window = tk.Toplevel(self.root)
        options_window.title("Simulation Options")
        options_window.geometry("300x200")
        options_window.configure(bg="#2a2a2a")
        
        tk.Label(options_window, text="Speed Control", 
                font=("Arial", 12, "bold"), bg="#2a2a2a", fg="white"
               ).pack(pady=10)
        
        speeds = [("0.5x (Slow)", 2000), ("1x (Normal)", 1000), 
                 ("2x (Fast)", 500), ("5x (Very Fast)", 200)]
        
        for label, speed_ms in speeds:
            tk.Button(options_window, text=label, 
                     command=lambda s=speed_ms, l=label.split()[0]: self.set_speed(s, l),
                     bg="#4a4a4a", fg="white", width=20
                    ).pack(pady=5)
    
    def set_speed(self, speed_ms, label):
        """Sets simulation speed."""
        self.speed = speed_ms
        self.speed_label.config(text=label)
        self._update_status(f"Speed set to {label}")
    
    def run(self):
        """Starts the Tkinter main loop."""
        self.root.mainloop()
