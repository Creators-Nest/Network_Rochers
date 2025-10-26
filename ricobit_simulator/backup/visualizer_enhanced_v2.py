"""
Enhanced RicoBit Topology Visualizer with Packet Flow Analysis
- Only adjacent ring connections (no internal crossing)
- Detailed packet flow analysis panel
- Step-by-step handshake protocol visualization
"""

import tkinter as tk
from tkinter import messagebox, scrolledtext
import math

class RicoBitVisualizer:
    def __init__(self, root, topology, simulator):
        self.root = root
        self.topology = topology
        self.simulator = simulator
        self.num_levels = topology.num_levels
        
        # Color scheme
        self.colors = {
            'bg_dark': '#2b2b2b',
            'bg_medium': '#3c3f41',
            'bg_light': '#4b4b4b',
            'panel_bg': '#313335',
            'text': '#d4d4d4',
            'accent': '#00ffff',
            'button': '#5a5a5a',
            'highlight': '#00ff00',
            'path': '#00ffff'
        }
        
        # Setup main window
        self.root.title("RicoBit Topology Visualizer - Enhanced")
        self.root.configure(bg=self.colors['bg_dark'])
        
        # Window geometry
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = min(1600, int(screen_width * 0.9))
        window_height = min(1000, int(screen_height * 0.9))
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Main container with light status bar
        self._create_status_bar()
        
        # Create UI
        self._create_ui()
        
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
        
        # Initial draw
        self.draw_topology()
        
        # Bind events
        self._bind_events()
    
    def _create_status_bar(self):
        """Create light status bar at top"""
        status_frame = tk.Frame(self.root, bg='#e0e0e0', height=30)
        status_frame.pack(side=tk.TOP, fill=tk.X)
        status_frame.pack_propagate(False)
        
        self.status_label = tk.Label(status_frame, text="Ready", 
                                     bg='#e0e0e0', fg='#000000',
                                     font=("Arial", 10), anchor=tk.W)
        self.status_label.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
    
    def _create_ui(self):
        """Create main UI layout"""
        # Main container
        main_container = tk.Frame(self.root, bg=self.colors['bg_dark'])
        main_container.pack(fill=tk.BOTH, expand=True, side=tk.TOP)
        
        # Left panel - Controls
        self.control_panel = tk.Frame(main_container, bg=self.colors['panel_bg'], width=400)
        self.control_panel.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        self.control_panel.pack_propagate(False)
        
        # Create scrollable control area
        canvas = tk.Canvas(self.control_panel, bg=self.colors['panel_bg'], highlightthickness=0)
        scrollbar = tk.Scrollbar(self.control_panel, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.colors['panel_bg'])
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add control sections
        self._create_topology_controls(scrollable_frame)
        self._create_routing_controls(scrollable_frame)
        self._create_flow_analysis_panel(scrollable_frame)
        self._create_view_controls(scrollable_frame)
        
        # Right panel - Canvas
        canvas_frame = tk.Frame(main_container, bg=self.colors['bg_dark'])
        canvas_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.canvas = tk.Canvas(canvas_frame, bg=self.colors['bg_dark'], 
                               highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
    
    def _create_section_header(self, parent, text):
        """Create section header"""
        header = tk.Label(parent, text=text, font=("Arial", 12, "bold"),
                         bg=self.colors['panel_bg'], fg=self.colors['accent'])
        header.pack(anchor=tk.W, padx=10, pady=(15, 5))
    
    def _create_topology_controls(self, parent):
        """Create topology configuration controls"""
        self._create_section_header(parent, "TOPOLOGY CONFIGURATION")
        
        frame = tk.Frame(parent, bg=self.colors['panel_bg'])
        frame.pack(fill=tk.X, padx=15, pady=5)
        
        # Rings slider
        tk.Label(frame, text="Number of Rings:", 
                font=("Arial", 10), bg=self.colors['panel_bg'], fg=self.colors['text']
               ).pack(anchor=tk.W, pady=(0, 2))
        
        self.rings_var = tk.IntVar(value=self.num_levels)
        self.rings_slider = tk.Scale(frame, from_=2, to=5, orient=tk.HORIZONTAL,
                                     variable=self.rings_var,
                                     bg=self.colors['bg_medium'], fg=self.colors['text'],
                                     highlightthickness=0, troughcolor=self.colors['bg_light'])
        self.rings_slider.pack(fill=tk.X, pady=5)
        
        tk.Button(frame, text="Create Topology", command=self.recreate_topology,
                 bg=self.colors['button'], fg=self.colors['text'], font=("Arial", 10, "bold"),
                 cursor="hand2").pack(fill=tk.X, pady=5)
    
    def _create_routing_controls(self, parent):
        """Create packet routing controls"""
        self._create_section_header(parent, "PACKET ROUTING")
        
        frame = tk.Frame(parent, bg=self.colors['panel_bg'])
        frame.pack(fill=tk.X, padx=15, pady=5)
        
        # Source
        src_frame = tk.Frame(frame, bg=self.colors['panel_bg'])
        src_frame.pack(fill=tk.X, pady=5)
        tk.Label(src_frame, text="Source Node:", 
                font=("Arial", 10), bg=self.colors['panel_bg'], fg=self.colors['text']
               ).pack(side=tk.LEFT)
        
        self.src_ring_var = tk.IntVar(value=0)
        tk.Spinbox(src_frame, from_=0, to=4, width=3, textvariable=self.src_ring_var,
                  bg=self.colors['bg_light'], fg=self.colors['text']).pack(side=tk.RIGHT, padx=2)
        tk.Label(src_frame, text="Ring:", 
                font=("Arial", 9), bg=self.colors['panel_bg'], fg=self.colors['text']
               ).pack(side=tk.RIGHT, padx=2)
        
        self.src_node_var = tk.IntVar(value=0)
        tk.Spinbox(src_frame, from_=0, to=15, width=3, textvariable=self.src_node_var,
                  bg=self.colors['bg_light'], fg=self.colors['text']).pack(side=tk.RIGHT, padx=2)
        tk.Label(src_frame, text="Node:", 
                font=("Arial", 9), bg=self.colors['panel_bg'], fg=self.colors['text']
               ).pack(side=tk.RIGHT, padx=2)
        
        # Destination
        dst_frame = tk.Frame(frame, bg=self.colors['panel_bg'])
        dst_frame.pack(fill=tk.X, pady=5)
        tk.Label(dst_frame, text="Dest Node:", 
                font=("Arial", 10), bg=self.colors['panel_bg'], fg=self.colors['text']
               ).pack(side=tk.LEFT)
        
        self.dst_ring_var = tk.IntVar(value=3)
        tk.Spinbox(dst_frame, from_=0, to=4, width=3, textvariable=self.dst_ring_var,
                  bg=self.colors['bg_light'], fg=self.colors['text']).pack(side=tk.RIGHT, padx=2)
        tk.Label(dst_frame, text="Ring:", 
                font=("Arial", 9), bg=self.colors['panel_bg'], fg=self.colors['text']
               ).pack(side=tk.RIGHT, padx=2)
        
        self.dst_node_var = tk.IntVar(value=7)
        tk.Spinbox(dst_frame, from_=0, to=15, width=3, textvariable=self.dst_node_var,
                  bg=self.colors['bg_light'], fg=self.colors['text']).pack(side=tk.RIGHT, padx=2)
        tk.Label(dst_frame, text="Node:", 
                font=("Arial", 9), bg=self.colors['panel_bg'], fg=self.colors['text']
               ).pack(side=tk.RIGHT, padx=2)
        
        # Buttons
        btn_frame = tk.Frame(frame, bg=self.colors['panel_bg'])
        btn_frame.pack(fill=tk.X, pady=5)
        
        tk.Button(btn_frame, text="Simulate", command=self.simulate_routing,
                 bg=self.colors['button'], fg=self.colors['text'], font=("Arial", 10)
                 ).pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        
        tk.Button(btn_frame, text="Animate", command=self.animate_routing,
                 bg=self.colors['button'], fg=self.colors['text'], font=("Arial", 10)
                 ).pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        
        tk.Button(btn_frame, text="Clear", command=self.clear_path,
                 bg=self.colors['button'], fg=self.colors['text'], font=("Arial", 10)
                 ).pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
    
    def _create_flow_analysis_panel(self, parent):
        """Create packet flow analysis panel"""
        self._create_section_header(parent, "PACKET FLOW ANALYSIS")
        
        frame = tk.Frame(parent, bg=self.colors['panel_bg'])
        frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
        
        # Scrolled text widget
        self.flow_text = scrolledtext.ScrolledText(frame, height=20, width=45, wrap=tk.WORD,
                                                   font=('Courier', 9), bg='#1e1e1e', fg='#00ff00')
        self.flow_text.pack(fill=tk.BOTH, expand=True)
        
        self._update_flow_analysis("Ready. Select source and destination, then click Animate.")
    
    def _update_flow_analysis(self, message, clear=False):
        """Update flow analysis text"""
        if clear:
            self.flow_text.delete(1.0, tk.END)
        self.flow_text.insert(tk.END, message + "\n")
        self.flow_text.see(tk.END)
    
    def _create_view_controls(self, parent):
        """Create view controls"""
        self._create_section_header(parent, "VIEW CONTROLS")
        
        frame = tk.Frame(parent, bg=self.colors['panel_bg'])
        frame.pack(fill=tk.X, padx=15, pady=5)
        
        tk.Button(frame, text="Reset View", command=self.reset_view,
                 bg=self.colors['button'], fg=self.colors['text'], font=("Arial", 10)
                 ).pack(fill=tk.X, pady=2)
        
        tk.Button(frame, text="Clear Highlights", command=self.clear_highlights,
                 bg=self.colors['button'], fg=self.colors['text'], font=("Arial", 10)
                 ).pack(fill=tk.X, pady=2)
        
        zoom_frame = tk.Frame(frame, bg=self.colors['panel_bg'])
        zoom_frame.pack(fill=tk.X, pady=5)
        tk.Button(zoom_frame, text="Zoom In (+)", command=self.zoom_in,
                 bg=self.colors['button'], fg=self.colors['text']
                 ).pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        tk.Button(zoom_frame, text="Zoom Out (-)", command=self.zoom_out,
                 bg=self.colors['button'], fg=self.colors['text']
                 ).pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
    
    def _bind_events(self):
        """Bind keyboard and mouse events"""
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)
        self.root.bind("<Control-plus>", lambda e: self.zoom_in())
        self.root.bind("<Control-minus>", lambda e: self.zoom_out())
        self.root.bind("<Control-0>", lambda e: self.reset_view())
        self.root.bind("<Escape>", lambda e: self.clear_highlights())
    
    def draw_topology(self):
        """Draw the complete topology"""
        self.canvas.delete("all")
        self.node_positions.clear()
        self.node_items.clear()
        self.edge_items.clear()
        
        self._calculate_positions()
        self._draw_connections()
        self._draw_nodes()
    
    def _calculate_positions(self):
        """Calculate node positions in circular rings"""
        canvas_width = self.canvas.winfo_width() or 800
        canvas_height = self.canvas.winfo_height() or 600
        center_x = canvas_width / 2
        center_y = canvas_height / 2
        base_radius = min(canvas_width, canvas_height) * 0.35
        
        for R in range(self.num_levels):
            num_nodes_in_ring = 2 ** R
            radius = base_radius * (R + 1) / self.num_levels
            
            for Nr in range(num_nodes_in_ring):
                angle = 2 * math.pi * Nr / num_nodes_in_ring - math.pi / 2
                x = center_x + radius * math.cos(angle)
                y = center_y + radius * math.sin(angle)
                self.node_positions[(R, Nr)] = (x, y)
    
    def _draw_connections(self):
        """Draw ONLY adjacent ring connections and tree connections"""
        drawn = set()
        for addr, node in self.topology.nodes.items():
            R, Nr = addr
            num_nodes_in_ring = 2 ** R
            
            for neighbor_addr in node.interfaces.keys():
                edge = tuple(sorted([addr, neighbor_addr]))
                if edge not in drawn:
                    neighbor_R, neighbor_Nr = neighbor_addr
                    
                    # Only draw if:
                    # 1. Same ring and adjacent nodes (left/right neighbors only)
                    # 2. Tree connections (parent-child between rings)
                    is_adjacent_ring = (R == neighbor_R and 
                                       (abs(Nr - neighbor_Nr) == 1 or 
                                        (Nr == 0 and neighbor_Nr == num_nodes_in_ring - 1) or
                                        (Nr == num_nodes_in_ring - 1 and neighbor_Nr == 0)))
                    is_tree = (R != neighbor_R)
                    
                    if is_adjacent_ring or is_tree:
                        x1, y1 = self.node_positions[addr]
                        x2, y2 = self.node_positions[neighbor_addr]
                        
                        cx1, cy1 = self._transform_coords(x1, y1)
                        cx2, cy2 = self._transform_coords(x2, y2)
                        
                        color = '#555555'
                        if edge in self.highlighted_edges:
                            color = self.colors['path']
                        
                        line_id = self.canvas.create_line(cx1, cy1, cx2, cy2, fill=color, width=2)
                        self.edge_items[edge] = line_id
                        drawn.add(edge)
    
    def _draw_nodes(self):
        """Draw nodes"""
        for addr, (x, y) in self.node_positions.items():
            cx, cy = self._transform_coords(x, y)
            
            color = '#4a90e2'
            if addr in self.highlighted_nodes:
                color = self.colors['highlight']
            
            r = 12 * self.zoom_level
            node_id = self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r, 
                                             fill=color, outline='#ffffff', width=2)
            
            R, Nr = addr
            label = f"({R},{Nr})"
            text_id = self.canvas.create_text(cx, cy - r - 15, text=label, 
                                             fill=self.colors['text'], font=("Arial", 9))
            
            self.node_items[addr] = node_id
    
    def _transform_coords(self, x, y):
        """Transform coordinates with zoom and pan"""
        return (x * self.zoom_level + self.pan_x, 
                y * self.zoom_level + self.pan_y)
    
    def on_canvas_click(self, event):
        """Handle canvas click to show node details"""
        for addr, item_id in self.node_items.items():
            coords = self.canvas.coords(item_id)
            if coords:
                x1, y1, x2, y2 = coords
                cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
                dist = math.sqrt((event.x - cx)**2 + (event.y - cy)**2)
                
                if dist < 15:
                    self._show_node_details(addr)
                    break
    
    def _show_node_details(self, addr):
        """Show node details in popup"""
        node = self.topology.nodes[addr]
        R, Nr = addr
        
        details = f"Node Details\n"
        details += f"{'=' * 30}\n"
        details += f"Address: ({R}, {Nr})\n"
        details += f"Ring: {R}\n"
        details += f"Node in Ring: {Nr}\n"
        details += f"\nConnections ({len(node.interfaces)}):\n"
        for neighbor_addr in node.interfaces.keys():
            details += f"  → ({neighbor_addr[0]}, {neighbor_addr[1]})\n"
        
        messagebox.showinfo("Node Information", details)
    
    def simulate_routing(self):
        """Simulate routing and highlight path"""
        path = self._compute_path()
        if not path:
            return
        
        self.clear_highlights()
        
        # Highlight path
        for i in range(len(path) - 1):
            addr = path[i]
            next_addr = path[i + 1]
            
            self.highlighted_nodes.add(addr)
            edge = tuple(sorted([addr, next_addr]))
            self.highlighted_edges.add(edge)
        
        self.highlighted_nodes.add(path[-1])
        self.draw_topology()
        
        self.status_label.config(text=f"Path: {len(path)} nodes")
    
    def animate_routing(self):
        """Animate routing with detailed packet flow analysis"""
        if self.animation_running:
            return
        
        path = self._compute_path()
        if not path:
            return
        
        self.animation_running = True
        self.clear_highlights()
        
        # Initialize flow analysis
        self._update_flow_analysis("=== PACKET TRANSFER INITIATED ===", clear=True)
        source_addr = path[0]
        dest_addr = path[-1]
        self._update_flow_analysis(f"\n📦 Packet Created at Node {source_addr}")
        self._update_flow_analysis(f"   Source: {source_addr}")
        self._update_flow_analysis(f"   Destination: {dest_addr}")
        self._update_flow_analysis(f"   Path Length: {len(path)-1} hops")
        self._update_flow_analysis(f"   start_timer = Clock()")
        
        def animate_step(index):
            if index >= len(path):
                self.animation_running = False
                self._update_flow_analysis("\n✅ PACKET DELIVERED SUCCESSFULLY")
                self._update_flow_analysis(f"   end_timer = Clock()")
                self._update_flow_analysis(f"   Latency = end_timer - start_timer")
                return
            
            addr = path[index]
            
            # Detailed flow analysis for each hop
            if index == 0:
                self._update_flow_analysis(f"\n--- HOP {index + 1}: Source Node {addr} ---")
                self._update_flow_analysis("1. Routing Logic: Determine next hop")
                self._update_flow_analysis("2. Packet → Send Buffer of interface")
            elif index < len(path) - 1:
                self._update_flow_analysis(f"\n--- HOP {index + 1}: Intermediate Node {addr} ---")
                self._update_flow_analysis("1. HANDSHAKE PROTOCOL:")
                self._update_flow_analysis("   • Sender: pin_REQ = 1 (Request)")
                self._update_flow_analysis("   • Receiver: Check Receive Buffer")
                self._update_flow_analysis("   • Receiver: pin_ACK = 1 (Acknowledge)")
                self._update_flow_analysis("   • bit_Busy = 1 (Both nodes)")
                self._update_flow_analysis("2. DATA TRANSFER:")
                self._update_flow_analysis("   • Packet → Send Register")
                self._update_flow_analysis("   • Serial transmission via pin_DATA")
                self._update_flow_analysis("   • Packet → Receive Register")
                self._update_flow_analysis("   • Packet → Receive Buffer")
                self._update_flow_analysis("   • bit_Busy = 0 (Reset)")
                self._update_flow_analysis("3. ROUTING CHECK:")
                self._update_flow_analysis(f"   • dest_address {dest_addr} ≠ current {addr}")
                self._update_flow_analysis("   • Forwarding needed")
                self._update_flow_analysis("4. RE-QUEUING:")
                next_addr = path[index + 1]
                self._update_flow_analysis(f"   • Routing Logic: Next hop = {next_addr}")
                self._update_flow_analysis("   • Packet moved to next Send Buffer")
            else:
                self._update_flow_analysis(f"\n--- HOP {index + 1}: Destination Node {addr} ---")
                self._update_flow_analysis("1. HANDSHAKE & TRANSFER:")
                self._update_flow_analysis("   • pin_REQ, pin_ACK sequence")
                self._update_flow_analysis("   • Serial data transfer")
                self._update_flow_analysis("   • Packet → Receive Buffer")
                self._update_flow_analysis("2. DESTINATION CHECK:")
                self._update_flow_analysis(f"   • dest_address {dest_addr} = current {addr}")
                self._update_flow_analysis("   • ✓ Destination Reached!")
                self._update_flow_analysis("3. DELIVERY:")
                self._update_flow_analysis("   • Packet → Application Logic")
                self._update_flow_analysis("   • Remove from system")
            
            # Visual highlight
            if addr in self.node_items:
                self.canvas.itemconfig(self.node_items[addr], fill=self.colors['highlight'])
            
            if index < len(path) - 1:
                next_addr = path[index + 1]
                edge = tuple(sorted([addr, next_addr]))
                if edge in self.edge_items:
                    self.canvas.itemconfig(self.edge_items[edge], fill=self.colors['path'], width=3)
                    self.highlighted_edges.add(edge)
            
            self.canvas.update()
            self.root.after(800, lambda: animate_step(index + 1))
        
        animate_step(0)
    
    def _compute_path(self):
        """Compute shortest path using BFS"""
        try:
            src_addr = (self.src_ring_var.get(), self.src_node_var.get())
            dst_addr = (self.dst_ring_var.get(), self.dst_node_var.get())
            
            if src_addr not in self.topology.nodes or dst_addr not in self.topology.nodes:
                messagebox.showerror("Error", "Invalid source or destination node")
                return None
            
            if src_addr == dst_addr:
                messagebox.showwarning("Warning", "Source and destination are the same")
                return None
            
            # BFS to find shortest path
            from collections import deque
            queue = deque([(src_addr, [src_addr])])
            visited = {src_addr}
            
            while queue:
                current, path = queue.popleft()
                
                if current == dst_addr:
                    return path
                
                for neighbor in self.topology.nodes[current].interfaces.keys():
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append((neighbor, path + [neighbor]))
            
            messagebox.showerror("Error", "No path found")
            return None
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return None
    
    def clear_path(self):
        """Clear routing highlights"""
        self.clear_highlights()
        self._update_flow_analysis("Path cleared.", clear=True)
    
    def clear_highlights(self):
        """Clear all highlights"""
        self.highlighted_edges.clear()
        self.highlighted_nodes.clear()
        self.draw_topology()
    
    def reset_view(self):
        """Reset view to default"""
        self.zoom_level = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self.draw_topology()
    
    def zoom_in(self):
        """Zoom in"""
        self.zoom_level = min(3.0, self.zoom_level * 1.2)
        self.draw_topology()
    
    def zoom_out(self):
        """Zoom out"""
        self.zoom_level = max(0.3, self.zoom_level / 1.2)
        self.draw_topology()
    
    def on_mousewheel(self, event):
        """Handle mouse wheel zoom"""
        if event.delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()
    
    def recreate_topology(self):
        """Recreate topology with new ring count"""
        from topology.ricobit_topology import RiCoBiT_Topology
        new_rings = self.rings_var.get()
        
        print(f"\nRecreating topology with {new_rings} rings...")
        self.topology = RiCoBiT_Topology(num_levels=new_rings)
        self.num_levels = new_rings
        
        self.clear_highlights()
        self.draw_topology()
        
        self.status_label.config(text=f"Topology recreated: {len(self.topology.nodes)} nodes")
    
    def run(self):
        """Start the GUI"""
        self.root.mainloop()
