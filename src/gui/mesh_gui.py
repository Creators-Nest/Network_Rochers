"""
Mesh Topology GUI with Control Panel and Visualization
Implements buffer-based routing with XY algorithm and AODV protocol
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import math
from typing import Optional, Tuple, List, Dict

# Use relative imports within src package
from ..core.node import Node, Direction, NodeStatus
from ..core.packet import Packet, PacketStatus, PacketType
from ..core.buffer import Buffer
from ..routing.xy_routing import XYRouting
from ..simulation.mesh_simulator import MeshSimulator, SimulationPhase


class MeshTopologyGUI:
    """
    Complete GUI for Mesh Topology Simulation
    
    Layout:
    - Left: Control Panel (configuration, routing, view controls, statistics)
    - Right: Visualization Area (network display with nodes, connections, packets)
    """
    
    def __init__(self, parent: tk.Frame, main_window):
        """
        Initialize Mesh Topology GUI
        
        Args:
            parent: Parent frame
            main_window: Reference to main window for status updates
        """
        self.parent = parent
        self.main_window = main_window
        
        # Network components
        self.nodes: Dict[Tuple[int, int], Node] = {}
        self.routing_algorithm = XYRouting()
        self.packets: List[Packet] = []
        self.simulator: Optional[MeshSimulator] = None  # Real simulator engine
        
        # Visualization state
        self.rows = 4
        self.cols = 4
        self.node_radius = 25  # Will be auto-adjusted
        self.zoom_level = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self.auto_adjust_size = True  # Auto-adjust node size based on grid
        
        # Selection state
        self.source_node: Optional[Tuple[int, int]] = None
        self.dest_node: Optional[Tuple[int, int]] = None
        self.selected_node: Optional[Tuple[int, int]] = None
        
        # Simulation state
        self.is_simulating = False
        self.is_paused = False
        self.simulation_step = 0
        self.current_packet: Optional[Packet] = None
        self.packet_data = ""  # User-provided packet data
        self.base_speed = 500  # Base speed in ms (1x speed)
        
        # Real simulation state tracking
        self.current_sim_phase = SimulationPhase.IDLE
        self.sim_events: List[str] = []
        
        # Colors - Enhanced for packet flow visualization
        self.colors = {
            # Node states
            'node_normal': '#3498db',           # Blue - Idle nodes
            'node_source': '#2ecc71',           # Green - Source node
            'node_dest': '#e74c3c',             # Red - Destination node
            'node_selected': '#f39c12',         # Orange - Selected
            'node_active': '#9b59b6',           # Purple - Active routing
            
            # Packet flow phases (based on mesh-working-flow)
            'phase_request': '#f39c12',         # Orange - Request (RREQ) phase
            'phase_acknowledge': '#3498db',     # Blue - Acknowledge (RREP) phase
            'phase_verify': '#9b59b6',          # Purple - Verify & forward routing
            'phase_send': '#2ecc71',            # Green - Data transmission
            
            # Buffer and flow control
            'buffer_normal': '#95a5a6',         # Gray - Normal buffer state
            'buffer_req': '#f39c12',            # Orange - REQ signal active
            'buffer_ack': '#3498db',            # Blue - ACK signal active
            'buffer_choke': '#e74c3c',          # Red - Choke/congestion
            'buffer_transfer': '#2ecc71',       # Green - Data transfer
            
            # Visual elements
            'connection': '#95a5a6',            # Gray - Network links
            'packet': '#e67e22',                # Orange - Packet marker
            'background': '#ecf0f1',            # Light gray - Canvas bg
            'text': '#2c3e50'                   # Dark blue - Text
        }
        
        # Packet flow phase tracking
        self.packet_phase = None  # Current phase: 'request', 'acknowledge', 'verify', 'send'
        
        # Hover tooltip state
        self.hover_node = None
        self.hover_timer = None
        self.tooltip_window = None
        self.hover_delay = 2000  # 2 seconds in milliseconds
        
        # Create GUI layout
        self._create_layout()
        self._create_aodv_status_bar()  # Create AODV protocol status bar at top
        self._create_control_panel()
        
        # Initialize network BEFORE creating visualization
        # (so nodes exist when canvas tries to draw)
        self.create_mesh_network()
        
        # Create visualization area (will draw the network)
        self._create_visualization_area()
    
    def _create_layout(self):
        """Create main layout with left panel, top indicator bar, visualization, and footer status bar"""
        # Left panel (Control Panel) - Fixed width
        self.control_panel = tk.Frame(
            self.parent,
            bg="#ffffff",
            width=350,
            relief=tk.RAISED,
            borderwidth=2
        )
        self.control_panel.pack(side=tk.LEFT, fill=tk.Y)
        self.control_panel.pack_propagate(False)
        
        # Right area container
        right_container = tk.Frame(self.parent, bg=self.colors['background'])
        right_container.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Top indicator bar (fixed height) - AODV Protocol Status
        self.indicator_bar = tk.Frame(
            right_container,
            bg="white",  # Changed to white background
            height=80,  # Taller for more info
            relief=tk.RAISED,
            borderwidth=2
        )
        self.indicator_bar.pack(side=tk.TOP, fill=tk.X)
        self.indicator_bar.pack_propagate(False)
        
        # Visualization area in the middle
        self.viz_frame = tk.Frame(right_container, bg=self.colors['background'])
        self.viz_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Bottom status bar (fixed height) - moved here from footer
        self.status_bar = tk.Frame(
            right_container,
            bg="white",  # White background
            height=30,
            relief=tk.SUNKEN,
            borderwidth=2
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_bar.pack_propagate(False)
    
    def _create_aodv_status_bar(self):
        """Create comprehensive AODV protocol status bar at top showing detailed packet info"""
        # Main container with white background
        main_container = tk.Frame(self.indicator_bar, bg="white")
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left section - Hop counter with icon
        left_section = tk.Frame(main_container, bg="#f0f0f0", relief=tk.RIDGE, borderwidth=2)
        left_section.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        
        self.hop_icon_label = tk.Label(
            left_section,
            text="📍",
            bg="#f0f0f0",
            fg="#2c3e50",
            font=("Arial", 20)
        )
        self.hop_icon_label.pack(side=tk.LEFT, padx=(8, 5))
        
        self.hop_info_label = tk.Label(
            left_section,
            text="Hop 0/0",
            bg="#f0f0f0",
            fg="#3498db",
            font=("Arial", 14, "bold")
        )
        self.hop_info_label.pack(side=tk.LEFT, padx=(0, 8))
        
        # Center section - Phase and route information
        center_section = tk.Frame(main_container, bg="#f0f0f0", relief=tk.RIDGE, borderwidth=2)
        center_section.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # Phase indicator with icon
        phase_frame = tk.Frame(center_section, bg="#f0f0f0")
        phase_frame.pack(side=tk.LEFT, padx=10, pady=5)
        
        tk.Label(
            phase_frame,
            text="Phase:",
            bg="#f0f0f0",
            fg="#2c3e50",
            font=("Arial", 10)
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        self.phase_display = tk.Label(
            phase_frame,
            text="📦 Data Transmission",
            bg="#f0f0f0",
            fg="#2ecc71",
            font=("Arial", 12, "bold")
        )
        self.phase_display.pack(side=tk.LEFT)
        
        # Separator
        tk.Label(
            center_section,
            text="|",
            bg="#f0f0f0",
            fg="#7f8c8d",
            font=("Arial", 14)
        ).pack(side=tk.LEFT, padx=5)
        
        # Route information
        route_frame = tk.Frame(center_section, bg="#f0f0f0")
        route_frame.pack(side=tk.LEFT, padx=5, pady=5)
        
        tk.Label(
            route_frame,
            text="Route:",
            bg="#f0f0f0",
            fg="#2c3e50",
            font=("Arial", 10)
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        self.route_display = tk.Label(
            route_frame,
            text="Clock: 13 | DATA DELIVERED at (2, 2)",
            bg="#f0f0f0",
            fg="#2c3e50",
            font=("Arial", 11, "bold")
        )
        self.route_display.pack(side=tk.LEFT)
        
        # Right section - Progress and signals
        right_section = tk.Frame(main_container, bg="#f0f0f0", relief=tk.RIDGE, borderwidth=2)
        right_section.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        
        # Progress indicator
        progress_frame = tk.Frame(right_section, bg="#f0f0f0")
        progress_frame.pack(side=tk.LEFT, padx=10, pady=5)
        
        tk.Label(
            progress_frame,
            text="Progress:",
            bg="#f0f0f0",
            fg="#2c3e50",
            font=("Arial", 10)
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        self.progress_display = tk.Label(
            progress_frame,
            text="100%",
            bg="#f0f0f0",
            fg="#2ecc71",
            font=("Arial", 12, "bold")
        )
        self.progress_display.pack(side=tk.LEFT)
        
        # Separator
        tk.Label(
            right_section,
            text="|",
            bg="#f0f0f0",
            fg="#7f8c8d",
            font=("Arial", 14)
        ).pack(side=tk.LEFT, padx=5)
        
        # Signals indicator
        signals_frame = tk.Frame(right_section, bg="#f0f0f0")
        signals_frame.pack(side=tk.LEFT, padx=(5, 10), pady=5)
        
        tk.Label(
            signals_frame,
            text="Signals:",
            bg="#f0f0f0",
            fg="#2c3e50",
            font=("Arial", 10)
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        self.signals_display = tk.Label(
            signals_frame,
            text="Transferring data",
            bg="#f0f0f0",
            fg="#3498db",
            font=("Arial", 11, "bold")
        )
        self.signals_display.pack(side=tk.LEFT)
        
        # Initialize with default "waiting" state
        self._reset_aodv_status()
    
    def _reset_aodv_status(self):
        """Reset AODV status bar to initial state"""
        self.hop_info_label.config(text="Hop 0/0", fg="#7f8c8d")
        self.phase_display.config(text="⚪ Waiting to Start", fg="#7f8c8d")
        self.route_display.config(text="No route selected", fg="#7f8c8d")
        self.progress_display.config(text="0%", fg="#7f8c8d")
        self.signals_display.config(text="Idle", fg="#7f8c8d")
        
    
    
    def _update_aodv_status(self, hop_current, hop_total, phase_text, phase_color, 
                            route_text, progress_pct, signals_text):
        """Update AODV status bar with current packet information"""
        self.hop_info_label.config(text=f"Hop {hop_current}/{hop_total}", fg="#3498db")
        self.phase_display.config(text=phase_text, fg=phase_color)
        self.route_display.config(text=route_text, fg="#2c3e50")
        self.progress_display.config(text=f"{progress_pct}%", fg="#2ecc71" if progress_pct == 100 else "#3498db")
        self.signals_display.config(text=signals_text, fg="#3498db")
    
    def _create_section(self, parent, title: str) -> tk.Frame:
        """Create the footer status bar showing AODV protocol flow progress"""
        # Title section
        title_frame = tk.Frame(self.footer_bar, bg="#1a252f")
        title_frame.pack(side=tk.TOP, fill=tk.X, pady=(5, 0))
        
        tk.Label(
            title_frame,
            text="📡 AODV Protocol Flow Status",
            font=("Arial", 11, "bold"),
            bg="#1a252f",
            fg="#3498db"
        ).pack(side=tk.LEFT, padx=15)
        
        # Flow progress bar frame
        flow_frame = tk.Frame(self.footer_bar, bg="#1a252f")
        flow_frame.pack(side=tk.TOP, fill=tk.X, expand=True, padx=20, pady=5)
        
        # Create flow stages based on mesh-working-flow
        self.flow_stages = [
            {
                'name': '1. REQUEST',
                'description': 'RREQ Broadcast',
                'icon': '📤',
                'color': self.colors['phase_request'],
                'detail': 'Source broadcasts RREQ to find path'
            },
            {
                'name': '2. FORWARD',
                'description': 'Route Discovery',
                'icon': '🔄',
                'color': '#e67e22',  # Orange
                'detail': 'Intermediate nodes forward RREQ'
            },
            {
                'name': '3. ACKNOWLEDGE',
                'description': 'RREP Reply',
                'icon': '📥',
                'color': self.colors['phase_acknowledge'],
                'detail': 'Destination sends RREP back'
            },
            {
                'name': '4. VERIFY',
                'description': 'Path Setup',
                'icon': '✓',
                'color': self.colors['phase_verify'],
                'detail': 'Nodes create forward routes'
            },
            {
                'name': '5. SEND',
                'description': 'Data Transfer',
                'icon': '📦',
                'color': self.colors['phase_send'],
                'detail': 'Actual data transmission'
            }
        ]
        
        # Create visual flow indicators
        self.flow_indicators = []
        for i, stage in enumerate(self.flow_stages):
            # Stage frame
            stage_frame = tk.Frame(flow_frame, bg="#1a252f")
            stage_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2)
            
            # Stage box with border
            stage_box = tk.Frame(stage_frame, bg="#2c3e50", relief=tk.RIDGE, borderwidth=2)
            stage_box.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
            
            # Icon and name
            header_frame = tk.Frame(stage_box, bg="#2c3e50")
            header_frame.pack(fill=tk.X, pady=(3, 0))
            
            icon_label = tk.Label(
                header_frame,
                text=stage['icon'],
                bg="#2c3e50",
                fg="white",
                font=("Arial", 14)
            )
            icon_label.pack(side=tk.LEFT, padx=(5, 2))
            
            name_label = tk.Label(
                header_frame,
                text=stage['name'],
                bg="#2c3e50",
                fg="#95a5a6",
                font=("Arial", 8, "bold")
            )
            name_label.pack(side=tk.LEFT)
            
            # Description
            desc_label = tk.Label(
                stage_box,
                text=stage['description'],
                bg="#2c3e50",
                fg="#7f8c8d",
                font=("Arial", 7)
            )
            desc_label.pack(pady=(0, 3))
            
            # Store references for updating
            self.flow_indicators.append({
                'box': stage_box,
                'icon': icon_label,
                'name': name_label,
                'desc': desc_label,
                'stage': stage
            })
            
            # Add arrow between stages (except last one)
            if i < len(self.flow_stages) - 1:
                arrow_label = tk.Label(
                    flow_frame,
                    text="→",
                    bg="#1a252f",
                    fg="#7f8c8d",
                    font=("Arial", 16, "bold")
                )
                arrow_label.pack(side=tk.LEFT, padx=2)
        
        # Detail status label at bottom
        self.flow_detail_label = tk.Label(
            self.footer_bar,
            text="ℹ️ Select source and destination nodes to start simulation",
            bg="#1a252f",
            fg="#95a5a6",
            font=("Arial", 9),
            anchor=tk.W
        )
        self.flow_detail_label.pack(side=tk.BOTTOM, fill=tk.X, padx=15, pady=(0, 5))
    
    def _create_control_panel(self):
        """Create modern left control panel with collapsible sections"""
        # Title with icon
        title_frame = tk.Frame(self.control_panel, bg="#000000")
        title_frame.pack(fill=tk.X, pady=(0, 5))
        
        title_label = tk.Label(
            title_frame,
            text="⚙ Control Panel",
            font=("Arial", 14, "bold"),
            bg="#000000",
            fg="white"
        )
        title_label.pack(pady=8)
        
        # Create container for canvas and scrollbar
        scroll_container = tk.Frame(self.control_panel, bg="#000000")
        scroll_container.pack(fill=tk.BOTH, expand=True)
        
        # Create scrollable canvas
        self.control_canvas = tk.Canvas(
            scroll_container, 
            bg="#565a5e", 
            highlightthickness=0,
            bd=0
        )
        
        # Scrollbar
        scrollbar = tk.Scrollbar(
            scroll_container, 
            orient="vertical", 
            command=self.control_canvas.yview,
            bg="#676e74",
            width=12
        )
        
        self.scrollable_frame = tk.Frame(self.control_canvas, bg="#000000")
        
        # Configure scrolling
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.control_canvas.configure(scrollregion=self.control_canvas.bbox("all"))
        )
        
        self.canvas_window = self.control_canvas.create_window(
            (0, 0), 
            window=self.scrollable_frame, 
            anchor="nw",
            width=328
        )
        
        self.control_canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.control_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Mouse wheel scrolling
        def scroll_mousewheel(event):
            if hasattr(event, 'delta'):
                delta = event.delta
                if abs(delta) > 10:
                    delta = delta // 120
                self.control_canvas.yview_scroll(-delta, "units")
            elif event.num == 5:
                self.control_canvas.yview_scroll(1, "units")
            elif event.num == 4:
                self.control_canvas.yview_scroll(-1, "units")
            return "break"
        
        def bind_to_mousewheel(widget):
            widget.bind("<MouseWheel>", scroll_mousewheel)
            widget.bind("<Button-4>", scroll_mousewheel)
            widget.bind("<Button-5>", scroll_mousewheel)
            for child in widget.winfo_children():
                bind_to_mousewheel(child)
        
        bind_to_mousewheel(self.control_panel)
        bind_to_mousewheel(self.control_canvas)
        bind_to_mousewheel(self.scrollable_frame)
        
        # Collapsible sections state
        self.section_states = {
            'topology': tk.BooleanVar(value=False),  # Collapsed by default
            'routing': tk.BooleanVar(value=True),    # Expanded
            'view': tk.BooleanVar(value=False),
            'simulation': tk.BooleanVar(value=True),
            'statistics': tk.BooleanVar(value=True)
        }
        
        # Add control sections
        self._create_topology_config_collapsible(self.scrollable_frame)
        self._create_packet_routing_collapsible(self.scrollable_frame)
        self._create_view_controls_collapsible(self.scrollable_frame)
        self._create_simulation_controls_collapsible(self.scrollable_frame)
        self._create_statistics_collapsible(self.scrollable_frame)
    
    def _create_collapsible_section(self, parent, title, icon, state_var):
        """Create a collapsible section with toggle button"""
        # Container
        container = tk.Frame(parent, bg="white")
        container.pack(fill=tk.X, padx=5, pady=2)
        
        # Header button (clickable to toggle)
        header = tk.Frame(container, bg="#e8e8e8", relief=tk.RAISED, bd=1)
        header.pack(fill=tk.X)
        
        def toggle():
            state_var.set(not state_var.get())
            update_arrow()
            if state_var.get():
                content_frame.pack(fill=tk.X, padx=2, pady=2)
            else:
                content_frame.pack_forget()
        
        header_btn = tk.Button(
            header,
            text=f"{icon} {title}",
            command=toggle,
            bg="#e8e8e8",
            fg="#000000",
            font=("Arial", 10, "bold"),
            relief=tk.FLAT,
            anchor="w",
            padx=10,
            pady=6,
            cursor="hand2",
            activebackground="#d0d0d0",
            activeforeground="#000000"
        )
        header_btn.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Arrow indicator
        arrow_label = tk.Label(
            header,
            text="▼" if state_var.get() else "▶",
            bg="#e8e8e8",
            fg="#2c3e50",
            font=("Arial", 10, "bold")
        )
        arrow_label.pack(side=tk.RIGHT, padx=10)
        
        def update_arrow():
            arrow_label.config(text="▼" if state_var.get() else "▶")
        
        # Content frame
        content_frame = tk.Frame(container, bg="white")
        if state_var.get():
            content_frame.pack(fill=tk.X, padx=2, pady=2)
        
        return content_frame
    
    def _create_topology_config_collapsible(self, parent):
        """Create collapsible topology configuration section"""
        content = self._create_collapsible_section(
            parent, "Topology Configuration", "⬛", self.section_states['topology']
        )
        
        # Grid size controls
        grid_frame = tk.Frame(content, bg="white", relief=tk.GROOVE, bd=2)
        grid_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(
            grid_frame,
            text="Rows:",
            bg="white",
            fg="#000000",
            font=("Arial", 9)
        ).grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        
        self.rows_spinbox = tk.Spinbox(
            grid_frame,
            from_=2,
            to=50,
            width=8,
            font=("Arial", 9)
        )
        self.rows_spinbox.delete(0, tk.END)
        self.rows_spinbox.insert(0, str(self.rows))
        self.rows_spinbox.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(
            grid_frame,
            text="Columns:",
            bg="white",
            fg="#000000",
            font=("Arial", 9)
        ).grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        
        self.cols_spinbox = tk.Spinbox(
            grid_frame,
            from_=2,
            to=50,
            width=8,
            font=("Arial", 9)
        )
        self.cols_spinbox.delete(0, tk.END)
        self.cols_spinbox.insert(0, str(self.cols))
        self.cols_spinbox.grid(row=1, column=1, padx=5, pady=5)
        
        # Apply button
        tk.Button(
            content,
            text="✓ Apply Configuration",
            command=self.apply_topology_config,
            bg="#27ae60",
            fg="white",
            font=("Arial", 9, "bold"),
            relief=tk.RAISED,
            cursor="hand2",
            pady=5
        ).pack(pady=5, padx=5, fill=tk.X)
    
    def _create_packet_routing_collapsible(self, parent):
        """Create collapsible packet routing section"""
        content = self._create_collapsible_section(
            parent, "Packet Routing", "📦", self.section_states['routing']
        )
        
        # Instructions
        tk.Label(
            content,
            text="Click nodes to select source & destination",
            bg="white",
            fg="#555555",
            font=("Arial", 8, "italic"),
            wraplength=280,
            justify=tk.LEFT
        ).pack(pady=(5, 10), padx=10)
        
        # Packet data input
        tk.Label(
            content,
            text="Packet Data:",
            bg="white",
            fg="#000000",
            font=("Arial", 9, "bold")
        ).pack(anchor=tk.W, padx=10)
        
        self.data_entry = tk.Text(
            content,
            height=3,
            width=30,
            font=("Courier", 9),
            wrap=tk.WORD
        )
        self.data_entry.pack(padx=10, pady=5, fill=tk.X)
        self.data_entry.insert(1.0, "Sample data packet")
        
        tk.Label(
            content,
            text="Enter data to send in packet\n(Will be transmitted as payload)",
            bg="white",
            fg="#777777",
            font=("Arial", 7, "italic")
        ).pack(padx=10)
        
        # Source and destination display
        info_frame = tk.Frame(content, bg="#f0f0f0", relief=tk.SUNKEN, bd=2)
        info_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(
            info_frame,
            text="Source:",
            bg="#f0f0f0",
            fg="#000000",
            font=("Arial", 9, "bold")
        ).grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        
        self.source_label = tk.Label(
            info_frame,
            text="Not selected",
            bg="#f0f0f0",
            fg="#27ae60",
            font=("Arial", 9, "bold")
        )
        self.source_label.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        tk.Label(
            info_frame,
            text="Destination:",
            bg="#f0f0f0",
            fg="#000000",
            font=("Arial", 9, "bold")
        ).grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        
        self.dest_label = tk.Label(
            info_frame,
            text="Not selected",
            bg="#f0f0f0",
            fg="#e74c3c",
            font=("Arial", 9, "bold")
        )
        self.dest_label.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
    
    def _create_view_controls_collapsible(self, parent):
        """Create collapsible view controls section"""
        content = self._create_collapsible_section(
            parent, "View Controls", "🔍", self.section_states['view']
        )
        
        btn_frame = tk.Frame(content, bg="white")
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Button(
            btn_frame,
            text="+ Zoom In",
            command=lambda: self.zoom(1.2),
            bg="#3498db",
            fg="white",
            font=("Arial", 8),
            width=12
        ).pack(side=tk.LEFT, padx=2)
        
        tk.Button(
            btn_frame,
            text="− Zoom Out",
            command=lambda: self.zoom(0.8),
            bg="#3498db",
            fg="white",
            font=("Arial", 8),
            width=12
        ).pack(side=tk.RIGHT, padx=2)
        
        tk.Button(
            content,
            text="⟲ Reset View",
            command=self.reset_view,
            bg="#95a5a6",
            fg="white",
            font=("Arial", 8),
            pady=3
        ).pack(pady=5, padx=5, fill=tk.X)
    
    def _create_simulation_controls_collapsible(self, parent):
        """Create collapsible simulation controls section"""
        content = self._create_collapsible_section(
            parent, "Simulation Controls", "▶", self.section_states['simulation']
        )
        
        # Start button
        self.start_btn = tk.Button(
            content,
            text="▶ Start Simulation",
            command=self.start_simulation,
            bg="#000000",
            fg="black",
            font=("Arial", 10, "bold"),
            relief=tk.RAISED,
            cursor="hand2",
            pady=8
        )
        self.start_btn.pack(pady=5, padx=5, fill=tk.X)
        
        # Step button
        self.step_btn = tk.Button(
            content,
            text="→ Step Forward",
            command=self.step_simulation,
            bg="#FFFDFD",
            fg="black",
            font=("Arial", 9),
            state=tk.DISABLED,
            cursor="hand2",
            pady=6
        )
        self.step_btn.pack(pady=5, padx=5, fill=tk.X)
        
        # Pause button
        self.pause_btn = tk.Button(
            content,
            text="⏸ Pause",
            command=self.pause_simulation,
            bg="#f39c12",
            fg="black",
            font=("Arial", 9),
            state=tk.DISABLED,
            cursor="hand2",
            pady=6
        )
        self.pause_btn.pack(pady=5, padx=5, fill=tk.X)
        
        # Reset button
        tk.Button(
            content,
            text="⟲ Reset",
            command=self.reset_simulation,
            bg="#e74c3c",
            fg="black",
            font=("Arial", 9),
            cursor="hand2",
            pady=6
        ).pack(pady=5, padx=5, fill=tk.X)
        
        # Speed control
        speed_frame = tk.Frame(content, bg="#f8f8f8", relief=tk.GROOVE, bd=2)
        speed_frame.pack(fill=tk.X, padx=5, pady=10)
        
        tk.Label(
            speed_frame,
            text="⚡ Speed Control",
            bg="#f8f8f8",
            fg="#2c3e50",
            font=("Arial", 9, "bold")
        ).pack(pady=5)
        
        speed_control_frame = tk.Frame(speed_frame, bg="#f8f8f8")
        speed_control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(
            speed_control_frame,
            text="Speed:",
            bg="#f8f8f8",
            fg="#000000",
            font=("Arial", 8)
        ).pack(side=tk.LEFT, padx=5)
        
        self.speed_multiplier = tk.DoubleVar(value=1.0)
        speed_slider = tk.Scale(
            speed_control_frame,
            from_=0.2,
            to=5.0,
            resolution=0.1,
            orient=tk.HORIZONTAL,
            variable=self.speed_multiplier,
            command=self._update_speed_display,
            bg="#f8f8f8",
            fg="#000000",
            highlightthickness=0,
            length=150
        )
        speed_slider.pack(side=tk.LEFT, padx=5)
        
        self.speed_display = tk.Label(
            speed_control_frame,
            text="1.0x",
            bg="#f8f8f8",
            fg="#27ae60",
            font=("Arial", 9, "bold"),
            width=5
        )
        self.speed_display.pack(side=tk.LEFT, padx=5)
        
        # Auto-step checkbox
        self.auto_step_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            speed_frame,
            text="Auto-step (continuous simulation)",
            variable=self.auto_step_var,
            bg="#f8f8f8",
            fg="#000000",
            selectcolor="#e0e0e0",
            font=("Arial", 8),
            activebackground="#f0f0f0",
            activeforeground="#000000"
        ).pack(pady=5)
    
    def _create_statistics_collapsible(self, parent):
        """Create collapsible statistics section"""
        content = self._create_collapsible_section(
            parent, "Statistics", "📊", self.section_states['statistics']
        )
        
        # Statistics text area
        self.stats_text = scrolledtext.ScrolledText(
            content,
            height=15,
            width=35,
            font=("Courier", 8),
            bg="#1a1a1a",
            fg="#00ff00",
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        self.stats_text.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)
    
    def _create_topology_config(self, parent):
        """Create topology configuration section"""
        section = self._create_section(parent, "📐 Topology Configuration")
        
        # Grid size controls
        grid_frame = tk.Frame(section, bg="#34495e")
        grid_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(
            grid_frame,
            text="Rows:",
            bg="#34495e",
            fg="white",
            font=("Arial", 10)
        ).grid(row=0, column=0, sticky=tk.W, pady=2)
        
        self.rows_spinbox = tk.Spinbox(
            grid_frame,
            from_=2,
            to=50,
            width=10,
            font=("Arial", 10)
        )
        self.rows_spinbox.delete(0, tk.END)
        self.rows_spinbox.insert(0, str(self.rows))
        self.rows_spinbox.grid(row=0, column=1, padx=5, pady=2)
        
        tk.Label(
            grid_frame,
            text="Columns:",
            bg="#34495e",
            fg="white",
            font=("Arial", 10)
        ).grid(row=1, column=0, sticky=tk.W, pady=2)
        
        self.cols_spinbox = tk.Spinbox(
            grid_frame,
            from_=2,
            to=50,
            width=10,
            font=("Arial", 10)
        )
        self.cols_spinbox.delete(0, tk.END)
        self.cols_spinbox.insert(0, str(self.cols))
        self.cols_spinbox.grid(row=1, column=1, padx=5, pady=2)
        
        # Apply button
        apply_btn = tk.Button(
            section,
            text="Apply Configuration",
            command=self.apply_topology_config,
            bg="#3498db",
            fg="white",
            font=("Arial", 10, "bold"),
            relief=tk.RAISED,
            cursor="hand2"
        )
        apply_btn.pack(pady=10, padx=10, fill=tk.X)
    
    def _create_packet_routing(self, parent):
        """Create packet routing section"""
        section = self._create_section(parent, "📦 Packet Routing")
        
        # Instructions
        info_label = tk.Label(
            section,
            text="Click nodes to select source (green)\nand destination (red)",
            bg="#34495e",
            fg="#ecf0f1",
            font=("Arial", 9),
            justify=tk.LEFT
        )
        info_label.pack(pady=5, padx=10)
        
        # Packet Data Input
        data_label = tk.Label(
            section,
            text="Packet Data:",
            bg="#34495e",
            fg="white",
            font=("Arial", 10, "bold")
        )
        data_label.pack(pady=(10, 2), padx=10, anchor=tk.W)
        
        self.data_entry = scrolledtext.ScrolledText(
            section,
            height=4,
            width=30,
            font=("Arial", 9),
            wrap=tk.WORD,
            bg="white",
            fg="#2c3e50"
        )
        self.data_entry.pack(pady=5, padx=10, fill=tk.X)
        self.data_entry.insert(1.0, "Sample data packet")
        
        # Data info
        data_info = tk.Label(
            section,
            text="Enter data to send in packet\n(Will be transmitted as payload)",
            bg="#34495e",
            fg="#95a5a6",
            font=("Arial", 8),
            justify=tk.LEFT
        )
        data_info.pack(pady=(0, 5), padx=10, anchor=tk.W)
        
        # Source selection
        source_frame = tk.Frame(section, bg="#34495e")
        source_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(
            source_frame,
            text="Source:",
            bg="#34495e",
            fg="white",
            font=("Arial", 10, "bold")
        ).pack(side=tk.LEFT)
        
        self.source_label = tk.Label(
            source_frame,
            text="Not selected",
            bg="#34495e",
            fg="#2ecc71",
            font=("Arial", 10)
        )
        self.source_label.pack(side=tk.LEFT, padx=10)
        
        # Destination selection
        dest_frame = tk.Frame(section, bg="#34495e")
        dest_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(
            dest_frame,
            text="Destination:",
            bg="#34495e",
            fg="white",
            font=("Arial", 10, "bold")
        ).pack(side=tk.LEFT)
        
        self.dest_label = tk.Label(
            dest_frame,
            text="Not selected",
            bg="#34495e",
            fg="#e74c3c",
            font=("Arial", 10)
        )
        self.dest_label.pack(side=tk.LEFT, padx=10)
        
        # Clear selections button
        clear_btn = tk.Button(
            section,
            text="Clear Selection",
            command=self.clear_selection,
            bg="#e74c3c",
            fg="white",
            font=("Arial", 9),
            cursor="hand2"
        )
        clear_btn.pack(pady=5, padx=10, fill=tk.X)
    
    def _create_view_controls(self, parent):
        """Create view control section"""
        section = self._create_section(parent, "🔍 View Controls")
        
        # Zoom controls
        zoom_frame = tk.Frame(section, bg="#34495e")
        zoom_frame.pack(pady=5, padx=10)
        
        tk.Button(
            zoom_frame,
            text="Zoom In (+)",
            command=self.zoom_in,
            bg="#27ae60",
            fg="white",
            width=12,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=2)
        
        tk.Button(
            zoom_frame,
            text="Zoom Out (-)",
            command=self.zoom_out,
            bg="#c0392b",
            fg="white",
            width=12,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=2)
        
        # Reset button
        tk.Button(
            section,
            text="Reset View",
            command=self.reset_view,
            bg="#16a085",
            fg="white",
            font=("Arial", 10),
            cursor="hand2"
        ).pack(pady=5, padx=10, fill=tk.X)
    
    def _create_simulation_controls(self, parent):
        """Create simulation control section"""
        section = self._create_section(parent, "▶️ Simulation Controls")
        
        # Start simulation button
        self.start_btn = tk.Button(
            section,
            text="Start Simulation",
            command=self.start_simulation,
            bg="#2ecc71",
            fg="white",
            font=("Arial", 11, "bold"),
            height=2,
            cursor="hand2"
        )
        self.start_btn.pack(pady=5, padx=10, fill=tk.X)
        
        # Step button
        self.step_btn = tk.Button(
            section,
            text="Step Forward",
            command=self.step_simulation,
            bg="#3498db",
            fg="white",
            font=("Arial", 10),
            state=tk.DISABLED,
            cursor="hand2"
        )
        self.step_btn.pack(pady=5, padx=10, fill=tk.X)
        
        # Pause/Resume button
        self.pause_btn = tk.Button(
            section,
            text="⏸️ Pause",
            command=self.pause_simulation,
            bg="#f39c12",
            fg="white",
            font=("Arial", 10),
            state=tk.DISABLED,
            cursor="hand2"
        )
        self.pause_btn.pack(pady=5, padx=10, fill=tk.X)
        
        # Reset simulation button
        tk.Button(
            section,
            text="Reset Simulation",
            command=self.reset_simulation,
            bg="#95a5a6",
            fg="white",
            font=("Arial", 10),
            cursor="hand2"
        ).pack(pady=5, padx=10, fill=tk.X)
        
        # Speed control section
        speed_section = tk.Frame(section, bg="#2c3e50", relief=tk.GROOVE, borderwidth=2)
        speed_section.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(
            speed_section,
            text="⚡ Speed Control",
            bg="#2c3e50",
            fg="#3498db",
            font=("Arial", 10, "bold")
        ).pack(pady=(5, 2))
        
        # Speed slider
        speed_frame = tk.Frame(speed_section, bg="#2c3e50")
        speed_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(
            speed_frame,
            text="Speed:",
            bg="#2c3e50",
            fg="white",
            font=("Arial", 9)
        ).pack(side=tk.LEFT)
        
        # Speed multiplier variable (0.2x to 5x)
        self.speed_multiplier = tk.DoubleVar(value=1.0)
        
        # Speed slider for multiplier
        self.speed_slider = tk.Scale(
            speed_frame,
            from_=0.2,
            to=5.0,
            resolution=0.1,
            orient=tk.HORIZONTAL,
            variable=self.speed_multiplier,
            command=self._update_speed_display,
            bg="#34495e",
            fg="white",
            highlightthickness=0,
            troughcolor="#2c3e50",
            activebackground="#3498db",
            length=120
        )
        self.speed_slider.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Speed value display with x multiplier
        self.speed_display = tk.Label(
            speed_frame,
            text="1.0x",
            bg="#2c3e50",
            fg="#2ecc71",
            font=("Arial", 9, "bold"),
            width=6
        )
        self.speed_display.pack(side=tk.LEFT, padx=2)
        
        # Preset speed buttons
        preset_frame = tk.Frame(speed_section, bg="#2c3e50")
        preset_frame.pack(fill=tk.X, padx=10, pady=(0, 8))
        
        tk.Label(
            preset_frame,
            text="Presets:",
            bg="#2c3e50",
            fg="#95a5a6",
            font=("Arial", 8)
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        preset_speeds = [
            ("0.2x", 0.2),
            ("0.5x", 0.5),
            ("1x", 1.0),
            ("2x", 2.0),
            ("5x", 5.0)
        ]
        
        for label, speed in preset_speeds:
            tk.Button(
                preset_frame,
                text=label,
                command=lambda s=speed: self.speed_multiplier.set(s),
                bg="#34495e",
                fg="white",
                font=("Arial", 8, "bold"),
                cursor="hand2",
                relief=tk.RAISED,
                borderwidth=1,
                width=4
            ).pack(side=tk.LEFT, padx=2, pady=2)
        
        # Add auto-step mode
        self.auto_step_var = tk.BooleanVar(value=True)
        auto_step_check = tk.Checkbutton(
            speed_section,
            text="Auto-step (continuous simulation)",
            variable=self.auto_step_var,
            bg="#2c3e50",
            fg="white",
            selectcolor="#34495e",
            activebackground="#2c3e50",
            activeforeground="white",
            font=("Arial", 8)
        )
        auto_step_check.pack(pady=(0, 5))
    
    def _create_statistics(self, parent):
        """Create statistics section"""
        section = self._create_section(parent, "📊 Statistics")
        
        # Stats text area
        self.stats_text = scrolledtext.ScrolledText(
            section,
            height=8,
            width=35,
            bg="#000000",
            fg="#ecf0f1",
            font=("Courier", 9),
            wrap=tk.WORD
        )
        self.stats_text.pack(pady=5, padx=10, fill=tk.BOTH)
        self.stats_text.config(state=tk.DISABLED)
        
        self.update_statistics()
    
    def _create_help_section(self, parent):
        """Create help section"""
        section = self._create_section(parent, "❓ Help & Guide")
        
        help_text = """
