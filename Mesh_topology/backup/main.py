from topology.ricobit_topology import RiCoBiT_Topology
from simulation.simulator import Simulator
from simulation.packet_generator import PacketGenerator
from gui.visualizer_enhanced import RicoBitVisualizer

if __name__ == "__main__":
    
    # 1. Initialize Topology (e.g., 4 levels for enhanced visualization)
    print("Initializing enhanced topology...")
    ricobit_net = RiCoBiT_Topology(num_levels=4)
    
    # 2. Initialize Simulator
    print("Initializing simulator...")
    simulator = Simulator(ricobit_net)
    
    # 3. Initialize Packet Generator
    print("Initializing packet generator...")
    generator = PacketGenerator(ricobit_net)
    
    # 4. Launch Enhanced GUI
    print("Launching Enhanced GUI...")
    visualizer = RicoBitVisualizer(ricobit_net, simulator, generator)
    visualizer.run()
