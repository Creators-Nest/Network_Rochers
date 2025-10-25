"""
Mesh Topology GUI with Control Panel and Visualization
Implements buffer-based routing with XY algorithm
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import math
from typing import Optional, Tuple, List, Dict

# Use relative imports within src package
from ..core.node import Node, Direction, NodeStatus
from ..core.packet import Packet, PacketStatus
from ..core.buffer import Buffer
from ..routing.xy_routing import XYRouting


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
        self.simulation_step = 0
        self.current_packet: Optional[Packet] = None
        self.packet_data = ""  # User-provided packet data
        self.active_packets: List[Packet] = []  # Support multiple packets
        self.packet_id_counter = 0  # Unique ID for each packet
        
        # Hover state for node expansion
        self.hover_node: Optional[Tuple[int, int]] = None
        self.hover_timer = None
        self.hover_delay = 2000  # 2 seconds in milliseconds
        self.expanded_node: Optional[Tuple[int, int]] = None
        
        # Colors
        self.colors = {
            'node_normal': '#3498db',
            'node_source': '#2ecc71',
            'node_dest': '#e74c3c',
            'node_selected': '#f39c12',
            'node_active': '#9b59b6',
            'connection': '#95a5a6',
            'packet': '#e67e22',
            'background': '#ecf0f1',
            'text': '#2c3e50'
        }
        
        # Create GUI layout
        self._create_layout()
        self._create_control_panel()
        
        # Initialize network BEFORE creating visualization
        # (so nodes exist when canvas tries to draw)
        self.create_mesh_network()
        
        # Create visualization area (will draw the network)
        self._create_visualization_area()
    
    def _create_layout(self):
        """Create main layout with left panel and right visualization"""
        # Left panel (Control Panel) - Fixed width
        self.control_panel = tk.Frame(
            self.parent,
            bg="#34495e",
            width=350,
            relief=tk.RAISED,
            borderwidth=2
        )
        self.control_panel.pack(side=tk.LEFT, fill=tk.Y)
        self.control_panel.pack_propagate(False)
        
        # Right area (Visualization)
        self.viz_frame = tk.Frame(self.parent, bg=self.colors['background'])
        self.viz_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
    
    def _create_control_panel(self):
        """Create left control panel with all controls"""
        # Title
        title_label = tk.Label(
            self.control_panel,
            text="Control Panel",
            font=("Arial", 16, "bold"),
            bg="#34495e",
            fg="white"
        )
        title_label.pack(pady=10)
        
        # Create scrollable frame for controls
        self.control_canvas = tk.Canvas(
            self.control_panel, 
            bg="#34495e", 
            highlightthickness=0,
            bd=0
        )
        scrollbar = ttk.Scrollbar(
            self.control_panel, 
            orient="vertical", 
            command=self.control_canvas.yview
        )
        self.scrollable_frame = tk.Frame(self.control_canvas, bg="#34495e")
        
        # Configure scrolling
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.control_canvas.configure(scrollregion=self.control_canvas.bbox("all"))
        )
        
        self.canvas_window = self.control_canvas.create_window(
            (0, 0), 
            window=self.scrollable_frame, 
            anchor="nw",
            width=330  # Fixed width to prevent horizontal scroll
        )
        
        self.control_canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        self.control_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Enable mouse wheel scrolling
        self._bind_mousewheel(self.control_canvas)
        self._bind_mousewheel(self.scrollable_frame)
        
        # Add control sections to scrollable frame
        self._create_topology_config(self.scrollable_frame)
        self._create_packet_routing(self.scrollable_frame)
        self._create_view_controls(self.scrollable_frame)
        self._create_simulation_controls(self.scrollable_frame)
        self._create_statistics(self.scrollable_frame)
        self._create_help_section(self.scrollable_frame)
    
    def _bind_mousewheel(self, widget):
        """Bind mouse wheel scrolling to widget"""
        # Windows
        widget.bind("<MouseWheel>", self._on_mousewheel)
        # Linux
        widget.bind("<Button-4>", self._on_mousewheel)
        widget.bind("<Button-5>", self._on_mousewheel)
        # Bind to all children recursively
        for child in widget.winfo_children():
            self._bind_mousewheel(child)
    
    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling"""
        if event.num == 5 or event.delta < 0:
            # Scroll down
            self.control_canvas.yview_scroll(1, "units")
        elif event.num == 4 or event.delta > 0:
            # Scroll up
            self.control_canvas.yview_scroll(-1, "units")
    
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
        
        # Simulation speed
        speed_frame = tk.Frame(section, bg="#34495e")
        speed_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(
            speed_frame,
            text="Speed (ms):",
            bg="#34495e",
            fg="white",
            font=("Arial", 9)
        ).pack(side=tk.LEFT)
        
        self.speed_var = tk.IntVar(value=500)
        speed_spinbox = tk.Spinbox(
            speed_frame,
            from_=100,
            to=2000,
            increment=100,
            textvariable=self.speed_var,
            width=8,
            font=("Arial", 9)
        )
        speed_spinbox.pack(side=tk.LEFT, padx=5)
    
    def _create_statistics(self, parent):
        """Create statistics section"""
        section = self._create_section(parent, "📊 Statistics")
        
        # Stats text area
        self.stats_text = scrolledtext.ScrolledText(
            section,
            height=8,
            width=35,
            bg="#2c3e50",
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

🎨 Colors:
  • Blue: Normal nodes
  • Green: Source node
  • Red: Destination node
  • Orange: Packet/Selected
  
⚠️ Signals:
  • REQ: Request buffer space
  • ACK: Acknowledge available
  • Choke: Congestion backpressure
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
        header = tk.Frame(parent, bg="#2c3e50", height=30)
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
        content = tk.Frame(parent, bg="#34495e", relief=tk.SUNKEN, borderwidth=1)
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
        self.canvas.bind("<Motion>", self.on_canvas_hover)
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
        
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if canvas_width <= 1:
            canvas_width = 800
        if canvas_height <= 1:
            canvas_height = 600
        
        # Calculate spacing with better handling for large grids
        margin = 80  # Reduced margin for large grids
        
        # Adjust margin based on grid size
        if max(self.rows, self.cols) > 20:
            margin = 50
        elif max(self.rows, self.cols) > 30:
            margin = 30
        
        available_width = canvas_width - 2 * margin
        available_height = canvas_height - 2 * margin
        
        # Better spacing calculation to prevent division issues
        if self.cols > 1:
            spacing_x = available_width / (self.cols - 1)
        else:
            spacing_x = available_width / 2
            
        if self.rows > 1:
            spacing_y = available_height / (self.rows - 1)
        else:
            spacing_y = available_height / 2
        
        # Auto-adjust node radius based on grid size
        if self.auto_adjust_size:
            # Calculate optimal node radius to fit the grid
            max_nodes = max(self.rows, self.cols)
            if max_nodes <= 5:
                self.node_radius = 25
            elif max_nodes <= 10:
                self.node_radius = 18
            elif max_nodes <= 15:
                self.node_radius = 12
            elif max_nodes <= 20:
                self.node_radius = 10
            elif max_nodes <= 30:
                self.node_radius = 7
            elif max_nodes <= 40:
                self.node_radius = 5
            else:  # 41-50
                self.node_radius = 4
            
            # Also adjust based on spacing to prevent overlap
            min_spacing = min(spacing_x, spacing_y)
            optimal_radius = min_spacing / 2.5  # Leave some gap between nodes
            self.node_radius = min(self.node_radius, optimal_radius)
            
            # Ensure minimum visible size
            self.node_radius = max(self.node_radius, 3)
        
        # Draw connections first (so they appear behind nodes)
        for row in range(self.rows):
            for col in range(self.cols):
                if (row, col) not in self.nodes:
                    continue
                
                node = self.nodes[(row, col)]
                x1 = margin + col * spacing_x * self.zoom_level + self.offset_x
                y1 = margin + row * spacing_y * self.zoom_level + self.offset_y
                
                # Draw horizontal connections with signal indicators
                if col < self.cols - 1 and (row, col + 1) in self.nodes:
                    x2 = margin + (col + 1) * spacing_x * self.zoom_level + self.offset_x
                    y2 = y1
                    
                    # Base connection line
                    self.canvas.create_line(
                        x1, y1, x2, y2,
                        fill=self.colors['connection'],
                        width=2,
                        tags="connection"
                    )
                    
                    # Draw signal indicators for EAST direction
                    self._draw_signal_indicators(node, Direction.EAST, x1, y1, x2, y2)
                
                # Draw vertical connections with signal indicators
                if row < self.rows - 1 and (row + 1, col) in self.nodes:
                    x2 = x1
                    y2 = margin + (row + 1) * spacing_y * self.zoom_level + self.offset_y
                    
                    # Base connection line
                    self.canvas.create_line(
                        x1, y1, x2, y2,
                        fill=self.colors['connection'],
                        width=2,
                        tags="connection"
                    )
                    
                    # Draw signal indicators for SOUTH direction
                    self._draw_signal_indicators(node, Direction.SOUTH, x1, y1, x2, y2)
        
        # Draw nodes (now as squares)
        for row in range(self.rows):
            for col in range(self.cols):
                # Check if node exists before accessing
                if (row, col) not in self.nodes:
                    continue
                
                x = margin + col * spacing_x * self.zoom_level + self.offset_x
                y = margin + row * spacing_y * self.zoom_level + self.offset_y
                
                # Determine node color
                node = self.nodes[(row, col)]
                if (row, col) == self.source_node:
                    color = self.colors['node_source']
                elif (row, col) == self.dest_node:
                    color = self.colors['node_dest']
                elif (row, col) == self.selected_node:
                    color = self.colors['node_selected']
                else:
                    color = self.colors['node_normal']
                
                # Draw node as SQUARE instead of circle
                size = self.node_radius * self.zoom_level
                self.canvas.create_rectangle(
                    x - size, y - size,
                    x + size, y + size,
                    fill=color,
                    outline=self.colors['text'],
                    width=2,
                    tags=f"node_{row}_{col}"
                )
                
                # Draw node label
                self.canvas.create_text(
                    x, y,
                    text=f"({row},{col})",
                    fill="white",
                    font=("Arial", int(10 * self.zoom_level), "bold"),
                    tags=f"label_{row}_{col}"
                )
                
                # Draw buffer status if active
                node = self.nodes[(row, col)]
                if not node.input_buffer.is_empty() or not node.output_buffer.is_empty():
                    buffer_text = f"I:{node.input_buffer.size()} O:{node.output_buffer.size()}"
                    self.canvas.create_text(
                        x, y + size + 15,
                        text=buffer_text,
                        fill=self.colors['text'],
                        font=("Arial", int(8 * self.zoom_level)),
                        tags=f"buffer_{row}_{col}"
                    )
        
        # Draw expanded node details if hovering
        if self.expanded_node:
            self.draw_expanded_node(self.expanded_node, margin, spacing_x, spacing_y)
        
        # Draw all active packet paths (support multiple packets)
        for packet in self.active_packets:
            if packet.status != PacketStatus.DELIVERED and len(packet.path) > 1:
                self.draw_packet_path(packet)
    
    def draw_packet_path(self, packet: Packet):
        """Draw the packet's path on the canvas as spears/arrows"""
        margin = 80
        
        # Adjust margin based on grid size
        if max(self.rows, self.cols) > 20:
            margin = 50
        elif max(self.rows, self.cols) > 30:
            margin = 30
        
        canvas_width = self.canvas.winfo_width() or 800
        canvas_height = self.canvas.winfo_height() or 600
        
        available_width = canvas_width - 2 * margin
        available_height = canvas_height - 2 * margin
        
        # Better spacing calculation
        if self.cols > 1:
            spacing_x = available_width / (self.cols - 1)
        else:
            spacing_x = available_width / 2
            
        if self.rows > 1:
            spacing_y = available_height / (self.rows - 1)
        else:
            spacing_y = available_height / 2
        
        # Draw path as spear-like arrows
        for i in range(len(packet.path) - 1):
            row1, col1 = packet.path[i]
            row2, col2 = packet.path[i + 1]
            
            x1 = margin + col1 * spacing_x * self.zoom_level + self.offset_x
            y1 = margin + row1 * spacing_y * self.zoom_level + self.offset_y
            x2 = margin + col2 * spacing_x * self.zoom_level + self.offset_x
            y2 = margin + row2 * spacing_y * self.zoom_level + self.offset_y
            
            # Draw spear-like arrow with larger arrowhead
            self.canvas.create_line(
                x1, y1, x2, y2,
                fill=self.colors['packet'],
                width=3,
                arrow=tk.LAST,
                arrowshape=(15, 20, 6),  # Larger, spear-like arrowhead
                tags="packet_path"
            )
        
        # Draw packet at current position as a spear/diamond shape
        if packet.current_node:
            row, col = packet.current_node
            x = margin + col * spacing_x * self.zoom_level + self.offset_x
            y = margin + row * spacing_y * self.zoom_level + self.offset_y
            
            size = self.node_radius * self.zoom_level * 0.4
            
            # Draw diamond/spear shape for current packet
            points = [
                x, y - size * 1.5,      # Top point (spear tip)
                x + size * 0.6, y,      # Right
                x, y + size * 0.8,      # Bottom
                x - size * 0.6, y       # Left
            ]
            
            self.canvas.create_polygon(
                points,
                fill=self.colors['packet'],
                outline="white",
                width=2,
                tags="packet_current"
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
    
    def find_node_at_position(self, x: int, y: int) -> Optional[Tuple[int, int]]:
        """Find node at given canvas position"""
        margin = 80
        
        # Adjust margin based on grid size
        if max(self.rows, self.cols) > 20:
            margin = 50
        elif max(self.rows, self.cols) > 30:
            margin = 30
        
        canvas_width = self.canvas.winfo_width() or 800
        canvas_height = self.canvas.winfo_height() or 600
        
        available_width = canvas_width - 2 * margin
        available_height = canvas_height - 2 * margin
        
        # Better spacing calculation
        if self.cols > 1:
            spacing_x = available_width / (self.cols - 1)
        else:
            spacing_x = available_width / 2
            
        if self.rows > 1:
            spacing_y = available_height / (self.rows - 1)
        else:
            spacing_y = available_height / 2
        
        size = self.node_radius * self.zoom_level
        
        for row in range(self.rows):
            for col in range(self.cols):
                node_x = margin + col * spacing_x * self.zoom_level + self.offset_x
                node_y = margin + row * spacing_y * self.zoom_level + self.offset_y
                
                # Check if point is inside square node
                if (node_x - size <= x <= node_x + size and 
                    node_y - size <= y <= node_y + size):
                    return (row, col)
        
        return None
    
    def on_canvas_hover(self, event):
        """Handle mouse hover over canvas"""
        hovered_node = self.find_node_at_position(event.x, event.y)
        
        if hovered_node != self.hover_node:
            # Cancel previous timer
            if self.hover_timer:
                self.canvas.after_cancel(self.hover_timer)
                self.hover_timer = None
            
            # Clear expansion if hovering away
            if hovered_node is None and self.expanded_node:
                self.expanded_node = None
                self.draw_network()
            
            self.hover_node = hovered_node
            
            # Start new timer if hovering over a node
            if self.hover_node:
                self.hover_timer = self.canvas.after(
                    self.hover_delay, 
                    lambda: self.expand_node(self.hover_node)
                )
    
    def on_canvas_leave(self, event):
        """Handle mouse leaving canvas"""
        if self.hover_timer:
            self.canvas.after_cancel(self.hover_timer)
            self.hover_timer = None
        
        self.hover_node = None
        if self.expanded_node:
            self.expanded_node = None
            self.draw_network()
    
    def expand_node(self, node_pos: Tuple[int, int]):
        """Expand node to show detailed router information"""
        if node_pos and node_pos in self.nodes:
            self.expanded_node = node_pos
            self.draw_network()
    
    def draw_expanded_node(self, node_pos: Tuple[int, int], margin: int, 
                          spacing_x: float, spacing_y: float):
        """Draw expanded node with detailed router information (as per image)"""
        row, col = node_pos
        node = self.nodes[node_pos]
        
        # Calculate base position
        x = margin + col * spacing_x * self.zoom_level + self.offset_x
        y = margin + row * spacing_y * self.zoom_level + self.offset_y
        
        # Expanded size (larger than normal) - INCREASED SIZE
        exp_width = 360
        exp_height = 380
        
        # Draw expanded background
        self.canvas.create_rectangle(
            x - exp_width/2, y - exp_height/2,
            x + exp_width/2, y + exp_height/2,
            fill="#2c3e50",
            outline="#e74c3c",
            width=3,
            tags="expanded_node"
        )
        
        # Title
        self.canvas.create_text(
            x, y - exp_height/2 + 20,
            text=f"Router Node ({row},{col})",
            fill="white",
            font=("Arial", 12, "bold"),
            tags="expanded_node"
        )
        
        # Draw signal indicators at top (REQ, ACK, DATA, CLK, Choke)
        signal_y = y - exp_height/2 + 45
        signals = [
            ("REQ", node.input_buffer.size() > 0),
            ("ACK", not node.input_buffer.is_full()),
            ("DATA", node.output_buffer.size() > 0),
            ("CLK", True),
            ("Choke", node.input_buffer.size() >= node.input_buffer.capacity * 0.8)
        ]
        
        signal_spacing = 40
        start_x = x - 80
        for i, (signal_name, is_active) in enumerate(signals):
            sig_x = start_x + i * signal_spacing
            
            # Draw signal circle indicator
            circle_radius = 8
            color = "#2ecc71" if is_active else "#7f8c8d"
            
            self.canvas.create_oval(
                sig_x - circle_radius, signal_y - circle_radius,
                sig_x + circle_radius, signal_y + circle_radius,
                fill=color,
                outline="white",
                width=2,
                tags="expanded_node"
            )
            
            # Draw signal label with larger font
            self.canvas.create_text(
                sig_x, signal_y + circle_radius + 12,
                text=signal_name,
                fill="white",
                font=("Arial", 9, "bold"),
                tags="expanded_node"
            )
        
        # Draw Routing Logic (hexagon) - LARGER SIZE
        self.draw_hexagon(x - 70, y + 10, 38, "#3498db", "Routing\nLogic")
        
        # Draw Application Logic (hexagon) - LARGER SIZE
        self.draw_hexagon(x, y + 10, 38, "#9b59b6", "Application\nLogic")
        
        # Draw Control Logic (hexagon) - LARGER SIZE
        self.draw_hexagon(x + 70, y + 10, 38, "#e67e22", "Control\nLogic")
        
        # Draw Send Buffer (circular with segments) - LARGER SIZE with label below
        self.draw_circular_buffer(x - 85, y + 95, 45, node.output_buffer, "Send Buffer")
        
        # Draw Receive Buffer (circular with segments) - LARGER SIZE with label below
        self.draw_circular_buffer(x + 85, y + 95, 45, node.input_buffer, "Receive Buffer")
        
        # Draw Send Register and Receive Register ADJACENT (side by side)
        register_y = y + exp_height/2 - 70
        
        # Send Register (left)
        self.canvas.create_rectangle(
            x - 100, register_y,
            x - 10, register_y + 22,
            fill="#34495e",
            outline="white",
            width=2,
            tags="expanded_node"
        )
        self.canvas.create_text(
            x - 55, register_y + 11,
            text="Send Register",
            fill="white",
            font=("Arial", 9, "bold"),
            tags="expanded_node"
        )
        
        # Receive Register (right)
        self.canvas.create_rectangle(
            x + 10, register_y,
            x + 100, register_y + 22,
            fill="#34495e",
            outline="white",
            width=2,
            tags="expanded_node"
        )
        self.canvas.create_text(
            x + 55, register_y + 11,
            text="Receive Register",
            fill="white",
            font=("Arial", 9, "bold"),
            tags="expanded_node"
        )
        
        # Draw status bits below circles with names below and counts
        bit_y = y + 170
        
        # Receive Bit (below left circle)
        self.canvas.create_text(
            x - 85, bit_y,
            text="Receive Bit",
            fill="white",
            font=("Arial", 10, "bold"),
            tags="expanded_node"
        )
        
        # Transfer Bit (below left circle)
        self.canvas.create_text(
            x - 85, bit_y + 20,
            text="Transfer Bit",
            fill="white",
            font=("Arial", 10, "bold"),
            tags="expanded_node"
        )
        
        # Busy Bit (below right circle)
        busy_status = "IDLE"
        if self.is_simulating and self.current_packet and node_pos == self.current_packet.current_node:
            busy_status = "BUSY"
        busy_color = "#e74c3c" if busy_status == "BUSY" else "#2ecc71"
        
        self.canvas.create_text(
            x + 85, bit_y,
            text="Busy Bit",
            fill="white",
            font=("Arial", 10, "bold"),
            tags="expanded_node"
        )
        self.canvas.create_text(
            x + 85, bit_y + 20,
            text=busy_status,
            fill=busy_color,
            font=("Arial", 11, "bold"),
            tags="expanded_node"
        )
        
        # Draw buffer statistics at bottom
        stats_y = y + exp_height/2 - 25
        stats_text = f"In: {node.input_buffer.size()}/{node.input_buffer.capacity}  |  Out: {node.output_buffer.size()}/{node.output_buffer.capacity}"
        self.canvas.create_text(
            x, stats_y,
            text=stats_text,
            fill="#ecf0f1",
            font=("Arial", 10, "bold"),
            tags="expanded_node"
        )
    
    def draw_hexagon(self, x: float, y: float, size: int, color: str, text: str):
        """Draw hexagon shape for logic blocks"""
        import math
        points = []
        for i in range(6):
            angle = math.pi / 3 * i
            px = x + size * math.cos(angle)
            py = y + size * math.sin(angle)
            points.extend([px, py])
        
        self.canvas.create_polygon(
            points,
            fill=color,
            outline="white",
            width=2,
            tags="expanded_node"
        )
        self.canvas.create_text(
            x, y,
            text=text,
            fill="white",
            font=("Arial", 7, "bold"),
            tags="expanded_node"
        )
    
    def draw_circular_buffer(self, x: float, y: float, radius: int, buffer, label: str):
        """Draw circular buffer with segments showing occupancy - label below, count inside"""
        from ..core.buffer import Buffer
        
        # Draw outer circle with thicker border
        self.canvas.create_oval(
            x - radius, y - radius,
            x + radius, y + radius,
            fill="#34495e",
            outline="white",
            width=3,
            tags="expanded_node"
        )
        
        # Draw segments (like pie chart)
        import math
        segments = 8  # Visual segments
        occupied = buffer.size()
        capacity = buffer.capacity
        
        for i in range(segments):
            angle_start = (360 / segments) * i
            angle_end = (360 / segments) * (i + 1)
            
            # Determine if segment is filled
            segment_threshold = (capacity / segments) * (i + 1)
            is_filled = occupied >= segment_threshold
            
            # Draw segment line
            angle_rad = math.radians(angle_start - 90)
            x1 = x + (radius * 0.3) * math.cos(angle_rad)
            y1 = y + (radius * 0.3) * math.sin(angle_rad)
            x2 = x + radius * math.cos(angle_rad)
            y2 = y + radius * math.sin(angle_rad)
            
            color = "#2ecc71" if is_filled else "#7f8c8d"
            self.canvas.create_line(
                x1, y1, x2, y2,
                fill=color,
                width=3,
                tags="expanded_node"
            )
        
        # Draw label BELOW the circle
        self.canvas.create_text(
            x, y + radius + 18,
            text=label,
            fill="white",
            font=("Arial", 10, "bold"),
            tags="expanded_node"
        )
        
        # Draw count INSIDE circle (center)
        self.canvas.create_text(
            x, y,
            text=f"{occupied}/{capacity}",
            fill="white",
            font=("Arial", 12, "bold"),
            tags="expanded_node"
        )
    
    def _draw_signal_indicators(self, node, direction: Direction, x1: float, y1: float, x2: float, y2: float):
        """
        Draw communication signal indicators between nodes (Figure 4)
        Shows REQ, ACK, DATA, CLK, Choke signals for unidirectional mode
        """
        signals = node.get_signal_state(direction)
        
        # Calculate midpoint for signal indicators
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2
        
        # Determine if connection is horizontal or vertical
        is_horizontal = abs(y2 - y1) < abs(x2 - x1)
        
        # Offset for signal indicators
        if is_horizontal:
            offset_x, offset_y = 0, -15
        else:
            offset_x, offset_y = 15, 0
        
        # Draw signal indicators only if any signal is active
        if any([signals['REQ'], signals['ACK'], signals['CLK'], signals['Choke']]):
            indicator_y = mid_y + offset_y
            indicator_x = mid_x + offset_x
            
            # REQ signal (red arrow if active)
            if signals['REQ']:
                self.canvas.create_text(
                    indicator_x, indicator_y - 10,
                    text="REQ→",
                    fill="#e74c3c",
                    font=("Arial", 9, "bold"),
                    tags="signal"
                )
            
            # ACK signal (green arrow if active)
            if signals['ACK']:
                self.canvas.create_text(
                    indicator_x, indicator_y + 2,
                    text="←ACK",
                    fill="#2ecc71",
                    font=("Arial", 9, "bold"),
                    tags="signal"
                )
            
            # CLK signal (blue pulse if active)
            if signals['CLK']:
                self.canvas.create_oval(
                    mid_x - 4, mid_y - 4,
                    mid_x + 4, mid_y + 4,
                    fill="#3498db",
                    outline="white",
                    width=2,
                    tags="signal"
                )
            
            # Choke signal (yellow warning if active)
            if signals['Choke']:
                self.canvas.create_text(
                    indicator_x, indicator_y + 12,
                    text="⚠",
                    fill="#f39c12",
                    font=("Arial", 12, "bold"),
                    tags="signal"
                )
    
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
            
            # Reset everything
            self.reset_simulation()
            self.create_mesh_network()
            self.clear_selection()
            
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
        """Start packet routing simulation - supports multiple parallel packets"""
        if self.source_node is None or self.dest_node is None:
            messagebox.showwarning(
                "Incomplete Selection",
                "Please select both source and destination nodes"
            )
            return
        
        if self.source_node == self.dest_node:
            messagebox.showwarning(
                "Invalid Selection",
                "Source and destination must be different!"
            )
            return
        
        # Get user-provided packet data
        self.packet_data = self.data_entry.get(1.0, tk.END).strip()
        if not self.packet_data:
            self.packet_data = "Default packet data"
        
        # Create new packet (packet_id is auto-generated by Packet class)
        new_packet = Packet(
            source=self.source_node,
            destination=self.dest_node,
            payload={
                "data": self.packet_data,
                "size": len(self.packet_data),
                "type": "user_packet"
            },
            creation_time=self.simulation_step,
            priority=1
        )
        
        # Calculate route using XY routing
        route = self.routing_algorithm.route(
            self.source_node,
            self.dest_node,
            self.rows,
            self.cols
        )
        
        new_packet.path = route
        new_packet.current_node = self.source_node
        new_packet.status = PacketStatus.IN_TRANSIT
        
        # Add to active packets list
        self.active_packets.append(new_packet)
        
        # Track total packets created
        self.packet_id_counter = new_packet.packet_id
        
        # Set as current packet for compatibility
        self.current_packet = new_packet
        
        # Update state
        self.is_simulating = True
        if self.simulation_step == 0:
            self.simulation_step = 0
        self.start_btn.config(state=tk.NORMAL)  # Allow adding more packets
        self.step_btn.config(state=tk.NORMAL)
        
        # Update status
        self.main_window.update_status(
            f"Packet #{new_packet.packet_id} created: {self.source_node} → {self.dest_node}"
        )
        
        # Clear selection to allow new packet creation
        self.source_node = None
        self.dest_node = None
        self.source_label.config(text="Not selected")
        self.dest_label.config(text="Not selected")
        
        # Start animation if not already running
        if len(self.active_packets) == 1:
            self.animate_simulation()
        
        self.draw_network()
        self.update_statistics()
    
    def step_simulation(self):
        """
        Move ALL active packets one step using Figure 4 protocol
        REQ/ACK/DATA/CLK/Choke handshaking mechanism
        """
        if not self.active_packets:
            return
        
        packets_to_remove = []
        
        # Phase 1: Request phase - packets request transfer (REQ signal)
        for packet in self.active_packets:
            if packet.status == PacketStatus.DELIVERED:
                packets_to_remove.append(packet)
                continue
            
            current_idx = packet.path.index(packet.current_node)
            
            # Check if reached destination
            if current_idx >= len(packet.path) - 1:
                packet.status = PacketStatus.DELIVERED
                packet.current_node = packet.destination
                self.main_window.update_status(
                    f"✓ Packet #{packet.packet_id} delivered to {packet.destination}!"
                )
                packets_to_remove.append(packet)
                continue
            
            # Get current and next node
            next_node_pos = packet.path[current_idx + 1]
            current_node = self.nodes[packet.current_node]
            next_node = self.nodes[next_node_pos]
            
            # Determine direction for transfer
            direction = self._get_direction(packet.current_node, next_node_pos)
            
            if direction:
                # Step 1: Check Choke signal (fairness mechanism)
                opposite_dir = self._opposite_direction(direction)
                if next_node.signals.get(opposite_dir, {}).get('Choke', False):
                    self.main_window.update_status(
                        f"⚠ Packet #{packet.packet_id}: Choke active, waiting for fairness"
                    )
                    continue
                
                # Step 2: Raise REQ signal (request transfer)
                if current_node.initiate_transfer(direction, packet):
                    # Step 3: Next node acknowledges (ACK signal)
                    if next_node.acknowledge_transfer(opposite_dir):
                        # Step 4: CLK pulse - complete transfer with DATA
                        transferred = next_node.complete_transfer(opposite_dir)
                        
                        if transferred:
                            # Update packet position
                            packet.current_node = next_node_pos
                            
                            # Move from current output buffer
                            if not current_node.output_buffer.is_empty():
                                current_node.output_buffer.dequeue()
                            
                            # Process at next node (Reception → Routing)
                            if not next_node.input_buffer.is_empty():
                                next_node.output_buffer.enqueue(next_node.input_buffer.dequeue())
                            
                            self.main_window.update_status(
                                f"→ Packet #{packet.packet_id}: {packet.current_node} (REQ→ACK→CLK→DATA)"
                            )
                        else:
                            self.main_window.update_status(
                                f"⚠ Packet #{packet.packet_id}: Transfer failed at {next_node_pos}"
                            )
                    else:
                        self.main_window.update_status(
                            f"⚠ Packet #{packet.packet_id}: No ACK from {next_node_pos}"
                        )
                else:
                    # Buffer full - cannot initiate transfer
                    self.main_window.update_status(
                        f"⚠ Packet #{packet.packet_id}: Buffer full at {next_node_pos}"
                    )
        
        # Remove delivered packets
        for packet in packets_to_remove:
            self.active_packets.remove(packet)
        
        # Update current_packet to first active packet
        if self.active_packets:
            self.current_packet = self.active_packets[0]
        else:
            self.current_packet = None
        
        self.simulation_step += 1
        self.draw_network()
        self.update_statistics()
        
        # Check if all packets delivered
        if not self.active_packets:
            self.is_simulating = False
            self.start_btn.config(state=tk.NORMAL)
            self.step_btn.config(state=tk.DISABLED)
            self.main_window.update_status("✓ All packets delivered!")
            messagebox.showinfo(
                "Simulation Complete",
                f"All packets successfully delivered!\nTotal steps: {self.simulation_step}"
            )
    
    def _get_direction(self, from_pos: Tuple[int, int], to_pos: Tuple[int, int]) -> Optional[Direction]:
        """Get direction from one position to another"""
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        
        if to_row < from_row:
            return Direction.NORTH
        elif to_row > from_row:
            return Direction.SOUTH
        elif to_col < from_col:
            return Direction.WEST
        elif to_col > from_col:
            return Direction.EAST
        
        return None
    
    def _opposite_direction(self, direction: Direction) -> Direction:
        """Get opposite direction"""
        opposites = {
            Direction.NORTH: Direction.SOUTH,
            Direction.SOUTH: Direction.NORTH,
            Direction.EAST: Direction.WEST,
            Direction.WEST: Direction.EAST,
        }
        return opposites.get(direction, direction)
    
    def animate_simulation(self):
        """Automatically animate the simulation - handles multiple packets"""
        if self.is_simulating and self.active_packets:
            self.step_simulation()
            # Continue animation if packets still active
            if self.active_packets:
                self.canvas.after(self.speed_var.get(), self.animate_simulation)
    
    def reset_simulation(self):
        """Reset simulation state"""
        self.is_simulating = False
        self.simulation_step = 0
        self.current_packet = None
        self.active_packets.clear()
        self.packet_id_counter = 0
        Packet.reset_counter()  # Reset the Packet class counter
        self.start_btn.config(state=tk.NORMAL)
        self.step_btn.config(state=tk.DISABLED)
        
        # Clear all buffers
        for node in self.nodes.values():
            node.input_buffer.clear()
            node.output_buffer.clear()
        
        self.main_window.update_status("Simulation reset")
        self.draw_network()
        self.update_statistics()
        for node in self.nodes.values():
            node.input_buffer.clear()
            node.output_buffer.clear()
            node.reset_statistics()
        
        self.draw_network()
        self.update_statistics()
        self.main_window.update_status("Simulation reset")
    
    def update_statistics(self):
        """Update statistics display with multiple packet support"""
        self.stats_text.config(state=tk.NORMAL)
        self.stats_text.delete(1.0, tk.END)
        
        stats = f"""Network Statistics:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Grid Size: {self.rows} × {self.cols}
Total Nodes: {len(self.nodes)}
Active Packets: {len(self.active_packets)}
Total Packets: {self.packet_id_counter}
Simulation Step: {self.simulation_step}

Status: {"Running" if self.is_simulating else "Idle"}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        if self.active_packets:
            stats += "\nActive Packets:\n"
            for packet in self.active_packets:
                progress = 0
                if packet.path:
                    current_idx = packet.path.index(packet.current_node) if packet.current_node in packet.path else 0
                    progress = int((current_idx / max(1, len(packet.path) - 1)) * 100)
                
                stats += f"  #{packet.packet_id}: {packet.current_node} → {packet.destination} ({progress}%)\n"
        
        self.stats_text.insert(1.0, stats)
        self.stats_text.config(state=tk.DISABLED)
