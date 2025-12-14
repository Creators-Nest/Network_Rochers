"""
Torus Topology Simulator
Manages the main simulation loop and state for torus network
With pending injection queue to prevent packet drops (like RiCoBiT)
"""

import sys
import os
from collections import defaultdict, deque

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class Simulator:
    """
    Manages the main simulation loop and state for torus topology.
    Works with EnhancedTorusTopology and EnhancedNode architecture.
    
    Includes pending injection queue to prevent packet drops when buffers are full.
    """
    def __init__(self, topology):
        self.topology = topology
        self.global_clock = 0
        self.injected_packets = []
        # Pending injections are retried once interface capacity becomes available
        self._pending_injections = defaultdict(deque)

    def inject_packet(self, packet):
        """Injects a packet immediately or queues it if the interface is saturated."""
        source_node = self.topology.nodes.get(packet.source_address)
        if not source_node:
            print(f"ERROR: No source node {packet.source_address} for packet {packet}")
            return

        # Try to inject the packet
        if source_node.inject_packet(packet):
            self._mark_packet_injected(packet)
            print(f"[Clock {self.global_clock}] SIM: Injected {packet}.")
        else:
            # Queue the packet for later retry instead of dropping
            self._pending_injections[packet.source_address].append(packet)
            print(f"[Clock {self.global_clock}] SIM: Queued {packet} until send buffer has space.")

    def _mark_packet_injected(self, packet):
        """Mark packet as injected and record timing."""
        packet.start_timer = self.global_clock
        self.injected_packets.append(packet)

    def _drain_pending_injections(self):
        """Replays deferred injections once their outgoing interfaces have room."""
        if not self._pending_injections:
            return

        for src_addr in list(self._pending_injections.keys()):
            queue = self._pending_injections.get(src_addr)
            if not queue:
                del self._pending_injections[src_addr]
                continue

            source_node = self.topology.nodes.get(src_addr)
            if not source_node:
                del self._pending_injections[src_addr]
                continue

            while queue:
                packet = queue[0]
                
                # Try to inject the packet
                if not source_node.inject_packet(packet):
                    break  # Still no capacity; retry on a future cycle.

                queue.popleft()
                self._mark_packet_injected(packet)
                print(f"[Clock {self.global_clock}] SIM: Injected queued {packet}.")

            if not queue:
                del self._pending_injections[src_addr]

    def run_simulation_step(self):
        """
        Executes one clock cycle of the simulation.
        Follows the dataflow logic with interface handshaking.
        """
        # First, try to inject any pending packets
        self._drain_pending_injections()
        
        # Phase A: Update sender logic on all interfaces
        for node in self.topology.nodes.values():
            for iface in node.interfaces.values():
                if hasattr(iface, 'connected_interface') and iface.connected_interface:
                    if hasattr(iface, 'update_sender_logic'):
                        iface.update_sender_logic()

        # Phase B: Update receiver logic on all interfaces
        for node in self.topology.nodes.values():
            for iface in node.interfaces.values():
                if hasattr(iface, 'connected_interface') and iface.connected_interface:
                    if hasattr(iface, 'update_receiver_logic'):
                        iface.update_receiver_logic()

        # Phase C: Update node logic (process received packets, routing)
        for node in self.topology.nodes.values():
            if hasattr(node, 'node_step'):
                node.node_step(self.global_clock)
            elif hasattr(node, 'update'):
                node.update()
            # Also process received packets explicitly
            if hasattr(node, 'process_received_packets'):
                node.process_received_packets()
            
        self.global_clock += 1
    
    def get_delivered_count(self):
        """Count delivered packets across all nodes."""
        count = 0
        for node in self.topology.nodes.values():
            if hasattr(node, 'consumed_packets'):
                count += len(node.consumed_packets)
        return count
    
    def get_all_consumed_packets(self):
        """Get all consumed packets from all nodes."""
        all_consumed = []
        for node in self.topology.nodes.values():
            if hasattr(node, 'consumed_packets'):
                for packet in node.consumed_packets:
                    if hasattr(packet, 'end_timer') and packet.end_timer < 0:
                        packet.end_timer = self.global_clock
                    all_consumed.append(packet)
        return all_consumed