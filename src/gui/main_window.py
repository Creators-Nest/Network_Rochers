"""
Main GUI Window for NoC Simulator
Provides interface for Mesh topology simulation with visualization
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional
from .mesh_gui import MeshTopologyGUI


class MainWindow:
    """
    Main application window for NoC Simulator
    
    Features:
    - Topology selection (Mesh, Torus, RiCoBiT)
    - Configuration controls
    - Visualization area
    - Statistics display
    """
    
    def __init__(self, root: tk.Tk):
        """
        Initialize main window
        
        Args:
            root: Tkinter root window
        """
        self.root = root
        self.root.title("Network-on-Chip Simulator")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 800)
        
        # Configure root window
        self.root.configure(bg="#f0f0f0")
        
        # Current topology GUI
        self.current_topology_gui: Optional[MeshTopologyGUI] = None
        
        # Create main layout
        self._create_header()
        self._create_main_content()
        self._create_status_bar()
        
        # Start with Mesh topology by default
        self.load_mesh_topology()
    
    def _create_header(self):
        """Create header with title and topology selector"""
        header_frame = tk.Frame(self.root, bg="#ffffff", height=60)
        header_frame.pack(side=tk.TOP, fill=tk.X)
        header_frame.pack_propagate(False)
        
        # Title
        title_label = tk.Label(
            header_frame,
            text="Network-on-Chip Simulator",
            font=("Arial", 20, "bold"),
            bg="#FFFFFF",
            fg="black"
        )
        title_label.pack(side=tk.LEFT, padx=20, pady=10)
        
        # Topology selector
        selector_frame = tk.Frame(header_frame, bg="#ffffff")
        selector_frame.pack(side=tk.RIGHT, padx=20)
        
        tk.Label(
            selector_frame,
            text="Topology:",
            font=("Arial", 12),
            bg="#ffffff",
            fg="black"
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        self.topology_var = tk.StringVar(value="Mesh")
        topology_combo = ttk.Combobox(
            selector_frame,
            textvariable=self.topology_var,
            values=["Mesh", "Torus", "RiCoBiT"],
            state="readonly",
            width=15,
            font=("Arial", 11)
        )
        topology_combo.pack(side=tk.LEFT)
        topology_combo.bind("<<ComboboxSelected>>", self._on_topology_change)
    
    def _create_main_content(self):
        """Create main content area"""
        self.content_frame = tk.Frame(self.root, bg="#f0f0f0")
        self.content_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
    
    def _create_status_bar(self):
        """Create status bar at bottom"""
        status_frame = tk.Frame(self.root, bg="#ffffff", height=30)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        status_frame.pack_propagate(False)
        
        self.status_label = tk.Label(
            status_frame,
            text="Ready",
            font=("Arial", 10),
            bg="#ffffff",
            fg="black",
            anchor=tk.W
        )
        self.status_label.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
    
    def _on_topology_change(self, event=None):
        """Handle topology selection change"""
        topology = self.topology_var.get()
        
        if topology == "Mesh":
            self.load_mesh_topology()
        elif topology == "Torus":
            self.update_status("Torus topology - Coming soon!")
            messagebox.showinfo("Coming Soon", "Torus topology will be available soon!")
        elif topology == "RiCoBiT":
            self.update_status("RiCoBiT topology - Coming soon!")
            messagebox.showinfo("Coming Soon", "RiCoBiT topology will be available soon!")
    
    def load_mesh_topology(self):
        """Load Mesh topology GUI"""
        # Clear existing content
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Create Mesh topology GUI
        self.current_topology_gui = MeshTopologyGUI(self.content_frame, self)
        self.update_status("Mesh topology loaded - Ready to simulate")
    
    def update_status(self, message: str):
        """
        Update status bar message
        
        Args:
            message: Status message to display
        """
        self.status_label.config(text=message)
        self.root.update_idletasks()
    
    def run(self):
        """Start the GUI main loop"""
        self.root.mainloop()


def main():
    """Main entry point for GUI application"""
    root = tk.Tk()
    app = MainWindow(root)
    app.run()


if __name__ == "__main__":
    main()
