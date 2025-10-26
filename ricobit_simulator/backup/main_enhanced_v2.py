from topology.ricobit_topology import RiCoBiT_Topology
from simulation.simulator import Simulator
from gui.visualizer_enhanced_v2 import RicoBitVisualizer
import tkinter as tk

if __name__ == "__main__":
    print("Initializing enhanced topology...")
    topology = RiCoBiT_Topology(num_levels=4)
    
    print("Initializing simulator...")
    simulator = Simulator(topology)
    
    print("Launching Enhanced GUI with Packet Flow Analysis...")
    root = tk.Tk()
    app = RicoBitVisualizer(root, topology, simulator)
    app.run()
