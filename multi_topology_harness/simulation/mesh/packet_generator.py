import random
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.mesh.packet import Packet

class PacketGenerator:
    """
    Generates traffic patterns as described in the paper.
    """
    def __init__(self, topology):
        self.topology = topology
        self.node_addresses = topology.get_all_node_addresses()
        self.distances = topology.all_pairs_distances
        self.packet_id_counter = 0

    def _get_packet_id(self):
        self.packet_id_counter += 1
        return f"Packet-{self.packet_id_counter}"
        
    def generate_longest_neighbor_traffic(self, num_packets, clock):
        """Generates 'longest neighbour first' traffic."""
        packets = []
        
        for _ in range(num_packets):
            # Find pair with maximum distance
            max_distance = 0
            best_pair = None
            
            for src in self.node_addresses:
                for dst in self.node_addresses:
                    if src != dst:
                        distance = self.distances[src][dst]
                        if distance > max_distance:
                            max_distance = distance
                            best_pair = (src, dst)
            
            if best_pair:
                src, dst = best_pair
                packet_id = self._get_packet_id()
                packet = Packet(src, dst, packet_id, clock)
                packets.append(packet)
                print(f"Generated: {packet_id} from {src} to {dst} (distance: {max_distance})")
        
        return packets
    
    def generate_uniform_random_traffic(self, num_packets, clock):
        """Generates uniform random traffic between nodes."""
        packets = []
        
        for _ in range(num_packets):
            src = random.choice(self.node_addresses)
            dst = random.choice([addr for addr in self.node_addresses if addr != src])
            
            packet_id = self._get_packet_id()
            packet = Packet(src, dst, packet_id, clock)
            packets.append(packet)
        
        return packets