Controls Guide:

🖱️ Mouse:
  • Click nodes to select source/dest
  • Drag to pan view (future)
  
⌨️ Simulation:
  1. Configure grid (2-50×2-50)
  2. Enter packet data
  3. Click source node (green)
  4. Click destination node (red)
  5. Click 'Start Simulation'
  6. Watch packet routing!

📐 NoC Router (Content.txt):
  • Reception: Receive Buffer (FIFO)
  • Routing: XY algorithm + REQ
  • Transmission: ACK + Transfer
  • Flow Control: Choke signal

🎨 Packet Flow Colors:
  • 🟠 Orange: REQUEST phase (RREQ)
  • 🔵 Blue: ACKNOWLEDGE phase (ACK)
  • 🟣 Purple: VERIFY routing path
  • 🟢 Green: DATA SEND transfer
  
🎨 Node States:
  • Blue: Normal/idle nodes
  • Green: Source node
  • Red: Destination node
  • Purple: Active routing
  
⚠️ Flow Control Signals:
  • REQ: Request buffer space
  • ACK: Acknowledge available
  • Choke: Congestion backpressure
  • Transfer: Data moving
        """
        
        help_label = tk.Label(
            section,
            text=help_text,
            bg="#34495e",
            fg="#ecf0f1",
            font=("Courier", 8),
            justify=tk.LEFT,
            anchor=tk.W
        )
        help_label.pack(pady=5, padx=10, fill=tk.BOTH)
    
    def _create_section(self, parent, title: str) -> tk.Frame:
        """
        Create a collapsible section in control panel
        
        Args:
            parent: Parent widget
            title: Section title
            
        Returns:
            Section frame
        """
        # Section header
        header = tk.Frame(parent, bg="#000000", height=30)
        header.pack(fill=tk.X, pady=(10, 0))
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text=title,
            font=("Arial", 11, "bold"),
            bg="#2c3e50",
            fg="white"
        ).pack(side=tk.LEFT, padx=10)
        
        # Section content
        content = tk.Frame(parent, bg="#000000", relief=tk.SUNKEN, borderwidth=1)
        content.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        return content
    
    def _create_visualization_area(self):
        """Create right visualization area with canvas"""
        # Canvas for drawing
        self.canvas = tk.Canvas(
            self.viz_frame,
            bg=self.colors['background'],
            highlightthickness=0
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Bind events
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<Configure>", self.on_canvas_resize)
        self.canvas.bind("<Motion>", self.on_canvas_motion)
        self.canvas.bind("<Leave>", self.on_canvas_leave)
        
        # Draw initial network
        self.draw_network()
    
    def create_mesh_network(self):
        """Create mesh network with nodes and connections"""
        self.nodes.clear()
        
        # Create nodes
        for row in range(self.rows):
            for col in range(self.cols):
                self.nodes[(row, col)] = Node(
                    position=(row, col),
                    buffer_capacity=10
                )
        
        # Connect nodes (mesh topology)
        for row in range(self.rows):
            for col in range(self.cols):
                current_node = self.nodes[(row, col)]
                
                # North
                if row > 0:
                    current_node.add_neighbor(Direction.NORTH, self.nodes[(row - 1, col)])
                
                # South
                if row < self.rows - 1:
                    current_node.add_neighbor(Direction.SOUTH, self.nodes[(row + 1, col)])
                
                # East
                if col < self.cols - 1:
                    current_node.add_neighbor(Direction.EAST, self.nodes[(row, col + 1)])
                
                # West
                if col > 0:
                    current_node.add_neighbor(Direction.WEST, self.nodes[(row, col - 1)])
        
        # Only draw if canvas exists
        if hasattr(self, 'canvas'):
            self.draw_network()
        
        self.update_statistics()
    
    def draw_network(self):
        """Draw the mesh network on canvas"""
        self.canvas.delete("all")
        
        # Safety check - ensure nodes exist before drawing
        if not self.nodes:
            return
        
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if canvas_width <= 1:
            canvas_width = 800
        if canvas_height <= 1:
            canvas_height = 600
        
        # Calculate spacing with better margin management for larger grids
        # Use smaller margins for larger grids to maximize visible space
        if max(self.rows, self.cols) <= 4:
            margin = 100
        elif max(self.rows, self.cols) <= 8:
            margin = 80
        elif max(self.rows, self.cols) <= 15:
            margin = 60
        else:
            margin = 40
        
        available_width = canvas_width - 2 * margin
        available_height = canvas_height - 2 * margin
        
        # Ensure we have positive spacing
        spacing_x = available_width / max(1, self.cols - 1) if self.cols > 1 else available_width / 2
        spacing_y = available_height / max(1, self.rows - 1) if self.rows > 1 else available_height / 2
        
        # Auto-adjust node radius based on grid size and available space
        if self.auto_adjust_size:
            # Calculate optimal node radius to fit the grid
            max_nodes = max(self.rows, self.cols)
            if max_nodes <= 5:
                base_radius = 25
            elif max_nodes <= 10:
                base_radius = 18
            elif max_nodes <= 15:
                base_radius = 12
            elif max_nodes <= 25:
                base_radius = 8
            elif max_nodes <= 35:
                base_radius = 6
            else:
                base_radius = 4
            
            # Also adjust based on spacing - prevent nodes from overlapping
            min_spacing = min(spacing_x, spacing_y)
            spacing_based_radius = min_spacing / 4  # Changed from /3 to /4 for better spacing
            self.node_radius = min(base_radius, spacing_based_radius)
            
            # Ensure minimum visible radius
            self.node_radius = max(self.node_radius, 3)
        
        # Draw connections first (so they appear behind nodes)
        for row in range(self.rows):
            for col in range(self.cols):
                x1 = margin + col * spacing_x * self.zoom_level + self.offset_x
                y1 = margin + row * spacing_y * self.zoom_level + self.offset_y
                
                # Draw horizontal connections
                if col < self.cols - 1:
                    x2 = margin + (col + 1) * spacing_x * self.zoom_level + self.offset_x
                    y2 = y1
                    self.canvas.create_line(
                        x1, y1, x2, y2,
                        fill=self.colors['connection'],
                        width=2,
                        tags="connection"
                    )
                
                # Draw vertical connections
                if row < self.rows - 1:
                    x2 = x1
                    y2 = margin + (row + 1) * spacing_y * self.zoom_level + self.offset_y
                    self.canvas.create_line(
                        x1, y1, x2, y2,
                        fill=self.colors['connection'],
                        width=2,
                        tags="connection"
                    )
        
        # Draw nodes
        for row in range(self.rows):
            for col in range(self.cols):
                x = margin + col * spacing_x * self.zoom_level + self.offset_x
                y = margin + row * spacing_y * self.zoom_level + self.offset_y
                
                # Determine node color based on state and packet activity
                if (row, col) == self.source_node:
                    color = self.colors['node_source']  # Green - Source
                    outline_color = self.colors['text']
                    outline_width = 3
                elif (row, col) == self.dest_node:
                    color = self.colors['node_dest']  # Red - Destination
                    outline_color = self.colors['text']
                    outline_width = 3
                elif (row, col) == self.selected_node:
                    color = self.colors['node_selected']  # Orange - Selected
                    outline_color = self.colors['text']
                    outline_width = 2
                # Highlight nodes in current packet path with phase colors
                elif (self.current_packet and 
                      (row, col) in self.current_packet.path and
                      (row, col) != self.current_packet.current_node):
                    # Node is part of the traversed path - show phase color
                    path_index = self.current_packet.path.index((row, col))
                    total_hops = len(self.current_packet.path) - 1
                    
                    if total_hops > 0:
                        progress = path_index / total_hops
                        
                        if progress < 0.3:
                            color = self.colors['phase_request']  # Orange
                        elif progress < 0.6:
                            color = self.colors['phase_acknowledge']  # Blue
                        elif progress < 0.9:
                            color = self.colors['phase_verify']  # Purple
                        else:
                            color = self.colors['phase_send']  # Green
                        
                        # Lighter shade for traversed nodes
                        outline_color = color
                        outline_width = 2
                    else:
                        color = self.colors['node_normal']
                        outline_color = self.colors['text']
                        outline_width = 2
                elif (self.current_packet and (row, col) == self.current_packet.current_node):
                    # Current packet position - use bright phase color
                    if hasattr(self, 'packet_phase'):
                        color = {
                            'request': self.colors['phase_request'],
                            'acknowledge': self.colors['phase_acknowledge'],
                            'verify': self.colors['phase_verify'],
                            'send': self.colors['phase_send']
                        }.get(self.packet_phase, self.colors['node_active'])
                    else:
                        color = self.colors['node_active']  # Purple - Active
                    outline_color = 'white'
                    outline_width = 4
                else:
                    color = self.colors['node_normal']  # Blue - Normal
                    outline_color = self.colors['text']
                    outline_width = 2
                
                # Draw node circle
                radius = self.node_radius * self.zoom_level
                self.canvas.create_oval(
                    x - radius, y - radius,
                    x + radius, y + radius,
                    fill=color,
                    outline=outline_color,
                    width=outline_width,
                    tags=f"node_{row}_{col}"
                )
                
                # Draw node label with scaled font size
                # Scale font size based on node radius
                label_font_size = max(6, int(self.node_radius * 0.4))
                self.canvas.create_text(
                    x, y,
                    text=f"({row},{col})",
                    fill="white",
                    font=("Arial", label_font_size, "bold"),
                    tags=f"label_{row}_{col}"
                )
                
                # Draw buffer status if active - only if node exists
                if (row, col) in self.nodes:
                    node = self.nodes[(row, col)]
                    if not node.input_buffer.is_empty() or not node.output_buffer.is_empty():
                        buffer_text = f"I:{node.input_buffer.size()} O:{node.output_buffer.size()}"
                        
                        # Color code buffer status
                        if node.input_buffer.size() >= node.input_buffer.capacity * 0.8:
                            buffer_color = self.colors['buffer_choke']  # Red - Congestion
                        elif not node.output_buffer.is_empty():
                            buffer_color = self.colors['buffer_transfer']  # Green - Transfer
                        else:
                            buffer_color = self.colors['text']
                        
                        # Scale buffer font too
                        buffer_font_size = max(6, int(self.node_radius * 0.3))
                        self.canvas.create_text(
                            x, y + radius + 10,
                            text=buffer_text,
                            fill=buffer_color,
                            font=("Arial", buffer_font_size, "bold"),
                            tags=f"buffer_{row}_{col}"
                        )
        
        # Draw current packet path if exists
        if self.current_packet and len(self.current_packet.path) > 1:
            self.draw_packet_path(self.current_packet)
    
    def draw_packet_path(self, packet: Packet):
        """
        Draw the packet's path with color-coded phases
        
        Phases based on mesh-working-flow:
        1. REQUEST (Orange): Route discovery - finding path
        2. ACKNOWLEDGE (Blue): Path verified - acknowledgment received
        3. VERIFY (Purple): Routing verified at intermediate nodes
        4. SEND (Green): Data transmission phase
        """
        canvas_width = self.canvas.winfo_width() or 800
        canvas_height = self.canvas.winfo_height() or 600
        
        # Use same margin calculation as draw_network
        if max(self.rows, self.cols) <= 4:
            margin = 100
        elif max(self.rows, self.cols) <= 8:
            margin = 80
        elif max(self.rows, self.cols) <= 15:
            margin = 60
        else:
            margin = 40
        
        available_width = canvas_width - 2 * margin
        available_height = canvas_height - 2 * margin
        
        spacing_x = available_width / max(1, self.cols - 1) if self.cols > 1 else available_width / 2
        spacing_y = available_height / max(1, self.rows - 1) if self.rows > 1 else available_height / 2
        
        # Calculate total hops and current progress
        # packet.path contains all nodes visited so far
        # packet.hops is the number of hops taken (len(path) - 1)
        actual_path_length = len(packet.path)
        total_hops = packet.hops
        
        # Determine packet phase based on progress to destination
        expected_total_hops = self.routing_algorithm.calculate_hops(
            packet.source,
            packet.destination
        )
        progress = total_hops / max(1, expected_total_hops)
        
        if packet.status == PacketStatus.DELIVERED:
            phase = 'send'  # Completed - all green
        elif progress < 0.3:
            phase = 'request'  # Route discovery
        elif progress < 0.6:
            phase = 'acknowledge'  # Route acknowledged
        elif progress < 0.9:
            phase = 'verify'  # Verifying and forwarding
        else:
            phase = 'send'  # Final transmission
        
        self.packet_phase = phase
        
        # Draw ONLY the actual path segments that have been traversed
        # packet.path[0] is source, packet.path[-1] is current position
        for i in range(len(packet.path) - 1):
            row1, col1 = packet.path[i]
            row2, col2 = packet.path[i + 1]
            
            x1 = margin + col1 * spacing_x * self.zoom_level + self.offset_x
            y1 = margin + row1 * spacing_y * self.zoom_level + self.offset_y
            x2 = margin + col2 * spacing_x * self.zoom_level + self.offset_x
            y2 = margin + row2 * spacing_y * self.zoom_level + self.offset_y
            
            # Determine segment color based on progress through EXPECTED path
            segment_progress = i / max(1, expected_total_hops)
            
            # All drawn segments are ACTUAL traversed segments (not future/projected)
            # Color them based on overall progress
            if segment_progress < 0.3:
                segment_color = self.colors['phase_request']  # Orange - REQUEST
            elif segment_progress < 0.6:
                segment_color = self.colors['phase_acknowledge']  # Blue - ACK
            elif segment_progress < 0.9:
                segment_color = self.colors['phase_verify']  # Purple - VERIFY
            else:
                segment_color = self.colors['phase_send']  # Green - SEND
            
            segment_width = 4
            
            # Draw the path segment (all segments are actual, no future projection)
            self.canvas.create_line(
                x1, y1, x2, y2,
                fill=segment_color,
                width=segment_width,
                arrow=tk.LAST if i == len(packet.path) - 2 else None,  # Arrow on last segment
                arrowshape=(10, 12, 5) if i == len(packet.path) - 2 else None,
                tags="packet_path"
            )
            
            # Add phase labels on current segment (last one)
            if i == len(packet.path) - 2 and i >= 0:
                mid_x = (x1 + x2) / 2
                mid_y = (y1 + y2) / 2
                
                # Phase label
                phase_label = {
                    'request': 'REQ',
                    'acknowledge': 'ACK',
                    'verify': 'VER',
                    'send': 'SEND'
                }.get(phase, '')
                
                if phase_label:
                    self.canvas.create_text(
                        mid_x, mid_y - 15,
                        text=phase_label,
                        fill=segment_color,
                        font=("Arial", int(9 * self.zoom_level), "bold"),
                        tags="phase_label"
                    )
        
        # Draw packet at current position with phase color
        if packet.current_node:
            row, col = packet.current_node
            x = margin + col * spacing_x * self.zoom_level + self.offset_x
            y = margin + row * spacing_y * self.zoom_level + self.offset_y
            
            # Packet color based on current phase
            packet_color = {
                'request': self.colors['phase_request'],
                'acknowledge': self.colors['phase_acknowledge'],
                'verify': self.colors['phase_verify'],
                'send': self.colors['phase_send']
            }.get(phase, self.colors['packet'])
            
            radius = self.node_radius * self.zoom_level * 0.4
            
            # Pulsing effect - draw two circles
            self.canvas.create_oval(
                x - radius * 1.3, y - radius * 1.3,
                x + radius * 1.3, y + radius * 1.3,
                fill='',
                outline=packet_color,
                width=2,
                tags="packet_pulse"
            )
            
            self.canvas.create_oval(
                x - radius, y - radius,
                x + radius, y + radius,
                fill=packet_color,
                outline="white",
                width=2,
                tags="packet_current"
            )
            
            # Add phase icon/text on packet
            phase_icon = {
                'request': '🔍',
                'acknowledge': '✓',
                'verify': '⚡',
                'send': '📦'
            }.get(phase, '•')
            
            self.canvas.create_text(
                x, y,
                text=phase_icon,
                fill="white",
                font=("Arial", int(12 * self.zoom_level), "bold"),
                tags="packet_icon"
            )
    
    def on_canvas_click(self, event):
        """Handle canvas click for node selection"""
        # Find clicked node
        clicked_node = self.find_node_at_position(event.x, event.y)
        
        if clicked_node:
            if self.source_node is None:
                # Set source
                self.source_node = clicked_node
                self.source_label.config(text=str(clicked_node))
                self.main_window.update_status(f"Source selected: {clicked_node}")
            elif self.dest_node is None and clicked_node != self.source_node:
                # Set destination
                self.dest_node = clicked_node
                self.dest_label.config(text=str(clicked_node))
                self.main_window.update_status(f"Destination selected: {clicked_node}")
            else:
                # Clear and start over
                self.clear_selection()
                self.source_node = clicked_node
                self.source_label.config(text=str(clicked_node))
            
            self.draw_network()
    
    def on_canvas_motion(self, event):
        """Handle mouse motion for hover tooltips"""
        # Check if mouse is over the tooltip window
        if self.tooltip_window:
            try:
                # Get tooltip geometry
                tooltip_x = self.tooltip_window.winfo_rootx()
                tooltip_y = self.tooltip_window.winfo_rooty()
                tooltip_width = self.tooltip_window.winfo_width()
                tooltip_height = self.tooltip_window.winfo_height()
                
                # Check if mouse is inside tooltip bounds (with margin)
                margin = 10
                if (tooltip_x - margin <= event.x_root <= tooltip_x + tooltip_width + margin and
                    tooltip_y - margin <= event.y_root <= tooltip_y + tooltip_height + margin):
                    # Mouse is over tooltip, keep it visible and don't process further
                    self._cancel_hover_timer()
                    return
            except:
                # Tooltip might have been destroyed
                pass
        
        # Find node at current position
        node_pos = self.find_node_at_position(event.x, event.y)
        
        if node_pos != self.hover_node:
            # Node changed - cancel any pending tooltip
            self._cancel_hover_timer()
            
            # Only hide tooltip if mouse is not near it
            if self.tooltip_window:
                try:
                    tooltip_x = self.tooltip_window.winfo_rootx()
                    tooltip_y = self.tooltip_window.winfo_rooty()
                    tooltip_width = self.tooltip_window.winfo_width()
                    tooltip_height = self.tooltip_window.winfo_height()
                    
                    margin = 30  # Larger margin for moving towards tooltip
                    if not (tooltip_x - margin <= event.x_root <= tooltip_x + tooltip_width + margin and
                           tooltip_y - margin <= event.y_root <= tooltip_y + tooltip_height + margin):
                        self._hide_tooltip()
                except:
                    self._hide_tooltip()
            
            if node_pos:
                # Start new hover timer
                self.hover_node = node_pos
                self.hover_timer = self.parent.after(
                    self.hover_delay,
                    lambda: self._show_node_tooltip(node_pos, event.x_root, event.y_root)
                )
            else:
                self.hover_node = None
    
    def on_canvas_leave(self, event):
        """Handle mouse leaving canvas"""
        self._cancel_hover_timer()
        
        # Don't hide tooltip if mouse is over it
        if self.tooltip_window:
            try:
                tooltip_x = self.tooltip_window.winfo_rootx()
                tooltip_y = self.tooltip_window.winfo_rooty()
                tooltip_width = self.tooltip_window.winfo_width()
                tooltip_height = self.tooltip_window.winfo_height()
                
                # Check if mouse is inside tooltip (with margin)
                margin = 30
                if (tooltip_x - margin <= event.x_root <= tooltip_x + tooltip_width + margin and
                    tooltip_y - margin <= event.y_root <= tooltip_y + tooltip_height + margin):
                    # Mouse is over tooltip, don't hide it
                    return
            except:
                pass
        
        self._hide_tooltip()
        self.hover_node = None
    
    def _cancel_hover_timer(self):
        """Cancel pending hover timer"""
        if self.hover_timer:
            self.parent.after_cancel(self.hover_timer)
            self.hover_timer = None
    
    def _hide_tooltip(self):
        """Hide tooltip window"""
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None
    
    def _delayed_tooltip_hide(self):
        """Hide tooltip after a delay, checking if mouse is still outside"""
        if self.tooltip_window and hasattr(self.tooltip_window, 'mouse_inside'):
            if not self.tooltip_window.mouse_inside:
                # Double-check mouse is not over tooltip
                try:
                    mouse_x = self.tooltip_window.winfo_pointerx()
                    mouse_y = self.tooltip_window.winfo_pointery()
                    tooltip_x = self.tooltip_window.winfo_rootx()
                    tooltip_y = self.tooltip_window.winfo_rooty()
                    tooltip_width = self.tooltip_window.winfo_width()
                    tooltip_height = self.tooltip_window.winfo_height()
                    
                    # Check if mouse is over tooltip
                    if (tooltip_x <= mouse_x <= tooltip_x + tooltip_width and
                        tooltip_y <= mouse_y <= tooltip_y + tooltip_height):
                        # Mouse is back, don't hide
                        self.tooltip_window.mouse_inside = True
                        return
                    
                    # Mouse is truly away, hide it
                    self._hide_tooltip()
                except:
                    self._hide_tooltip()
    
    def _check_and_hide_tooltip(self):
        """Check if tooltip should be hidden based on mouse position"""
        if self.tooltip_window and hasattr(self.tooltip_window, 'mouse_inside'):
            if not self.tooltip_window.mouse_inside:
                self._hide_tooltip()
    
    def _show_node_tooltip(self, node_pos: Tuple[int, int], x_root: int, y_root: int):
        """Show accordion-style tooltip with node information"""
        if node_pos not in self.nodes:
            return
        
        node = self.nodes[node_pos]
        row, col = node_pos
        
        # Create tooltip window
        self._hide_tooltip()
        self.tooltip_window = tk.Toplevel(self.parent)
        self.tooltip_window.wm_overrideredirect(True)
        
        # Keep reference to prevent garbage collection
        self.tooltip_window.tooltip_active = True
        self.tooltip_window.mouse_inside = False
        
        # Bind events to keep tooltip visible when mouse enters it
        def on_tooltip_enter(e):
            """Mouse entered tooltip area"""
            self._cancel_hover_timer()
            if self.tooltip_window:
                self.tooltip_window.mouse_inside = True
        
        def on_tooltip_leave(e):
            """Mouse left tooltip area"""
            if not self.tooltip_window:
                return
                
            try:
                # Get current mouse position
                x, y = e.x_root, e.y_root
                tooltip_x = self.tooltip_window.winfo_rootx()
                tooltip_y = self.tooltip_window.winfo_rooty()
                tooltip_width = self.tooltip_window.winfo_width()
                tooltip_height = self.tooltip_window.winfo_height()
                
                # Add margin to prevent premature hiding
                margin = 5
                if (tooltip_x - margin <= x <= tooltip_x + tooltip_width + margin and
                    tooltip_y - margin <= y <= tooltip_y + tooltip_height + margin):
                    # Still inside, don't hide
                    return
                
                # Truly left - mark and schedule hide check
                self.tooltip_window.mouse_inside = False
                # Short delay before hiding to handle rapid movements
                self.parent.after(200, lambda: self._delayed_tooltip_hide())
            except:
                if self.tooltip_window:
                    self.tooltip_window.mouse_inside = False
        
        self.tooltip_window.bind("<Enter>", on_tooltip_enter, add="+")
        self.tooltip_window.bind("<Leave>", on_tooltip_leave, add="+")
        
        # Main frame
        main_frame = tk.Frame(
            self.tooltip_window,
            bg="#2c3e50",
            relief=tk.RIDGE,
            borderwidth=2
        )
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header container with close button
        header_container = tk.Frame(main_frame, bg="#1e2a3a")
        header_container.pack(fill=tk.X)
        
        # Header - Node ID
        header = tk.Label(
            header_container,
            text=f"▣ Node ({row}, {col})",
            bg="#1e2a3a",
            fg="#ecf0f1",
            font=("Arial", 11, "bold"),
            pady=8,
            padx=10
        )
        header.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Close button
        close_btn = tk.Button(
            header_container,
            text="✕",
            command=self._hide_tooltip,
            bg="#e74c3c",
            fg="white",
            font=("Arial", 12, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            padx=8,
            pady=4,
            activebackground="#c0392b",
            activeforeground="white"
        )
        close_btn.pack(side=tk.RIGHT, padx=5)
        
        # Content frame with scrollbar
        content = tk.Frame(main_frame, bg="#34495e")
        content.pack(fill=tk.BOTH, expand=True)
        
        # Accordion state variables
        packets_expanded = tk.BooleanVar(value=True)
        buffer_expanded = tk.BooleanVar(value=False)
        flow_expanded = tk.BooleanVar(value=False)
        routing_expanded = tk.BooleanVar(value=False)
        
        # --- PACKETS SECTION (ACCORDION) ---
        packets_container = tk.Frame(content, bg="#2c3e50")
        packets_container.pack(fill=tk.X, pady=1)
        
        def toggle_packets():
            packets_expanded.set(not packets_expanded.get())
            packets_arrow.config(text="▼" if packets_expanded.get() else "▶")
            if packets_expanded.get():
                packets_content.pack(fill=tk.X, padx=5, pady=2)
            else:
                packets_content.pack_forget()
        
        packets_header = tk.Frame(packets_container, bg="#2c3e50", cursor="hand2")
        packets_header.pack(fill=tk.X)
        packets_header.bind("<Button-1>", lambda e: toggle_packets())
        
        packets_arrow = tk.Label(
            packets_header,
            text="▼" if packets_expanded.get() else "▶",
            bg="#2c3e50",
            fg="#3498db",
            font=("Arial", 9, "bold"),
            width=2
        )
        packets_arrow.pack(side=tk.LEFT, padx=3)
        packets_arrow.bind("<Button-1>", lambda e: toggle_packets())
        
        packets_title = tk.Label(
            packets_header,
            text="📦 PACKETS IN BUFFERS",
            bg="#2c3e50",
            fg="#ecf0f1",
            font=("Arial", 9, "bold"),
            anchor="w",
            pady=4
        )
        packets_title.pack(side=tk.LEFT, fill=tk.X, expand=True)
        packets_title.bind("<Button-1>", lambda e: toggle_packets())
        
        # Packets content
        packets_content = tk.Frame(packets_container, bg="#34495e")
        if packets_expanded.get():
            packets_content.pack(fill=tk.X, padx=5, pady=2)
        
        # Check for REAL packets in buffers
        packets_in_node = []
        if node.input_buffer.size() > 0:
            packets_in_node.append(("INPUT", node.input_buffer.get_all_packets()))
        if node.output_buffer.size() > 0:
            packets_in_node.append(("OUTPUT", node.output_buffer.get_all_packets()))
        
        if packets_in_node:
            for buffer_type, packets in packets_in_node:
                buffer_label = tk.Label(
                    packets_content,
                    text=f"🔹 {buffer_type} Buffer:",
                    bg="#34495e",
                    fg="#3498db",
                    font=("Arial", 8, "bold"),
                    anchor="w",
                    padx=5
                )
                buffer_label.pack(fill=tk.X)
                
                for packet in packets:
                    packet_info = tk.Frame(packets_content, bg="white", relief=tk.SOLID, borderwidth=1)
                    packet_info.pack(fill=tk.X, pady=2, padx=5)
                    
                    details = [
                        f"Type: {packet.packet_type.value.upper()}",
                        f"ID: {packet.packet_id}",
                        f"From: {packet.source} → To: {packet.destination}",
                        f"Hops: {packet.hops}"
                    ]
                    
                    if packet.packet_type.value == "data":
                        data_preview = packet.payload.get('data', '')[:15]
                        details.append(f"Data: {data_preview}...")
                    elif packet.packet_type.value == "rreq":
                        details.append(f"Broadcast ID: {packet.broadcast_id}")
                        details.append(f"Seq: {packet.source_sequence_num}")
                    elif packet.packet_type.value == "rrep":
                        details.append(f"Seq: {packet.dest_sequence_num}")
                    
                    for detail in details:
                        lbl = tk.Label(
                            packet_info,
                            text=detail,
                            bg="white",
                            fg="#2c3e50",
                            font=("Courier", 7),
                            anchor="w",
                            padx=3,
                            pady=1
                        )
                        lbl.pack(fill=tk.X)
        else:
            no_packet = tk.Label(
                packets_content,
                text="No packets in buffers",
                bg="#ecf0f1",
                fg="#7f8c8d",
                font=("Arial", 8, "italic"),
                padx=5,
                pady=3
            )
            no_packet.pack(fill=tk.X, pady=2)
        
        # --- BUFFER SECTION (ACCORDION) ---
        buffer_container = tk.Frame(content, bg="#2c3e50")
        buffer_container.pack(fill=tk.X, pady=1)
        
        def toggle_buffer():
            buffer_expanded.set(not buffer_expanded.get())
            buffer_arrow.config(text="▼" if buffer_expanded.get() else "▶")
            if buffer_expanded.get():
                buffer_content.pack(fill=tk.X, padx=5, pady=2)
            else:
                buffer_content.pack_forget()
        
        buffer_header = tk.Frame(buffer_container, bg="#2c3e50", cursor="hand2")
        buffer_header.pack(fill=tk.X)
        buffer_header.bind("<Button-1>", lambda e: toggle_buffer())
        
        buffer_arrow = tk.Label(
            buffer_header,
            text="▼" if buffer_expanded.get() else "▶",
            bg="#2c3e50",
            fg="#3498db",
            font=("Arial", 9, "bold"),
            width=2
        )
        buffer_arrow.pack(side=tk.LEFT, padx=3)
        buffer_arrow.bind("<Button-1>", lambda e: toggle_buffer())
        
        buffer_title = tk.Label(
            buffer_header,
            text="📊 BUFFER",
            bg="#2c3e50",
            fg="#ecf0f1",
            font=("Arial", 9, "bold"),
            anchor="w",
            pady=4
        )
        buffer_title.pack(side=tk.LEFT, fill=tk.X, expand=True)
        buffer_title.bind("<Button-1>", lambda e: toggle_buffer())
        
        # Buffer content
        buffer_content = tk.Frame(buffer_container, bg="#34495e")
        if buffer_expanded.get():
            buffer_content.pack(fill=tk.X, padx=5, pady=2)
        
        buffer_info = tk.Frame(buffer_content, bg="white", relief=tk.SOLID, borderwidth=1)
        buffer_info.pack(fill=tk.X, padx=5)
        
        input_size = node.input_buffer.size()
        input_capacity = node.input_buffer.capacity
        input_pct = int((input_size / input_capacity) * 100) if input_capacity > 0 else 0
        
        input_label = tk.Label(
            buffer_info,
            text=f"Input:  {input_size}/{input_capacity} ({input_pct}%)",
            bg="white",
            fg="#27ae60" if input_pct < 50 else "#f39c12" if input_pct < 80 else "#e74c3c",
            font=("Courier", 8, "bold"),
            anchor="w",
            padx=5,
            pady=2
        )
        input_label.pack(fill=tk.X)
        
        output_size = node.output_buffer.size()
        output_capacity = node.output_buffer.capacity
        output_pct = int((output_size / output_capacity) * 100) if output_capacity > 0 else 0
        
        output_label = tk.Label(
            buffer_info,
            text=f"Output: {output_size}/{output_capacity} ({output_pct}%)",
            bg="white",
            fg="#27ae60" if output_pct < 50 else "#f39c12" if output_pct < 80 else "#e74c3c",
            font=("Courier", 8, "bold"),
            anchor="w",
            padx=5,
            pady=2
        )
        output_label.pack(fill=tk.X)
        
        # --- FLOW CONTROL SECTION (ACCORDION) ---
        flow_container = tk.Frame(content, bg="#2c3e50")
        flow_container.pack(fill=tk.X, pady=1)
        
        def toggle_flow():
            flow_expanded.set(not flow_expanded.get())
            flow_arrow.config(text="▼" if flow_expanded.get() else "▶")
            if flow_expanded.get():
                flow_content.pack(fill=tk.X, padx=5, pady=2)
            else:
                flow_content.pack_forget()
        
        flow_header = tk.Frame(flow_container, bg="#2c3e50", cursor="hand2")
        flow_header.pack(fill=tk.X)
        flow_header.bind("<Button-1>", lambda e: toggle_flow())
        
        flow_arrow = tk.Label(
            flow_header,
            text="▼" if flow_expanded.get() else "▶",
            bg="#2c3e50",
            fg="#3498db",
            font=("Arial", 9, "bold"),
            width=2
        )
        flow_arrow.pack(side=tk.LEFT, padx=3)
        flow_arrow.bind("<Button-1>", lambda e: toggle_flow())
        
        flow_title = tk.Label(
            flow_header,
            text="🚦 FLOW CONTROL",
            bg="#2c3e50",
            fg="#ecf0f1",
            font=("Arial", 9, "bold"),
            anchor="w",
            pady=4
        )
        flow_title.pack(side=tk.LEFT, fill=tk.X, expand=True)
        flow_title.bind("<Button-1>", lambda e: toggle_flow())
        
        # Flow content
        flow_content = tk.Frame(flow_container, bg="#34495e")
        if flow_expanded.get():
            flow_content.pack(fill=tk.X, padx=5, pady=2)
        
        signals_info = tk.Frame(flow_content, bg="white", relief=tk.SOLID, borderwidth=1)
        signals_info.pack(fill=tk.X, padx=5)
        
        signals = [
            ("REQ", node.req_signal, "🟠" if node.req_signal else "⚪"),
            ("ACK", node.ack_signal, "🔵" if node.ack_signal else "⚪"),
            ("Transfer", node.transfer_signal, "🟢" if node.transfer_signal else "⚪"),
            ("Choke", node.choke_signal, "🔴" if node.choke_signal else "⚪")
        ]
        
        for signal_name, signal_state, icon in signals:
            signal_text = f"{icon} {signal_name}: {'ACTIVE' if signal_state else 'Inactive'}"
            signal_lbl = tk.Label(
                signals_info,
                text=signal_text,
                bg="white",
                fg="#27ae60" if signal_state else "#95a5a6",
                font=("Courier", 7, "bold" if signal_state else "normal"),
                anchor="w",
                padx=5,
                pady=1
            )
            signal_lbl.pack(fill=tk.X)
        
        # --- ROUTING TABLE SECTION (ACCORDION) ---
        if node.routing_table:
            routing_container = tk.Frame(content, bg="#2c3e50")
            routing_container.pack(fill=tk.X, pady=1)
            
            def toggle_routing():
                routing_expanded.set(not routing_expanded.get())
                routing_arrow.config(text="▼" if routing_expanded.get() else "▶")
                if routing_expanded.get():
                    routing_content.pack(fill=tk.X, padx=5, pady=2)
                else:
                    routing_content.pack_forget()
            
            routing_header = tk.Frame(routing_container, bg="#2c3e50", cursor="hand2")
            routing_header.pack(fill=tk.X)
            routing_header.bind("<Button-1>", lambda e: toggle_routing())
            
            routing_arrow = tk.Label(
                routing_header,
                text="▼" if routing_expanded.get() else "▶",
                bg="#2c3e50",
                fg="#3498db",
                font=("Arial", 9, "bold"),
                width=2
            )
            routing_arrow.pack(side=tk.LEFT, padx=3)
            routing_arrow.bind("<Button-1>", lambda e: toggle_routing())
            
            routing_title = tk.Label(
                routing_header,
                text="🗺️ ROUTING TABLE",
                bg="#2c3e50",
                fg="#ecf0f1",
                font=("Arial", 9, "bold"),
                anchor="w",
                pady=4
            )
            routing_title.pack(side=tk.LEFT, fill=tk.X, expand=True)
            routing_title.bind("<Button-1>", lambda e: toggle_routing())
            
            # Routing content
            routing_content = tk.Frame(routing_container, bg="#34495e")
            if routing_expanded.get():
                routing_content.pack(fill=tk.X, padx=5, pady=2)
            
            routing_info = tk.Frame(routing_content, bg="white", relief=tk.SOLID, borderwidth=1)
            routing_info.pack(fill=tk.X, padx=5)
            
            for i, (dest, route) in enumerate(list(node.routing_table.items())[:3]):
                route_text = f"{dest} → {route.next_hop} (hops:{route.hop_count})"
                route_lbl = tk.Label(
                    routing_info,
                    text=route_text,
                    bg="white",
                    fg="#2c3e50",
                    font=("Courier", 7),
                    anchor="w",
                    padx=5,
                    pady=1
                )
                route_lbl.pack(fill=tk.X)
            
            if len(node.routing_table) > 3:
                more_lbl = tk.Label(
                    routing_info,
                    text=f"... +{len(node.routing_table) - 3} more",
                    bg="white",
                    fg="#7f8c8d",
                    font=("Courier", 7, "italic"),
                    anchor="w",
                    padx=5,
                    pady=1
                )
                more_lbl.pack(fill=tk.X)
        
        # Position tooltip intelligently based on node position
        # Update to get actual size first
        self.tooltip_window.update_idletasks()
        tooltip_width = self.tooltip_window.winfo_width()
        tooltip_height = self.tooltip_window.winfo_height()
        
        # Bind all child widgets to keep tooltip active
        def bind_tooltip_events(widget):
            """Recursively bind enter/leave events to all widgets"""
            widget.bind("<Enter>", on_tooltip_enter, add="+")
            widget.bind("<Leave>", on_tooltip_leave, add="+")
            for child in widget.winfo_children():
                bind_tooltip_events(child)
        
        # Apply to all widgets in tooltip
        bind_tooltip_events(main_frame)
        
        # Get screen dimensions
        screen_width = self.tooltip_window.winfo_screenwidth()
        screen_height = self.tooltip_window.winfo_screenheight()
        
        # Determine if node is in bottom half of screen
        is_bottom_node = y_root > screen_height / 2
        is_right_node = x_root > screen_width / 2
        
        # Smart positioning:
        # - Bottom nodes: show tooltip ABOVE
        # - Top nodes: show tooltip BELOW
        # - Right nodes: show tooltip to LEFT
        # - Left nodes: show tooltip to RIGHT
        
        if is_bottom_node:
            tooltip_y = y_root - tooltip_height - 20  # Above cursor
        else:
            tooltip_y = y_root + 20  # Below cursor
        
        if is_right_node:
            tooltip_x = x_root - tooltip_width - 20  # Left of cursor
        else:
            tooltip_x = x_root + 20  # Right of cursor
        
        # Final bounds check - ensure tooltip stays on screen
        tooltip_x = max(10, min(tooltip_x, screen_width - tooltip_width - 10))
        tooltip_y = max(10, min(tooltip_y, screen_height - tooltip_height - 10))
        
        self.tooltip_window.wm_geometry(f"+{tooltip_x}+{tooltip_y}")

    
    def find_node_at_position(self, x: int, y: int) -> Optional[Tuple[int, int]]:
        """Find node at given canvas position"""
        # Use same margin calculation as draw_network
        if max(self.rows, self.cols) <= 4:
            margin = 100
        elif max(self.rows, self.cols) <= 8:
            margin = 80
        elif max(self.rows, self.cols) <= 15:
            margin = 60
        else:
            margin = 40
            
        canvas_width = self.canvas.winfo_width() or 800
        canvas_height = self.canvas.winfo_height() or 600
        
        available_width = canvas_width - 2 * margin
        available_height = canvas_height - 2 * margin
        
        spacing_x = available_width / max(1, self.cols - 1) if self.cols > 1 else available_width / 2
        spacing_y = available_height / max(1, self.rows - 1) if self.rows > 1 else available_height / 2
        
        radius = self.node_radius * self.zoom_level
        
        for row in range(self.rows):
            for col in range(self.cols):
                node_x = margin + col * spacing_x * self.zoom_level + self.offset_x
                node_y = margin + row * spacing_y * self.zoom_level + self.offset_y
                
                distance = math.sqrt((x - node_x)**2 + (y - node_y)**2)
                if distance <= radius:
                    return (row, col)
        
        return None
    
    def on_canvas_resize(self, event):
        """Handle canvas resize"""
        self.draw_network()
    
    def apply_topology_config(self):
        """Apply topology configuration changes"""
        try:
            new_rows = int(self.rows_spinbox.get())
            new_cols = int(self.cols_spinbox.get())
            
            if new_rows < 2 or new_rows > 50 or new_cols < 2 or new_cols > 50:
                messagebox.showwarning(
                    "Invalid Configuration",
                    "Rows and columns must be between 2 and 50"
                )
                return
            
            self.rows = new_rows
            self.cols = new_cols
            
            # Reset state first
            self.source_node = None
            self.dest_node = None
            self.source_label.config(text="Not selected")
            self.dest_label.config(text="Not selected")
            
            # Reset simulation
            self.is_simulating = False
            self.simulation_step = 0
            self.current_packet = None
            self.packet_phase = None
            
            # Hide any active tooltips
            self._cancel_hover_timer()
            self._hide_tooltip()
            
            # Create new network (this must happen before drawing)
            self.create_mesh_network()
            
            # Now safe to draw
            self.draw_network()
            self.update_statistics()
            
            self.main_window.update_status(f"Mesh network created: {self.rows}×{self.cols}")
            
        except ValueError:
            messagebox.showerror("Error", "Invalid input values")
    
    def clear_selection(self):
        """Clear source and destination selection"""
        self.source_node = None
        self.dest_node = None
        self.source_label.config(text="Not selected")
        self.dest_label.config(text="Not selected")
        self.draw_network()
    
    def zoom_in(self):
        """Zoom in the view"""
        self.zoom_level *= 1.2
        self.draw_network()
    
    def zoom_out(self):
        """Zoom out the view"""
        self.zoom_level /= 1.2
        self.draw_network()
    
    def reset_view(self):
        """Reset view to default"""
        self.zoom_level = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self.draw_network()
    
    def start_simulation(self):
        """Start REAL packet routing simulation with AODV protocol"""
        if self.source_node is None or self.dest_node is None:
            messagebox.showwarning(
                "Incomplete Selection",
                "Please select both source and destination nodes"
            )
            return
        
        # Get user-provided packet data
        self.packet_data = self.data_entry.get(1.0, tk.END).strip()
        if not self.packet_data:
            self.packet_data = "Default packet data"
        
        # Create REAL simulator
        self.simulator = MeshSimulator(self.nodes)
        
        # Start simulation - this initiates RREQ broadcast
        success = self.simulator.start_simulation(
            source=self.source_node,
            destination=self.dest_node,
            data=self.packet_data
        )
        
        if not success:
            messagebox.showerror("Error", "Failed to start simulation")
            return
        
        self.is_simulating = True
        self.is_paused = False
        self.simulation_step = 0
        self.current_packet = self.simulator.data_packet
        self.current_sim_phase = SimulationPhase.ROUTE_DISCOVERY
        
        self.start_btn.config(state=tk.DISABLED)
        self.step_btn.config(state=tk.DISABLED if self.auto_step_var.get() else tk.NORMAL)
        self.pause_btn.config(state=tk.NORMAL, text="⏸️ Pause", bg="#f39c12")
        
        # Initialize AODV status bar
        self._update_aodv_status(
            hop_current=0,
            hop_total=self.routing_algorithm.calculate_hops(self.source_node, self.dest_node),
            phase_text="🟠 Route Discovery (RREQ)",
            phase_color=self.colors['phase_request'],
            route_text=f"Broadcasting RREQ from {self.source_node}",
            progress_pct=0,
            signals_text="RREQ Broadcast"
        )
        
        self.main_window.update_status(
            f"🔍 REAL SIMULATION STARTED | Phase: ROUTE_DISCOVERY | "
            f"Broadcasting RREQ from {self.source_node} to find route to {self.dest_node}"
        )
        self.animate_simulation()
    
    def step_simulation(self):
        """
        Perform ONE REAL clock cycle of simulation
        
        This implements proper NoC behavior:
        1. ROUTE_DISCOVERY: RREQ packets broadcast through network
        2. ROUTE_REPLY: RREP packets return to source
        3. DATA_TRANSFER: Actual data sent using established route
        
        Each step represents one clock cycle with proper flow control
        """
        if not self.simulator or self.simulator.is_complete():
            return
        
        # Execute one clock cycle
        step_info = self.simulator.step()
        
        self.simulation_step = step_info['clock_cycle']
        self.current_sim_phase = SimulationPhase[step_info['phase'].upper()]
        self.sim_events = step_info.get('events', [])
        
        # Update packet reference for visualization
        self.current_packet = self.simulator.data_packet
        
        # Determine phase for visualization
        if self.current_sim_phase == SimulationPhase.ROUTE_DISCOVERY:
            self.packet_phase = 'request'
            phase_text = "🟠 Route Discovery (RREQ)"
            phase_color = self.colors['phase_request']
            signals = f"RREQ: {len(self.simulator.rreq_packets)} active"
        elif self.current_sim_phase == SimulationPhase.ROUTE_REPLY:
            self.packet_phase = 'acknowledge'
            phase_text = "🔵 Route Reply (RREP)"
            phase_color = self.colors['phase_acknowledge']
            signals = f"RREP: {len(self.simulator.rrep_packets)} active"
        elif self.current_sim_phase == SimulationPhase.DATA_TRANSFER:
            self.packet_phase = 'send'
            phase_text = "🟢 Data Transfer"
            phase_color = self.colors['phase_send']
            signals = "Transferring data"
        else:
            self.packet_phase = None
            phase_text = "✅ Complete"
            phase_color = "#2ecc71"
            signals = "Finished"
        
        # Update AODV status
        if self.current_packet:
            total_hops = self.routing_algorithm.calculate_hops(
                self.current_packet.source,
                self.current_packet.destination
            )
            
            current_hop = self.current_packet.hops if self.current_sim_phase == SimulationPhase.DATA_TRANSFER else 0
            
            route_text = f"Clock: {self.simulation_step}"
            if self.sim_events:
                route_text += f" | {self.sim_events[0]}"
            
            self._update_aodv_status(
                hop_current=current_hop,
                hop_total=total_hops,
                phase_text=phase_text,
                phase_color=phase_color,
                route_text=route_text,
                progress_pct=int((current_hop / max(1, total_hops)) * 100),
                signals_text=signals
            )
        
        # Build status message
        event_str = " | ".join(self.sim_events[:3]) if self.sim_events else "Processing..."
        status_msg = (
            f"⏱️ Cycle {self.simulation_step} | "
            f"Phase: {self.current_sim_phase.value.upper()} | "
            f"{event_str}"
        )
        
        if step_info.get('completed'):
            self.is_simulating = False
            self.is_paused = False
            self.start_btn.config(state=tk.NORMAL)
            self.step_btn.config(state=tk.DISABLED)
            self.pause_btn.config(state=tk.DISABLED)
            
            stats = self.simulator.get_statistics()
            
            if stats['data_delivered']:
                status_msg = (
                    f"✅ DELIVERY COMPLETE! | "
                    f"Cycles: {stats['clock_cycles']} | "
                    f"Latency: {stats['latency']} | "
                    f"RREQ: {stats['total_rreq_sent']} | "
                    f"RREP: {stats['total_rrep_sent']} | "
                    f"Data Transfers: {stats['total_data_transfers']} | "
                    f"Choke Signals: {stats['total_choke_signals']}"
                )
            else:
                status_msg = f"❌ Simulation ended without delivery | Cycles: {stats['clock_cycles']}"
        
        self.main_window.update_status(status_msg)
        self.draw_network()
        self.update_statistics()
    def pause_simulation(self):
        """Pause or resume the simulation"""
        if not self.is_simulating:
            return
        
        self.is_paused = not self.is_paused
        
        if self.is_paused:
            self.pause_btn.config(text="▶️ Resume", bg="#2ecc71")
            self.step_btn.config(state=tk.NORMAL)
            self.main_window.update_status("⏸️ Simulation paused - Use 'Step Forward' for manual control")
        else:
            self.pause_btn.config(text="⏸️ Pause", bg="#f39c12")
            self.step_btn.config(state=tk.DISABLED if self.auto_step_var.get() else tk.NORMAL)
            self.main_window.update_status("▶️ Simulation resumed")
            self.animate_simulation()
    
    def _update_speed_display(self, value=None):
        """Update speed display label when slider changes"""
        speed = self.speed_multiplier.get()
        self.speed_display.config(text=f"{speed:.1f}x")
    
    def animate_simulation(self):
        """Animate simulation with delays, respecting pause and auto-step settings"""
        if not self.is_simulating or self.is_paused:
            return
        
        # Only auto-step if enabled
        if self.auto_step_var.get():
            self.step_simulation()
        
        if self.is_simulating and not self.is_paused:
            # Calculate delay: base_speed / multiplier
            # Higher multiplier = faster (less delay)
            # Lower multiplier = slower (more delay)
            multiplier = self.speed_multiplier.get()
            delay = int(self.base_speed / multiplier)
            self.canvas.after(delay, self.animate_simulation)
    
    def reset_simulation(self):
        """Reset simulation state"""
        self.is_simulating = False
        self.is_paused = False
        self.simulation_step = 0
        self.current_packet = None
        self.packet_phase = None
        self.simulator = None
        self.current_sim_phase = SimulationPhase.IDLE
        self.sim_events = []
        
        self.start_btn.config(state=tk.NORMAL)
        self.step_btn.config(state=tk.DISABLED)
        self.pause_btn.config(state=tk.DISABLED, text="⏸️ Pause", bg="#f39c12")
        
        # Reset AODV status bar
        self._reset_aodv_status()
        
        # Hide any active tooltips
        self._cancel_hover_timer()
        self._hide_tooltip()
        
        # Clear all buffers and reset nodes
        for node in self.nodes.values():
            node.input_buffer.clear()
            node.output_buffer.clear()
            node.reset_statistics()
            node.routing_table.clear()
            node.reverse_routes.clear()
            node.rreq_cache.clear()
            node.req_signal = False
            node.ack_signal = False
            node.choke_signal = False
            node.transfer_signal = False
        
        self.draw_network()
        self.update_statistics()
        self.main_window.update_status("Simulation reset")
    
    def update_statistics(self):
        """Update statistics display with REAL simulation metrics"""
        self.stats_text.config(state=tk.NORMAL)
        self.stats_text.delete(1.0, tk.END)
        
        stats = f"""Network Statistics:
