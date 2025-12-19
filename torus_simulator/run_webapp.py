"""
Run script for Torus Topology Web Application
Launches Flask server for web-based NoC simulation
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from webapp.enhanced_app import app, topology, simulator
from topology.enhanced_torus_topology import EnhancedTorusTopology
from simulation.simulator import Simulator

if __name__ == '__main__':
    print("="*70)
    print("Enhanced Torus Topology NoC Simulator - Web Application")
    print("="*70)
    print("Initializing default 4x4 torus topology with wraparound connections...")
    
    # Initialize default topology
    from webapp import enhanced_app
    enhanced_app.topology = EnhancedTorusTopology(width=4, height=4)
    enhanced_app.simulator = Simulator(enhanced_app.topology)
    
    print(f"Topology: {enhanced_app.topology.width}x{enhanced_app.topology.height} torus")
    print(f"Total Nodes: {len(enhanced_app.topology.nodes)}")
    print(f"Wraparound connections enabled (torus topology)")
    print()
    print("Starting Flask server...")
    print("Server URL: http://localhost:5000")
    print("="*70)
    print()
    
    # Run Flask app
    app.run(debug=True, host='0.0.0.0', port=5002)
