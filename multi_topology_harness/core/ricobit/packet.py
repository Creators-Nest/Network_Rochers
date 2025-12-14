class Packet:
    _id_counter = 0

    def __init__(
        self,
        source_address,
        dest_address,
        data="payload",
        sim_clock=0,
        packet_id=None,
        payload_size=1,
        metadata=None,
    ):
        type(self)._id_counter += 1
        self.packet_id = packet_id or f"pkt-{type(self)._id_counter}"
        self.source_address = source_address
        self.dest_address = dest_address
        self.data = data
        self.payload_size = max(int(payload_size) if payload_size else 1, 1)
        self.metrics_metadata = metadata
        self.start_timer = None if sim_clock is None else sim_clock
        self.end_timer = -1
        self.hops_traversed = 0

    def __repr__(self):
        return (
            f"Packet(id={self.packet_id}, data={self.data}, "
            f"{self.source_address} -> {self.dest_address})"
        )