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
        
        # Calculate spacing
        margin = 100
        available_width = canvas_width - 2 * margin
        available_height = canvas_height - 2 * margin
        
        spacing_x = available_width / max(1, self.cols - 1) if self.cols > 1 else available_width
        spacing_y = available_height / max(1, self.rows - 1) if self.rows > 1 else available_height
        
        # Auto-adjust node radius based on grid size
        if self.auto_adjust_size:
            # Calculate optimal node radius to fit the grid
            max_nodes = max(self.rows, self.cols)
            if max_nodes <= 5:
                self.node_radius = 25
            elif max_nodes <= 10:
                self.node_radius = 20
            elif max_nodes <= 20:
                self.node_radius = 12
            elif max_nodes <= 30:
                self.node_radius = 8
            else:
                self.node_radius = 5
            
            # Also adjust based on spacing
            min_spacing = min(spacing_x, spacing_y)
            optimal_radius = min_spacing / 3
            self.node_radius = min(self.node_radius, optimal_radius)
        
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
                
                # Determine node color
                if (row, col) == self.source_node:
                    color = self.colors['node_source']
                elif (row, col) == self.dest_node:
                    color = self.colors['node_dest']
                elif (row, col) == self.selected_node:
                    color = self.colors['node_selected']
                else:
                    color = self.colors['node_normal']
                
                # Draw node circle
                radius = self.node_radius * self.zoom_level
                self.canvas.create_oval(
                    x - radius, y - radius,
                    x + radius, y + radius,
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
                        x, y + radius + 15,
                        text=buffer_text,
                        fill=self.colors['text'],
                        font=("Arial", int(8 * self.zoom_level)),
                        tags=f"buffer_{row}_{col}"
                    )
        
        # Draw current packet path if exists
        if self.current_packet and len(self.current_packet.path) > 1:
            self.draw_packet_path(self.current_packet)
    
    def draw_packet_path(self, packet: Packet):
        """Draw the packet's path on the canvas"""
        margin = 100
        canvas_width = self.canvas.winfo_width() or 800
        canvas_height = self.canvas.winfo_height() or 600
        
        available_width = canvas_width - 2 * margin
        available_height = canvas_height - 2 * margin
        
        spacing_x = available_width / max(1, self.cols - 1) if self.cols > 1 else available_width
        spacing_y = available_height / max(1, self.rows - 1) if self.rows > 1 else available_height
        
        # Draw path
        for i in range(len(packet.path) - 1):
            row1, col1 = packet.path[i]
            row2, col2 = packet.path[i + 1]
            
            x1 = margin + col1 * spacing_x * self.zoom_level + self.offset_x
            y1 = margin + row1 * spacing_y * self.zoom_level + self.offset_y
            x2 = margin + col2 * spacing_x * self.zoom_level + self.offset_x
            y2 = margin + row2 * spacing_y * self.zoom_level + self.offset_y
            
            self.canvas.create_line(
                x1, y1, x2, y2,
                fill=self.colors['packet'],
                width=4,
                arrow=tk.LAST,
                arrowshape=(10, 12, 5),
                tags="packet_path"
            )
        
        # Draw packet at current position
        if packet.current_node:
            row, col = packet.current_node
            x = margin + col * spacing_x * self.zoom_level + self.offset_x
            y = margin + row * spacing_y * self.zoom_level + self.offset_y
            
            radius = self.node_radius * self.zoom_level * 0.3
            self.canvas.create_oval(
                x - radius, y - radius,
                x + radius, y + radius,
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
        margin = 100
        canvas_width = self.canvas.winfo_width() or 800
        canvas_height = self.canvas.winfo_height() or 600
        
        available_width = canvas_width - 2 * margin
        available_height = canvas_height - 2 * margin
        
        spacing_x = available_width / max(1, self.cols - 1) if self.cols > 1 else available_width
        spacing_y = available_height / max(1, self.rows - 1) if self.rows > 1 else available_height
        
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
            
            # Reset everything
            self.clear_selection()
            self.reset_simulation()
            self.create_mesh_network()
            
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
        """Start packet routing simulation following Content.txt specification"""
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
        
        # Create packet with user data
        # Following Content.txt: packet contains header (destination) + payload (data)
        self.current_packet = Packet(
            source=self.source_node,
            destination=self.dest_node,
            payload={
                "data": self.packet_data,
                "size": len(self.packet_data),
                "type": "user_packet"
            },
            creation_time=self.simulation_step
        )
        
        # Step 1 (Content.txt): Reception and Input
        # Inject packet at source - goes to Send Buffer first
        source_node = self.nodes[self.source_node]
        source_node.inject_packet(self.current_packet)
        
        self.is_simulating = True
        self.simulation_step = 0
        self.start_btn.config(state=tk.DISABLED)
        self.step_btn.config(state=tk.NORMAL)
        
        self.main_window.update_status(
            f"Simulation started - Sending: '{self.packet_data[:30]}...'"
        )
        self.animate_simulation()
    
    def step_simulation(self):
        """
        Perform one simulation step following Content.txt specification:
        1. Reception and Input (Receive Bit, Receive Buffer)
        2. Routing and Decision (Routing Logic, REQ signal)
        3. Transmission and Flow Control (ACK, Transfer Bit, CLK)
        4. Congestion Management (Choke signal)
        """
        if not self.current_packet or self.current_packet.status == PacketStatus.DELIVERED:
            return
        
        current_pos = self.current_packet.current_node
        current_node = self.nodes[current_pos]
        
        # Step 2 (Content.txt): Routing and Decision
        # Routing Logic reads destination address from header flit
        next_direction = self.routing_algorithm.get_next_direction(
            current_node,
            self.current_packet
        )
        
        if next_direction is None:
            # Step 4 (Content.txt): Local Interaction
            # Packet has reached destination - eject from Receive Buffer
            self.current_packet.deliver(self.simulation_step)
            self.is_simulating = False
            self.start_btn.config(state=tk.NORMAL)
            self.step_btn.config(state=tk.DISABLED)
            
            # Show delivered data
            delivered_data = self.current_packet.payload.get("data", "")
            self.main_window.update_status(
                f"✓ Packet delivered! Data: '{delivered_data[:30]}...' | "
                f"Hops: {self.current_packet.hops} | "
                f"Latency: {self.current_packet.get_latency()} cycles"
            )
        else:
            # Step 2 (Content.txt): Control Logic sends REQ signal to downstream
            next_node = current_node.get_neighbor(next_direction)
            
            if next_node:
                # Step 4 (Content.txt): Check for congestion
                # If Receive Buffer nearly full, assert Choke signal
                if next_node.input_buffer.size() >= next_node.input_buffer.capacity * 0.8:
                    self.main_window.update_status(
                        f"⚠ Choke signal! Buffer congestion at {next_node.position}"
                    )
                
                # Step 3 (Content.txt): Transmission and Flow Control
                # Downstream sends ACK signal if buffer space available
                if not next_node.input_buffer.is_full():
                    # Transfer Bit asserted - move packet across link (synchronized by CLK)
                    # Packet moves from Send Register to Receive Buffer of next node
                    next_node.receive_packet(self.current_packet, self.simulation_step)
                    self.simulation_step += 1
                    
                    self.main_window.update_status(
                        f"Routing: {current_pos} → {next_node.position} ({next_direction.name})"
                    )
                else:
                    # No ACK - buffer full, backpressure flow control active
                    self.main_window.update_status(
                        f"⚠ Backpressure! Buffer full at {next_node.position}"
                    )
        
        self.draw_network()
        self.update_statistics()
    
    def animate_simulation(self):
        """Animate simulation with delays"""
        if not self.is_simulating:
            return
        
        self.step_simulation()
        
        if self.is_simulating:
            delay = self.speed_var.get()
            self.canvas.after(delay, self.animate_simulation)
    
    def reset_simulation(self):
        """Reset simulation state"""
        self.is_simulating = False
        self.simulation_step = 0
        self.current_packet = None
        self.start_btn.config(state=tk.NORMAL)
        self.step_btn.config(state=tk.DISABLED)
        
        # Clear all buffers
        for node in self.nodes.values():
            node.input_buffer.clear()
            node.output_buffer.clear()
            node.reset_statistics()
        
        self.draw_network()
        self.update_statistics()
        self.main_window.update_status("Simulation reset")
    
    def update_statistics(self):
        """Update statistics display"""
        self.stats_text.config(state=tk.NORMAL)
        self.stats_text.delete(1.0, tk.END)
        
        stats = f"""Network Statistics:
━━━━━━━━━━━━━━━━━━━━━━━━━
Topology: Mesh {self.rows}×{self.cols}
Total Nodes: {len(self.nodes)}
Routing: XY Algorithm

"""
        
        if self.source_node and self.dest_node:
            hops = self.routing_algorithm.calculate_hops(
                self.source_node,
                self.dest_node
            )
            stats += f"""Routing Info:
Source: {self.source_node}
Destination: {self.dest_node}
Expected Hops: {hops}

"""
        
        if self.current_packet:
            packet_data = self.current_packet.payload.get("data", "")
            data_preview = packet_data[:30] + "..." if len(packet_data) > 30 else packet_data
            
            stats += f"""Current Packet:
ID: {self.current_packet.packet_id}
Data: "{data_preview}"
Size: {len(packet_data)} bytes
Status: {self.current_packet.status.value}
Current Hops: {self.current_packet.hops}
"""
            if self.current_packet.status == PacketStatus.DELIVERED:
                stats += f"Latency: {self.current_packet.get_latency()} cycles\n"
            
            # Show buffer flow control info
            if self.current_packet.current_node:
                curr_node = self.nodes[self.current_packet.current_node]
                stats += f"""\nBuffer Status (Content.txt):
Receive Buffer: {curr_node.input_buffer.size()}/{curr_node.input_buffer.capacity}
Send Buffer: {curr_node.output_buffer.size()}/{curr_node.output_buffer.capacity}
"""
                # Show if Choke signal would be asserted
                if curr_node.input_buffer.size() >= curr_node.input_buffer.capacity * 0.8:
                    stats += "⚠ Choke Signal: ACTIVE\n"
        
        # Node statistics
        total_generated = sum(n.packets_generated for n in self.nodes.values())
        total_received = sum(n.packets_received for n in self.nodes.values())
        
        if total_generated > 0 or total_received > 0:
            stats += f"""\nPacket Statistics:
Generated: {total_generated}
Received: {total_received}
"""
        
        self.stats_text.insert(1.0, stats)
        self.stats_text.config(state=tk.DISABLED)
