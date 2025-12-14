from .interface import Interface

class Node:
    """
    Represents a single node in the topology.
    Holds interfaces and a routing table.
    """
    def __init__(self, address):
        self.address = address
        self.interfaces = {} # Key: neighbor_address, Value: Interface
        self.routing_table = {} # Key: dest_address, Value: next_hop_address
        self.application_logic_buffer = []
        self.metrics_collector = None

    def add_connection(self, neighbor_node):
        """Creates a bidirectional connection to another node."""
        if neighbor_node.address not in self.interfaces:
            iface = Interface()
            neighbor_node.add_connection_reciprocal(self, iface)
            self.interfaces[neighbor_node.address] = iface

    def add_connection_reciprocal(self, neighbor_node, iface):
        """Helper for add_connection."""
        self.interfaces[neighbor_node.address] = Interface()
        self.interfaces[neighbor_node.address].connect(iface)

    def route(self, packet):
        """Looks up the next-hop interface for a packet."""
        next_hop_address = self.routing_table.get(packet.dest_address)
        if next_hop_address and next_hop_address in self.interfaces:
            return self.interfaces[next_hop_address]
        return None

    def attach_metrics_collector(self, collector):
        self.metrics_collector = collector

    def node_step(self, global_clock):
        """
        Handles internal packet processing:
        - Checks receive buffers
        - Routes packets to destination or next hop
        - Processes ALL available packets per cycle for high throughput
        """
        for neighbor_addr, iface in self.interfaces.items():
            # Process ALL packets in receive buffer (not just one)
            packets_to_retry = []
            
            while not iface.receive_buffer.is_empty():
                packet = iface.receive_buffer.dequeue()
                
                if packet.dest_address == self.address:
                    # Destination Reached!
                    packet.end_timer = global_clock
                    self.application_logic_buffer.append(packet)
                    if self.metrics_collector:
                        self.metrics_collector.record_delivery(packet, global_clock)
                else:
                    # Not Destination - Perform Routing
                    next_hop_iface = self.route(packet)
                    if next_hop_iface:
                        if not next_hop_iface.send_buffer.is_full():
                            next_hop_iface.send_buffer.enqueue(packet)
                        else:
                            # Congestion: save for retry
                            packets_to_retry.append(packet)
                    else:
                        # No route - keep packet for retry
                        packets_to_retry.append(packet)
            
            # Re-queue packets that couldn't be forwarded
            for pkt in packets_to_retry:
                iface.receive_buffer.enqueue(pkt)