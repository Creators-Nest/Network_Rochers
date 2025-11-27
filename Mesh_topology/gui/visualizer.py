"""
Mesh Topology Visualizer - White Theme with Real Packet Transfer
Features:
- White/light theme
- Status bar showing Hop, Phase, Route, Progress, Signals
- Real packet transfer simulation
- 2D grid layout for mesh topology
- Square nodes representing mesh routers
- Visual packet animation with phase indicators
"""

import tkinter as tk
from tkinter import messagebox, scrolledtext
from tkinter import ttk
import math
from collections import deque
from gui.packet_animator import PacketAnimator

class MeshVisualizer:
    def __init__(self, root, topology, simulator):
        self.root = root
        self.topology = topology
        self.simulator = simulator
        self.width = topology.width
        self.height = topology.height
        
        # WHITE THEME COLOR SCHEME
        self.colors = {
            'bg': '#ffffff',              # White background
            'panel_bg': '#f5f5f5',        # Light gray panels
            'canvas_bg': '#f8f9fa',       # Light canvas background
            'text': '#000000',            # Black text
            'text_light': '#666666',      # Gray text
            'accent': '#00ffff',          # Cyan accent
            'button': '#e0e0e0',          # Light button
            'button_text': '#000000',     # Black button text
            'highlight': '#00ff00',       # Green highlight
            'path': '#00ffff',            # Cyan path
            'node': '#4a90e2',            # Blue nodes
            'node_border': '#2c3e50',     # Dark node border for visibility
            'connection': '#b0b0b0',      # Gray connections
            'status_bg': '#e8e8e8',       # Status bar background
            'status_text': '#333333'      # Status bar text
        }
        
        # Setup main window
        self.root.title("Mesh Topology Visualizer")
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
        
        # Node selection state for click-to-select
        self.selection_mode = True  # Always in selection mode
        self.selected_source = None
        self.selected_dest = None
        self.selected_dests = []  # Multiple destinations for 1:M mode
        self.click_count = 0
        self.auto_start_timer = None  # Timer for auto-start after 5 seconds
        self.is_auto_started = False  # Track if simulation was auto-started
        
        # Transfer type: '1:1' or '1:M'
        self.transfer_type = '1:1'
        self.current_dest_index = 0  # Track which destination is being processed in 1:M
        self.transfer_results = []  # Store results for each transfer in 1:M mode
        
        # Hover state for node details modal
        self.hover_node = None
        self.hover_timer = None
        self.hover_overlay = None  # Canvas overlay instead of window
        self.hover_overlay_items = []  # Track canvas items for the overlay
        
        # Packet transfer state
        self.current_packet = None
        self.current_path = []
        self.current_hop = 0
        self.transfer_phase = "Waiting to Start"
        self.transfer_progress = 0
        self.signal_status = "Idle"
        
        # Animation speed control (milliseconds per hop)
        self.animation_speed = 1000  # Default 1 second per hop
        
        # Create UI
        self._create_status_bar()
        self._create_ui()
        
        # Packet animator for visual effects
        self.packet_animator = PacketAnimator(self.canvas)
        
        # Animation items tracking
        self.animation_items = []
        
        # Node positioning and visualization state
        self.node_positions = {}
        self.node_items = {}
        self.edge_items = {}
        self.highlighted_edges = set()
        self.highlighted_nodes = set()
        self.animation_running = False
        self.completed_path_nodes = set()  # Track nodes in completed path (turn green)
        self.path_clear_timer = None  # Timer for clearing path after completion
        self.fixed_control_x = None  # Fixed X position for control panel
        self.fixed_control_y = None  # Fixed Y position for control panel
        
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
        
        # Bottom row: Transfer details (Handshake/Buffer status) - INCREASED FONT SIZE
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
        """Update status bar with current packet transfer state and real-time details"""
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
            'Route Computed': '📍'
        }
        icon = phase_icons.get(self.transfer_phase, '⚪')
        self.phase_label.config(text=f"{icon} {self.transfer_phase}")
        
        # Update route
        if self.current_path:
            route_str = " → ".join([f"({r},{n})" for r, n in self.current_path])
            self.route_label.config(text=route_str if len(route_str) < 60 else route_str[:57] + "...")
        else:
            self.route_label.config(text="No route selected")
        
        # Update transfer details with real interface state
        if interface_state:
            details = f"REQ:{interface_state.get('req', 0)} ACK:{interface_state.get('ack', 0)} "
            details += f"| Busy:{interface_state.get('busy', 0)} Transfer:{interface_state.get('transfer', 0)} "
            details += f"| SendBuf:{interface_state.get('send_buf', '0/0')} RecvBuf:{interface_state.get('recv_buf', '0/0')}"
            self.transfer_details_label.config(text=details)
        elif self.animation_running:
            self.transfer_details_label.config(text=f"Processing transfer at {current_node or 'unknown'}")
        else:
            self.transfer_details_label.config(text="Ready for packet transfer")
        
        # Update progress with visual bar
        self.progress_label.config(text=f"{self.transfer_progress}%")
        progress_width = int(100 * (self.transfer_progress / 100))
        self.progress_canvas.coords(self.progress_bar, 0, 0, progress_width, 8)
        
        # Change progress bar color based on state
        if self.transfer_progress == 100:
            self.progress_canvas.itemconfig(self.progress_bar, fill='#27ae60')  # Green
        elif self.animation_running:
            self.progress_canvas.itemconfig(self.progress_bar, fill='#3498db')  # Blue
        else:
            self.progress_canvas.itemconfig(self.progress_bar, fill='#95a5a6')  # Gray
        
        # Update signals
        self.signals_label.config(text=self.signal_status)
        
        # Update timer (if packet exists)
        if self.current_packet:
            timer_val = self.current_packet.start_timer + self.current_hop
            self.timer_label.config(text=str(timer_val))
        else:
            self.timer_label.config(text="0")
        
        # Update hop indicator animation
        if self.animation_running:
            # Pulse animation for active transfer
            self.hop_canvas.itemconfig(self.hop_indicator, fill='#27ae60')  # Green when active
        else:
            self.hop_canvas.itemconfig(self.hop_indicator, fill='#e74c3c')  # Red when idle
    
    def _create_ui(self):
        """Create main UI layout"""
        main_container = tk.Frame(self.root, bg=self.colors['bg'])
        main_container.pack(fill=tk.BOTH, expand=True, side=tk.TOP)
        
        # Create PanedWindow to allow resizable sidebar
        self.paned_window = tk.PanedWindow(main_container, orient=tk.HORIZONTAL, 
                                           sashwidth=6, sashrelief=tk.RAISED,
                                           bg=self.colors['bg'], bd=0)
        self.paned_window.pack(fill=tk.BOTH, expand=True)
        
        # Left panel - Controls (RESIZABLE)
        self.control_panel = tk.Frame(self.paned_window, bg=self.colors['panel_bg'], width=280, relief=tk.RIDGE, bd=2)
        self.paned_window.add(self.control_panel, minsize=200, stretch="never")
        
        # Create scrollable control area with VISIBLE scrollbar
        canvas = tk.Canvas(self.control_panel, bg=self.colors['panel_bg'], highlightthickness=0)
        # Create a ttk style for visible scrollbar
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
        
        # Right panel - Canvas with overlay controls
        canvas_frame = tk.Frame(self.paned_window, bg=self.colors['bg'], relief=tk.SUNKEN, bd=2)
        self.paned_window.add(canvas_frame, minsize=400, stretch="always")
        
        self.canvas = tk.Canvas(canvas_frame, bg=self.colors['canvas_bg'], highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Create floating view controls on canvas
        self._create_floating_view_controls()
    
    def _create_section_header(self, parent, text):
        """Create section header"""
        header = tk.Label(parent, text=text, font=("Arial", 11, "bold"),
                         bg=self.colors['panel_bg'], fg='#000000')  # Changed to black
        header.pack(anchor=tk.W, padx=10, pady=(15, 5))
    
    def _create_topology_controls(self, parent):
        """Create topology configuration controls"""
        self._create_section_header(parent, "TOPOLOGY CONFIGURATION")
        
        frame = tk.Frame(parent, bg=self.colors['panel_bg'])
        frame.pack(fill=tk.X, padx=15, pady=5)
        
        tk.Label(frame, text="Mesh Width:", font=("Arial", 10),
                bg=self.colors['panel_bg'], fg=self.colors['text']
               ).pack(anchor=tk.W, pady=(0, 2))
        
        self.width_var = tk.IntVar(value=self.width)
        self.width_slider = tk.Scale(frame, from_=3, to=10, orient=tk.HORIZONTAL,
                                     variable=self.width_var,
                                     bg=self.colors['panel_bg'], fg=self.colors['text'],
                                     highlightthickness=0, troughcolor='white')
        self.width_slider.pack(fill=tk.X, pady=2)
        
        tk.Label(frame, text="Mesh Height:", font=("Arial", 10),
                bg=self.colors['panel_bg'], fg=self.colors['text']
               ).pack(anchor=tk.W, pady=(5, 2))
        
        self.height_var = tk.IntVar(value=self.height)
        self.height_slider = tk.Scale(frame, from_=3, to=10, orient=tk.HORIZONTAL,
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
        
        # Transfer Type Selection
        type_frame = tk.Frame(frame, bg='#fff3e0', relief=tk.RIDGE, bd=2)
        type_frame.pack(fill=tk.X, pady=(0, 8))
        
        tk.Label(type_frame, text="Transfer Type:", font=("Arial", 9, "bold"),
                bg='#fff3e0', fg='#e65100').pack(side=tk.LEFT, padx=8, pady=5)
        
        self.transfer_type_var = tk.StringVar(value='1:1')
        
        tk.Radiobutton(type_frame, text="1:1 (One-to-One)", variable=self.transfer_type_var,
                      value='1:1', command=self._on_transfer_type_change,
                      bg='#fff3e0', fg='#424242', font=("Arial", 8),
                      activebackground='#ffe0b2', selectcolor='white').pack(side=tk.LEFT, padx=5)
        
        tk.Radiobutton(type_frame, text="1:M (One-to-Many)", variable=self.transfer_type_var,
                      value='1:M', command=self._on_transfer_type_change,
                      bg='#fff3e0', fg='#424242', font=("Arial", 8),
                      activebackground='#ffe0b2', selectcolor='white').pack(side=tk.LEFT, padx=5)
        
        # Click-to-select instruction with live feedback
        instruction_frame = tk.Frame(frame, bg='#e3f2fd', relief=tk.RIDGE, bd=2)
        instruction_frame.pack(fill=tk.X, pady=(0, 8))
        
        self.instruction_label = tk.Label(instruction_frame, 
                text="💡 Click nodes to select:\n1st click = Source, 2nd click = Destination",
                font=("Arial", 8, "bold"), bg='#e3f2fd', fg='#1976d2',
                justify=tk.LEFT, wraplength=280)
        self.instruction_label.pack(padx=8, pady=5)
        
        # Source - Better Labels
        src_frame = tk.Frame(frame, bg='white', relief=tk.SUNKEN, bd=1)
        src_frame.pack(fill=tk.X, pady=3)
        
        src_inner = tk.Frame(src_frame, bg='white')
        src_inner.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(src_inner, text="🟢 Source Node:", font=("Arial", 9, "bold"),
                bg='white', fg='#2e7d32'
               ).pack(side=tk.LEFT)
        
        # Display selected source
        self.src_display_label = tk.Label(src_inner, text="Not selected", 
                                          font=("Courier", 9, "bold"),
                                          bg='white', fg='#999999')
        self.src_display_label.pack(side=tk.LEFT, padx=10)
        
        # Manual input
        manual_src_frame = tk.Frame(src_inner, bg='white')
        manual_src_frame.pack(side=tk.RIGHT)
        
        self.src_ring_var = tk.IntVar()
        self.src_node_var = tk.IntVar()
        
        tk.Label(manual_src_frame, text="Ring:", font=("Arial", 8),
                bg='white', fg='#666666').pack(side=tk.LEFT, padx=2)
        tk.Spinbox(manual_src_frame, from_=0, to=14, width=3, 
                  textvariable=self.src_ring_var,
                  bg='white', fg=self.colors['text'], font=("Arial", 9),
                  command=self._update_source_from_spinbox).pack(side=tk.LEFT, padx=1)
        
        tk.Label(manual_src_frame, text="Node:", font=("Arial", 8),
                bg='white', fg='#666666').pack(side=tk.LEFT, padx=(5, 2))
        tk.Spinbox(manual_src_frame, from_=0, to=31, width=3, 
                  textvariable=self.src_node_var,
                  bg='white', fg=self.colors['text'], font=("Arial", 9),
                  command=self._update_source_from_spinbox).pack(side=tk.LEFT, padx=1)
        
        # Destination - Better Labels
        dst_frame = tk.Frame(frame, bg='white', relief=tk.SUNKEN, bd=1)
        dst_frame.pack(fill=tk.X, pady=3)
        
        dst_inner = tk.Frame(dst_frame, bg='white')
        dst_inner.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(dst_inner, text="🔴 Destination Node:", font=("Arial", 9, "bold"),
                bg='white', fg='#c62828'
               ).pack(side=tk.LEFT)
        
        # Display selected destination
        self.dst_display_label = tk.Label(dst_inner, text="Not selected", 
                                          font=("Courier", 9, "bold"),
                                          bg='white', fg='#999999')
        self.dst_display_label.pack(side=tk.LEFT, padx=10)
        
        # Manual input
        manual_dst_frame = tk.Frame(dst_inner, bg='white')
        manual_dst_frame.pack(side=tk.RIGHT)
        
        self.dst_ring_var = tk.IntVar()
        self.dst_node_var = tk.IntVar()
        
        tk.Label(manual_dst_frame, text="Ring:", font=("Arial", 8),
                bg='white', fg='#666666').pack(side=tk.LEFT, padx=2)
        tk.Spinbox(manual_dst_frame, from_=0, to=14, width=3, 
                  textvariable=self.dst_ring_var,
                  bg='white', fg=self.colors['text'], font=("Arial", 9),
                  command=self._update_dest_from_spinbox).pack(side=tk.LEFT, padx=1)
        
        tk.Label(manual_dst_frame, text="Node:", font=("Arial", 8),
                bg='white', fg='#666666').pack(side=tk.LEFT, padx=(5, 2))
        tk.Spinbox(manual_dst_frame, from_=0, to=31, width=3, 
                  textvariable=self.dst_node_var,
                  bg='white', fg=self.colors['text'], font=("Arial", 9),
                  command=self._update_dest_from_spinbox).pack(side=tk.LEFT, padx=1)
    
    def _update_source_from_spinbox(self):
        """Update source display when spinbox changes"""
        ring = self.src_ring_var.get()
        node = self.src_node_var.get()
        self.selected_source = (ring, node)
        self.src_display_label.config(text=f"({ring}, {node})")
    
    def _update_dest_from_spinbox(self):
        """Update destination display when spinbox changes"""
        ring = self.dst_ring_var.get()
        node = self.dst_node_var.get()
        self.selected_dest = (ring, node)
        self.dst_display_label.config(text=f"({ring}, {node})")
    
    def _create_flow_analysis_panel(self, parent):
        """Create enhanced packet flow analysis panel WITHOUT timeline visualization"""
        self._create_section_header(parent, "PACKET FLOW ANALYSIS")
        
        frame = tk.Frame(parent, bg=self.colors['panel_bg'])
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Detailed log (text) - WHITE BACKGROUND with BLACK TEXT - INCREASED SIZE
        log_label = tk.Label(frame, text="Detailed Log:", font=("Arial", 9, "bold"),
                            bg=self.colors['panel_bg'], fg='#000000')
        log_label.pack(anchor=tk.W, pady=(0, 3))
        
        # INCREASED HEIGHT from 12 to 18, and width from 30 to 35
        self.flow_text = scrolledtext.ScrolledText(frame, height=18, width=35, wrap=tk.WORD,
                                                   font=('Courier', 8), bg='white', fg='black')
        self.flow_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure text tags for colored output
        self.flow_text.tag_config('hop', foreground='#2196F3', font=('Courier', 8, 'bold'))  # Blue
        self.flow_text.tag_config('phase', foreground='#FF9800', font=('Courier', 8, 'bold'))  # Orange
        self.flow_text.tag_config('success', foreground='#4CAF50', font=('Courier', 8, 'bold'))  # Green
        self.flow_text.tag_config('error', foreground='#f44336', font=('Courier', 8, 'bold'))  # Red
        self.flow_text.tag_config('info', foreground='#666666', font=('Courier', 8))  # Gray
        self.flow_text.tag_config('header', foreground='#9C27B0', font=('Courier', 8, 'bold'))  # Purple
        
        self._update_flow_analysis("Ready. Select source and destination, then click Animate.", clear=True)
    
    def _update_flow_analysis(self, message, clear=False, tag=None):
        """Update flow analysis text with colored tags"""
        if clear:
            self.flow_text.delete(1.0, tk.END)
        
        # Parse message to apply colors to specific patterns
        if tag:
            # Direct tag application
            self.flow_text.insert(tk.END, message + "\n", tag)
        else:
            # Smart parsing for automatic coloring
            lines = message.split('\n')
            for line in lines:
                if '===' in line or 'PACKET' in line.upper():
                    # Header lines
                    self.flow_text.insert(tk.END, line + "\n", 'header')
                elif line.strip().startswith('--- HOP'):
                    # Hop indicators
                    self.flow_text.insert(tk.END, line + "\n", 'hop')
                elif line.strip().startswith('PHASE'):
                    # Phase indicators
                    self.flow_text.insert(tk.END, line + "\n", 'phase')
                elif '✅' in line or 'DELIVERED' in line or 'complete' in line.lower():
                    # Success messages
                    self.flow_text.insert(tk.END, line + "\n", 'success')
                elif '❌' in line or 'ERROR' in line or 'FAIL' in line:
                    # Error messages
                    self.flow_text.insert(tk.END, line + "\n", 'error')
                elif line.strip().startswith('•') or line.strip().startswith('→'):
                    # Info lines
                    self.flow_text.insert(tk.END, line + "\n", 'info')
                else:
                    # Default black text
                    self.flow_text.insert(tk.END, line + "\n")
        
        self.flow_text.see(tk.END)
    
    def _on_speed_change(self, value):
        """Handle speed slider change"""
        self.animation_speed = int(value)
        # Update both speed labels if they exist
        if hasattr(self, 'speed_label_sim'):
            self.speed_label_sim.config(text=f"{int(value)} ms")
        # Sync entry field
        if hasattr(self, 'speed_entry'):
            self.speed_entry.delete(0, tk.END)
            self.speed_entry.insert(0, str(int(value)))
    
    def _on_speed_entry_change(self, event=None):
        """Handle speed entry field change"""
        try:
            value = int(self.speed_entry.get())
            # Clamp value to valid range
            value = max(200, min(8000, value))
            
            # Update animation speed
            self.animation_speed = value
            
            # Sync slider
            self.speed_var.set(value)
            
            # Update label
            if hasattr(self, 'speed_label_sim'):
                self.speed_label_sim.config(text=f"{value} ms")
            
            # Update entry field in case it was clamped
            self.speed_entry.delete(0, tk.END)
            self.speed_entry.insert(0, str(value))
            
        except ValueError:
            # Invalid input, reset to current value
            self.speed_entry.delete(0, tk.END)
            self.speed_entry.insert(0, str(self.animation_speed))
    
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
        
        # Reduced width slider (from 150 to 60)
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
        
        # Bind entry field to update speed when user types
        self.speed_entry.bind('<Return>', self._on_speed_entry_change)
        self.speed_entry.bind('<FocusOut>', self._on_speed_entry_change)
        
        tk.Label(speed_control_frame, text="ms", font=("Arial", 8),
                bg=self.colors['panel_bg'], fg=self.colors['text']
               ).pack(side=tk.LEFT, padx=1)
        
        self.speed_label_sim = tk.Label(speed_frame, text="1000 ms", font=("Arial", 7),
                                        bg=self.colors['panel_bg'], fg=self.colors['text'])
        self.speed_label_sim.pack(anchor=tk.CENTER, pady=1)
        
        # Control Buttons - INLINE (Horizontal)
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
    
    def _update_simulation_details(self):
        """Update simulation controls - sync button states"""
        # Sync both animate buttons
        if hasattr(self, 'animate_button') and hasattr(self, 'animate_button_sim'):
            button_text = self.animate_button.cget('text')
            self.animate_button_sim.config(text=button_text)
        
        # Update speed label and sync entry field
        if hasattr(self, 'speed_label_sim'):
            self.speed_label_sim.config(text=f"{self.animation_speed} ms")
        if hasattr(self, 'speed_entry'):
            self.speed_entry.delete(0, tk.END)
            self.speed_entry.insert(0, str(self.animation_speed))
    
    def _create_floating_view_controls(self):
        """Create floating view controls on canvas (like map controls) - TOP RIGHT CORNER"""
        # Create a more visible control frame
        control_frame = tk.Frame(self.canvas, bg='#f0f0f0', relief=tk.RAISED, bd=3)
        
        # Zoom and reset buttons - more visible design
        zoom_frame = tk.Frame(control_frame, bg='#f0f0f0')
        zoom_frame.pack(padx=5, pady=5)
        
        # Reset button (Home icon)
        tk.Button(zoom_frame, text="🏠", command=self.reset_view,
                 bg='#4CAF50', fg='white', font=("Arial", 14, "bold"),
                 width=3, height=1, relief=tk.RAISED, cursor="hand2",
                 activebackground='#45a049').pack(pady=2)
        
        # + button (Zoom In)
        tk.Button(zoom_frame, text="+", command=self.zoom_in,
                 bg='#2196F3', fg='white', font=("Arial", 16, "bold"),
                 width=3, height=1, relief=tk.RAISED, cursor="hand2",
                 activebackground='#1976D2').pack(pady=2)
        
        # - button (Zoom Out)
        tk.Button(zoom_frame, text="−", command=self.zoom_out,
                 bg='#2196F3', fg='white', font=("Arial", 16, "bold"),
                 width=3, height=1, relief=tk.RAISED, cursor="hand2",
                 activebackground='#1976D2').pack(pady=2)
        
        # Position the control frame in top-right corner with proper anchor
        self.floating_controls = self.canvas.create_window(0, 0, window=control_frame, anchor='nw', tags='floating_controls')
        
        # Update position ONLY on canvas resize, NOT on zoom
        def update_position(event=None):
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            if canvas_width > 1 and canvas_height > 1:
                # Position controls in top-right corner, accounting for control frame size
                control_width = control_frame.winfo_reqwidth() or 60  # fallback width
                x_pos = canvas_width - control_width - 10  # 10px margin from right edge
                y_pos = 10  # 10px from top edge
                # Store fixed position
                self.fixed_control_x = x_pos
                self.fixed_control_y = y_pos
                self.canvas.coords(self.floating_controls, x_pos, y_pos)
        
        # Only bind to Configure event (resize), not draw_topology
        self.canvas.bind('<Configure>', update_position)
        # Initial positioning after canvas is ready
        self.root.after(200, update_position)
        
        # Make draggable for trackpad compatibility
        self._make_draggable(control_frame)
    def _make_draggable(self, widget):
        """Make widget draggable for trackpad compatibility"""
        widget._drag_data = {"x": 0, "y": 0}
        
        def on_press(event):
            widget._drag_data["x"] = event.x
            widget._drag_data["y"] = event.y
        
        def on_drag(event):
            # Calculate movement
            dx = event.x - widget._drag_data["x"]
            dy = event.y - widget._drag_data["y"]
            
            # Get current position
            x, y = self.canvas.coords(self.floating_controls)
            
            # Move the window
            self.canvas.coords(self.floating_controls, x + dx, y + dy)
        
        widget.bind("<Button-1>", on_press)
        widget.bind("<B1-Motion>", on_drag)
    
    def _create_view_controls(self, parent):
        """This method is no longer used - view controls are now floating"""
        pass
    
    def _bind_events(self):
        """Bind keyboard and mouse events"""
        # Use ButtonPress for drag detection, ButtonRelease for click detection
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_press)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_release)
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)
        self.canvas.bind("<Motion>", self.on_mouse_motion)  # For cursor feedback
        # Hover window removed - no longer showing node info on hover
        
        self.root.bind("<Control-plus>", lambda e: self.zoom_in())
        self.root.bind("<Control-minus>", lambda e: self.zoom_out())
        self.root.bind("<Control-0>", lambda e: self.reset_view())
        self.root.bind("<Escape>", lambda e: self.clear_highlights())
    
    def on_mouse_press(self, event):
        """Handle mouse press for drag start"""
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        self.drag_start_pan_x = self.pan_x
        self.drag_start_pan_y = self.pan_y
        self.is_dragging = False  # Will be set to True if mouse moves
    
    def on_mouse_drag(self, event):
        """Handle mouse drag for panning"""
        if hasattr(self, 'drag_start_x'):
            # Calculate drag distance
            dx = event.x - self.drag_start_x
            dy = event.y - self.drag_start_y
            
            # Only start dragging if moved more than 5 pixels (prevents accidental drag)
            if abs(dx) > 5 or abs(dy) > 5:
                self.is_dragging = True
                
                # Update pan position
                self.pan_x = self.drag_start_pan_x + dx
                self.pan_y = self.drag_start_pan_y + dy
                
                # Redraw topology with new pan position
                self.draw_topology()
    
    def on_mouse_release(self, event):
        """Handle mouse release - if not dragging, treat as click for node selection"""
        # If not dragging (or minimal drag), treat as a click for node selection
        if not self.is_dragging:
            self.on_canvas_click(event)
        
        self.is_dragging = False
    
    def on_mouse_motion(self, event):
        """Handle mouse motion for cursor feedback, node highlighting, and edge hover"""
        # Find node under cursor
        hovered_node = None
        for addr, item_id in self.node_items.items():
            coords = self.canvas.coords(item_id)
            if coords:
                x1, y1, x2, y2 = coords
                cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
                dist = math.sqrt((event.x - cx)**2 + (event.y - cy)**2)
                
                # Scale hover detection radius with zoom level
                hover_radius = max(15, 12 * self.zoom_level + 5)
                if dist < hover_radius:
                    hovered_node = addr
                    break
        
        # Check for edge hover (only if not hovering over a node)
        hovered_edge = None
        if not hovered_node:
            # Check all edges
            for edge_key, line_id in self.edge_items.items():
                coords = self.canvas.coords(line_id)
                if coords and len(coords) == 4:
                    x1, y1, x2, y2 = coords
                    dist = self._point_to_line_distance(event.x, event.y, x1, y1, x2, y2)
                    # Hover threshold for edges (scaled with zoom)
                    edge_threshold = max(8, 6 * self.zoom_level)
                    if dist < edge_threshold:
                        hovered_edge = edge_key
                        break
        
        # Update cursor based on what's being hovered
        if hovered_node:
            self.canvas.config(cursor="hand2")  # Pointing hand cursor for nodes
            # Cancel any edge hover timer
            if hasattr(self, '_edge_hover_timer') and self._edge_hover_timer:
                self.root.after_cancel(self._edge_hover_timer)
                self._edge_hover_timer = None
            # Close any interface popup
            self._close_interface_popup()
            
            # Highlight the node being hovered (if not already selected)
            if hovered_node != self.selected_source and hovered_node != self.selected_dest:
                if hovered_node in self.node_items:
                    self.canvas.itemconfig(self.node_items[hovered_node], width=3)
        
        elif hovered_edge:
            self.canvas.config(cursor="crosshair")  # Crosshair cursor for edges
            
            # If hovering over a new edge, start timer
            if not hasattr(self, '_current_hovered_edge') or self._current_hovered_edge != hovered_edge:
                # Cancel previous timer
                if hasattr(self, '_edge_hover_timer') and self._edge_hover_timer:
                    self.root.after_cancel(self._edge_hover_timer)
                
                # Store current edge and mouse position
                self._current_hovered_edge = hovered_edge
                self._hover_mouse_x = event.x
                self._hover_mouse_y = event.y
                
                # Start 2-second timer
                self._edge_hover_timer = self.root.after(2000, 
                    lambda: self._show_interface_info(hovered_edge, event.x, event.y))
            else:
                # Update mouse position for popup placement
                self._hover_mouse_x = event.x
                self._hover_mouse_y = event.y
        
        else:
            self.canvas.config(cursor="")  # Default cursor
            # Cancel edge hover timer
            if hasattr(self, '_edge_hover_timer') and self._edge_hover_timer:
                self.root.after_cancel(self._edge_hover_timer)
                self._edge_hover_timer = None
            self._current_hovered_edge = None
            # Close interface popup when not hovering
            self._close_interface_popup()
        
        # Reset previously hovered nodes (except selected ones)
        if hasattr(self, '_last_hovered_node') and self._last_hovered_node != hovered_node:
            if (self._last_hovered_node and 
                self._last_hovered_node != self.selected_source and 
                self._last_hovered_node != self.selected_dest and
                self._last_hovered_node in self.node_items):
                self.canvas.itemconfig(self.node_items[self._last_hovered_node], width=2)
        
        self._last_hovered_node = hovered_node
    
    def _point_to_line_distance(self, px, py, x1, y1, x2, y2):
        """Calculate perpendicular distance from point (px, py) to line segment (x1,y1)-(x2,y2)"""
        # Vector from line start to point
        dx = x2 - x1
        dy = y2 - y1
        if dx == 0 and dy == 0:
            # Line segment is actually a point
            return math.sqrt((px - x1)**2 + (py - y1)**2)
        
        # Parameter t for closest point on line
        t = ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)
        t = max(0, min(1, t))  # Clamp to line segment
        
        # Closest point on line segment
        closest_x = x1 + t * dx
        closest_y = y1 + t * dy
        
        # Distance from point to closest point
        return math.sqrt((px - closest_x)**2 + (py - closest_y)**2)
    
    def _show_interface_info(self, edge, mouse_x, mouse_y):
        """Show comprehensive interface diagram popup for an edge after 2 second hover"""
        # Close any existing interface popup
        if hasattr(self, '_interface_popup') and self._interface_popup:
            try:
                self.canvas.delete(self._interface_popup)
            except:
                pass
        
        # Get the two nodes from the edge
        node1_addr, node2_addr = edge
        
        # Get interface from node1 to node2
        if node1_addr in self.topology.nodes and node2_addr in self.topology.nodes[node1_addr].interfaces:
            node = self.topology.nodes[node1_addr]
            interface = node.interfaces[node2_addr]
            
            # Create popup frame with border
            popup_frame = tk.Frame(self.canvas, bg='black', relief=tk.RAISED, bd=2)
            
            # Inner frame
            inner_frame = tk.Frame(popup_frame, bg='white', bd=1)
            inner_frame.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
            
            # Title with close button
            header = tk.Frame(inner_frame, bg='#34495e', height=28)
            header.pack(fill=tk.X)
            header.pack_propagate(False)
            
            tk.Label(header, text=f"Interface: {node1_addr} ↔ {node2_addr}",
                    font=("Arial", 9, "bold"), bg='#34495e', fg='white').pack(side=tk.LEFT, padx=8, pady=4)
            
            close_btn = tk.Button(header, text="✖", command=self._close_interface_popup,
                                 bg='#e74c3c', fg='white', font=("Arial", 7, "bold"),
                                 relief=tk.FLAT, cursor="hand2", padx=3, pady=0,
                                 activebackground='#c0392b', bd=0)
            close_btn.pack(side=tk.RIGHT, padx=4)
            
            # Main content area
            content = tk.Frame(inner_frame, bg='white')
            content.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
            
            # Top section - Pins and Bits
            self._draw_interface_pins_section(content, interface)
            
            # Middle section - Logic blocks
            self._draw_interface_logic_section(content)
            
            # Bottom section - Buffers and Registers
            self._draw_interface_buffers_section(content, interface)
            
            # Position popup near mouse
            popup_x = min(mouse_x + 15, self.canvas.winfo_width() - 350)
            popup_y = min(mouse_y + 15, self.canvas.winfo_height() - 300)
            
            self._interface_popup = self.canvas.create_window(popup_x, popup_y,
                                                              window=popup_frame, anchor='nw',
                                                              tags='interface_popup')
    
    def _draw_interface_pins_section(self, parent, interface):
        """Draw the top section with pins and status bits"""
        pins_frame = tk.Frame(parent, bg='white')
        pins_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Top pins row
        top_row = tk.Frame(pins_frame, bg='white')
        top_row.pack(fill=tk.X)
        
        pins = [
            ("REQ", interface.pin_REQ),
            ("ACK", interface.pin_ACK),
            ("DATA", interface.pin_DATA is not None),
            ("CLK", True),  # Always active
            ("Choke", interface.pin_CHOKE)
        ]
        
        for pin_name, pin_status in pins:
            pin_frame = tk.Frame(top_row, bg='#ecf0f1', relief=tk.RAISED, bd=1)
            pin_frame.pack(side=tk.LEFT, padx=2)
            
            # Pin indicator (filled circle if active)
            indicator = tk.Canvas(pin_frame, width=10, height=10, bg='#ecf0f1', highlightthickness=0)
            indicator.pack(pady=2)
            color = '#2ecc71' if pin_status else '#95a5a6'
            indicator.create_oval(2, 2, 8, 8, fill=color, outline='#34495e')
            
            tk.Label(pin_frame, text=pin_name, font=("Arial", 7, "bold"),
                    bg='#ecf0f1', fg='#2c3e50').pack(pady=1, padx=4)
        
        # Side status bits
        sides_frame = tk.Frame(pins_frame, bg='white')
        sides_frame.pack(fill=tk.X, pady=3)
        
        # Left side - Receive Bit
        left_bit = tk.Frame(sides_frame, bg='#dfe6e9', relief=tk.RAISED, bd=1)
        left_bit.pack(side=tk.LEFT, padx=2)
        tk.Label(left_bit, text="● Receive Bit" if interface.bit_Receive else "○ Receive Bit",
                font=("Arial", 7), bg='#dfe6e9', fg='#2ecc71' if interface.bit_Receive else '#95a5a6').pack(padx=4, pady=2)
        
        # Right side - Transfer Bit and Busy Bit
        right_bits = tk.Frame(sides_frame, bg='white')
        right_bits.pack(side=tk.RIGHT)
        
        transfer_bit = tk.Frame(right_bits, bg='#dfe6e9', relief=tk.RAISED, bd=1)
        transfer_bit.pack(side=tk.LEFT, padx=2)
        tk.Label(transfer_bit, text="● Transfer Bit" if interface.bit_Transfer else "○ Transfer Bit",
                font=("Arial", 7), bg='#dfe6e9', fg='#3498db' if interface.bit_Transfer else '#95a5a6').pack(padx=4, pady=2)
        
        busy_bit = tk.Frame(right_bits, bg='#dfe6e9', relief=tk.RAISED, bd=1)
        busy_bit.pack(side=tk.LEFT, padx=2)
        tk.Label(busy_bit, text="● Busy Bit" if interface.bit_Busy else "○ Busy Bit",
                font=("Arial", 7), bg='#dfe6e9', fg='#e74c3c' if interface.bit_Busy else '#95a5a6').pack(padx=4, pady=2)
    
    def _draw_interface_logic_section(self, parent):
        """Draw the middle section with logic blocks"""
        logic_frame = tk.Frame(parent, bg='white')
        logic_frame.pack(fill=tk.X, pady=5)
        
        logic_blocks = ["Routing\nLogic", "Application\nLogic", "Control\nLogic"]
        
        for i, block_name in enumerate(logic_blocks):
            block = tk.Frame(logic_frame, bg='#ecf0f1', relief=tk.RAISED, bd=2)
            block.pack(side=tk.LEFT, padx=4, expand=True, fill=tk.BOTH)
            
            # Hexagon-like shape label
            tk.Label(block, text=block_name, font=("Arial", 7, "bold"),
                    bg='#ecf0f1', fg='#2c3e50', justify=tk.CENTER).pack(pady=8, padx=8)
    
    def _draw_interface_buffers_section(self, parent, interface):
        """Draw the bottom section with buffers and registers"""
        buffers_frame = tk.Frame(parent, bg='white')
        buffers_frame.pack(fill=tk.X, pady=5)
        
        # Left buffer (circular representation)
        left_buffer = tk.Frame(buffers_frame, bg='white')
        left_buffer.pack(side=tk.LEFT, padx=5)
        
        self._draw_circular_buffer(left_buffer, "Send Buffer", 
                                   len(interface.send_buffer.buffer),
                                   interface.send_buffer.buffer.maxlen)
        
        # Center - Registers
        registers = tk.Frame(buffers_frame, bg='white')
        registers.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=8)
        
        # Send Register
        send_reg = tk.Frame(registers, bg='#ecf0f1', relief=tk.SUNKEN, bd=1)
        send_reg.pack(fill=tk.X, pady=2)
        reg_data = "Empty" if interface.send_register is None else f"Packet"
        tk.Label(send_reg, text=f"Send Register: {reg_data}", font=("Arial", 7),
                bg='#ecf0f1', fg='#2c3e50').pack(pady=4, padx=8)
        
        # Receive Register
        recv_reg = tk.Frame(registers, bg='#ecf0f1', relief=tk.SUNKEN, bd=1)
        recv_reg.pack(fill=tk.X, pady=2)
        reg_data = "Empty" if interface.receive_register is None else f"Packet"
        tk.Label(recv_reg, text=f"Receive Register: {reg_data}", font=("Arial", 7),
                bg='#ecf0f1', fg='#2c3e50').pack(pady=4, padx=8)
        
        # Right buffer (circular representation)
        right_buffer = tk.Frame(buffers_frame, bg='white')
        right_buffer.pack(side=tk.RIGHT, padx=5)
        
        self._draw_circular_buffer(right_buffer, "Receive Buffer",
                                   len(interface.receive_buffer.buffer),
                                   interface.receive_buffer.buffer.maxlen)
    
    def _draw_circular_buffer(self, parent, label, used, total):
        """Draw a circular buffer representation"""
        frame = tk.Frame(parent, bg='white')
        frame.pack()
        
        # Label
        tk.Label(frame, text=label, font=("Arial", 6, "bold"),
                bg='white', fg='#2c3e50').pack()
        
        # Circular representation
        canvas = tk.Canvas(frame, width=50, height=50, bg='white', highlightthickness=0)
        canvas.pack()
        
        # Draw circle
        canvas.create_oval(5, 5, 45, 45, outline='#34495e', width=2)
        
        # Draw segments (4 segments for 4-slot buffer)
        segments = total
        for i in range(segments):
            angle1 = i * (360 / segments) - 90
            angle2 = (i + 1) * (360 / segments) - 90
            
            # Filled if used
            if i < used:
                # Draw filled segment
                import math
                x1 = 25 + 18 * math.cos(math.radians(angle1))
                y1 = 25 + 18 * math.sin(math.radians(angle1))
                x2 = 25 + 18 * math.cos(math.radians(angle2))
                y2 = 25 + 18 * math.sin(math.radians(angle2))
                
                canvas.create_arc(7, 7, 43, 43, start=angle1, extent=(360/segments),
                                 fill='#3498db', outline='#2c3e50', width=1)
            
            # Draw segment divider lines
            x_outer = 25 + 20 * math.cos(math.radians(angle1))
            y_outer = 25 + 20 * math.sin(math.radians(angle1))
            x_inner = 25 + 15 * math.cos(math.radians(angle1))
            y_inner = 25 + 15 * math.sin(math.radians(angle1))
            canvas.create_line(x_inner, y_inner, x_outer, y_outer, fill='#34495e', width=1)
        
        # Center text
        tk.Label(frame, text=f"{used}/{total}", font=("Arial", 7, "bold"),
                bg='white', fg='#2c3e50').pack()
    
    def _close_interface_popup(self):
        """Close the interface popup and cancel any hover timers"""
        if hasattr(self, '_interface_popup') and self._interface_popup:
            try:
                self.canvas.delete(self._interface_popup)
            except:
                pass
            self._interface_popup = None
        
        # Cancel edge hover timer
        if hasattr(self, '_edge_hover_timer') and self._edge_hover_timer:
            self.root.after_cancel(self._edge_hover_timer)
            self._edge_hover_timer = None
        
        self._current_hovered_edge = None
    
    def draw_topology(self):
        """Draw the complete mesh topology"""
        # Delete all canvas items EXCEPT floating controls and hover overlay
        for item in self.canvas.find_all():
            tags = self.canvas.gettags(item)
            if 'floating_controls' not in tags and 'hover_overlay' not in tags:
                self.canvas.delete(item)
        
        self.node_positions.clear()
        self.node_items.clear()
        self.edge_items.clear()
        
        self._calculate_positions_grid()
        
        self._draw_grid_lines()    # Draw grid lines FIRST
        self._draw_connections()   # Then mesh connections
        self._draw_nodes()          # Finally square nodes on top
        
        # Ensure floating controls are properly positioned after redraw
        if hasattr(self, 'floating_controls') and self.floating_controls:
            try:
                canvas_width = self.canvas.winfo_width()
                if canvas_width > 1:
                    control_width = 60  # fallback width
                    x_pos = canvas_width - control_width - 10
                    y_pos = 10
                    self.canvas.coords(self.floating_controls, x_pos, y_pos)
            except:
                pass
    
    def _calculate_positions_grid(self):
        """Calculate node positions in a 2D grid layout for mesh topology"""
        canvas_width = self.canvas.winfo_width() or 800
        canvas_height = self.canvas.winfo_height() or 600
        
        # Calculate spacing for grid
        margin = 80  # Margin from edges
        usable_width = canvas_width - 2 * margin
        usable_height = canvas_height - 2 * margin
        
        spacing_x = usable_width / max(1, self.width - 1) if self.width > 1 else usable_width / 2
        spacing_y = usable_height / max(1, self.height - 1) if self.height > 1 else usable_height / 2
        
        # Place nodes in grid
        for x in range(self.width):
            for y in range(self.height):
                px = margin + x * spacing_x
                py = margin + y * spacing_y
                self.node_positions[(x, y)] = (px, py)
    
    def _draw_grid_lines(self):
        """Draw grid lines to show mesh structure"""
        # Draw vertical lines
        for x in range(self.width):
            if (0, 0) in self.node_positions and (x, 0) in self.node_positions:
                x1, y1 = self.node_positions[(x, 0)]
                x2, y2 = self.node_positions[(x, self.height - 1)]
                cx1, cy1 = self._transform_coords(x1, y1)
                cx2, cy2 = self._transform_coords(x2, y2)
                self.canvas.create_line(cx1, cy1, cx2, cy2, 
                                       fill='#e0e0e0', width=1, dash=(2, 2), tags='grid_line')
        
        # Draw horizontal lines
        for y in range(self.height):
            if (0, y) in self.node_positions and (self.width - 1, y) in self.node_positions:
                x1, y1 = self.node_positions[(0, y)]
                x2, y2 = self.node_positions[(self.width - 1, y)]
                cx1, cy1 = self._transform_coords(x1, y1)
                cx2, cy2 = self._transform_coords(x2, y2)
                self.canvas.create_line(cx1, cy1, cx2, cy2, 
                                       fill='#e0e0e0', width=1, dash=(2, 2), tags='grid_line')
    
    def _draw_connections(self):
        """Draw mesh connections (N, S, E, W neighbors)"""
        drawn = set()
        for addr, node in self.topology.nodes.items():
            for neighbor_addr in node.interfaces.keys():
                edge = tuple(sorted([addr, neighbor_addr]))
                if edge not in drawn and addr in self.node_positions and neighbor_addr in self.node_positions:
                    x1, y1 = self.node_positions[addr]
                    x2, y2 = self.node_positions[neighbor_addr]
                    
                    cx1, cy1 = self._transform_coords(x1, y1)
                    cx2, cy2 = self._transform_coords(x2, y2)
                    
                    # Use proper connection color from theme
                    color = self.colors['connection']
                    width = 2
                    if edge in self.highlighted_edges:
                        color = self.colors['path']
                        width = 4
                    
                    line_id = self.canvas.create_line(cx1, cy1, cx2, cy2, fill=color, width=width)
                    self.edge_items[edge] = line_id
                    drawn.add(edge)
    
    def _draw_nodes(self):
        """Draw nodes as squares (mesh style)"""
        for addr, (x, y) in self.node_positions.items():
            cx, cy = self._transform_coords(x, y)
            
            color = self.colors['node']
            if addr in self.highlighted_nodes:
                color = self.colors['highlight']
            
            # Ensure minimum visible size for square nodes
            size = max(10, 15 * self.zoom_level)  # Minimum 10 pixels half-size
            node_id = self.canvas.create_rectangle(
                cx - size, cy - size, 
                cx + size, cy + size, 
                fill=color, outline=self.colors['node_border'], width=2
            )
            
            x_coord, y_coord = addr
            label = f"({x_coord},{y_coord})"
            # Adjust text position based on zoom level for better visibility
            text_offset = max(22, size + 16)  # Minimum 22 pixels offset
            text_id = self.canvas.create_text(cx, cy - text_offset, text=label, 
                                             fill='#2c3e50', font=("Arial", 9, "bold"))
            
            self.node_items[addr] = node_id
    
    def _transform_coords(self, x, y):
        """Transform coordinates with zoom and pan"""
        return (x * self.zoom_level + self.pan_x, 
                y * self.zoom_level + self.pan_y)
    
    def on_canvas_click(self, event):
        """Handle canvas click for node selection or info display"""
        # Check if clicking on a node
        clicked_node = None
        for addr, item_id in self.node_items.items():
            coords = self.canvas.coords(item_id)
            if coords:
                x1, y1, x2, y2 = coords
                cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
                dist = math.sqrt((event.x - cx)**2 + (event.y - cy)**2)
                
                # Scale click detection radius with zoom level (minimum 15 pixels)
                click_radius = max(15, 12 * self.zoom_level + 5)  # Node radius + 5 pixel margin
                if dist < click_radius:
                    clicked_node = addr
                    break
        
        if clicked_node is None:
            return
        
        # Click-to-select mode
        R, Nr = clicked_node
        
        if self.click_count == 0:
            # First click - set source - clear any previous simulation
            self._clear_previous_simulation()
            
            self.selected_source = clicked_node
            self.selected_dests = []  # Reset destinations list
            self.src_ring_var.set(R)
            self.src_node_var.set(Nr)
            self.src_display_label.config(text=f"({R}, {Nr})", fg='#1565c0')
            self.click_count = 1
            
            # Visual feedback only - no popup
            self._highlight_selected_node(clicked_node, 'source')
            
            # Update instruction label based on transfer type
            if hasattr(self, 'instruction_label'):
                if self.transfer_type == '1:1':
                    self.instruction_label.config(text="✓ Source selected. Click another node for destination.", fg='#2e7d32')
                else:  # 1:M
                    self.instruction_label.config(text="✓ Source selected. Click nodes for destinations (Click source again to finish).", fg='#2e7d32')
            
        else:
            # Subsequent clicks - set destination(s)
            if clicked_node == self.selected_source:
                # For 1:M mode, clicking source again means done selecting destinations
                if self.transfer_type == '1:M' and len(self.selected_dests) > 0:
                    self._start_multicast_simulation()
                else:
                    if hasattr(self, 'instruction_label'):
                        self.instruction_label.config(text="⚠ Destination cannot be same as source. Choose different node.", fg='#c62828')
                return
            
            # Check if already selected as destination
            if clicked_node in self.selected_dests:
                if hasattr(self, 'instruction_label'):
                    self.instruction_label.config(text="⚠ Node already selected as destination. Choose different node.", fg='#c62828')
                return
            
            if self.transfer_type == '1:1':
                # Single destination mode
                self.selected_dest = clicked_node
                self.selected_dests = [clicked_node]
                self.dst_ring_var.set(R)
                self.dst_node_var.set(Nr)
                self.dst_display_label.config(text=f"({R}, {Nr})", fg='#c62828')
                self.click_count = 0
                
                # Visual feedback
                self._highlight_selected_node(clicked_node, 'dest')
                if hasattr(self, 'instruction_label'):
                    self.instruction_label.config(text="✓ Destination selected. Simulation starting in 5 seconds...", fg='#1565c0')
                
                # Auto-start simulation after 5 seconds
                if self.auto_start_timer:
                    self.root.after_cancel(self.auto_start_timer)
                
                def auto_start_sim():
                    self.is_auto_started = True
                    self.animate_routing()
                
                self.auto_start_timer = self.root.after(5000, auto_start_sim)
                self.root.after(2000, self.clear_highlights)
                
            else:  # 1:M mode
                # Multiple destinations mode
                self.selected_dests.append(clicked_node)
                self._highlight_selected_node(clicked_node, 'dest')
                
                # Update display
                dest_text = ", ".join([f"({d[0]},{d[1]})" for d in self.selected_dests])
                self.dst_display_label.config(text=dest_text if len(dest_text) < 30 else f"{len(self.selected_dests)} nodes", fg='#c62828')
                
                if hasattr(self, 'instruction_label'):
                    self.instruction_label.config(
                        text=f"✓ {len(self.selected_dests)} destination(s) selected. Click source to start or more nodes.", 
                        fg='#2e7d32'
                    )
    
    def on_canvas_hover(self, event):
        """Handle canvas hover for node details display with 500ms delay"""
        # Find node under cursor
        hovered_node = None
        for addr, item_id in self.node_items.items():
            coords = self.canvas.coords(item_id)
            if coords:
                x1, y1, x2, y2 = coords
                cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
                dist = math.sqrt((event.x - cx)**2 + (event.y - cy)**2)
                
                # Scale hover detection radius with zoom level (same as click detection)
                hover_radius = max(15, 12 * self.zoom_level + 5)
                if dist < hover_radius:
                    hovered_node = addr
                    break
        
        # If hovering over a different node or moved away
        if hovered_node != self.hover_node:
            # Cancel existing timer
            if self.hover_timer:
                self.root.after_cancel(self.hover_timer)
                self.hover_timer = None
            
            # Close existing hover overlay
            if self.hover_overlay and hovered_node is None:
                self._close_hover_overlay()
            
            # Update hover node
            self.hover_node = hovered_node
            
            # Start new timer if hovering over a node (reduced to 500ms)
            if hovered_node:
                self.hover_timer = self.root.after(500, lambda: self._show_hover_node_info(hovered_node, event.x, event.y))
    
    def _show_hover_node_info(self, addr, mouse_x, mouse_y):
        """Show detailed node information in a canvas overlay (non-modal, stays until closed)"""
        if self.hover_node != addr:
            return  # Node changed, don't show
        
        # Close existing hover overlay
        if self.hover_overlay:
            self._close_hover_overlay()
        
        # Create canvas overlay near the node
        node = self.topology.nodes[addr]
        R, Nr = addr
        
        # Get node position on canvas
        if addr in self.node_positions:
            node_x, node_y = self.node_positions[addr]
            canvas_x, canvas_y = self._transform_coords(node_x, node_y)
        else:
            canvas_x, canvas_y = mouse_x, mouse_y
        
        # Create overlay frame
        overlay_width = 350
        overlay_height = 400
        
        # Position overlay to the right of the node, or left if too close to edge
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
        tk.Label(header, text=f"NODE ({R},{Nr})", 
                font=("Arial", 12, "bold"), bg='#2c3e50', fg='white').pack(side=tk.LEFT, padx=10, pady=8)
        
        # Close button
        close_btn = tk.Button(header, text="✖", command=self._close_hover_overlay,
                             bg='#e74c3c', fg='white', font=("Arial", 10, "bold"),
                             relief=tk.FLAT, cursor="hand2", padx=6, pady=2,
                             activebackground='#c0392b', bd=0)
        close_btn.pack(side=tk.RIGHT, padx=5, pady=5)
        
        # Content area with scrollbar
        content_container = tk.Frame(overlay_frame, bg='white')
        content_container.pack(fill=tk.BOTH, expand=True)
        
        canvas_inner = tk.Canvas(content_container, bg='white', highlightthickness=0, 
                                height=overlay_height - 50, width=overlay_width - 20)
        scrollbar = tk.Scrollbar(content_container, orient=tk.VERTICAL, command=canvas_inner.yview)
        scrollable_content = tk.Frame(canvas_inner, bg='white')
        
        scrollable_content.bind("<Configure>", 
            lambda e: canvas_inner.configure(scrollregion=canvas_inner.bbox("all")))
        
        canvas_inner.create_window((0, 0), window=scrollable_content, anchor="nw")
        canvas_inner.configure(yscrollcommand=scrollbar.set)
        
        canvas_inner.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add node information sections (compact version)
        self._add_compact_info_section(scrollable_content, "📊 Basic Info", 
                                      self._format_basic_info_compact(node, addr), '#e8f4f8')
        
        self._add_compact_info_section(scrollable_content, "🔗 Connections", 
                                      self._format_neighbors_compact(node, addr), '#f4f6f7')
        
        self._add_compact_info_section(scrollable_content, "📦 Buffers", 
                                      self._format_buffer_compact(node), '#fff3e0')
        
        if self.current_packet and addr in self.current_path:
            self._add_compact_info_section(scrollable_content, "🎯 Routing", 
                                          self._format_packet_routing_compact(addr), '#fce4ec')
        
        # Create the overlay window on canvas
        self.hover_overlay = self.canvas.create_window(overlay_x, overlay_y, 
                                                       window=overlay_frame, anchor='nw',
                                                       tags='hover_overlay')
        self.hover_overlay_items.append(self.hover_overlay)
        
        # Make overlay draggable
        self._make_overlay_draggable(overlay_frame)
    
    def _add_compact_info_section(self, parent, title, content, bg_color):
        """Create a compact information section for the overlay"""
        section = tk.Frame(parent, bg=bg_color, relief=tk.FLAT, bd=1)
        section.pack(fill=tk.X, padx=5, pady=3)
        
        # Title
        tk.Label(section, text=title, font=("Arial", 9, "bold"),
                bg=bg_color, fg='#2c3e50', anchor='w').pack(fill=tk.X, padx=8, pady=3)
        
        # Content
        tk.Label(section, text=content, font=('Courier New', 8),
                bg='white', fg='#2c3e50', justify=tk.LEFT, 
                anchor='nw').pack(fill=tk.X, padx=8, pady=3)
    
    def _format_basic_info_compact(self, node, addr):
        """Format basic node information (compact)"""
        R, Nr = addr
        return f"Ring: {R} | Pos: {Nr} | Size: {2**R}\nConnections: {len(node.interfaces)}"
    
    def _format_neighbors_compact(self, node, addr):
        """Format neighbors information (compact)"""
        R, Nr = addr
        ring_neighbors = [n for n in node.interfaces.keys() if n[0] == R]
        tree_neighbors = [n for n in node.interfaces.keys() if n[0] != R]
        
        info = ""
        if ring_neighbors:
            info += f"Ring: {len(ring_neighbors)} nodes\n"
        if tree_neighbors:
            info += f"Tree: {len(tree_neighbors)} nodes\n"
            info += "  " + ", ".join([f"({n[0]},{n[1]})" for n in sorted(tree_neighbors)[:3]])
            if len(tree_neighbors) > 3:
                info += f" +{len(tree_neighbors)-3}"
        return info
    
    def _format_buffer_compact(self, node):
        """Format buffer status (compact)"""
        total_send = sum(len(iface.send_buffer.buffer) for iface in node.interfaces.values())
        total_recv = sum(len(iface.receive_buffer.buffer) for iface in node.interfaces.values())
        app_buf = len(node.application_logic_buffer)
        
        info = f"Send: {total_send} | Recv: {total_recv}"
        if app_buf > 0:
            info += f"\nApp Buffer: {app_buf} delivered"
        return info
    
    def _format_packet_routing_compact(self, addr):
        """Format packet routing information (compact)"""
        hop_index = self.current_path.index(addr)
        return f"Hop {hop_index + 1}/{len(self.current_path)}\n{self.current_path[0]} → {self.current_path[-1]}"
    
    def _make_overlay_draggable(self, frame):
        """Make overlay frame draggable"""
        frame._drag_data = {"x": 0, "y": 0}
        
        def on_press(event):
            frame._drag_data["x"] = event.x
            frame._drag_data["y"] = event.y
        
        def on_drag(event):
            dx = event.x - frame._drag_data["x"]
            dy = event.y - frame._drag_data["y"]
            
            # Get current position
            x, y = self.canvas.coords(self.hover_overlay)
            
            # Move the overlay
            self.canvas.coords(self.hover_overlay, x + dx, y + dy)
        
        # Bind to header only for dragging
        for child in frame.winfo_children():
            if isinstance(child, tk.Frame) and child.cget('bg') == '#2c3e50':
                child.bind("<Button-1>", on_press)
                child.bind("<B1-Motion>", on_drag)
                break
    
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
        """Highlight selected node with better visibility"""
        if addr in self.node_items:
            if node_type == 'source':
                color = '#2e7d32'  # Green
                outline = '#1b5e20'  # Darker green
            else:
                color = '#c62828'  # Red
                outline = '#8e0000'  # Darker red
            
            # Make it stand out with thicker border
            self.canvas.itemconfig(self.node_items[addr], fill=color, outline=outline, width=4)
            
            # Add a pulsing effect by scaling
            self.canvas.itemconfig(self.node_items[addr], width=5)
    
    def _show_detailed_node_info(self, addr, is_hover=False):
        """Show detailed node information in a clean, readable modal/hover dialog"""
        node = self.topology.nodes[addr]
        R, Nr = addr
        
        # Create window (modal or hover)
        if is_hover:
            info_window = tk.Toplevel(self.root)
            self.hover_window = info_window
        else:
            info_window = tk.Toplevel(self.root)
        
        info_window.title(f"📡 Node ({R},{Nr}) - Detailed Information")
        info_window.configure(bg='white')
        info_window.geometry("550x650")
        
        # Make it modal if not hover
        if not is_hover:
            info_window.transient(self.root)
            info_window.grab_set()
        
        # Center the modal on screen
        info_window.update_idletasks()
        x = (info_window.winfo_screenwidth() // 2) - 275
        y = (info_window.winfo_screenheight() // 2) - 325
        info_window.geometry(f"550x650+{x}+{y}")
        
        # Header with close button (X icon) in the header
        header = tk.Frame(info_window, bg='#2c3e50', height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        # Create header content frame
        header_content = tk.Frame(header, bg='#2c3e50')
        header_content.pack(fill=tk.BOTH, expand=True)
        
        # Close button (X) in top-right corner of header
        close_btn = tk.Button(header_content, text="✖", 
                             command=lambda: self._close_info_window(info_window),
                             bg='#e74c3c', fg='white', font=("Arial", 14, "bold"),
                             relief=tk.FLAT, cursor="hand2", padx=10, pady=5,
                             activebackground='#c0392b', activeforeground='white',
                             bd=0)
        close_btn.pack(side=tk.RIGHT, padx=10, pady=10)
        
        # Title and subtitle in header
        title_frame = tk.Frame(header_content, bg='#2c3e50')
        title_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=15)
        
        tk.Label(title_frame, text=f"NODE ({R},{Nr}) - DETAILS", 
                font=("Arial", 18, "bold"), bg='#2c3e50', fg='white').pack(anchor=tk.W, pady=(8, 2))
        tk.Label(title_frame, text=f"Ring: {R} | Position: {Nr} | Ring Size: {2**R} nodes", 
                font=("Arial", 10), bg='#2c3e50', fg='#ecf0f1').pack(anchor=tk.W)
        
        # Main scrollable content
        main_frame = tk.Frame(info_window, bg='white')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        
        canvas = tk.Canvas(main_frame, bg='white', highlightthickness=0)
        scrollbar = tk.Scrollbar(main_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='white')
        
        scrollable_frame.bind("<Configure>", 
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create information sections
        self._create_info_section(scrollable_frame, "📊 BASIC INFORMATION", 
                                 self._format_basic_info(node, addr), '#e8f4f8', '#2980b9')
        
        self._create_info_section(scrollable_frame, "🔗 NEIGHBORS & CONNECTIONS", 
                                 self._format_neighbors_info(node, addr), '#f4f6f7', '#7f8c8d')
        
        self._create_info_section(scrollable_frame, "� BUFFER STATUS", 
                                 self._format_buffer_status(node), '#fff3e0', '#f39c12')
        
        self._create_info_section(scrollable_frame, "� FLOW CONTROL STATE", 
                                 self._format_flow_control(node), '#e8f5e9', '#27ae60')
        
        if self.current_packet and addr in self.current_path:
            self._create_info_section(scrollable_frame, "� PACKET ROUTING INFO", 
                                     self._format_packet_routing(addr), '#fce4ec', '#e91e63')
        
        # ESC to close
        info_window.bind("<Escape>", lambda e: self._close_info_window(info_window))
        
        # Auto-close hover window when mouse leaves
        if is_hover:
            info_window.bind("<Leave>", lambda e: self._close_info_window(info_window))
        else:
            self.root.wait_window(info_window)
    
    def _close_info_window(self, window):
        """Close info window safely"""
        try:
            if window == self.hover_window:
                self.hover_window = None
            window.destroy()
        except:
            pass
    
    def _create_info_section(self, parent, title, content, bg_color, title_color):
        """Create a clean information section"""
        section = tk.Frame(parent, bg=bg_color, relief=tk.RAISED, bd=1)
        section.pack(fill=tk.X, padx=10, pady=5)
        
        # Title bar
        title_frame = tk.Frame(section, bg=title_color)
        title_frame.pack(fill=tk.X)
        
        tk.Label(title_frame, text=title, font=("Arial", 11, "bold"),
                bg=title_color, fg='white', anchor='w').pack(fill=tk.X, padx=12, pady=8)
        
        # Content with better readability
        content_frame = tk.Frame(section, bg='white')
        content_frame.pack(fill=tk.X, padx=8, pady=8)
        
        content_label = tk.Label(content_frame, text=content, 
                                font=('Courier New', 9), bg='white', fg='#2c3e50',
                                justify=tk.LEFT, anchor='w')
        content_label.pack(fill=tk.X, padx=8, pady=4)
    
    def _format_basic_info(self, node, addr):
        """Format basic node information"""
        R, Nr = addr
        info = f"""Address:        ({R}, {Nr})
Ring Level:     {R}
Position:       {Nr}
Ring Size:      {2**R} nodes
Interfaces:     {len(node.interfaces)} connections
"""
        return info
    
    def _format_neighbors_info(self, node, addr):
        """Format neighbors information"""
        R, Nr = addr
        info = ""
        
        ring_neighbors = []
        tree_neighbors = []
        
        for neighbor_addr in node.interfaces.keys():
            n_R, n_Nr = neighbor_addr
            if R == n_R:
                ring_neighbors.append((n_R, n_Nr))
            else:
                tree_neighbors.append((n_R, n_Nr))
        
        if ring_neighbors:
            info += "RING CONNECTIONS:\n"
            for n_R, n_Nr in sorted(ring_neighbors):
                info += f"  → ({n_R:2d}, {n_Nr:2d})\n"
            info += "\n"
        
        if tree_neighbors:
            info += "TREE CONNECTIONS:\n"
            for n_R, n_Nr in sorted(tree_neighbors):
                rel = "Parent" if n_R < R else "Child"
                info += f"  → ({n_R:2d}, {n_Nr:2d})  [{rel}]\n"
        
        return info
    
    def _format_buffer_status(self, node):
        """Format buffer status with REAL dynamic data"""
        info = ""
        
        for idx, (neighbor_addr, interface) in enumerate(node.interfaces.items(), 1):
            send_size = len(interface.send_buffer.buffer)
            send_cap = interface.send_buffer.buffer.maxlen
            recv_size = len(interface.receive_buffer.buffer)
            recv_cap = interface.receive_buffer.buffer.maxlen
            
            info += f"Interface #{idx} → ({neighbor_addr[0]}, {neighbor_addr[1]}):\n"
            
            # Send buffer with visual bar
            send_pct = (send_size * 10 // send_cap) if send_cap > 0 else 0
            info += f"  Send:    {send_size:2d}/{send_cap:2d} "
            info += f"[{'█' * send_pct}{'░' * (10 - send_pct)}] "
            info += f"({int(send_size/send_cap*100) if send_cap > 0 else 0}%)\n"
            
            # Receive buffer with visual bar
            recv_pct = (recv_size * 10 // recv_cap) if recv_cap > 0 else 0
            info += f"  Receive: {recv_size:2d}/{recv_cap:2d} "
            info += f"[{'█' * recv_pct}{'░' * (10 - recv_pct)}] "
            info += f"({int(recv_size/recv_cap*100) if recv_cap > 0 else 0}%)\n"
            
            # Show actual packets in buffers
            if send_size > 0:
                info += f"  📤 Send Queue: "
                packets_info = []
                for pkt in list(interface.send_buffer.buffer)[:3]:  # Show first 3
                    packets_info.append(f"{pkt.dest_address}")
                info += ", ".join(packets_info)
                if send_size > 3:
                    info += f" +{send_size-3} more"
                info += "\n"
            
            if recv_size > 0:
                info += f"  📥 Recv Queue: "
                packets_info = []
                for pkt in list(interface.receive_buffer.buffer)[:3]:  # Show first 3
                    packets_info.append(f"{pkt.dest_address}")
                info += ", ".join(packets_info)
                if recv_size > 3:
                    info += f" +{recv_size-3} more"
                info += "\n"
            
            info += "\n"
        
        # Show application buffer if not empty
        if node.application_logic_buffer:
            info += f"📬 APPLICATION BUFFER:\n"
            info += f"  Delivered packets: {len(node.application_logic_buffer)}\n"
            for pkt in node.application_logic_buffer[:5]:  # Show first 5
                latency = pkt.end_timer - pkt.start_timer
                info += f"  • From {pkt.source_address}, Latency: {latency}\n"
            if len(node.application_logic_buffer) > 5:
                info += f"  ... +{len(node.application_logic_buffer)-5} more\n"
        
        return info if info else "All buffers empty"
    
    def _format_flow_control(self, node):
        """Format flow control information with REAL pin/bit states"""
        info = ""
        
        for idx, (neighbor_addr, interface) in enumerate(node.interfaces.items(), 1):
            info += f"Interface #{idx} → ({neighbor_addr[0]}, {neighbor_addr[1]}):\n"
            
            # Status bits with visual indicators
            busy_icon = "🔴" if interface.bit_Busy else "🟢"
            transfer_icon = "🔵" if interface.bit_Transfer else "⚪"
            receive_icon = "🟣" if interface.bit_Receive else "⚪"
            
            info += f"  {busy_icon} Busy:      {'YES (Active)' if interface.bit_Busy else 'NO  (Idle)'}\n"
            info += f"  {transfer_icon} Transfer:  {'YES (Sending)' if interface.bit_Transfer else 'NO  (Ready)'}\n"
            info += f"  {receive_icon} Receive:   {'YES (Receiving)' if interface.bit_Receive else 'NO  (Ready)'}\n"
            
            # Handshake pins
            req_state = "HIGH ✓" if interface.pin_REQ else "LOW  ✗"
            ack_state = "HIGH ✓" if interface.pin_ACK else "LOW  ✗"
            choke_state = "HIGH ⚠" if interface.pin_CHOKE else "LOW  ✓"
            
            info += f"  📌 pin_REQ:   {req_state}\n"
            info += f"  📌 pin_ACK:   {ack_state}\n"
            info += f"  📌 pin_CHOKE: {choke_state}\n"
            
            # Data register status
            if interface.send_register:
                info += f"  📝 Send Reg:  Packet to {interface.send_register.dest_address}\n"
            else:
                info += f"  📝 Send Reg:  Empty\n"
            
            if interface.receive_register:
                info += f"  📝 Recv Reg:  Packet to {interface.receive_register.dest_address}\n"
            else:
                info += f"  📝 Recv Reg:  Empty\n"
            
            # Timeout counter
            if interface.timeout_counter > 0:
                info += f"  ⏱️  Timeout:   {interface.timeout_counter}/{interface.TIMEOUT_LIMIT}\n"
            
            info += "\n"
        
        return info
    
    def _format_packet_routing(self, addr):
        """Format packet routing information"""
        hop_index = self.current_path.index(addr)
        total_hops = len(self.current_path) - 1
        
        info = f"Current packet is at this node!\n\n"
        info += f"Hop: {hop_index + 1} of {len(self.current_path)}\n"
        info += f"Source: {self.current_path[0]}\n"
        info += f"Destination: {self.current_path[-1]}\n"
        info += f"Total hops: {total_hops}\n\n"
        info += f"Path:\n"
        
        for i, node in enumerate(self.current_path):
            marker = "▶ " if i == hop_index else "  "
            info += f"{marker}{node}\n"
        
        return info
    
    def simulate_routing(self):
        """Simulate routing and highlight path"""
        path = self._compute_path()
        if not path:
            return
        
        # Clear old highlights first (but keep the path for drawing)
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
        
        # NOW draw the topology (which will highlight the path)
        self.draw_topology()
        
        # Update status bar
        self.current_hop = 0
        self.transfer_phase = "Route Computed"
        self.transfer_progress = 0
        self.signal_status = "Ready"
        self._update_status_bar()
        self._update_simulation_details()
    
    def animate_routing(self):
        """Animate REAL packet routing with detailed step-by-step visualization and pause/resume"""
        # If already running, toggle pause
        if self.animation_running:
            self.is_paused = not self.is_paused
            if self.is_paused:
                if hasattr(self, 'animate_button_sim'):
                    self.animate_button_sim.config(text="Resume")
                self.transfer_phase = "Paused"
                self.signal_status = "Paused"
                self._update_status_bar()
                self._update_simulation_details()
            else:
                if hasattr(self, 'animate_button_sim'):
                    self.animate_button_sim.config(text="Pause")
                self.transfer_phase = "Transferring"
                self.signal_status = "Active"
                self._update_status_bar()
                self._update_simulation_details()
            return
        
        path = self._compute_path()
        if not path:
            return
        
        self.animation_running = True
        self.is_paused = False
        # Don't reset is_auto_started here - keep it if set by auto_start_sim
        if hasattr(self, 'animate_button_sim'):
            self.animate_button_sim.config(text="Pause")
        self.clear_highlights()
        self.current_path = path
        self.current_hop = 0
        
        # Clear any previous animations
        self.packet_animator.clear_animations()
        
        # Create real packet
        from core.packet import Packet
        self.current_packet = Packet(
            source_address=path[0],
            dest_address=path[-1],
            data=f"Test packet from {path[0]} to {path[-1]}"
        )
        
        # Initialize flow analysis
        self._update_flow_analysis("=== REAL PACKET TRANSFER INITIATED ===", clear=True)
        self._update_flow_analysis(f"\n📦 Packet Created:")
        self._update_flow_analysis(f"   Source: {self.current_packet.source_address}")
        self._update_flow_analysis(f"   Destination: {self.current_packet.dest_address}")
        self._update_flow_analysis(f"   Data: {self.current_packet.data}")
        self._update_flow_analysis(f"   start_timer = {self.current_packet.start_timer}")
        
        # Update simulation details
        self._update_simulation_details()
        
        def animate_step(index):
            # Skip pause check if auto-started (continuous execution)
            if self.is_paused and not self.is_auto_started:
                # Re-schedule the same step after a short delay
                self.root.after(100, lambda: animate_step(index))
                return
            
            if index >= len(path):
                self.animation_running = False
                self.is_paused = False
                self.is_auto_started = False  # Reset auto-start flag
                if hasattr(self, 'animate_button_sim'):
                    self.animate_button_sim.config(text="Animate")
                self.current_packet.end_timer = self.current_packet.start_timer + (len(path) - 1)
                latency = self.current_packet.end_timer - self.current_packet.start_timer
                
                self._update_flow_analysis(f"\n✅ PACKET DELIVERED!")
                self._update_flow_analysis(f"   end_timer = {self.current_packet.end_timer}")
                self._update_flow_analysis(f"   Latency = {latency} time units")
                
                self.transfer_phase = "Completed"
                self.transfer_progress = 100
                self.signal_status = "Idle"
                self._update_status_bar()
                self._update_simulation_details()
                
                # Show final delivered packet
                if path[-1] in self.node_positions:
                    x, y = self.node_positions[path[-1]]
                    cx, cy = self._transform_coords(x, y)
                    self.packet_animator.draw_packet_at_node(cx, cy, phase='delivered')
                
                # Check if 1:M multicast mode
                if self.transfer_type == '1:M' and hasattr(self, 'transfer_results'):
                    # Call multicast delivery complete
                    self._on_multicast_delivery_complete(path[-1], path, latency)
                else:
                    # Schedule path clearing after 1 minute (60000 ms) for 1:1 mode
                    if self.path_clear_timer:
                        self.root.after_cancel(self.path_clear_timer)
                    self.path_clear_timer = self.root.after(60000, self._clear_completed_path)
                
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
                interface_state = {
                    'req': 1 if interface.pin_REQ else 0,
                    'ack': 1 if interface.pin_ACK else 0,
                    'busy': 1 if interface.bit_Busy else 0,
                    'transfer': 1 if interface.bit_Transfer else 0,
                    'send_buf': f"{len(interface.send_buffer.buffer)}/{interface.send_buffer.buffer.maxlen}",
                    'recv_buf': f"{len(interface.receive_buffer.buffer)}/{interface.receive_buffer.buffer.maxlen}"
                }
            
            # Get node position for packet animation
            if addr in self.node_positions:
                x, y = self.node_positions[addr]
                cx, cy = self._transform_coords(x, y)
            
            # Detailed flow analysis with MULTIPLE sub-phases
            if index == 0:
                # SOURCE NODE - 3 phases
                self._animate_source_node(addr, next_addr, cx, cy, path, interface_state)
                
            elif next_addr is not None:
                # INTERMEDIATE NODE (including last hop to destination) - 5 phases
                self._animate_intermediate_node(addr, next_addr, cx, cy, path, index, interface_state)
            
            # Visual highlight nodes and edges
            # Current node in yellow during transfer
            if addr in self.node_items:
                self.canvas.itemconfig(self.node_items[addr], fill=self.colors['highlight'])
            
            # Mark previous node as completed (green) after packet moves away
            if index > 0:
                prev_addr = path[index - 1]
                if prev_addr in self.node_items:
                    self.canvas.itemconfig(self.node_items[prev_addr], fill='#4caf50')  # Green for completed
                    self.completed_path_nodes.add(prev_addr)
            
            if next_addr:
                edge = tuple(sorted([addr, next_addr]))
                if edge in self.edge_items:
                    self.canvas.itemconfig(self.edge_items[edge], fill=self.colors['path'], width=3)
                    self.highlighted_edges.add(edge)
            
            # Update simulation details
            self._update_simulation_details()
            
            self.canvas.update()
            
            # Callback to move to next hop - will be called after all animations complete
            def move_to_next_hop():
                animate_step(index + 1)
            
            # Store callback for animations to use
            self._current_hop_callback = move_to_next_hop
        
        animate_step(0)
    
    def _get_arc_points_for_hop(self, start_node, end_node):
        """Get arc points for a hop if it's a ring connection, None otherwise
        
        Args:
            start_node: (ring, node_nr) tuple
            end_node: (ring, node_nr) tuple
            
        Returns:
            List of (x, y) transformed canvas coordinates if ring hop, None otherwise
        """
        start_R, start_Nr = start_node
        end_R, end_Nr = end_node
        
        # Check if this is a ring hop (same ring)
        if start_R != end_R or start_R == 0:
            return None
        
        # For mesh, straight line connections don't need arc rendering
        # Simply return None to skip arc animation (mesh uses direct lines)
        return None
    
    def _animate_source_node(self, addr, next_addr, cx, cy, path, interface_state):
        """Animate source node packet creation and initial send"""
        self.transfer_phase = "Packet Created"
        self.signal_status = "Idle → REQ"
        
        # Get node and interface for clock tracking
        node = self.topology.nodes[addr]
        interface = node.interfaces.get(next_addr)
        clk = 0  # Initial clock
        
        self._update_flow_analysis(f"\n--- HOP 1/{len(path)-1}: Source Node {addr} ---")
        self._update_flow_analysis(f"[clk={clk}] Packet Creation")
        self._update_flow_analysis("  • Application creates packet")
        self._update_flow_analysis(f"  • Destination set to {path[-1]}")
        
        # Update status bar with INITIAL interface state (all zeros at start)
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
        
        # Get arc points if this is a ring hop
        arc_points = self._get_arc_points_for_hop(addr, next_addr)
        
        # After short delay, show routing phase
        def show_routing():
            self.transfer_phase = "Routing"
            self.signal_status = "Computing"
            clk_routing = clk + 1
            self._update_flow_analysis(f"[clk={clk_routing}] Routing Logic")
            self._update_flow_analysis(f"  • Next hop determined: {next_addr}")
            self._update_flow_analysis("  • Packet placed in Send Buffer")
            
            routing_state = {
                'req': 0, 'ack': 0, 'busy': 0, 'transfer': 0,
                'send_buf': '1/4', 'recv_buf': '0/4'
            }
            self._update_status_bar(current_node=addr, next_node=next_addr, interface_state=routing_state)
            # Activity ring removed - not required
        
        self.root.after(int(self.animation_speed * 0.2), show_routing)
        
        # Show REQ phase - pointer goes to check conditions
        def show_req():
            self.transfer_phase = "Checking Conditions"
            self.signal_status = "REQ=1"
            clk_req = clk + 2
            self._update_flow_analysis(f"[clk={clk_req}] Request & Condition Check")
            self._update_flow_analysis(f"  • Pointer sent: {addr} → {next_addr}")
            self._update_flow_analysis("  • Checking: Buffer availability")
            self._update_flow_analysis("  • Checking: Channel status")
            self._update_flow_analysis(f"  • Waiting for ACK from {next_addr}")
            
            # Update with REQ=1 as handshake begins
            req_state = {
                'req': 1, 'ack': 0, 'busy': 0, 'transfer': 0,
                'send_buf': '1/4', 'recv_buf': '0/4'
            }
            self._update_status_bar(current_node=addr, next_node=next_addr, interface_state=req_state)
            
            # Show CHECK pointer (blue) going to check conditions
            # Use callback to wait for animation to complete before showing ACK
            def on_req_complete():
                # After REQ animation completes, show ACK
                show_ack()
            
            self.packet_animator.draw_transfer_arrow(cx, cy, ncx, ncy, phase='req', arc_points=arc_points, callback=on_req_complete)
        
        self.root.after(int(self.animation_speed * 0.4), show_req)
        
        # Show ACK phase - conditions verified, pointer returns
        def show_ack():
            self.transfer_phase = "ACK"
            self.signal_status = "ACK=1"
            clk_ack = clk + 3
            self._update_flow_analysis(f"[clk={clk_ack}] Acknowledgment (Conditions OK)")
            self._update_flow_analysis(f"  • Buffer available: ✓")
            self._update_flow_analysis(f"  • Channel ready: ✓")
            self._update_flow_analysis(f"  • ACK sent back: {next_addr} → {addr}")
            self._update_flow_analysis("  • Channel locked for data transfer")
            
            # Update with ACK=1
            ack_state = {
                'req': 1, 'ack': 1, 'busy': 1, 'transfer': 0,
                'send_buf': '1/4', 'recv_buf': '0/4'
            }
            self._update_status_bar(current_node=addr, next_node=next_addr, interface_state=ack_state)
            
            # Show ACK pointer (green) returning - same pointer coming back
            # Use callback to wait for ACK animation before showing data transfer
            def on_ack_complete():
                # After ACK animation completes, show data transfer
                show_data()
            
            self.packet_animator.draw_transfer_arrow(cx, cy, ncx, ncy, phase='ack', arc_points=arc_points, callback=on_ack_complete)
        
        # Don't schedule show_ack independently - it will be called by REQ callback
        # self.root.after(int(self.animation_speed * 0.6), show_ack)  # REMOVED
        
        # Show DATA transfer - blue hexagonal packet moving
        def show_data():
            self.transfer_phase = "DATA Transfer"
            self.signal_status = "Transferring"
            clk_data = clk + 4
            self._update_flow_analysis(f"[clk={clk_data}] Data Transfer")
            self._update_flow_analysis(f"  • Blue packet moving: {addr} → {next_addr}")
            self._update_flow_analysis("  • bit_Transfer = 1")
            self._update_flow_analysis("  • Send Buffer → Receive Buffer")
            
            # Update with Transfer=1
            data_state = {
                'req': 1, 'ack': 1, 'busy': 1, 'transfer': 1,
                'send_buf': '0/4', 'recv_buf': '1/4'
            }
            self._update_status_bar(current_node=addr, next_node=next_addr, interface_state=data_state)
            
            # Clear any existing packet visuals (including 'D' text) before transfer
            self.packet_animator.clear_animations()
            
            # Animate blue hexagonal packet from source to next node
            # After data transfer completes, move to next hop
            def on_data_complete():
                # Data transfer finished, now move to next hop
                if hasattr(self, '_current_hop_callback'):
                    self._current_hop_callback()
            
            self.packet_animator.animate_packet_transfer((cx, cy), (ncx, ncy), color='#0066ff', callback=on_data_complete)
        
        # Don't schedule show_data - it's called by ACK callback
    
    def _animate_intermediate_node(self, addr, next_addr, cx, cy, path, index, interface_state):
        """Animate intermediate node with detailed handshake and transfer phases"""
        # Check if next_addr is the final destination
        is_last_hop = (next_addr == path[-1])
        
        if is_last_hop:
            # This is the last hop to the destination
            self._update_flow_analysis(f"\n--- HOP {index + 1}/{len(path)-1}: {addr} → Destination {next_addr} ---")
        else:
            # Regular intermediate hop
            self._update_flow_analysis(f"\n--- HOP {index + 1}/{len(path)-1}: Intermediate Node {addr} ---")
        
        # Get next node position
        nx, ny = self.node_positions[next_addr]
        ncx, ncy = self._transform_coords(nx, ny)
        
        # Get arc points if this is a ring hop
        arc_points = self._get_arc_points_for_hop(addr, next_addr)
        
        # Clock tracking for this hop
        base_clk = index * 5  # Each hop takes approximately 5 clock cycles
        
        # Phase 1: REQ (Request & Condition Check) - Pointer goes to check
        self.transfer_phase = "Checking Conditions"
        self.signal_status = "REQ=1"
        self._update_flow_analysis(f"[clk={base_clk}] Request & Condition Check")
        self._update_flow_analysis(f"  • Pointer sent: {addr} → {next_addr}")
        self._update_flow_analysis("  • Checking buffer availability")
        self._update_flow_analysis("  • Checking channel status")
        self._update_flow_analysis(f"  • Waiting for ACK from {next_addr}")
        
        # Show REQ=1, ACK=0
        handshake_state_1 = {
            'req': 1, 'ack': 0, 'busy': 0, 'transfer': 0,
            'send_buf': '1/4', 'recv_buf': '0/4'
        }
        self._update_status_bar(current_node=addr, next_node=next_addr, interface_state=handshake_state_1)
        
        # Callback to execute when REQ animation completes
        def on_req_complete():
            # After REQ completes, show ACK
            show_ack()
        
        # Show CHECK pointer going to destination - will call on_req_complete when done
        self.packet_animator.draw_transfer_arrow(cx, cy, ncx, ncy, phase='req', arc_points=arc_points, callback=on_req_complete)
        # Activity ring removed - not required
        
        # Phase 2: ACK (Acknowledgment - Conditions verified) - Pointer returns
        def show_ack():
            self.transfer_phase = "ACK"
            self.signal_status = "ACK=1"
            self._update_flow_analysis(f"[clk={base_clk + 1}] Acknowledgment (Conditions OK)")
            self._update_flow_analysis(f"  • Buffer available: ✓")
            self._update_flow_analysis(f"  • Channel ready: ✓")
            self._update_flow_analysis(f"  • ACK sent back: {next_addr} → {addr}")
            self._update_flow_analysis("  • bit_Busy = 1 (Channel locked)")
            
            # Show REQ=1, ACK=1, Busy=1
            handshake_state_2 = {
                'req': 1, 'ack': 1, 'busy': 1, 'transfer': 0,
                'send_buf': '1/4', 'recv_buf': '0/4'
            }
            self._update_status_bar(current_node=addr, next_node=next_addr, interface_state=handshake_state_2)
            
            # Callback to execute when ACK animation completes
            def on_ack_complete():
                # After ACK completes, show data transfer
                show_data_transfer()
            
            # Show ACK pointer returning (green) - will call on_ack_complete when done
            self.packet_animator.draw_transfer_arrow(cx, cy, ncx, ncy, phase='ack', arc_points=arc_points, callback=on_ack_complete)
            # Activity ring removed - not required
        
        # Don't schedule show_ack with self.root.after - it's called by callback
        # self.root.after(int(self.animation_speed * 0.2), show_ack)  # REMOVED
        
        # Phase 3: Data Transfer - Blue hexagonal packet moving after ACK received
        def show_data_transfer():
            self.transfer_phase = "DATA Transfer"
            self.signal_status = "Transferring"
            self._update_flow_analysis(f"[clk={base_clk + 2}] Data Transfer")
            self._update_flow_analysis(f"  • Blue packet moving: {addr} → {next_addr}")
            self._update_flow_analysis("  • bit_Transfer = 1")
            self._update_flow_analysis("  • Send Buffer → Receive Buffer")
            
            # Show Transfer=1
            transfer_state = {
                'req': 1, 'ack': 1, 'busy': 1, 'transfer': 1,
                'send_buf': '0/4', 'recv_buf': '1/4'
            }
            self._update_status_bar(current_node=addr, next_node=next_addr, interface_state=transfer_state)
            
            # Animate blue hexagonal packet from current to next node
            # After packet arrives, show reception and then move to next hop
            def on_data_complete():
                show_reception()
            
            self.packet_animator.animate_packet_transfer((cx, cy), (ncx, ncy), color='#0066ff', callback=on_data_complete)
        
        # Don't schedule show_data_transfer - it's called by ACK callback
        
        # Phase 4: Reception - called after data transfer completes
        def show_reception():
            self.transfer_phase = "Received"
            self.signal_status = "Packet at dest"
            self._update_flow_analysis(f"[clk={base_clk + 3}] Reception Complete")
            self._update_flow_analysis("  • Packet arrived at next node")
            self._update_flow_analysis("  • Placed in Receive Buffer")
            
            # Clear packet from previous node before showing at new node
            self.packet_animator.clear_animations()
            
            # Show packet at destination node
            self.packet_animator.draw_packet_at_node(ncx, ncy, phase='transferring')
            
            # After showing reception, do routing check
            self.root.after(int(self.animation_speed * 0.2), show_routing_check)
        
        # Phase 5: Routing Check - called after reception
        def show_routing_check():
            self.transfer_phase = "Routing"
            self.signal_status = "Checking dest"
            
            # Check if this is the final destination
            is_final_dest = (next_addr == path[-1])
            
            if is_final_dest:
                # This packet reached its final destination
                self._update_flow_analysis(f"[clk={base_clk + 4}] Final Delivery")
                self._update_flow_analysis(f"  • Dest {path[-1]} = Current {next_addr} ✓")
                self._update_flow_analysis(f"  • Packet successfully reached destination")
                self._update_flow_analysis("  • Packet → Application Logic Buffer")
                self._update_flow_analysis("  • Transfer complete!")
            else:
                # Continue routing to next hop
                self._update_flow_analysis(f"[clk={base_clk + 4}] Routing Decision")
                self._update_flow_analysis(f"  • Dest {path[-1]} ≠ Current {addr}")
                self._update_flow_analysis(f"  • Next hop determined: {next_addr}")
                self._update_flow_analysis("  • Handshake reset (REQ=0, ACK=0)")
            
            # Reset handshake
            reset_state = {
                'req': 0, 'ack': 0, 'busy': 0, 'transfer': 0,
                'send_buf': '0/4', 'recv_buf': '0/4'
            }
            self._update_status_bar(current_node=addr, next_node=next_addr, interface_state=reset_state)
            
            # After routing check complete, move to next hop
            if hasattr(self, '_current_hop_callback'):
                self.root.after(int(self.animation_speed * 0.2), self._current_hop_callback)
    
    def _animate_destination_node(self, addr, cx, cy, path, index, interface_state):
        """Animate final delivery to destination node"""
        self.transfer_phase = "Delivering"
        self.signal_status = "Final ACK"
        
        # Clock tracking for destination
        base_clk = index * 5
        
        # Fix: This is the last hop, so it should be HOP {index+1}/{index+1}
        total_hops = index + 1
        self._update_flow_analysis(f"\n--- HOP {total_hops}/{total_hops}: Destination Node {addr} ---")
        self._update_flow_analysis(f"[clk={base_clk}] Final Handshake")
        self._update_flow_analysis("  • Handshake completed")
        self._update_flow_analysis(f"  • Dest {path[-1]} = Current {addr} ✓")
        self._update_flow_analysis(f"  • Packet successfully reached destination")
        
        # Show final handshake state
        final_handshake = {
            'req': 1, 'ack': 1, 'busy': 0, 'transfer': 0,
            'send_buf': '0/4', 'recv_buf': '1/4'
        }
        self._update_status_bar(current_node=addr, next_node=None, interface_state=final_handshake)
        
        # Phase 2: Delivery to application (after half time)
        def show_final_delivery():
            self.transfer_phase = "Completed"
            self.signal_status = "Delivered"
            self._update_flow_analysis(f"[clk={base_clk + 1}] Delivery to Application")
            self._update_flow_analysis("  • Packet → Application Logic Buffer")
            self._update_flow_analysis("  • Transfer complete!")
            self._update_flow_analysis(f"  • Final destination: {addr}")
            
            # All cleared after delivery
            delivered_state = {
                'req': 0, 'ack': 0, 'busy': 0, 'transfer': 0,
                'send_buf': '0/4', 'recv_buf': '0/4'
            }
            self._update_status_bar(current_node=addr, next_node=None, interface_state=delivered_state)
            
            self.packet_animator.draw_packet_at_node(cx, cy, phase='delivered')
            # Activity ring removed - not required
        
        self.root.after(int(self.animation_speed * 0.5), show_final_delivery)
    
    def _compute_path(self):
        """Compute path using RicoBit routing tables"""
        try:
            src_addr = (self.src_ring_var.get(), self.src_node_var.get())
            dst_addr = (self.dst_ring_var.get(), self.dst_node_var.get())
            
            if src_addr not in self.topology.nodes or dst_addr not in self.topology.nodes:
                messagebox.showerror("Error", "Invalid source or destination node")
                return None
            
            if src_addr == dst_addr:
                messagebox.showwarning("Warning", "Source and destination are the same")
                return None
            
            print(f"\n{'='*60}")
            print(f"COMPUTING PATH: {src_addr} -> {dst_addr}")
            print(f"{'='*60}")
            
            # Use routing table to trace path
            path = [src_addr]
            current = src_addr
            visited = set([src_addr])
            
            hop_num = 0
            while current != dst_addr:
                # Get next hop from routing table
                next_hop = self.topology.nodes[current].routing_table.get(dst_addr)
                
                print(f"\nHop {hop_num}: At {current}")
                print(f"  Routing table lookup for dest {dst_addr}: next_hop = {next_hop}")
                
                if next_hop is None:
                    messagebox.showerror("Error", f"No route found from {current} to {dst_addr}")
                    return None
                
                # Check for loops
                if next_hop in visited:
                    messagebox.showerror("Error", f"Routing loop detected at {next_hop}")
                    return None
                
                # Verify next hop is connected
                if next_hop not in self.topology.nodes[current].interfaces:
                    messagebox.showerror("Error", f"Invalid next hop {next_hop} from {current}")
                    return None
                
                # Determine hop type
                current_R, current_Nr = current
                next_R, next_Nr = next_hop
                if current_R == next_R:
                    hop_type = "RING"
                else:
                    hop_type = "TREE"
                print(f"  -> Moving to {next_hop} ({hop_type} hop)")
                
                path.append(next_hop)
                visited.add(next_hop)
                current = next_hop
                hop_num += 1
                
                # Safety check
                if len(path) > 1000:
                    messagebox.showerror("Error", "Path too long - possible routing loop")
                    return None
            
            print(f"\nPATH COMPUTED SUCCESSFULLY:")
            print(f"  Total hops: {len(path) - 1}")
            print(f"  Path: {' -> '.join(str(p) for p in path)}")
            print(f"{'='*60}\n")
            
            return path
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return None
    
    def clear_path(self):
        """Clear routing highlights and packet animations"""
        self.clear_highlights()
        self.packet_animator.clear_animations()
        # No arc_renderer in mesh (uses straight lines)
        self.current_packet = None
        self.current_path = []
        self.current_hop = 0
        self.transfer_phase = "Waiting to Start"
        self.transfer_progress = 0
        self.signal_status = "Idle"
        self.animation_running = False
        self.is_paused = False
        if hasattr(self, 'animate_button_sim'):
            self.animate_button_sim.config(text="Animate")
        self._update_status_bar()
        self._update_simulation_details()
        self._update_flow_analysis("Path cleared. Ready for new transfer.", clear=True)
    
    def clear_highlights(self):
        """Clear all highlights and packet animations"""
        self.highlighted_edges.clear()
        self.highlighted_nodes.clear()
        self.packet_animator.clear_animations()
        # No arc_renderer in mesh (uses straight lines)
        
        # Clear animation items (arcs, etc.)
        for item in self.animation_items:
            try:
                self.canvas.delete(item)
            except:
                pass
        self.animation_items.clear()
        
        self.draw_topology()
    
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
        
        # Calculate zoom factor
        zoom_factor = 1.2
        old_zoom = self.zoom_level
        new_zoom = min(30.0, old_zoom * zoom_factor)  # Increased zoom limit by 10x
        
        # Adjust pan to zoom from center
        self.pan_x = canvas_center_x - (canvas_center_x - self.pan_x) * (new_zoom / old_zoom)
        self.pan_y = canvas_center_y - (canvas_center_y - self.pan_y) * (new_zoom / old_zoom)
        
        self.zoom_level = new_zoom
        self.draw_topology()
        
        # Restore control panel position after zoom
        self._restore_control_panel_position()
    
    def zoom_out(self):
        """Zoom out from center"""
        canvas_center_x = self.canvas.winfo_width() / 2
        canvas_center_y = self.canvas.winfo_height() / 2
        
        # Calculate zoom factor
        zoom_factor = 1.2
        old_zoom = self.zoom_level
        new_zoom = max(0.3, old_zoom / zoom_factor)
        
        # Adjust pan to zoom from center
        self.pan_x = canvas_center_x - (canvas_center_x - self.pan_x) * (new_zoom / old_zoom)
        self.pan_y = canvas_center_y - (canvas_center_y - self.pan_y) * (new_zoom / old_zoom)
        
        self.zoom_level = new_zoom
        self.draw_topology()
        
        # Restore control panel position after zoom
        self._restore_control_panel_position()
    
    def on_mousewheel(self, event):
        """Handle mouse wheel zoom"""
        if event.delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()
    
    def recreate_topology(self):
        """Recreate topology with new mesh dimensions"""
        from topology.mesh_topology import MeshTopology
        from simulation.simulator import Simulator
        
        new_width = self.width_var.get()
        new_height = self.height_var.get()
        
        print(f"\nRecreating topology with {new_width}x{new_height} mesh...")
        self.topology = MeshTopology(width=new_width, height=new_height)
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
        self._update_simulation_details()
    
    def _restore_control_panel_position(self):
        """Restore control panel to fixed position after zoom"""
        if self.fixed_control_x is not None and self.fixed_control_y is not None:
            if hasattr(self, 'floating_controls') and self.floating_controls:
                self.canvas.coords(self.floating_controls, self.fixed_control_x, self.fixed_control_y)
    
    def _clear_previous_simulation(self):
        """Clear previous simulation path and reset state for new simulation"""
        # Cancel any pending path clear timer
        if self.path_clear_timer:
            self.root.after_cancel(self.path_clear_timer)
            self.path_clear_timer = None
        
        # Cancel auto-start timer
        if self.auto_start_timer:
            self.root.after_cancel(self.auto_start_timer)
            self.auto_start_timer = None
        
        # Clear completed path nodes
        self._clear_completed_path()
        
        # Reset simulation state
        self.animation_running = False
        self.is_paused = False
        self.is_auto_started = False
        self.click_count = 0
        
        # Redraw to clear all highlights
        self.draw_topology()
    
    def _clear_completed_path(self):
        """Clear the completed path visualization (green nodes and highlighted edges)"""
        # Reset completed path nodes to default color
        for addr in self.completed_path_nodes:
            if addr in self.node_items:
                # Reset to default node color (light blue)
                self.canvas.itemconfig(self.node_items[addr], fill='#64b5f6')
        
        # Clear the set
        self.completed_path_nodes.clear()
        
        # Reset highlighted edges
        for edge in list(self.highlighted_edges):
            if edge in self.edge_items:
                self.canvas.itemconfig(self.edge_items[edge], fill=self.colors['edge'], width=2)
        self.highlighted_edges.clear()
        
        # Clear selected nodes visual
        if self.selected_source and self.selected_source in self.node_items:
            self.canvas.itemconfig(self.node_items[self.selected_source], fill='#64b5f6', width=2)
        if self.selected_dest and self.selected_dest in self.node_items:
            self.canvas.itemconfig(self.node_items[self.selected_dest], fill='#64b5f6', width=2)
        
        self.canvas.update()
    
    def _on_transfer_type_change(self):
        """Handle transfer type change between 1:1 and 1:M"""
        self.transfer_type = self.transfer_type_var.get()
        
        # Clear any ongoing selection
        self._clear_previous_simulation()
        self.click_count = 0
        self.selected_source = None
        self.selected_dest = None
        self.selected_dests = []
        
        # Update instruction
        if hasattr(self, 'instruction_label'):
            if self.transfer_type == '1:1':
                self.instruction_label.config(
                    text="💡 Click nodes to select:\n1st click = Source, 2nd click = Destination",
                    fg='#1976d2'
                )
            else:
                self.instruction_label.config(
                    text="💡 Click source, then multiple destinations.\nClick source again to start simulation.",
                    fg='#1976d2'
                )
        
        # Clear displays
        self.src_display_label.config(text="Not selected", fg='#999999')
        self.dst_display_label.config(text="Not selected", fg='#999999')
    
    def _start_multicast_simulation(self):
        """Start 1:M multicast simulation"""
        self.click_count = 0
        self.current_dest_index = 0
        self.transfer_results = []
        
        if hasattr(self, 'instruction_label'):
            self.instruction_label.config(
                text=f"✓ Starting multicast to {len(self.selected_dests)} destinations...",
                fg='#1565c0'
            )
        
        # Auto-start first transfer after 5 seconds
        if self.auto_start_timer:
            self.root.after_cancel(self.auto_start_timer)
        
        def start_first_transfer():
            self.is_auto_started = True
            self._process_next_multicast_destination()
        
        self.auto_start_timer = self.root.after(5000, start_first_transfer)
        self.root.after(2000, self.clear_highlights)
    
    def _process_next_multicast_destination(self):
        """Process next destination in 1:M multicast mode"""
        if self.current_dest_index >= len(self.selected_dests):
            # All destinations reached - show results
            self._show_multicast_results()
            return
        
        # Set current destination
        current_dest = self.selected_dests[self.current_dest_index]
        self.selected_dest = current_dest
        
        # Update display
        self.dst_display_label.config(
            text=f"Dest {self.current_dest_index + 1}/{len(self.selected_dests)}: ({current_dest[0]},{current_dest[1]})",
            fg='#c62828'
        )
        
        # Start routing to this destination
        self.animate_routing()
    
    def _on_multicast_delivery_complete(self, dest_addr, path, latency):
        """Called when one destination in multicast receives the packet"""
        # Record transfer result
        result = {
            'destination': dest_addr,
            'path': path,
            'hops': len(path) - 1,
            'latency': latency,
            'status': 'Success'
        }
        self.transfer_results.append(result)
        
        # Send ACK signal back to source (visual only)
        self._send_ack_to_source(dest_addr)
    
    def _send_ack_to_source(self, from_dest):
        """Visualize ACK signal from destination back to source using reverse path"""
        if from_dest not in self.node_positions or self.selected_source not in self.node_positions:
            self._proceed_to_next_destination()
            return
        
        # Get the path that was used (should be stored from animate_routing)
        if not hasattr(self, 'current_path') or not self.current_path:
            self._proceed_to_next_destination()
            return
        
        # Reverse the path for ACK signal
        reverse_path = list(reversed(self.current_path))
        
        # Show ACK message
        self._update_flow_analysis(f"\n✉ ACK Signal: {from_dest} → {self.selected_source}")
        self._update_flow_analysis(f"  • Destination {self.current_dest_index + 1} reached successfully")
        self._update_flow_analysis(f"  • Sending acknowledgment back through path")
        self._update_flow_analysis(f"  • ACK Path: {' → '.join(str(n) for n in reverse_path)}")
        
        # Animate ACK signal hopping back through the path
        self._animate_ack_through_path(reverse_path, 0)
    
    def _animate_ack_through_path(self, path, index):
        """Animate ACK signal moving back through the path hop by hop"""
        if index >= len(path) - 1:
            # ACK reached source - proceed to next destination
            self._update_flow_analysis(f"  • ACK received at source {self.selected_source}")
            self._proceed_to_next_destination()
            return
        
        # Get current and next hop
        current = path[index]
        next_hop = path[index + 1]
        
        if current not in self.node_positions or next_hop not in self.node_positions:
            # Skip this hop
            self._animate_ack_through_path(path, index + 1)
            return
        
        # Get positions
        cx, cy = self.node_positions[current]
        ccx, ccy = self._transform_coords(cx, cy)
        
        nx, ny = self.node_positions[next_hop]
        ncx, ncy = self._transform_coords(nx, ny)
        
        # Animate green ACK signal from current to next
        def next_ack_hop():
            self._animate_ack_through_path(path, index + 1)
        
        self.packet_animator.draw_transfer_arrow(
            ccx, ccy, ncx, ncy,
            phase='ack',
            callback=next_ack_hop
        )
    
    def _proceed_to_next_destination(self):
        """Move to next destination in multicast sequence"""
        self.current_dest_index += 1
        
        # Proceed to next transfer after brief delay
        if self.current_dest_index < len(self.selected_dests):
            self._update_flow_analysis(f"\n{'='*60}")
            self._update_flow_analysis(f"Proceeding to destination {self.current_dest_index + 1}/{len(self.selected_dests)}...")
            # Short delay before next transfer (1 second)
            self.root.after(1000, self._process_next_multicast_destination)
        else:
            # All done - show results popup
            self._show_multicast_results()
    
    def _show_multicast_results(self):
        """Show final results popup for 1:M multicast transfer"""
        # Create results window
        results_window = tk.Toplevel(self.root)
        results_window.title("Multicast Transfer Results")
        results_window.geometry("700x500")
        results_window.configure(bg='white')
        
        # Header
        header_frame = tk.Frame(results_window, bg='#1976d2', height=60)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text="✓ Multicast Transfer Complete",
                font=("Arial", 16, "bold"), bg='#1976d2', fg='white').pack(pady=15)
        
        # Summary
        summary_frame = tk.Frame(results_window, bg='#e3f2fd', relief=tk.RIDGE, bd=2)
        summary_frame.pack(fill=tk.X, padx=20, pady=10)
        
        total_hops = sum(r['hops'] for r in self.transfer_results)
        total_latency = sum(r['latency'] for r in self.transfer_results)
        avg_hops = total_hops / len(self.transfer_results) if self.transfer_results else 0
        avg_latency = total_latency / len(self.transfer_results) if self.transfer_results else 0
        
        summary_text = f"""Source: {self.selected_source}
Destinations: {len(self.transfer_results)}
Total Hops: {total_hops}
Average Hops: {avg_hops:.1f}
Total Latency: {total_latency} time units
Average Latency: {avg_latency:.1f} time units"""
        
        tk.Label(summary_frame, text=summary_text, font=("Courier", 10),
                bg='#e3f2fd', fg='#0d47a1', justify=tk.LEFT).pack(padx=15, pady=10)
        
        # Detailed results table
        tk.Label(results_window, text="Detailed Transfer Results:",
                font=("Arial", 12, "bold"), bg='white', fg='#333').pack(anchor=tk.W, padx=20, pady=(10, 5))
        
        # Scrollable frame for results
        canvas_frame = tk.Frame(results_window, bg='white')
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        canvas = tk.Canvas(canvas_frame, bg='white', highlightthickness=0)
        scrollbar = tk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='white')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Table headers
        headers_frame = tk.Frame(scrollable_frame, bg='#37474f')
        headers_frame.pack(fill=tk.X)
        
        tk.Label(headers_frame, text="#", width=5, font=("Arial", 9, "bold"),
                bg='#37474f', fg='white', anchor='w').pack(side=tk.LEFT, padx=2, pady=5)
        tk.Label(headers_frame, text="Destination", width=15, font=("Arial", 9, "bold"),
                bg='#37474f', fg='white', anchor='w').pack(side=tk.LEFT, padx=2, pady=5)
        tk.Label(headers_frame, text="Hops", width=8, font=("Arial", 9, "bold"),
                bg='#37474f', fg='white', anchor='w').pack(side=tk.LEFT, padx=2, pady=5)
        tk.Label(headers_frame, text="Latency", width=10, font=("Arial", 9, "bold"),
                bg='#37474f', fg='white', anchor='w').pack(side=tk.LEFT, padx=2, pady=5)
        tk.Label(headers_frame, text="Status", width=10, font=("Arial", 9, "bold"),
                bg='#37474f', fg='white', anchor='w').pack(side=tk.LEFT, padx=2, pady=5)
        
        # Results rows
        for i, result in enumerate(self.transfer_results):
            row_bg = '#f5f5f5' if i % 2 == 0 else 'white'
            row_frame = tk.Frame(scrollable_frame, bg=row_bg)
            row_frame.pack(fill=tk.X)
            
            tk.Label(row_frame, text=str(i+1), width=5, font=("Courier", 9),
                    bg=row_bg, fg='#333', anchor='w').pack(side=tk.LEFT, padx=2, pady=3)
            tk.Label(row_frame, text=str(result['destination']), width=15, font=("Courier", 9),
                    bg=row_bg, fg='#333', anchor='w').pack(side=tk.LEFT, padx=2, pady=3)
            tk.Label(row_frame, text=str(result['hops']), width=8, font=("Courier", 9),
                    bg=row_bg, fg='#333', anchor='w').pack(side=tk.LEFT, padx=2, pady=3)
            tk.Label(row_frame, text=str(result['latency']), width=10, font=("Courier", 9),
                    bg=row_bg, fg='#333', anchor='w').pack(side=tk.LEFT, padx=2, pady=3)
            tk.Label(row_frame, text=result['status'], width=10, font=("Courier", 9),
                    bg=row_bg, fg='#2e7d32', anchor='w').pack(side=tk.LEFT, padx=2, pady=3)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Close button
        tk.Button(results_window, text="Close", command=results_window.destroy,
                 bg='#1976d2', fg='white', font=("Arial", 11, "bold"),
                 padx=30, pady=8, cursor="hand2").pack(pady=15)
    
    def run(self):
        """Start the GUI"""
        self.root.mainloop()
