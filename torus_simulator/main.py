from topology.torus_topology import TorusTopology
from simulation.simulator import Simulator
from gui.visualizer_ricobit_style import TorusVisualizer
import tkinter as tk

if __name__ == "__main__":
    print("Initializing Torus Topology...")
    topology = TorusTopology(width=4, height=4)
    
    print("Initializing simulator...")
    simulator = Simulator(topology)
    
    print("Launching Torus Topology Visualizer...")
    root = tk.Tk()
    app = TorusVisualizer(root, topology, simulator)
    app.run()