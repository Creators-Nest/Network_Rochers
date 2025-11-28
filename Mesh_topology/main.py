from topology.mesh_topology import MeshTopology
from simulation.simulator import Simulator
from gui.visualizer import MeshVisualizer
import tkinter as tk

if __name__ == "__main__":
    print("Initializing Mesh Topology (White Theme)...")
    topology = MeshTopology(width=6, height=6)
    
    print("Initializing simulator...")
    simulator = Simulator(topology)
    
    print("Launching White Theme GUI with Real Packet Transfer...")
    root = tk.Tk()
    app = MeshVisualizer(root, topology, simulator)
    app.run()
