"""
Startup script for Enhanced Mesh Topology Flask Application
"""

import os
import sys

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Initialize topology and simulator
from topology.enhanced_mesh_topology import EnhancedMeshTopology
from simulation.simulator import Simulator

# Create instances
topology = EnhancedMeshTopology(width=6, height=6)
simulator = Simulator(topology)

# Import Flask app
from webapp.app import create_app

# Create app instance
app = create_app(width=6, height=6)

if __name__ == '__main__':
    print("="*70)
    print(" Enhanced Mesh Topology NoC Simulator - Web Application")
    print("="*70)
    print(f" Topology: {topology.width}x{topology.height} mesh")
    print(f" Total Nodes: {len(topology.nodes)}")
    print(f" Buffer Capacity: {topology.buffer_capacity} packets per interface")
    print("="*70)
    print(" Server: http://localhost:5000")
    print(" Press Ctrl+C to stop")
    print("="*70)
    print()
    
    app.run(debug=True, host='0.0.0.0', port=5002)
