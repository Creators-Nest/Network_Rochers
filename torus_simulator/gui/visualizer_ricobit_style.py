"""
Torus Topology Visualizer - RicoBit Style Interface
Features matching RicoBit simulator:
- Detailed status bar with REQ/ACK signals
- Real packet transfer simulation with handshake protocol
- Step-by-step animation with clock timing
- Comprehensive flow analysis
"""

import tkinter as tk
from tkinter import messagebox, scrolledtext
from tkinter import ttk
import math
from gui.packet_animator import PacketAnimator
from gui.torus_renderer import TorusRenderer

class TorusVisualizer:
    def __init__(self, root, topology, simulator):
        self.root = root
        self.topology = topology
        self.simulator = simulator
        self.width = topology.width
        self.height = topology.height
        
        # WHITE THEME COLOR SCHEME (matching RicoBit)
        self.colors = {
            'bg': '#ffffff',
            'panel_bg': '#f5f5f5',
            'canvas_bg': '#f8f9fa',
            'text': '#000000',
            'text_light': '#666666',
            'accent': '#00ffff',
            'button': '#e0e0e0',
            'button_text': '#000000',
            'highlight': '#00ff00',
            'path': '#00ffff',
            'node': '#4a90e2',
            'node_border': '#2c3e50',
            'connection': '#b0b0b0',
            'status_bg': '#e8e8e8',
            'status_text': '#333333'
        }
        
        # Setup main window
        self.root.title("Torus Topology Visualizer")
        self.root.configure(bg=self.colors['bg'])
        
        # Window geometry
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = min(1600, int(screen_width * 0.9))
        window_height = min(1000, int(screen_height * 0.9))
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Animation control state
        self.is_paused = False
        
        # Node selection state
        self.selection_mode = False
        self.selected_source = None
        self.selected_dest = None
        self.click_count = 0
        
        # Buffer display state
        self.buffer_display_node = None
        self.buffer_display_items = []
        
        # Hover state
        self.hover_node = None
        self.hover_timer = None
        self.hover_overlay = None
        self.hover_overlay_items = []
        
        # Packet transfer state
        self.current_packet = None
        self.current_path = []
        self.current_hop = 0
        self.transfer_phase = "Waiting to Start"
        self.transfer_progress = 0
        self.signal_status = "Idle"
        
        # Animation speed control
        self.animation_speed = 1000
        
        # Create UI
        self._create_status_bar()
        self._create_ui()
        
        # Packet animator and torus renderer
        self.packet_animator = PacketAnimator(self.canvas)
        self.torus_renderer = TorusRenderer(self.canvas, self.colors)
        
        # Animation items tracking
        self.animation_items = []
        
        # Buffer state tracking for animation
        self.buffer_states = {}  # Track buffer states per node
        
        # Node positioning and visualization state
        self.node_positions = {}
        self.node_items = {}
        self.edge_items = {}
        self.highlighted_edges = set()
        self.highlighted_nodes = set()
        self.animation_running = False
        
        # View state
        self.zoom_level = 1.0
        self.pan_x = 0
        self.pan_y = 0
        
        # Drag state
        self.is_dragging = False
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.drag_start_pan_x = 0
        self.drag_start_pan_y = 0
        
        # Initial draw
        self.draw_topology()
        
        # Bind events
        self._bind_events()
    
    def _create_status_bar(self):
        """Create enhanced status bar with real-time packet flow information"""
        status_frame = tk.Frame(self.root, bg=self.colors['status_bg'], height=100, relief=tk.RAISED, bd=1)
        status_frame.pack(side=tk.TOP, fill=tk.X)
        status_frame.pack_propagate(False)
        
        # Left section - Hop indicator with animated dot
        hop_frame = tk.Frame(status_frame, bg='white', relief=tk.SUNKEN, bd=1)
        hop_frame.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.Y)
        
        hop_inner = tk.Frame(hop_frame, bg='white')
        hop_inner.pack(padx=10, pady=5)
        
        # Animated indicator dot
        self.hop_canvas = tk.Canvas(hop_inner, width=20, height=20, bg='white', highlightthickness=0)
        self.hop_canvas.pack(side=tk.LEFT, padx=5)
        self.hop_indicator = self.hop_canvas.create_oval(5, 5, 15, 15, fill='red', outline='')
        
        self.hop_label = tk.Label(hop_inner, text="Hop 0/0", font=("Arial", 14, "bold"), 
                                 bg='white', fg='#666666')
        self.hop_label.pack(side=tk.LEFT, padx=5)
        
        # Current/Next node display
        hop_nodes = tk.Frame(hop_frame, bg='white')
        hop_nodes.pack(padx=10, pady=2)
        self.hop_nodes_label = tk.Label(hop_nodes, text="", font=("Arial", 9), 
                                        bg='white', fg='#888888')
        self.hop_nodes_label.pack()
        
        # Middle section - Phase, Route, and Transfer Details
        middle_frame = tk.Frame(status_frame, bg='white', relief=tk.SUNKEN, bd=1)
        middle_frame.pack(side=tk.LEFT, padx=5, pady=10, fill=tk.BOTH, expand=True)
        
        middle_inner = tk.Frame(middle_frame, bg='white')
        middle_inner.pack(fill=tk.BOTH, expand=True, padx=15, pady=8)
        
        # Top row: Phase and Route
        top_row = tk.Frame(middle_inner, bg='white')
        top_row.pack(fill=tk.X)
        
        # Phase with icon
        phase_frame = tk.Frame(top_row, bg='white')
        phase_frame.pack(side=tk.LEFT, padx=15)
        
        tk.Label(phase_frame, text="Phase:", font=("Arial", 10, "bold"), bg='white', fg='#999999'
                ).pack(side=tk.LEFT, padx=5)
        self.phase_label = tk.Label(phase_frame, text="⚪ Waiting to Start", font=("Arial", 11), 
                                   bg='white', fg='#666666')
        self.phase_label.pack(side=tk.LEFT)
        
        # Separator
        tk.Label(top_row, text="|", font=("Arial", 14), bg='white', fg='#cccccc'
                ).pack(side=tk.LEFT, padx=8)
        
        # Route
        route_frame = tk.Frame(top_row, bg='white')
        route_frame.pack(side=tk.LEFT, padx=15, fill=tk.X, expand=True)
        
        tk.Label(route_frame, text="Route:", font=("Arial", 10, "bold"), bg='white', fg='#999999'
                ).pack(side=tk.LEFT, padx=5)
        self.route_label = tk.Label(route_frame, text="No route selected", font=("Arial", 10), 
                                   bg='white', fg='#666666')
        self.route_label.pack(side=tk.LEFT)
        
        # Bottom row: Transfer details
        bottom_row = tk.Frame(middle_inner, bg='white')
        bottom_row.pack(fill=tk.X, pady=(8, 0))
        
        self.transfer_details_label = tk.Label(bottom_row, 
                                               text="Ready for packet transfer", 
                                               font=("Courier", 10, "bold"), 
                                               bg='white', fg='#333333',
                                               anchor='w')
        self.transfer_details_label.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Right section - Progress, Signals, and Timer
        right_frame = tk.Frame(status_frame, bg='white', relief=tk.SUNKEN, bd=1)
        right_frame.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.Y)
        
        right_inner = tk.Frame(right_frame, bg='white')
        right_inner.pack(padx=15, pady=8)
        
        # Progress with bar
        progress_frame = tk.Frame(right_inner, bg='white')
        progress_frame.pack(side=tk.LEFT, padx=15)
        
        tk.Label(progress_frame, text="Progress:", font=("Arial", 10), bg='white', fg='#999999'
                ).pack(anchor=tk.W)
        
        prog_display = tk.Frame(progress_frame, bg='white')
        prog_display.pack()
        
        self.progress_label = tk.Label(prog_display, text="0%", font=("Arial", 12, "bold"), 
                                      bg='white', fg='#666666')
        self.progress_label.pack(side=tk.LEFT)
        
        # Progress bar
        self.progress_canvas = tk.Canvas(progress_frame, width=100, height=8, 
                                        bg='#e0e0e0', highlightthickness=0)
        self.progress_canvas.pack(pady=2)
        self.progress_bar = self.progress_canvas.create_rectangle(0, 0, 0, 8, fill='#4CAF50', outline='')
        
        # Separator
        tk.Label(right_inner, text="|", font=("Arial", 14), bg='white', fg='#cccccc'
                ).pack(side=tk.LEFT, padx=8)
        
        # Signals and Timer
        signals_frame = tk.Frame(right_inner, bg='white')
        signals_frame.pack(side=tk.LEFT, padx=15)
        
        tk.Label(signals_frame, text="Signals:", font=("Arial", 10), bg='white', fg='#999999'
                ).pack(anchor=tk.W)
        self.signals_label = tk.Label(signals_frame, text="Idle", font=("Arial", 10, "bold"), 
                                     bg='white', fg='#666666')
        self.signals_label.pack()
        
        tk.Label(signals_frame, text="Timer:", font=("Arial", 9), bg='white', fg='#999999'
                ).pack(anchor=tk.W, pady=(3, 0))
        self.timer_label = tk.Label(signals_frame, text="0", font=("Arial", 9), 
                                    bg='white', fg='#666666')
        self.timer_label.pack()
    
    def _update_status_bar(self, current_node=None, next_node=None, interface_state=None):
        """Update status bar with current packet transfer state"""
        # Update hop with current/next node info
        total_hops = len(self.current_path) - 1 if self.current_path else 0
        self.hop_label.config(text=f"Hop {self.current_hop}/{total_hops}")
        
        # Show current and next nodes
        if current_node and next_node:
            self.hop_nodes_label.config(text=f"{current_node} → {next_node}")
        elif current_node:
            self.hop_nodes_label.config(text=f"At: {current_node}")
        else:
            self.hop_nodes_label.config(text="")
        
        # Update phase with appropriate icon
        phase_icons = {
            'Waiting to Start': '⚪',
            'Packet Created': '📦',
            'Handshake': '🤝',
            'Transferring': '📤',
            'Receiving': '📥',
            'Routing': '🔄',
            'Delivering': '🎯',
            'Completed': '✅',
            'Route Computed': '📍',
            'REQ': '🔴',
            'ACK': '🟢',
            'Paused': '⏸️'
        }
        icon = phase_icons.get(self.transfer_phase, '⚪')
        self.phase_label.config(text=f"{icon} {self.transfer_phase}")
        
        # Update route
        if self.current_path:
            route_str = " → ".join([f"({x},{y})" for x, y in self.current_path])
            self.route_label.config(text=route_str if len(route_str) < 60 else route_str[:57] + "...")
        else:
            self.route_label.config(text="No route selected")
        
        # Update transfer details
        if interface_state:
            details = f"REQ:{interface_state.get('req', 0)} ACK:{interface_state.get('ack', 0)} "
            details += f"| Busy:{interface_state.get('busy', 0)} Transfer:{interface_state.get('transfer', 0)} "
            details += f"| SendBuf:{interface_state.get('send_buf', '0/0')} RecvBuf:{interface_state.get('recv_buf', '0/0')}"
            self.transfer_details_label.config(text=details)
        elif self.animation_running:
            self.transfer_details_label.config(text=f"Processing transfer at {current_node or 'unknown'}")
        else:
            self.transfer_details_label.config(text="Ready for packet transfer")
        
        # Update progress
        self.progress_label.config(text=f"{self.transfer_progress}%")
        progress_width = int(100 * (self.transfer_progress / 100))
        self.progress_canvas.coords(self.progress_bar, 0, 0, progress_width, 8)
        
        # Update signals
        self.signals_label.config(text=self.signal_status)
        
        # Update timer
        if self.current_packet:
            timer_val = self.current_packet.start_timer + self.current_hop
            self.timer_label.config(text=str(timer_val))
        else:
            self.timer_label.config(text="0")
        
        # Update hop indicator animation
        if self.animation_running:
            self.hop_canvas.itemconfig(self.hop_indicator, fill='#27ae60')  # Green when active
        else:
            self.hop_canvas.itemconfig(self.hop_indicator, fill='#e74c3c')  # Red when idle

    def _create_ui(self):
        """Create main UI layout matching RicoBit"""
        main_container = tk.Frame(self.root, bg=self.colors['bg'])
        main_container.pack(fill=tk.BOTH, expand=True, side=tk.TOP)
        
        # Create PanedWindow to allow resizable sidebar
        self.paned_window = tk.PanedWindow(main_container, orient=tk.HORIZONTAL, 
                                           sashwidth=6, sashrelief=tk.RAISED,
                                           bg=self.colors['bg'], bd=0)
        self.paned_window.pack(fill=tk.BOTH, expand=True)
        
        # Left panel - Controls
        self.control_panel = tk.Frame(self.paned_window, bg=self.colors['panel_bg'], width=280, relief=tk.RIDGE, bd=2)
        self.paned_window.add(self.control_panel, minsize=200, stretch="never")
        
        # Create scrollable control area
        canvas = tk.Canvas(self.control_panel, bg=self.colors['panel_bg'], highlightthickness=0)
        style = ttk.Style()
        style.theme_use('default')
        style.configure("Vertical.TScrollbar", 
                       background='#d0d0d0',
                       troughcolor='#f0f0f0',
                       bordercolor='#a0a0a0',
                       arrowcolor='#404040',
                       width=16)
        
        scrollbar = ttk.Scrollbar(self.control_panel, orient="vertical", command=canvas.yview, style="Vertical.TScrollbar")
        scrollable_frame = tk.Frame(canvas, bg=self.colors['panel_bg'])
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Enable mousewheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add control sections
        self._create_topology_controls(scrollable_frame)
        self._create_routing_controls(scrollable_frame)
        self._create_simulation_details(scrollable_frame)
        self._create_flow_analysis_panel(scrollable_frame)
        
        # Right panel - Canvas
        canvas_frame = tk.Frame(self.paned_window, bg=self.colors['bg'], relief=tk.SUNKEN, bd=2)
        self.paned_window.add(canvas_frame, minsize=400, stretch="always")
        
        self.canvas = tk.Canvas(canvas_frame, bg=self.colors['canvas_bg'], highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Create floating view controls
        self._create_floating_view_controls()
    
    def _create_section_header(self, parent, text):
        """Create section header"""
        header = tk.Label(parent, text=text, font=("Arial", 11, "bold"),
                         bg=self.colors['panel_bg'], fg='#000000')
        header.pack(anchor=tk.W, padx=10, pady=(15, 5))
    
    def _create_topology_controls(self, parent):
        """Create topology configuration controls"""
        self._create_section_header(parent, "TOPOLOGY CONFIGURATION")
        
        frame = tk.Frame(parent, bg=self.colors['panel_bg'])
        frame.pack(fill=tk.X, padx=15, pady=5)
        
        # Width control
        tk.Label(frame, text="Torus Width:", font=("Arial", 10),
                bg=self.colors['panel_bg'], fg=self.colors['text']
               ).pack(anchor=tk.W, pady=(0, 2))
        
        self.width_var = tk.IntVar(value=self.width)
        self.width_slider = tk.Scale(frame, from_=3, to=8, orient=tk.HORIZONTAL,
                                     variable=self.width_var,
                                     bg=self.colors['panel_bg'], fg=self.colors['text'],
                                     highlightthickness=0, troughcolor='white')
        self.width_slider.pack(fill=tk.X, pady=2)
        
        # Height control
        tk.Label(frame, text="Torus Height:", font=("Arial", 10),
                bg=self.colors['panel_bg'], fg=self.colors['text']
               ).pack(anchor=tk.W, pady=(5, 2))
        
        self.height_var = tk.IntVar(value=self.height)
        self.height_slider = tk.Scale(frame, from_=3, to=8, orient=tk.HORIZONTAL,
                                      variable=self.height_var,
                                      bg=self.colors['panel_bg'], fg=self.colors['text'],
                                      highlightthickness=0, troughcolor='white')
        self.height_slider.pack(fill=tk.X, pady=2)
        
        tk.Button(frame, text="Create Topology", command=self.recreate_topology,
                 bg=self.colors['button'], fg=self.colors['button_text'],
                 font=("Arial", 10, "bold"), cursor="hand2", relief=tk.RAISED
                 ).pack(fill=tk.X, pady=5)
    
    def _create_routing_controls(self, parent):
        """Create packet routing controls with better labels and click-to-select"""
        self._create_section_header(parent, "PACKET ROUTING")
        
        frame = tk.Frame(parent, bg=self.colors['panel_bg'])
        frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Click-to-select instruction
        instruction_frame = tk.Frame(frame, bg='#e3f2fd', relief=tk.RIDGE, bd=1)
        instruction_frame.pack(fill=tk.X, pady=(0, 5))
        
        tk.Label(instruction_frame, 
                text="💡 Click nodes to select:\n1st click = Source, 2nd click = Destination",
                font=("Arial", 7), bg='#e3f2fd', fg='#1976d2',
                justify=tk.LEFT).pack(padx=5, pady=3)
        
        # Source
        src_frame = tk.Frame(frame, bg='white', relief=tk.SUNKEN, bd=1)
        src_frame.pack(fill=tk.X, pady=3)
        
        src_inner = tk.Frame(src_frame, bg='white')
        src_inner.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(src_inner, text="🟢 Source Node:", font=("Arial", 9, "bold"),
                bg='white', fg='#2e7d32'
               ).pack(side=tk.LEFT)
        
        self.src_display_label = tk.Label(src_inner, text="(0, 0)", 
                                          font=("Courier", 9, "bold"),
                                          bg='white', fg='#2e7d32')
        self.src_display_label.pack(side=tk.LEFT, padx=10)
        
        # Manual input
        manual_src_frame = tk.Frame(src_inner, bg='white')
        manual_src_frame.pack(side=tk.RIGHT)
        
        self.src_x_var = tk.IntVar(value=0)
        self.src_y_var = tk.IntVar(value=0)
        
        tk.Label(manual_src_frame, text="X:", font=("Arial", 8),
                bg='white', fg='#666666').pack(side=tk.LEFT, padx=2)
        tk.Spinbox(manual_src_frame, from_=0, to=7, width=3, 
                  textvariable=self.src_x_var,
                  bg='white', fg=self.colors['text'], font=("Arial", 9),
                  command=self._update_source_from_spinbox).pack(side=tk.LEFT, padx=1)
        
        tk.Label(manual_src_frame, text="Y:", font=("Arial", 8),
                bg='white', fg='#666666').pack(side=tk.LEFT, padx=(5, 2))
        tk.Spinbox(manual_src_frame, from_=0, to=7, width=3, 
                  textvariable=self.src_y_var,
                  bg='white', fg=self.colors['text'], font=("Arial", 9),
                  command=self._update_source_from_spinbox).pack(side=tk.LEFT, padx=1)
        
        # Destination
        dst_frame = tk.Frame(frame, bg='white', relief=tk.SUNKEN, bd=1)
        dst_frame.pack(fill=tk.X, pady=3)
        
        dst_inner = tk.Frame(dst_frame, bg='white')
        dst_inner.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(dst_inner, text="🔴 Destination Node:", font=("Arial", 9, "bold"),
                bg='white', fg='#c62828'
               ).pack(side=tk.LEFT)
        
        self.dst_display_label = tk.Label(dst_inner, text="(2, 2)", 
                                          font=("Courier", 9, "bold"),
                                          bg='white', fg='#c62828')
        self.dst_display_label.pack(side=tk.LEFT, padx=10)
        
        # Manual input
        manual_dst_frame = tk.Frame(dst_inner, bg='white')
        manual_dst_frame.pack(side=tk.RIGHT)
        
        self.dst_x_var = tk.IntVar(value=2)
        self.dst_y_var = tk.IntVar(value=2)
        
        tk.Label(manual_dst_frame, text="X:", font=("Arial", 8),
                bg='white', fg='#666666').pack(side=tk.LEFT, padx=2)
        tk.Spinbox(manual_dst_frame, from_=0, to=7, width=3, 
                  textvariable=self.dst_x_var,
                  bg='white', fg=self.colors['text'], font=("Arial", 9),
                  command=self._update_dest_from_spinbox).pack(side=tk.LEFT, padx=1)
        
        tk.Label(manual_dst_frame, text="Y:", font=("Arial", 8),
                bg='white', fg='#666666').pack(side=tk.LEFT, padx=(5, 2))
        tk.Spinbox(manual_dst_frame, from_=0, to=7, width=3, 
                  textvariable=self.dst_y_var,
                  bg='white', fg=self.colors['text'], font=("Arial", 9),
                  command=self._update_dest_from_spinbox).pack(side=tk.LEFT, padx=1)
    
    def _update_source_from_spinbox(self):
        """Update source display when spinbox changes"""
        x = self.src_x_var.get()
        y = self.src_y_var.get()
        self.selected_source = (x, y)
        self.src_display_label.config(text=f"({x}, {y})")
    
    def _update_dest_from_spinbox(self):
        """Update destination display when spinbox changes"""
        x = self.dst_x_var.get()
        y = self.dst_y_var.get()
        self.selected_dest = (x, y)
        self.dst_display_label.config(text=f"({x}, {y})")
    
    def _create_simulation_details(self, parent):
        """Create simulation controls section"""
        self._create_section_header(parent, "SIMULATION CONTROLS")
        
        frame = tk.Frame(parent, bg=self.colors['panel_bg'])
        frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Animation Speed Control
        speed_frame = tk.Frame(frame, bg=self.colors['panel_bg'])
        speed_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(speed_frame, text="Animation Speed:", font=("Arial", 9, "bold"),
                bg=self.colors['panel_bg'], fg=self.colors['text']
               ).pack(anchor=tk.W, pady=(3, 1))
        
        speed_control_frame = tk.Frame(speed_frame, bg=self.colors['panel_bg'])
        speed_control_frame.pack(fill=tk.X)
        
        tk.Label(speed_control_frame, text="Slow", font=("Arial", 7),
                bg=self.colors['panel_bg'], fg=self.colors['text_light']
               ).pack(side=tk.LEFT, padx=1)
        
        self.speed_var = tk.IntVar(value=1000)
        self.speed_slider = tk.Scale(speed_control_frame, from_=200, to=8000, 
                                     orient=tk.HORIZONTAL, variable=self.speed_var,
                                     command=self._on_speed_change,
                                     bg=self.colors['panel_bg'], fg=self.colors['text'],
                                     highlightthickness=0, relief=tk.FLAT,
                                     showvalue=False, length=60)
        self.speed_slider.pack(side=tk.LEFT, padx=3)
        
        tk.Label(speed_control_frame, text="Fast", font=("Arial", 7),
                bg=self.colors['panel_bg'], fg=self.colors['text_light']
               ).pack(side=tk.LEFT, padx=1)
        
        # Add entry field for manual input
        self.speed_entry = tk.Entry(speed_control_frame, width=6, font=("Arial", 9),
                                   bg='white', fg=self.colors['text'],
                                   relief=tk.SUNKEN, bd=1)
        self.speed_entry.pack(side=tk.LEFT, padx=5)
        self.speed_entry.insert(0, "1000")
        
        # Bind entry field
        self.speed_entry.bind('<Return>', self._on_speed_entry_change)
        self.speed_entry.bind('<FocusOut>', self._on_speed_entry_change)
        
        tk.Label(speed_control_frame, text="ms", font=("Arial", 8),
                bg=self.colors['panel_bg'], fg=self.colors['text']
               ).pack(side=tk.LEFT, padx=1)
        
        self.speed_label_sim = tk.Label(speed_frame, text="1000 ms", font=("Arial", 7),
                                        bg=self.colors['panel_bg'], fg=self.colors['text'])
        self.speed_label_sim.pack(anchor=tk.CENTER, pady=1)
        
        # Control Buttons
        btn_frame = tk.Frame(frame, bg=self.colors['panel_bg'])
        btn_frame.pack(fill=tk.X, pady=5)
        
        # Simulate button
        tk.Button(btn_frame, text="Simulate", command=self.simulate_routing,
                 bg='#4CAF50', fg='black',
                 font=("Arial", 8, "bold"), relief=tk.RAISED, cursor="hand2"
                 ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=1)
        
        # Animate/Pause button
        self.animate_button_sim = tk.Button(btn_frame, text="Animate", command=self.animate_routing,
                 bg='#2196F3', fg='black',
                 font=("Arial", 8, "bold"), relief=tk.RAISED, cursor="hand2")
        self.animate_button_sim.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=1)
        
        # Clear button
        tk.Button(btn_frame, text="Clear", command=self.clear_path,
                 bg='#f44336', fg='black',
                 font=("Arial", 8, "bold"), relief=tk.RAISED, cursor="hand2"
                 ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=1)
    
    def _on_speed_change(self, value):
        """Handle speed slider change"""
        self.animation_speed = int(value)
        if hasattr(self, 'speed_label_sim'):
            self.speed_label_sim.config(text=f"{int(value)} ms")
        if hasattr(self, 'speed_entry'):
            self.speed_entry.delete(0, tk.END)
            self.speed_entry.insert(0, str(int(value)))
    
    def _on_speed_entry_change(self, event=None):
        """Handle speed entry field change"""
        try:
            value = int(self.speed_entry.get())
            value = max(200, min(8000, value))
            
            self.animation_speed = value
            self.speed_var.set(value)
            
            if hasattr(self, 'speed_label_sim'):
                self.speed_label_sim.config(text=f"{value} ms")
            
            self.speed_entry.delete(0, tk.END)
            self.speed_entry.insert(0, str(value))
            
        except ValueError:
            self.speed_entry.delete(0, tk.END)
            self.speed_entry.insert(0, str(self.animation_speed))

    def _create_flow_analysis_panel(self, parent):
        """Create packet flow analysis panel"""
        self._create_section_header(parent, "PACKET FLOW ANALYSIS")
        
        frame = tk.Frame(parent, bg=self.colors['panel_bg'])
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Detailed log
        log_label = tk.Label(frame, text="Detailed Log:", font=("Arial", 9, "bold"),
                            bg=self.colors['panel_bg'], fg='#000000')
        log_label.pack(anchor=tk.W, pady=(0, 3))
        
        self.flow_text = scrolledtext.ScrolledText(frame, height=18, width=35, wrap=tk.WORD,
                                                   font=('Courier', 8), bg='white', fg='black')
        self.flow_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure text tags for colored output
        self.flow_text.tag_config('hop', foreground='#2196F3', font=('Courier', 8, 'bold'))
        self.flow_text.tag_config('phase', foreground='#FF9800', font=('Courier', 8, 'bold'))
        self.flow_text.tag_config('success', foreground='#4CAF50', font=('Courier', 8, 'bold'))
        self.flow_text.tag_config('error', foreground='#f44336', font=('Courier', 8, 'bold'))
        self.flow_text.tag_config('info', foreground='#666666', font=('Courier', 8))
        self.flow_text.tag_config('header', foreground='#9C27B0', font=('Courier', 8, 'bold'))
        
        self._update_flow_analysis("Ready. Select source and destination, then click Animate.", clear=True)
    
    def _update_flow_analysis(self, message, clear=False, tag=None):
        """Update flow analysis text with colored tags"""
        if clear:
            self.flow_text.delete(1.0, tk.END)
        
        if tag:
            self.flow_text.insert(tk.END, message + "\n", tag)
        else:
            lines = message.split('\n')
            for line in lines:
                if '===' in line or 'PACKET' in line.upper():
                    self.flow_text.insert(tk.END, line + "\n", 'header')
                elif line.strip().startswith('--- HOP'):
                    self.flow_text.insert(tk.END, line + "\n", 'hop')
                elif line.strip().startswith('PHASE'):
                    self.flow_text.insert(tk.END, line + "\n", 'phase')
                elif '✅' in line or 'DELIVERED' in line or 'complete' in line.lower():
                    self.flow_text.insert(tk.END, line + "\n", 'success')
                elif '❌' in line or 'ERROR' in line or 'FAIL' in line:
                    self.flow_text.insert(tk.END, line + "\n", 'error')
                elif line.strip().startswith('•') or line.strip().startswith('→'):
                    self.flow_text.insert(tk.END, line + "\n", 'info')
                else:
                    self.flow_text.insert(tk.END, line + "\n")
        
        self.flow_text.see(tk.END)
    
    def _create_floating_view_controls(self):
        """Create floating view controls on canvas"""
        control_frame = tk.Frame(self.canvas, bg='#f0f0f0', relief=tk.RAISED, bd=3)
        
        zoom_frame = tk.Frame(control_frame, bg='#f0f0f0')
        zoom_frame.pack(padx=5, pady=5)
        
        # Reset button
        tk.Button(zoom_frame, text="🏠", command=self.reset_view,
                 bg='#4CAF50', fg='white', font=("Arial", 14, "bold"),
                 width=3, height=1, relief=tk.RAISED, cursor="hand2",
                 activebackground='#45a049').pack(pady=2)
        
        # + button
        tk.Button(zoom_frame, text="+", command=self.zoom_in,
                 bg='#2196F3', fg='white', font=("Arial", 16, "bold"),
                 width=3, height=1, relief=tk.RAISED, cursor="hand2",
                 activebackground='#1976D2').pack(pady=2)
        
        # - button
        tk.Button(zoom_frame, text="−", command=self.zoom_out,
                 bg='#2196F3', fg='white', font=("Arial", 16, "bold"),
                 width=3, height=1, relief=tk.RAISED, cursor="hand2",
                 activebackground='#1976D2').pack(pady=2)
        
        # Position controls in top-right corner
        self.floating_controls = self.canvas.create_window(0, 0, window=control_frame, anchor='nw', tags='floating_controls')
        
        def update_position(event=None):
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            if canvas_width > 1 and canvas_height > 1:
                control_width = 60
                x_pos = canvas_width - control_width - 10
                y_pos = 10
                self.canvas.coords(self.floating_controls, x_pos, y_pos)
        
        self.canvas.bind('<Configure>', update_position)
        self.root.after(200, update_position)
    
    def draw_topology(self):
        """Draw the torus topology"""
        # Delete all canvas items except floating controls
        for item in self.canvas.find_all():
            tags = self.canvas.gettags(item)
            if 'floating_controls' not in tags and 'hover_overlay' not in tags:
                self.canvas.delete(item)
        
        self.node_positions.clear()
        self.node_items.clear()
        self.edge_items.clear()
        
        self._calculate_positions_grid()
        self.torus_renderer.draw_grid_lines(self.width, self.height, self.node_positions, self._transform_coords, self.zoom_level)
        self._draw_connections()
        self._draw_nodes()
        
        # Only draw routing path if we have a valid path and not currently animating
        if self.current_path and not self.animation_running:
            try:
                self.torus_renderer.draw_routing_path(self.current_path, self.node_positions, self._transform_coords, self.zoom_level)
            except (AttributeError, tk.TclError):
                pass
        
        # Ensure floating controls are positioned correctly
        if hasattr(self, 'floating_controls') and self.floating_controls:
            try:
                canvas_width = self.canvas.winfo_width()
                if canvas_width > 1:
                    control_width = 60
                    x_pos = canvas_width - control_width - 10
                    y_pos = 10
                    self.canvas.coords(self.floating_controls, x_pos, y_pos)
            except:
                pass
    
    def _calculate_positions_grid(self):
        """Calculate node positions in 2D grid"""
        canvas_width = self.canvas.winfo_width() or 800
        canvas_height = self.canvas.winfo_height() or 600
        
        margin = 80
        available_width = canvas_width - 2 * margin
        available_height = canvas_height - 2 * margin
        
        x_spacing = available_width / max(1, self.width - 1) if self.width > 1 else 0
        y_spacing = available_height / max(1, self.height - 1) if self.height > 1 else 0
        
        for x in range(self.width):
            for y in range(self.height):
                pos_x = margin + x * x_spacing
                pos_y = margin + y * y_spacing
                self.node_positions[(x, y)] = (pos_x, pos_y)
    
    def _draw_connections(self):
        """Draw connections between nodes"""
        drawn = set()
        for addr, node in self.topology.nodes.items():
            for neighbor_addr in node.interfaces.keys():
                edge = tuple(sorted([addr, neighbor_addr]))
                if edge not in drawn:
                    x1, y1 = self.node_positions[addr]
                    x2, y2 = self.node_positions[neighbor_addr]
                    cx1, cy1 = self._transform_coords(x1, y1)
                    cx2, cy2 = self._transform_coords(x2, y2)
                    
                    # Check wraparound
                    ax, ay = addr
                    nx, ny = neighbor_addr
                    is_wraparound = (abs(ax - nx) > 1) or (abs(ay - ny) > 1)
                    
                    color = self.colors['path'] if edge in self.highlighted_edges else self.colors['connection']
                    width = 4 if edge in self.highlighted_edges else 1
                    
                    if is_wraparound:
                        line_id = self.canvas.create_line(cx1, cy1, cx2, cy2, fill=color, width=width, dash=(5, 5))
                    else:
                        line_id = self.canvas.create_line(cx1, cy1, cx2, cy2, fill=color, width=width)
                    
                    self.edge_items[edge] = line_id
                    drawn.add(edge)
    
    def _draw_nodes(self):
        """Draw nodes"""
        for addr, (x, y) in self.node_positions.items():
            cx, cy = self._transform_coords(x, y)
            color = self.colors['highlight'] if addr in self.highlighted_nodes else self.colors['node']
            r = max(8, 12 * self.zoom_level)
            
            node_id = self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r, 
                                             fill=color, outline=self.colors['node_border'], width=2)
            
            x_coord, y_coord = addr
            label = f"({x_coord},{y_coord})"
            text_offset = max(20, r + 15)
            self.canvas.create_text(cx, cy - text_offset, text=label, fill='#2c3e50', font=("Arial", 9, "bold"))
            
            self.node_items[addr] = node_id
    
    def _transform_coords(self, x, y):
        """Transform coordinates with zoom and pan"""
        return (x * self.zoom_level + self.pan_x, y * self.zoom_level + self.pan_y)
    
    def simulate_routing(self):
        """Simulate routing and highlight path"""
        path = self._compute_path()
        if not path:
            return
        
        # Clear old highlights first
        self.highlighted_edges.clear()
        self.highlighted_nodes.clear()
        self.packet_animator.clear_animations()
        
        # Set the new path
        self.current_path = path
        
        # Highlight path nodes and edges
        for i in range(len(path) - 1):
            addr = path[i]
            next_addr = path[i + 1]
            
            self.highlighted_nodes.add(addr)
            edge = tuple(sorted([addr, next_addr]))
            self.highlighted_edges.add(edge)
        
        self.highlighted_nodes.add(path[-1])
        
        # Draw the topology with highlighted path
        self.draw_topology()
        
        # Update status bar
        self.current_hop = 0
        self.transfer_phase = "Route Computed"
        self.transfer_progress = 0
        self.signal_status = "Ready"
        self._update_status_bar()
        self._update_flow_analysis(f"XY Route computed: {' → '.join(str(p) for p in path)}", clear=True)
    
    def animate_routing(self):
        """Animate REAL packet routing with detailed step-by-step visualization"""
        # If already running, toggle pause
        if self.animation_running:
            self.is_paused = not self.is_paused
            if self.is_paused:
                if hasattr(self, 'animate_button_sim'):
                    self.animate_button_sim.config(text="Resume")
                self.transfer_phase = "Paused"
                self.signal_status = "Paused"
                self._update_status_bar()
            else:
                if hasattr(self, 'animate_button_sim'):
                    self.animate_button_sim.config(text="Pause")
                self.transfer_phase = "Transferring"
                self.signal_status = "Active"
                self._update_status_bar()
            return
        
        path = self._compute_path()
        if not path:
            return
        
        self.animation_running = True
        self.is_paused = False
        if hasattr(self, 'animate_button_sim'):
            self.animate_button_sim.config(text="Pause")
        
        # Clear animations without redrawing topology yet
        self.packet_animator.clear_animations()
        self.highlighted_edges.clear()
        self.highlighted_nodes.clear()
        
        self.current_path = path
        self.current_hop = 0
        
        # Clear any previous animations
        self.packet_animator.clear_animations()
        
        # Initialize buffer states for all nodes in path
        self.buffer_states = {}
        for addr in path:
            self.buffer_states[addr] = {
                'send_buf': 0,
                'recv_buf': 0
            }
        
        # Inject packet into source node's send buffer
        source_node = self.topology.nodes[path[0]]
        if len(path) > 1:
            next_hop = path[1]
            if next_hop in source_node.interfaces:
                interface = source_node.interfaces[next_hop]
                interface.send_buffer.enqueue(self.current_packet)
                self.buffer_states[path[0]]['send_buf'] = len(interface.send_buffer.buffer)
        
        # Create real packet
        from core.packet import Packet
        self.current_packet = Packet(
            source_address=path[0],
            dest_address=path[-1],
            data=f"Test packet from {path[0]} to {path[-1]}",
            sim_clock=0
        )
        
        # Initialize flow analysis
        self._update_flow_analysis("=== REAL PACKET TRANSFER INITIATED ===", clear=True)
        self._update_flow_analysis(f"\n📦 Packet Created:")
        self._update_flow_analysis(f"   Source: {self.current_packet.source_address}")
        self._update_flow_analysis(f"   Destination: {self.current_packet.dest_address}")
        self._update_flow_analysis(f"   Data: {self.current_packet.data}")
        self._update_flow_analysis(f"   start_timer = {self.current_packet.start_timer}")
        
        def animate_step(index):
            # Check if animation was stopped
            if not self.animation_running:
                return
                
            # Check if paused
            if self.is_paused:
                self.root.after(100, lambda: animate_step(index))
                return
            
            if index >= len(path):
                self.animation_running = False
                self.is_paused = False
                if hasattr(self, 'animate_button_sim'):
                    self.animate_button_sim.config(text="Animate")
                
                try:
                    self.current_packet.end_timer = self.current_packet.start_timer + (len(path) - 1)
                    latency = self.current_packet.end_timer - self.current_packet.start_timer
                    
                    self._update_flow_analysis(f"\n✅ PACKET DELIVERED!")
                    self._update_flow_analysis(f"   end_timer = {self.current_packet.end_timer}")
                    self._update_flow_analysis(f"   Latency = {latency} time units")
                except AttributeError:
                    self._update_flow_analysis(f"\n✅ PACKET DELIVERED!")
                    self._update_flow_analysis(f"   Animation completed successfully")
                
                self.transfer_phase = "Completed"
                self.transfer_progress = 100
                self.signal_status = "Idle"
                self._update_status_bar()
                
                # Show final delivered packet
                if path[-1] in self.node_positions:
                    x, y = self.node_positions[path[-1]]
                    cx, cy = self._transform_coords(x, y)
                    self.packet_animator.draw_packet_at_node(cx, cy, phase='delivered')
                
                return
            
            addr = path[index]
            next_addr = path[index + 1] if index < len(path) - 1 else None
            self.current_hop = index
            self.transfer_progress = int((index / (len(path) - 1)) * 100) if len(path) > 1 else 100
            
            # Get node and interface for real state
            node = self.topology.nodes[addr]
            interface_state = None
            
            if next_addr and next_addr in node.interfaces:
                interface = node.interfaces[next_addr]
                try:
                    interface_state = {
                        'req': 1 if hasattr(interface, 'pin_REQ') and interface.pin_REQ else 0,
                        'ack': 1 if hasattr(interface, 'pin_ACK') and interface.pin_ACK else 0,
                        'busy': 1 if hasattr(interface, 'bit_Busy') and interface.bit_Busy else 0,
                        'transfer': 1 if hasattr(interface, 'bit_Transfer') and interface.bit_Transfer else 0,
                        'send_buf': f"{len(interface.send_buffer.buffer) if hasattr(interface, 'send_buffer') and hasattr(interface.send_buffer, 'buffer') else 0}/4",
                        'recv_buf': f"{len(interface.receive_buffer.buffer) if hasattr(interface, 'receive_buffer') and hasattr(interface.receive_buffer, 'buffer') else 0}/4"
                    }
                except AttributeError:
                    # Fallback interface state if attributes don't exist
                    interface_state = {
                        'req': 0, 'ack': 0, 'busy': 0, 'transfer': 0,
                        'send_buf': '0/4', 'recv_buf': '0/4'
                    }
            
            # Get node position for packet animation
            if addr in self.node_positions:
                x, y = self.node_positions[addr]
                cx, cy = self._transform_coords(x, y)
            
            # Detailed flow analysis with handshake phases
            if index == 0:
                # SOURCE NODE
                self._animate_source_node(addr, next_addr, cx, cy, path, interface_state)
            elif next_addr is not None:
                # INTERMEDIATE NODE
                self._animate_intermediate_node(addr, next_addr, cx, cy, path, index, interface_state)
            
            # Visual highlight nodes and edges
            if addr in self.node_items:
                self.canvas.itemconfig(self.node_items[addr], fill=self.colors['highlight'])
            
            if next_addr:
                edge = tuple(sorted([addr, next_addr]))
                if edge in self.edge_items:
                    self.canvas.itemconfig(self.edge_items[edge], fill=self.colors['path'], width=3)
                    self.highlighted_edges.add(edge)
            
            self.canvas.update()
            
            # Use the current animation_speed for the delay
            self.root.after(self.animation_speed, lambda: animate_step(index + 1))
        
        animate_step(0)
        self._start_buffer_refresh()
    
    def _animate_source_node(self, addr, next_addr, cx, cy, path, interface_state):
        """Animate source node packet creation and initial send"""
        self.transfer_phase = "Packet Created"
        self.signal_status = "Idle → REQ"
        
        clk = 0
        
        self._update_flow_analysis(f"\n--- HOP 1/{len(path)-1}: Source Node {addr} ---")
        self._update_flow_analysis(f"[clk={clk}] Packet Creation")
        self._update_flow_analysis("  • Application creates packet")
        self._update_flow_analysis(f"  • Destination set to {path[-1]}")
        
        # Update status bar with initial interface state
        initial_state = {
            'req': 0, 'ack': 0, 'busy': 0, 'transfer': 0,
            'send_buf': '0/4', 'recv_buf': '0/4'
        }
        self._update_status_bar(current_node=addr, next_node=next_addr, interface_state=initial_state)
        
        # Visual: Show packet created at source
        self.packet_animator.draw_packet_at_node(cx, cy, phase='created')
        
        # Get next node position
        nx, ny = self.node_positions[next_addr]
        ncx, ncy = self._transform_coords(nx, ny)
        
        # Schedule animation phases with proper timing
        delay_base = max(200, int(self.animation_speed * 0.2))
        
        # Show routing phase
        def show_routing():
            if not self.animation_running or self.is_paused:
                return
            self.transfer_phase = "Routing"
            self.signal_status = "Computing"
            clk_routing = clk + 1
            self._update_flow_analysis(f"[clk={clk_routing}] XY Routing Logic")
            self._update_flow_analysis(f"  • Next hop determined: {next_addr}")
            self._update_flow_analysis("  • Packet placed in Send Buffer")
            
            # Update buffer state - packet in send buffer
            if addr in self.buffer_states:
                self.buffer_states[addr]['send_buf'] = 1
            
            # Refresh buffer display if showing this node
            if self.buffer_display_node == addr:
                self._show_buffer_display(addr)
            
            routing_state = {
                'req': 0, 'ack': 0, 'busy': 0, 'transfer': 0,
                'send_buf': f"{self.buffer_states[addr]['send_buf']}/4",
                'recv_buf': f"{self.buffer_states[addr]['recv_buf']}/4"
            }
            self._update_status_bar(current_node=addr, next_node=next_addr, interface_state=routing_state)
            self.packet_animator.draw_node_activity_ring(cx, cy, activity='processing')
        
        # Show REQ phase
        def show_req():
            if not self.animation_running or self.is_paused:
                return
            self.transfer_phase = "REQ"
            self.signal_status = "REQ=1"
            clk_req = clk + 2
            self._update_flow_analysis(f"[clk={clk_req}] Request (REQ)")
            self._update_flow_analysis(f"  • pin_REQ = 1 ({addr} → {next_addr})")
            self._update_flow_analysis(f"  • Waiting for ACK from {next_addr}")
            
            req_state = {
                'req': 1, 'ack': 0, 'busy': 0, 'transfer': 0,
                'send_buf': f"{self.buffer_states[addr]['send_buf']}/4",
                'recv_buf': f"{self.buffer_states[addr]['recv_buf']}/4"
            }
            self._update_status_bar(current_node=addr, next_node=next_addr, interface_state=req_state)
            
            # Show REQ arrow
            self.packet_animator.draw_transfer_arrow(cx, cy, ncx, ncy, phase='req')
        
        # Show ACK phase
        def show_ack():
            if not self.animation_running or self.is_paused:
                return
            self.transfer_phase = "ACK"
            self.signal_status = "ACK=1"
            clk_ack = clk + 3
            self._update_flow_analysis(f"[clk={clk_ack}] Acknowledgment (ACK)")
            self._update_flow_analysis(f"  • pin_ACK = 1 ({next_addr} → {addr})")
            self._update_flow_analysis("  • Channel ready for data transfer")
            
            ack_state = {
                'req': 1, 'ack': 1, 'busy': 1, 'transfer': 0,
                'send_buf': f"{self.buffer_states[addr]['send_buf']}/4",
                'recv_buf': f"{self.buffer_states[addr]['recv_buf']}/4"
            }
            self._update_status_bar(current_node=addr, next_node=next_addr, interface_state=ack_state)
            
            # Show ACK arrow (from receiver back to sender)
            self.packet_animator.draw_transfer_arrow(ncx, ncy, cx, cy, phase='ack')
        
        # Show data transfer
        def show_data():
            if not self.animation_running or self.is_paused:
                return
            self.transfer_phase = "Transferring"
            self.signal_status = "Sending Data"
            clk_data = clk + 4
            self._update_flow_analysis(f"[clk={clk_data}] Data Transfer")
            self._update_flow_analysis("  • Packet data transmitted")
            self._update_flow_analysis(f"  • Moving to next hop: {next_addr}")
            
            # Update actual interface buffers and buffer states
            node = self.topology.nodes[addr]
            if next_addr in node.interfaces:
                interface = node.interfaces[next_addr]
                if not interface.send_buffer.is_empty():
                    packet = interface.send_buffer.dequeue()
                    # Move to next node's receive buffer
                    next_node = self.topology.nodes[next_addr]
                    if addr in next_node.interfaces:
                        next_interface = next_node.interfaces[addr]
                        next_interface.receive_buffer.enqueue(packet)
            
            # Update buffer states
            if addr in self.buffer_states:
                self.buffer_states[addr]['send_buf'] = 0
            if next_addr in self.buffer_states:
                self.buffer_states[next_addr]['recv_buf'] = 1
            
            # Refresh buffer displays
            if self.buffer_display_node == addr:
                self._show_buffer_display(addr)
            elif self.buffer_display_node == next_addr:
                self._show_buffer_display(next_addr)
            
            data_state = {
                'req': 1, 'ack': 1, 'busy': 1, 'transfer': 1,
                'send_buf': f"{self.buffer_states[addr]['send_buf']}/4",
                'recv_buf': f"{self.buffer_states.get(next_addr, {}).get('recv_buf', 0)}/4"
            }
            self._update_status_bar(current_node=addr, next_node=next_addr, interface_state=data_state)
            
            # Animate packet movement
            self.packet_animator.animate_packet_movement(cx, cy, ncx, ncy, duration=delay_base)
        
        # Schedule the phases
        self.root.after(delay_base, show_routing)
        self.root.after(delay_base * 2, show_req)
        self.root.after(delay_base * 3, show_ack)
        self.root.after(delay_base * 4, show_data)
    
    def _animate_intermediate_node(self, addr, next_addr, cx, cy, path, index, interface_state):
        """Animate intermediate node with detailed handshake and transfer phases"""
        is_last_hop = (next_addr == path[-1])
        
        if is_last_hop:
            self._update_flow_analysis(f"\n--- HOP {index + 1}/{len(path)-1}: {addr} → Destination {next_addr} ---")
        else:
            self._update_flow_analysis(f"\n--- HOP {index + 1}/{len(path)-1}: Intermediate Node {addr} ---")
        
        # Get next node position
        nx, ny = self.node_positions[next_addr]
        ncx, ncy = self._transform_coords(nx, ny)
        
        base_clk = index * 5
        
        # Phase 1: REQ
        self.transfer_phase = "REQ"
        self.signal_status = "REQ=1"
        self._update_flow_analysis(f"[clk={base_clk}] Request (REQ)")
        self._update_flow_analysis(f"  • pin_REQ = 1 ({addr} → {next_addr})")
        self._update_flow_analysis(f"  • Waiting for ACK from {next_addr}")
        
        # Initialize buffer state for this node if not exists
        if addr not in self.buffer_states:
            self.buffer_states[addr] = {'send_buf': 0, 'recv_buf': 1}  # Has received packet
        
        handshake_state_1 = {
            'req': 1, 'ack': 0, 'busy': 0, 'transfer': 0,
            'send_buf': f"{self.buffer_states[addr]['send_buf']}/4",
            'recv_buf': f"{self.buffer_states[addr]['recv_buf']}/4"
        }
        self._update_status_bar(current_node=addr, next_node=next_addr, interface_state=handshake_state_1)
        
        self.packet_animator.draw_transfer_arrow(cx, cy, ncx, ncy, phase='req')
        self.packet_animator.draw_node_activity_ring(cx, cy, activity='busy')
        
        # Schedule animation phases with proper timing
        delay_base = max(200, int(self.animation_speed * 0.2))
        
        # Phase 2: ACK
        def show_ack():
            if not self.animation_running or self.is_paused:
                return
            self.transfer_phase = "ACK"
            self.signal_status = "ACK=1"
            self._update_flow_analysis(f"[clk={base_clk + 1}] Acknowledgment (ACK)")
            self._update_flow_analysis(f"  • pin_ACK = 1 ({next_addr} → {addr})")
            self._update_flow_analysis("  • bit_Busy = 1 (Channel locked)")
            
            handshake_state_2 = {
                'req': 1, 'ack': 1, 'busy': 1, 'transfer': 0,
                'send_buf': f"{self.buffer_states[addr]['send_buf']}/4",
                'recv_buf': f"{self.buffer_states[addr]['recv_buf']}/4"
            }
            self._update_status_bar(current_node=addr, next_node=next_addr, interface_state=handshake_state_2)
            
            self.packet_animator.draw_transfer_arrow(ncx, ncy, cx, cy, phase='ack')
            self.packet_animator.draw_node_activity_ring(ncx, ncy, activity='ready')
        
        # Phase 3: Data Transfer
        def show_data_transfer():
            if not self.animation_running or self.is_paused:
                return
            self.transfer_phase = "Transferring"
            self.signal_status = "pin_DATA active"
            self._update_flow_analysis(f"[clk={base_clk + 2}] Data Transfer")
            self._update_flow_analysis("  • Send Register → pin_DATA")
            self._update_flow_analysis(f"  • Direction: {addr} → {next_addr}")
            
            # Update actual interface buffers - packet moves from receive to send buffer
            node = self.topology.nodes[addr]
            if next_addr in node.interfaces:
                # Move packet from receive buffer to send buffer
                send_interface = node.interfaces[next_addr]
                # Find interface that has the packet in receive buffer
                for neighbor_addr, interface in node.interfaces.items():
                    if not interface.receive_buffer.is_empty():
                        packet = interface.receive_buffer.dequeue()
                        send_interface.send_buffer.enqueue(packet)
                        break
            
            # Update buffer states
            if addr in self.buffer_states:
                self.buffer_states[addr]['recv_buf'] = 0
                self.buffer_states[addr]['send_buf'] = 1
            
            # Refresh buffer display
            if self.buffer_display_node == addr:
                self._show_buffer_display(addr)
            
            transfer_state = {
                'req': 1, 'ack': 1, 'busy': 1, 'transfer': 1,
                'send_buf': f"{self.buffer_states.get(addr, {}).get('send_buf', 1)}/4",
                'recv_buf': f"{self.buffer_states.get(addr, {}).get('recv_buf', 0)}/4"
            }
            self._update_status_bar(current_node=addr, next_node=next_addr, interface_state=transfer_state)
            
            self.packet_animator.draw_transfer_arrow(cx, cy, ncx, ncy, phase='data')
            self.packet_animator.draw_packet_at_node(cx, cy, phase='sending')
            
            # Animate packet movement
            self.packet_animator.animate_packet_movement(cx, cy, ncx, ncy, duration=delay_base)
        
        # Phase 4: Reception
        def show_reception():
            if not self.animation_running or self.is_paused:
                return
            self.transfer_phase = "Receiving"
            self.signal_status = "bit_Receive=1"
            self._update_flow_analysis(f"[clk={base_clk + 3}] Reception at Next Node")
            self._update_flow_analysis("  • pin_DATA → Receive Register")
            self._update_flow_analysis("  • Packet placed in Receive Buffer")
            
            # Update buffer states - packet received at next node
            if addr in self.buffer_states:
                self.buffer_states[addr]['send_buf'] = 0
            if next_addr in self.buffer_states:
                self.buffer_states[next_addr]['recv_buf'] = 1
            
            # Refresh buffer displays
            if self.buffer_display_node == addr:
                self._show_buffer_display(addr)
            elif self.buffer_display_node == next_addr:
                self._show_buffer_display(next_addr)
            
            receive_state = {
                'req': 1, 'ack': 1, 'busy': 1, 'transfer': 1,
                'send_buf': f"{self.buffer_states.get(addr, {}).get('send_buf', 0)}/4",
                'recv_buf': f"{self.buffer_states.get(next_addr, {}).get('recv_buf', 1)}/4"
            }
            self._update_status_bar(current_node=addr, next_node=next_addr, interface_state=receive_state)
            
            self.packet_animator.draw_packet_at_node(ncx, ncy, phase='receiving')
        
        # Phase 5: Routing Check
        def show_routing_check():
            if not self.animation_running or self.is_paused:
                return
            self.transfer_phase = "Routing"
            self.signal_status = "Checking dest"
            
            is_final_dest = (next_addr == path[-1])
            
            if is_final_dest:
                self._update_flow_analysis(f"[clk={base_clk + 4}] Final Delivery")
                self._update_flow_analysis(f"  • Dest {path[-1]} = Current {next_addr} ✓")
                self._update_flow_analysis(f"  • Packet successfully reached destination")
                self._update_flow_analysis("  • Packet in Receive Buffer (1/4)")
                # Final destination - packet stays in receive buffer to show delivery
                if next_addr in self.buffer_states:
                    self.buffer_states[next_addr]['recv_buf'] = 1
            else:
                self._update_flow_analysis(f"[clk={base_clk + 4}] XY Routing Decision")
                self._update_flow_analysis(f"  • Dest {path[-1]} ≠ Current {addr}")
                self._update_flow_analysis(f"  • Next hop determined: {next_addr}")
                self._update_flow_analysis("  • Handshake reset (REQ=0, ACK=0)")
            
            reset_state = {
                'req': 0, 'ack': 0, 'busy': 0, 'transfer': 0,
                'send_buf': f"{self.buffer_states.get(addr, {}).get('send_buf', 0)}/4",
                'recv_buf': f"{self.buffer_states.get(next_addr, {}).get('recv_buf', 1 if is_final_dest else 0)}/4"
            }
            self._update_status_bar(current_node=addr, next_node=next_addr, interface_state=reset_state)
            
            self.packet_animator.draw_node_activity_ring(ncx, ncy, activity='processing')
        
        # Schedule the phases
        self.root.after(delay_base, show_ack)
        self.root.after(delay_base * 2, show_data_transfer)
        self.root.after(delay_base * 3, show_reception)
        self.root.after(delay_base * 4, show_routing_check)

    def _compute_path(self):
        """Compute path using XY routing"""
        try:
            src_addr = (self.src_x_var.get(), self.src_y_var.get())
            dst_addr = (self.dst_x_var.get(), self.dst_y_var.get())
            
            if src_addr not in self.topology.nodes or dst_addr not in self.topology.nodes:
                messagebox.showerror("Error", "Invalid source or destination node")
                return None
            
            if src_addr == dst_addr:
                messagebox.showwarning("Warning", "Source and destination are the same")
                return None
            
            print(f"\n{'='*60}")
            print(f"COMPUTING XY PATH: {src_addr} -> {dst_addr}")
            print(f"{'='*60}")
            
            # Use XY routing to get path
            path = self.topology.router.get_full_path(src_addr, dst_addr)
            
            if not path:
                messagebox.showerror("Error", "No XY route found")
                return None
            
            print(f"\nXY PATH COMPUTED SUCCESSFULLY:")
            print(f"  Total hops: {len(path) - 1}")
            print(f"  Path: {' -> '.join(str(p) for p in path)}")
            print(f"{'='*60}\n")
            
            return path
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return None
    
    def clear_path(self):
        """Clear routing highlights and packet animations"""
        # Stop any running animations
        self.animation_running = False
        self.is_paused = False
        
        # Clear visual elements
        self.clear_highlights()
        self.packet_animator.clear_animations()
        self.torus_renderer.clear_paths()
        self._hide_buffer_display()
        
        # Reset state
        self.current_packet = None
        self.current_path = []
        self.current_hop = 0
        self.transfer_phase = "Waiting to Start"
        self.transfer_progress = 0
        self.signal_status = "Idle"
        
        # Update UI
        if hasattr(self, 'animate_button_sim'):
            self.animate_button_sim.config(text="Animate")
        self._update_status_bar()
        self._update_flow_analysis("Path cleared. Ready for new transfer.", clear=True)
    
    def clear_highlights(self):
        """Clear all highlights and packet animations"""
        self.highlighted_edges.clear()
        self.highlighted_nodes.clear()
        
        # Clear animations safely
        try:
            self.packet_animator.clear_animations()
        except (AttributeError, tk.TclError):
            pass
            
        try:
            self.torus_renderer.clear_paths()
        except (AttributeError, tk.TclError):
            pass
        
        # Clear animation items
        for item in self.animation_items[:]:
            try:
                if hasattr(self.canvas, 'winfo_exists') and self.canvas.winfo_exists():
                    self.canvas.delete(item)
            except (tk.TclError, AttributeError):
                pass
        self.animation_items.clear()
        
        # Only redraw if not currently animating
        if not self.animation_running:
            try:
                self.draw_topology()
            except (AttributeError, tk.TclError):
                pass
    
    def recreate_topology(self):
        """Recreate topology with new dimensions"""
        from topology.torus_topology import TorusTopology
        from simulation.simulator import Simulator
        
        new_width = self.width_var.get()
        new_height = self.height_var.get()
        
        print(f"\nRecreating torus topology with {new_width}x{new_height} dimensions...")
        self.topology = TorusTopology(new_width, new_height)
        self.simulator = Simulator(self.topology)
        self.width = new_width
        self.height = new_height
        
        self.clear_highlights()
        self.current_packet = None
        self.current_path = []
        self.animation_running = False
        self.is_paused = False
        if hasattr(self, 'animate_button_sim'):
            self.animate_button_sim.config(text="Animate")
        self.draw_topology()
        
        self.transfer_phase = "Topology Recreated"
        self.signal_status = "Idle"
        self._update_status_bar()
    
    def reset_view(self):
        """Reset view"""
        self.zoom_level = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self.draw_topology()
    
    def zoom_in(self):
        """Zoom in from center"""
        canvas_center_x = self.canvas.winfo_width() / 2
        canvas_center_y = self.canvas.winfo_height() / 2
        
        zoom_factor = 1.2
        old_zoom = self.zoom_level
        new_zoom = min(3.0, old_zoom * zoom_factor)
        
        # Adjust pan to zoom from center
        self.pan_x = canvas_center_x - (canvas_center_x - self.pan_x) * (new_zoom / old_zoom)
        self.pan_y = canvas_center_y - (canvas_center_y - self.pan_y) * (new_zoom / old_zoom)
        
        self.zoom_level = new_zoom
        self.draw_topology()
    
    def zoom_out(self):
        """Zoom out from center"""
        canvas_center_x = self.canvas.winfo_width() / 2
        canvas_center_y = self.canvas.winfo_height() / 2
        
        zoom_factor = 1.2
        old_zoom = self.zoom_level
        new_zoom = max(0.3, old_zoom / zoom_factor)
        
        # Adjust pan to zoom from center
        self.pan_x = canvas_center_x - (canvas_center_x - self.pan_x) * (new_zoom / old_zoom)
        self.pan_y = canvas_center_y - (canvas_center_y - self.pan_y) * (new_zoom / old_zoom)
        
        self.zoom_level = new_zoom
        self.draw_topology()
    
    def _bind_events(self):
        """Bind keyboard and mouse events"""
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)
        self.canvas.bind("<Motion>", self.on_canvas_hover)
        
        # Mouse drag functionality
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_press)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_release)
        
        self.root.bind("<Control-plus>", lambda e: self.zoom_in())
        self.root.bind("<Control-minus>", lambda e: self.zoom_out())
        self.root.bind("<Control-0>", lambda e: self.reset_view())
        self.root.bind("<Escape>", lambda e: self.clear_highlights())
    
    def on_canvas_click(self, event):
        """Handle canvas click for node selection and buffer display"""
        clicked_node = None
        for addr, item_id in self.node_items.items():
            coords = self.canvas.coords(item_id)
            if coords:
                x1, y1, x2, y2 = coords
                cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
                dist = math.sqrt((event.x - cx)**2 + (event.y - cy)**2)
                
                click_radius = max(15, 12 * self.zoom_level + 5)
                if dist < click_radius:
                    clicked_node = addr
                    break
        
        if clicked_node is None:
            self._hide_buffer_display()
            return
        
        x, y = clicked_node
        
        # Show buffer display for clicked node
        self._show_buffer_display(clicked_node)
        
        if self.click_count == 0:
            # First click - set source
            self.selected_source = clicked_node
            self.src_x_var.set(x)
            self.src_y_var.set(y)
            self.src_display_label.config(text=f"({x}, {y})")
            self.click_count = 1
            
            # Visual feedback
            self._highlight_selected_node(clicked_node, 'source')
            
        elif self.click_count == 1:
            # Second click - set destination
            if clicked_node == self.selected_source:
                return
            
            self.selected_dest = clicked_node
            self.dst_x_var.set(x)
            self.dst_y_var.set(y)
            self.dst_display_label.config(text=f"({x}, {y})")
            self.click_count = 0
            
            # Visual feedback
            self._highlight_selected_node(clicked_node, 'dest')
            
            # Clear selection highlights after a moment
            self.root.after(2000, self.clear_highlights)
    
    def on_canvas_hover(self, event):
        """Handle canvas hover for node details display"""
        # Find node under cursor
        hovered_node = None
        for addr, item_id in self.node_items.items():
            coords = self.canvas.coords(item_id)
            if coords:
                x1, y1, x2, y2 = coords
                cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
                dist = math.sqrt((event.x - cx)**2 + (event.y - cy)**2)
                
                hover_radius = max(15, 12 * self.zoom_level + 5)
                if dist < hover_radius:
                    hovered_node = addr
                    break
        
        # If hovering over a different node or moved away
        if hovered_node != self.hover_node:
            if self.hover_timer:
                self.root.after_cancel(self.hover_timer)
                self.hover_timer = None
            
            if self.hover_overlay and hovered_node is None:
                self._close_hover_overlay()
            
            self.hover_node = hovered_node
            
            if hovered_node:
                self.hover_timer = self.root.after(500, lambda: self._show_hover_node_info(hovered_node, event.x, event.y))
    
    def _show_hover_node_info(self, addr, mouse_x, mouse_y):
        """Show detailed node information in a canvas overlay"""
        if self.hover_node != addr:
            return
        
        if self.hover_overlay:
            self._close_hover_overlay()
        
        node = self.topology.nodes[addr]
        x, y = addr
        
        # Get node position on canvas
        if addr in self.node_positions:
            node_x, node_y = self.node_positions[addr]
            canvas_x, canvas_y = self._transform_coords(node_x, node_y)
        else:
            canvas_x, canvas_y = mouse_x, mouse_y
        
        # Create overlay frame
        overlay_width = 300
        overlay_height = 200
        
        # Position overlay
        canvas_width = self.canvas.winfo_width()
        if canvas_x + overlay_width + 20 < canvas_width:
            overlay_x = canvas_x + 30
        else:
            overlay_x = canvas_x - overlay_width - 30
        
        overlay_y = max(10, min(canvas_y - overlay_height // 2, 
                                self.canvas.winfo_height() - overlay_height - 10))
        
        # Create frame on canvas
        overlay_frame = tk.Frame(self.canvas, bg='white', relief=tk.RAISED, bd=3)
        overlay_frame.configure(highlightbackground='#2c3e50', highlightthickness=2)
        
        # Header with close button
        header = tk.Frame(overlay_frame, bg='#2c3e50', height=40)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        # Title
        tk.Label(header, text=f"NODE ({x},{y})", 
                font=("Arial", 12, "bold"), bg='#2c3e50', fg='white').pack(side=tk.LEFT, padx=10, pady=8)
        
        # Close button
        close_btn = tk.Button(header, text="✖", command=self._close_hover_overlay,
                             bg='#e74c3c', fg='white', font=("Arial", 10, "bold"),
                             relief=tk.FLAT, cursor="hand2", padx=6, pady=2,
                             activebackground='#c0392b', bd=0)
        close_btn.pack(side=tk.RIGHT, padx=5, pady=5)
        
        # Content
        content_frame = tk.Frame(overlay_frame, bg='white')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Get real-time buffer states from actual interfaces
        try:
            send_buf = sum(len(iface.send_buffer.buffer) for iface in node.interfaces.values())
            recv_buf = sum(len(iface.receive_buffer.buffer) for iface in node.interfaces.values())
        except AttributeError:
            send_buf = recv_buf = 0
        
        # Basic info with real-time buffer states
        info_text = f"Coordinates: ({x}, {y})\n"
        info_text += f"Neighbors: {len(node.interfaces)}\n"
        info_text += f"Send Buffer: {send_buf}/4 packets\n"
        info_text += f"Recv Buffer: {recv_buf}/4 packets\n"
        info_text += f"App Buffer: {len(node.application_logic_buffer)} packets"
        
        # Add animation status with existing icons
        if self.animation_running and addr in self.current_path:
            hop_index = self.current_path.index(addr) if addr in self.current_path else -1
            if hop_index == self.current_hop:
                info_text += f"\n\n📤 Currently Processing"
            elif hop_index < self.current_hop:
                info_text += f"\n\n✅ Packet Processed"
            elif hop_index > self.current_hop:
                info_text += f"\n\n⚪ Waiting for Packet"
        
        tk.Label(content_frame, text=info_text, font=('Courier New', 9),
                bg='white', fg='#2c3e50', justify=tk.LEFT, anchor='nw').pack(fill=tk.X)
        
        # Create the overlay window on canvas
        self.hover_overlay = self.canvas.create_window(overlay_x, overlay_y, 
                                                       window=overlay_frame, anchor='nw',
                                                       tags='hover_overlay')
        self.hover_overlay_items.append(self.hover_overlay)
    
    def _close_hover_overlay(self):
        """Close the hover overlay"""
        if self.hover_overlay:
            try:
                self.canvas.delete(self.hover_overlay)
            except:
                pass
            self.hover_overlay = None
            self.hover_overlay_items.clear()
            self.hover_node = None
    
    def _highlight_selected_node(self, addr, node_type):
        """Highlight selected node temporarily"""
        if addr in self.node_items:
            if node_type == 'source':
                color = '#2e7d32'  # Green
            else:
                color = '#c62828'  # Red
            self.canvas.itemconfig(self.node_items[addr], fill=color, width=4)
    
    def on_mousewheel(self, event):
        """Handle mouse wheel zoom"""
        if event.delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()
    
    def on_mouse_press(self, event):
        """Handle mouse press for drag start"""
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        self.drag_start_pan_x = self.pan_x
        self.drag_start_pan_y = self.pan_y
        self.is_dragging = True
    
    def on_mouse_drag(self, event):
        """Handle mouse drag for panning"""
        if hasattr(self, 'is_dragging') and self.is_dragging:
            dx = event.x - self.drag_start_x
            dy = event.y - self.drag_start_y
            
            self.pan_x = self.drag_start_pan_x + dx
            self.pan_y = self.drag_start_pan_y + dy
            
            self.draw_topology()
    
    def on_mouse_release(self, event):
        """Handle mouse release for drag end"""
        self.is_dragging = False
    
    def _show_buffer_display(self, node_addr):
        """Show buffer display for a node"""
        self._hide_buffer_display()  # Clear previous display
        
        if node_addr not in self.node_positions:
            return
            
        self.buffer_display_node = node_addr
        x, y = self.node_positions[node_addr]
        cx, cy = self._transform_coords(x, y)
        
        # Get node and its interfaces
        node = self.topology.nodes.get(node_addr)
        if not node:
            return
        
        # Define buffer positions and labels
        buffer_info = [
            ('UP', cx, cy - 50, (node_addr[0], (node_addr[1] - 1) % self.height)),
            ('DOWN', cx, cy + 50, (node_addr[0], (node_addr[1] + 1) % self.height)),
            ('LEFT', cx - 50, cy, ((node_addr[0] - 1) % self.width, node_addr[1])),
            ('RIGHT', cx + 50, cy, ((node_addr[0] + 1) % self.width, node_addr[1]))
        ]
        
        for direction, bx, by, neighbor_addr in buffer_info:
            # Get interface to this neighbor
            interface = node.interfaces.get(neighbor_addr)
            if interface:
                try:
                    send_count = len(interface.send_buffer.buffer)
                    recv_count = len(interface.receive_buffer.buffer)
                except AttributeError:
                    send_count = recv_count = 0
            else:
                send_count = recv_count = 0
            
            # Use color coding for buffer status
            if send_count > 0 or recv_count > 0:
                box_color = '#ffffcc'  # Light yellow for active buffers
                text_color = '#cc6600'  # Orange text for active
            else:
                box_color = 'white'
                text_color = '#333333'
            
            # Draw buffer box
            box_item = self.canvas.create_rectangle(
                bx - 20, by - 15, bx + 20, by + 15,
                fill=box_color, outline='#333333', width=2
            )
            self.buffer_display_items.append(box_item)
            
            # Draw direction label
            dir_item = self.canvas.create_text(
                bx, by - 25, text=f"{direction} BUFFER",
                fill='#666666', font=('Arial', 8, 'bold')
            )
            self.buffer_display_items.append(dir_item)
            
            # Draw buffer counts
            count_item = self.canvas.create_text(
                bx, by, text=f"Send: {send_count}/4\nRecv: {recv_count}/4",
                fill=text_color, font=('Arial', 9, 'bold'), justify=tk.CENTER
            )
            self.buffer_display_items.append(count_item)
        
        # Draw node label
        label_item = self.canvas.create_text(
            cx, cy + 80, text=f"Node {node_addr} Buffers",
            fill='#000000', font=('Arial', 10, 'bold'), justify=tk.CENTER
        )
        self.buffer_display_items.append(label_item)
    
    def _hide_buffer_display(self):
        """Hide buffer display"""
        for item in self.buffer_display_items:
            try:
                self.canvas.delete(item)
            except:
                pass
        self.buffer_display_items.clear()
        self.buffer_display_node = None
    
    def _start_buffer_refresh(self):
        """Start periodic buffer display refresh during animation"""
        def refresh_buffers():
            if self.animation_running and self.buffer_display_node:
                self._show_buffer_display(self.buffer_display_node)
                self.root.after(500, refresh_buffers)
        
        if self.animation_running:
            refresh_buffers()
    
    def run(self):
        """Start the GUI"""
        self.root.mainloop()