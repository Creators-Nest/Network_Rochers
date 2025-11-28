from topology.ricobit_topology import RiCoBiT_Topology
from simulation.simulator import Simulator
from gui.visualizer import RicoBitVisualizer
import tkinter as tk

if __name__ == "__main__":
    print("Initializing RicoBit Topology (White Theme)...")
    topology = RiCoBiT_Topology(num_levels=5)
    
    print("Initializing simulator...")
    simulator = Simulator(topology)
    
    print("Launching White Theme GUI with Real Packet Transfer...")
    root = tk.Tk()
    app = RicoBitVisualizer(root, topology, simulator)
    app.run()