━━━━━━━━━━━━━━━━━━━━━━━━━
Topology: Mesh {self.rows}×{self.cols}
Total Nodes: {len(self.nodes)}
Routing: XY + AODV Protocol

"""
        
        if self.simulator:
            sim_stats = self.simulator.get_statistics()
            stats += f"""Real Simulation Status:
━━━━━━━━━━━━━━━━━━━━━━━━━
Clock Cycles: {sim_stats['clock_cycles']}
Phase: {sim_stats['phase'].upper()}
Route Established: {'✓ Yes' if sim_stats['route_established'] else '✗ No'}

AODV Protocol Metrics:
━━━━━━━━━━━━━━━━━━━━━━━━━
RREQ Sent: {sim_stats['total_rreq_sent']}
RREP Sent: {sim_stats['total_rrep_sent']}
Data Transfers: {sim_stats['total_data_transfers']}
Choke Signals: {sim_stats['total_choke_signals']}

"""
            
            if sim_stats['data_delivered']:
                stats += f"""Delivery Status:
━━━━━━━━━━━━━━━━━━━━━━━━━
Status: ✅ DELIVERED
Latency: {sim_stats['latency']} cycles
"""
        
        if self.source_node and self.dest_node:
            hops = self.routing_algorithm.calculate_hops(
                self.source_node,
                self.dest_node
            )
            stats += f"""Routing Info:
