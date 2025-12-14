class Packet:
    def __init__(self, source_address, dest_address, data="payload", sim_clock=0):
        self.source_address = source_address
        self.dest_address = dest_address
        self.data = data
        self.start_timer = sim_clock
        self.end_timer = -1

    def __repr__(self):
        return f"Packet({self.data}, {self.source_address} -> {self.dest_address})"