class Simulator:
    """
    Manages the main simulation loop and state.
    """
    def __init__(self, topology):
        self.topology = topology
        self.global_clock = 0

    def inject_packet(self, packet):
        """Injects a packet into the correct node's send buffer."""
        source_node = self.topology.nodes.get(packet.source_address)
        if source_node:
            # Route to find first interface
            iface = source_node.route(packet)
            if iface:
                iface.send_buffer.enqueue(packet)
                print(f"[Clock {self.global_clock}] SIM: Injected {packet}.")
            else:
                print(f"ERROR: No route for packet {packet} at source.")

    def run_simulation_step(self):
        """
        Executes one clock cycle of the simulation.
        This follows the dataflow diagram (Fig 10) logic.
        """
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