━━━━━━━━━━━━━━━━━━━━━━━━━
Source: {self.source_node}
Destination: {self.dest_node}
Expected Hops: {hops}

"""
        
        if self.current_packet:
            packet_data = self.current_packet.payload.get("data", "")
            data_preview = packet_data[:30] + "..." if len(packet_data) > 30 else packet_data
            
            stats += f"""Current Packet:
━━━━━━━━━━━━━━━━━━━━━━━━━
ID: {self.current_packet.packet_id}
Type: {self.current_packet.packet_type.value.upper()}
Data: "{data_preview}"
Status: {self.current_packet.status.value}
Hops Taken: {self.current_packet.hops}
"""
            
            # Show current node buffer status
            if self.current_packet.current_node and self.current_packet.current_node in self.nodes:
                curr_node = self.nodes[self.current_packet.current_node]
                stats += f"""
Buffer Status (Current Node):
━━━━━━━━━━━━━━━━━━━━━━━━━
Node: {curr_node.position}
Input:  {curr_node.input_buffer.size()}/{curr_node.input_buffer.capacity} ({int(curr_node.input_buffer.utilization())}%)
Output: {curr_node.output_buffer.size()}/{curr_node.output_buffer.capacity} ({int(curr_node.output_buffer.utilization())}%)

