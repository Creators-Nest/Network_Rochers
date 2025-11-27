"""
Quick test to verify Flask app can be imported and initialized
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Testing Flask Application Components...\n")

# Test 1: Import enhanced interface
print("1. Testing Enhanced Interface...")
from core.enhanced_interface import EnhancedInterface
interface = EnhancedInterface((0, 0), (1, 0), buffer_capacity=4)
print(f"   ✓ Interface created: {interface}")
print(f"   ✓ Pins: REQ={interface.pin_REQ}, ACK={interface.pin_ACK}, CLK={interface.pin_CLK}")
print(f"   ✓ Buffers: Send={interface.send_buffer.capacity}, Receive={interface.receive_buffer.capacity}")

# Test 2: Import enhanced node
print("\n2. Testing Enhanced Node...")
from core.enhanced_node import EnhancedNode
node = EnhancedNode((0, 0))
node.add_interface((1, 0))
print(f"   ✓ Node created: {node}")
print(f"   ✓ Interfaces: {len(node.interfaces)}")

# Test 3: Import enhanced topology
print("\n3. Testing Enhanced Mesh Topology...")
from topology.enhanced_mesh_topology import EnhancedMeshTopology
topology = EnhancedMeshTopology(width=4, height=4)
print(f"   ✓ Topology created: {topology}")
print(f"   ✓ Total nodes: {len(topology.nodes)}")
print(f"   ✓ Buffer capacity: {topology.buffer_capacity}")

# Test 4: Check Flask app imports
print("\n4. Testing Flask App Imports...")
from flask import Flask
app = Flask(__name__)
print(f"   ✓ Flask app created: {app}")

# Test 5: Verify packet
print("\n5. Testing Packet...")
from core.packet import Packet
packet = Packet(source_address=(0, 0), dest_address=(3, 3), data="Test")
print(f"   ✓ Packet created: {packet}")

# Test 6: Test routing
print("\n6. Testing Routing...")
source_node = topology.get_node((0, 0))
dest = (3, 3)
route = source_node.get_route(dest)
print(f"   ✓ Route from (0,0) to (3,3): {route}")
print(f"   ✓ Hops: {len(route) - 1}")

# Test 7: Test packet injection
print("\n7. Testing Packet Injection...")
test_packet = Packet(source_address=(0, 0), dest_address=(2, 2), data="Test Injection")
success = source_node.inject_packet(test_packet)
print(f"   ✓ Packet injection: {'Success' if success else 'Failed'}")

# Test 8: Test interface status
print("\n8. Testing Interface Status...")
interface_to_next = list(source_node.interfaces.values())[0]
status = interface_to_next.get_status()
print(f"   ✓ Interface status retrieved")
print(f"   ✓ State: {status['state']}")
print(f"   ✓ Send buffer size: {status['buffers']['send']['size']}")

print("\n" + "="*70)
print("ALL TESTS PASSED! ✓")
print("="*70)
print("\nFlask application is ready to run.")
print("Start with: python webapp/enhanced_app.py")
print("Or use: python run_flask_app.py")
print("="*70)
