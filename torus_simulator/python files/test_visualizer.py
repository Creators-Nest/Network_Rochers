#!/usr/bin/env python3
"""
Test script for the RicoBit-style torus visualizer.
"""

import tkinter as tk
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from topology.torus_topology import TorusTopology
from simulation.simulator import Simulator
from gui.visualizer_ricobit_style import TorusVisualizer

def main():
    """Main function to run the visualizer."""
    try:
        # Create topology
        print("Creating 4x4 torus topology...")
        topology = TorusTopology(4, 4)
        
        # Create simulator
        print("Initializing simulator...")
        simulator = Simulator(topology)
        
        # Create GUI
        print("Starting GUI...")
        root = tk.Tk()
        visualizer = TorusVisualizer(root, topology, simulator)
        
        print("GUI ready! You can now:")
        print("1. Select source and destination nodes by clicking")
        print("2. Click 'Simulate' to compute and highlight the path")
        print("3. Click 'Animate' to see detailed packet transfer")
        print("4. Use zoom controls and drag to navigate")
        
        visualizer.run()
        
    except Exception as e:
        print(f"Error starting visualizer: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()