Flow Control Signals:
━━━━━━━━━━━━━━━━━━━━━━━━━
"""
                
                if curr_node.req_signal:
                    stats += "  🟠 REQ: ACTIVE (Requesting transfer)\n"
                else:
                    stats += "  ○ REQ: Inactive\n"
                
                if curr_node.ack_signal:
                    stats += "  🔵 ACK: ACTIVE (Buffer available)\n"
                else:
                    stats += "  ○ ACK: Inactive\n"
                
                if curr_node.transfer_signal:
                    stats += "  🟢 Transfer: ACTIVE\n"
                else:
                    stats += "  ○ Transfer: Inactive\n"
                
                if curr_node.choke_signal:
                    stats += "  🔴 Choke: ACTIVE (Congestion!)\n"
                else:
                    stats += "  ○ Choke: Inactive\n"
                
                # Show routing table
                if curr_node.routing_table:
                    stats += f"""
Routing Table:
━━━━━━━━━━━━━━━━━━━━━━━━━
"""
                    for dest, route in list(curr_node.routing_table.items())[:5]:  # Show first 5
                        stats += f"  {dest} → {route.next_hop.value.upper()} (hops: {route.hop_count}, seq: {route.sequence_num})\n"
            
            # Recent simulation events
            if self.sim_events:
                stats += f"""
Recent Events:
━━━━━━━━━━━━━━━━━━━━━━━━━
"""
                for event in self.sim_events[:5]:  # Show last 5 events
                    stats += f"  • {event}\n"
            
            # Phase legend
            stats += f"""
Phase Legend:
━━━━━━━━━━━━━━━━━━━━━━━━━
🟠 ROUTE_DISCOVERY = RREQ broadcast
🔵 ROUTE_REPLY = RREP unicast
🟢 DATA_TRANSFER = Payload transmission
✅ COMPLETED = Simulation finished
"""
        
        self.stats_text.insert(1.0, stats)
        self.stats_text.config(state=tk.DISABLED)
