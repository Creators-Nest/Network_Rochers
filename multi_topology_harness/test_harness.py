#!/usr/bin/env python3
"""
Quick test to verify the unified harness works correctly
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_mesh():
    """Test mesh topology"""
    print("\n=== Testing Mesh Topology ===")
    try:
        from topology.mesh.enhanced_mesh_topology import EnhancedMeshTopology
        from simulation.mesh.simulator import Simulator
        from core.mesh.packet import Packet
        
        topology = EnhancedMeshTopology(width=3, height=3, buffer_capacity=4)
        print(f"  Created {len(topology.nodes)} nodes")
        
        simulator = Simulator(topology)
        
        # Create test packet
        packet = Packet(
            source_address=(0, 0),
            dest_address=(2, 2),
            data="test_mesh",
            sim_clock=0
        )
        
        simulator.inject_packet(packet)
        
        # Run a few cycles
        for _ in range(20):
            simulator.run_simulation_step()
        
        delivered = simulator.get_delivered_count()
        print(f"  Delivered: {delivered} packet(s)")
        print("  ✓ Mesh test passed")
        return True
    except Exception as e:
        print(f"  ✗ Mesh test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ricobit():
    """Test RiCoBiT topology"""
    print("\n=== Testing RiCoBiT Topology ===")
    try:
        from topology.ricobit.ricobit_topology import RiCoBiT_Topology
        from simulation.ricobit.simulator import Simulator
        from core.ricobit.packet import Packet
        
        topology = RiCoBiT_Topology(num_levels=4)
        print(f"  Created {len(topology.nodes)} nodes")
        
        simulator = Simulator(topology)
        
        # Get two valid addresses
        addresses = list(topology.nodes.keys())
        if len(addresses) >= 2:
            src = addresses[0]
            dst = addresses[-1]
            
            packet = Packet(
                source_address=src,
                dest_address=dst,
                data="test_ricobit",
                sim_clock=0,
                packet_id="test_pkt_1"
            )
            
            simulator.inject_packet(packet)
            
            # Run a few cycles
            for _ in range(30):
                simulator.run_simulation_step()
            
            delivered = simulator.metrics.delivered_count
            print(f"  Delivered: {delivered} packet(s)")
        
        print("  ✓ RiCoBiT test passed")
        return True
    except Exception as e:
        print(f"  ✗ RiCoBiT test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_torus():
    """Test Torus topology"""
    print("\n=== Testing Torus Topology ===")
    try:
        from topology.torus.enhanced_torus_topology import EnhancedTorusTopology
        from simulation.torus.simulator import Simulator
        from core.torus.packet import Packet
        
        topology = EnhancedTorusTopology(width=3, height=3, buffer_capacity=4)
        print(f"  Created {len(topology.nodes)} nodes")
        
        simulator = Simulator(topology)
        
        # Create test packet
        packet = Packet(
            source_address=(0, 0),
            dest_address=(2, 2),
            data="test_torus",
            sim_clock=0
        )
        
        simulator.inject_packet(packet)
        
        # Run a few cycles
        for _ in range(20):
            simulator.run_simulation_step()
        
        delivered = simulator.get_delivered_count()
        print(f"  Delivered: {delivered} packet(s)")
        print("  ✓ Torus test passed")
        return True
    except Exception as e:
        print(f"  ✗ Torus test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_unified_config():
    """Test unified configuration"""
    print("\n=== Testing Unified Configuration ===")
    try:
        from unified_harness.config import UnifiedConfig, TopologyConfig, SimulationConfig
        
        config = UnifiedConfig(
            mesh=TopologyConfig(width=3, height=3),
            ricobit=TopologyConfig(num_levels=4),
            torus=TopologyConfig(width=3, height=3),
            simulation=SimulationConfig(num_packets=10)
        )
        
        print(f"  Enabled topologies: {[t.value for t in config.get_enabled_topologies()]}")
        print(f"  Configuration summary: {config.summary()}")
        print("  ✓ Config test passed")
        return True
    except Exception as e:
        print(f"  ✗ Config test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("MULTI-TOPOLOGY HARNESS QUICK TEST")
    print("=" * 60)
    
    results = []
    
    # Test each component
    results.append(("Mesh", test_mesh()))
    results.append(("RiCoBiT", test_ricobit()))
    results.append(("Torus", test_torus()))
    results.append(("Config", test_unified_config()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
