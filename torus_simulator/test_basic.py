#!/usr/bin/env python3
"""
Simple test to verify the visualizer works correctly.
"""

import tkinter as tk
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all imports work correctly."""
    try:
        from topology.torus_topology import TorusTopology
        from simulation.simulator import Simulator
        from gui.visualizer_ricobit_style import TorusVisualizer
        print("✓ All imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

def test_basic_functionality():
    """Test basic functionality without GUI."""
    try:
        from topology.torus_topology import TorusTopology
        from simulation.simulator import Simulator
        
        # Create topology
        topology = TorusTopology(4, 4)
        print("✓ Topology created successfully")
        
        # Create simulator
        simulator = Simulator(topology)
        print("✓ Simulator created successfully")
        
        # Test path computation
        path = topology.router.get_full_path((0, 0), (2, 2))
        if path:
            print(f"✓ Path computation successful: {path}")
        else:
            print("✗ Path computation failed")
            return False
            
        return True
    except Exception as e:
        print(f"✗ Basic functionality test failed: {e}")
        return False

def main():
    """Run tests."""
    print("Running visualizer tests...")
    
    if not test_imports():
        return False
        
    if not test_basic_functionality():
        return False
        
    print("\n✓ All tests passed! The visualizer should work correctly.")
    print("\nTo run the full GUI, use: python test_visualizer.py")
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)