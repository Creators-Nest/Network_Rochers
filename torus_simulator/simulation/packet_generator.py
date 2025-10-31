import random
from core.packet import Packet

class PacketGenerator:
    """
    Generates packets for torus topology simulation.
    """
    def __init__(self, topology):
        self.topology = topology
        self.packet_id = 0
    
    def generate_random_packet(self, sim_clock=0):
        """Generate a packet with random source and destination."""
        addresses = list(self.topology.nodes.keys())
        source = random.choice(addresses)
        dest = random.choice([addr for addr in addresses if addr != source])
        
        self.packet_id += 1
        return Packet(
            source_address=source,
            dest_address=dest,
            data=f"packet_{self.packet_id}",
            sim_clock=sim_clock
        )
    
    def generate_packet(self, source, dest, sim_clock=0):
        """Generate a packet with specific source and destination."""
        self.packet_id += 1
        return Packet(
            source_address=source,
            dest_address=dest,
            data=f"packet_{self.packet_id}",
            sim_clock=sim_clock
        )