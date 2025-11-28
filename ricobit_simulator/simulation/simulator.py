from collections import defaultdict, deque


class Simulator:
    """Coordinates packet injection and drives the simulation clock."""

    def __init__(self, topology):
        self.topology = topology
        self.global_clock = 0
        self._pending_injections = defaultdict(deque)

    def inject_packet(self, packet):
        """Injects a packet immediately or queues it if the interface is saturated."""
        source_node = self.topology.nodes.get(packet.source_address)
        if not source_node:
            print(f"ERROR: No source node for packet {packet}.")
            return

        iface = source_node.route(packet)
        if not iface:
            print(f"ERROR: No route for packet {packet} at source.")
            return

        if iface.send_buffer.enqueue(packet):
            print(f"[Clock {self.global_clock}] SIM: Injected {packet}.")
            return

        self._pending_injections[packet.source_address].append(packet)
        print(
            f"[Clock {self.global_clock}] SIM: Queued {packet} until send buffer has space."
        )

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
                iface = source_node.route(packet)
                if not iface:
                    print(f"ERROR: No route for queued packet {packet} at source.")
                    queue.popleft()
                    continue

                if not iface.send_buffer.enqueue(packet):
                    break

                queue.popleft()
                print(
                    f"[Clock {self.global_clock}] SIM: Injected queued {packet}."
                )

            if not queue:
                del self._pending_injections[src_addr]

    def run_simulation_step(self):
        """
        Executes one clock cycle of the simulation.
        This follows the dataflow diagram (Fig 10) logic.
        """
        self._drain_pending_injections()

        # Phase A: Update sender logic (reads state, sets REQ)
        for node in self.topology.nodes.values():
            for iface in node.interfaces.values():
                if iface.connected_interface:
                    iface.update_sender_logic()

        # Phase B: Update receiver logic (reads REQ, sets ACK, xfers data)
        for node in self.topology.nodes.values():
            for iface in node.interfaces.values():
                if iface.connected_interface:
                    iface.update_receiver_logic()

        # Phase C: Update node logic (routes received packets)
        for node in self.topology.nodes.values():
            node.node_step(self.global_clock)
            
        self.global_clock += 1