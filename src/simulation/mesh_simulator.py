"""
Real Mesh Network Simulator Engine
Implements proper NoC simulation with clock cycles, flow control, and AODV routing
"""

from typing import Dict, List, Tuple, Optional, Set
from ..core.node import Node, Direction, NodeStatus
from ..core.packet import Packet, PacketStatus, PacketType
from ..core.buffer import Buffer
from enum import Enum


class SimulationPhase(Enum):
    """Simulation phases following mesh-working-flow"""
    IDLE = "idle"
    ROUTE_DISCOVERY = "route_discovery"  # RREQ broadcast
    ROUTE_REPLY = "route_reply"          # RREP unicast
    DATA_TRANSFER = "data_transfer"      # Actual data transmission
    COMPLETED = "completed"


class MeshSimulator:
    """
    Real mesh network simulator with proper clock cycles and flow control
    
    Implements:
    - Clock-cycle based execution
    - AODV route discovery (RREQ/RREP)
    - Buffer-based flow control (REQ/ACK/Choke signals)
    - Per-link packet transfer
    - Proper routing table management
    """
    
    def __init__(self, nodes: Dict[Tuple[int, int], Node]):
        """
        Initialize simulator
        
        Args:
            nodes: Dictionary of nodes by position
        """
        self.nodes = nodes
        self.clock_cycle = 0
        self.phase = SimulationPhase.IDLE
        
        # Active packets in the network
        self.data_packet: Optional[Packet] = None
        self.rreq_packets: List[Packet] = []
        self.rrep_packets: List[Packet] = []
        
        # Packets waiting to be transferred (current_node, packet, next_direction)
        self.pending_transfers: List[Tuple[Node, Packet, Direction]] = []
        
        # Route discovery state
        self.route_established = False
        self.source_node: Optional[Tuple[int, int]] = None
        self.dest_node: Optional[Tuple[int, int]] = None
        
        # Statistics
        self.total_rreq_sent = 0
        self.total_rrep_sent = 0
        self.total_data_transfers = 0
        self.total_choke_signals = 0
        
    def start_simulation(self, source: Tuple[int, int], destination: Tuple[int, int],
                        data: str) -> bool:
        """
        Start simulation by initiating route discovery
        
        Args:
            source: Source node position
            destination: Destination node position
            data: Data to send
            
        Returns:
            True if started successfully
        """
        if source not in self.nodes or destination not in self.nodes:
            return False
        
        self.source_node = source
        self.dest_node = destination
        self.clock_cycle = 0
        self.phase = SimulationPhase.ROUTE_DISCOVERY
        self.route_established = False
        
        # Reset all nodes
        for node in self.nodes.values():
            node.clock_cycle = 0
            node.rreq_cache.clear()
            node.reverse_routes.clear()
            # Clear old routes but keep topology
            
        # Create data packet (will be sent after route discovery)
        self.data_packet = Packet(
            source=source,
            destination=destination,
            payload={"data": data, "size": len(data)},
            creation_time=0,
            packet_type=PacketType.DATA
        )
        
        # Initiate RREQ from source
        source_node = self.nodes[source]
        rreq_packets = source_node.send_rreq(destination)
        
        # Queue RREQ packets for broadcast
        for rreq, direction in rreq_packets:
            self.pending_transfers.append((source_node, rreq, direction))
            self.rreq_packets.append(rreq)
        
        self.total_rreq_sent += len(rreq_packets)
        
        return True
    
    def step(self) -> Dict:
        """
        Execute one clock cycle of simulation
        
        Returns:
            Dictionary with step information
        """
        self.clock_cycle += 1
        
        # Tick all node clocks
        for node in self.nodes.values():
            node.tick_clock()
        
        step_info = {
            'clock_cycle': self.clock_cycle,
            'phase': self.phase.value,
            'packets_in_flight': 0,
            'transfers': 0,
            'choke_signals': 0,
            'route_established': self.route_established,
            'events': []
        }
        
        if self.phase == SimulationPhase.ROUTE_DISCOVERY:
            step_info.update(self._step_route_discovery())
        elif self.phase == SimulationPhase.ROUTE_REPLY:
            step_info.update(self._step_route_reply())
        elif self.phase == SimulationPhase.DATA_TRANSFER:
            step_info.update(self._step_data_transfer())
        
        return step_info
    
    def _step_route_discovery(self) -> Dict:
        """Process RREQ packets (route discovery phase)"""
        events = []
        new_pending = []
        
        # Process all pending RREQ transfers
        for current_node, rreq, direction in self.pending_transfers:
            next_node = current_node.get_neighbor(direction)
            
            if next_node is None:
                continue
            
            # Flow Control Step 1: Send REQ signal
            current_node.req_signal = True
            events.append(f"REQ: {current_node.position}→{next_node.position}")
            
            # Flow Control Step 2: Check for ACK (buffer space available)
            if not next_node.choke_signal and not next_node.input_buffer.is_full():
                # ACK received - transfer packet
                next_node.ack_signal = True
                
                if next_node.input_buffer.enqueue(rreq):
                    current_node.transfer_signal = True
                    events.append(f"TRANSFER: {current_node.position}→{next_node.position}")
                    
                    # Process RREQ at next node
                    responses = next_node.process_rreq(rreq, self._get_reverse_direction(direction))
                    
                    for response_packet, response_dir in responses:
                        if response_packet.packet_type == PacketType.RREP:
                            # RREP generated - move to route reply phase
                            self.rrep_packets.append(response_packet)
                            new_pending.append((next_node, response_packet, response_dir))
                            events.append(f"RREP Generated at {next_node.position}")
                        elif response_packet.packet_type == PacketType.RREQ:
                            # Forward RREQ
                            new_pending.append((next_node, response_packet, response_dir))
            else:
                # No ACK - choke signal active
                events.append(f"CHOKE: {next_node.position} (buffer full)")
                self.total_choke_signals += 1
                new_pending.append((current_node, rreq, direction))  # Retry next cycle
        
        self.pending_transfers = new_pending
        
        # Check if we've received RREP (transition to route reply phase)
        if self.rrep_packets:
            self.phase = SimulationPhase.ROUTE_REPLY
            events.append("Phase: ROUTE_DISCOVERY → ROUTE_REPLY")
        
        # Timeout check - if no progress after 50 cycles, fail
        if self.clock_cycle > 50 and not self.rrep_packets:
            self.phase = SimulationPhase.COMPLETED
            events.append("Route discovery timeout")
        
        return {
            'events': events,
            'packets_in_flight': len(self.pending_transfers),
            'transfers': len([e for e in events if 'TRANSFER' in e]),
            'choke_signals': len([e for e in events if 'CHOKE' in e])
        }
    
    def _step_route_reply(self) -> Dict:
        """Process RREP packets (route reply phase)"""
        events = []
        new_pending = []
        
        # Process all pending RREP transfers
        for current_node, rrep, direction in self.pending_transfers:
            next_node = current_node.get_neighbor(direction)
            
            if next_node is None:
                continue
            
            # Flow control: REQ/ACK
            current_node.req_signal = True
            
            if not next_node.choke_signal and not next_node.input_buffer.is_full():
                next_node.ack_signal = True
                
                if next_node.input_buffer.enqueue(rrep):
                    current_node.transfer_signal = True
                    events.append(f"RREP: {current_node.position}→{next_node.position}")
                    
                    # Process RREP
                    result = next_node.process_rrep(rrep, self._get_reverse_direction(direction))
                    
                    if result is not None:
                        # Forward RREP
                        forward_packet, forward_dir = result
                        new_pending.append((next_node, forward_packet, forward_dir))
                    else:
                        # RREP reached source - route established!
                        if next_node.position == self.source_node:
                            self.route_established = True
                            self.phase = SimulationPhase.DATA_TRANSFER
                            events.append(f"Route established: {self.source_node}→{self.dest_node}")
                            
                            # Inject data packet at source
                            source_node = self.nodes[self.source_node]
                            source_node.output_buffer.enqueue(self.data_packet)
            else:
                events.append(f"CHOKE: {next_node.position}")
                self.total_choke_signals += 1
                new_pending.append((current_node, rrep, direction))
        
        self.pending_transfers = new_pending
        
        return {
            'events': events,
            'packets_in_flight': len(self.pending_transfers),
            'route_established': self.route_established
        }
    
    def _step_data_transfer(self) -> Dict:
        """Transfer actual data packet using established route"""
        events = []
        
        if not self.data_packet or self.data_packet.status == PacketStatus.DELIVERED:
            self.phase = SimulationPhase.COMPLETED
            return {'events': ['Simulation complete'], 'completed': True}
        
        current_pos = self.data_packet.current_node
        current_node = self.nodes[current_pos]
        
        # Check if at destination
        if current_pos == self.dest_node:
            self.data_packet.deliver(self.clock_cycle)
            current_node.packets_received += 1
            self.phase = SimulationPhase.COMPLETED
            events.append(f"DATA DELIVERED at {current_pos}")
            return {
                'events': events,
                'completed': True,
                'latency': self.data_packet.get_latency()
            }
        
        # Get next hop from routing table
        next_direction = current_node.get_next_hop(self.dest_node)
        
        if next_direction is None:
            events.append(f"ERROR: No route from {current_pos} to {self.dest_node}")
            self.data_packet.drop(self.clock_cycle)
            self.phase = SimulationPhase.COMPLETED
            return {'events': events, 'error': True}
        
        next_node = current_node.get_neighbor(next_direction)
        
        # Flow Control: REQ signal
        current_node.req_signal = True
        events.append(f"REQ: {current_pos}→{next_node.position}")
        
        # Flow Control: Check ACK
        if not next_node.choke_signal and not next_node.input_buffer.is_full():
            # ACK received - transfer data
            next_node.ack_signal = True
            
            # Move packet from output buffer of current to input buffer of next
            packet = current_node.output_buffer.dequeue()
            if packet and next_node.input_buffer.enqueue(packet):
                current_node.transfer_signal = True
                packet.add_hop(next_node.position, self.clock_cycle)
                current_node.packets_forwarded += 1
                self.total_data_transfers += 1
                
                # Move to next node's output buffer for next transfer
                next_node.output_buffer.enqueue(packet)
                
                events.append(f"DATA: {current_pos}→{next_node.position}")
        else:
            # Choke signal - wait
            events.append(f"CHOKE: {next_node.position} (backpressure)")
            self.total_choke_signals += 1
        
        return {
            'events': events,
            'current_hop': self.data_packet.hops,
            'packets_in_flight': 1,
            'choke_signals': 1 if next_node.choke_signal else 0
        }
    
    def _get_reverse_direction(self, direction: Direction) -> Direction:
        """Get opposite direction"""
        reverse_map = {
            Direction.NORTH: Direction.SOUTH,
            Direction.SOUTH: Direction.NORTH,
            Direction.EAST: Direction.WEST,
            Direction.WEST: Direction.EAST
        }
        return reverse_map.get(direction, direction)
    
    def is_complete(self) -> bool:
        """Check if simulation is complete"""
        return self.phase == SimulationPhase.COMPLETED
    
    def get_statistics(self) -> Dict:
        """Get simulation statistics"""
        return {
            'clock_cycles': self.clock_cycle,
            'phase': self.phase.value,
            'route_established': self.route_established,
            'total_rreq_sent': self.total_rreq_sent,
            'total_rrep_sent': self.total_rrep_sent,
            'total_data_transfers': self.total_data_transfers,
            'total_choke_signals': self.total_choke_signals,
            'data_delivered': self.data_packet and self.data_packet.status == PacketStatus.DELIVERED,
            'latency': self.data_packet.get_latency() if self.data_packet and self.data_packet.status == PacketStatus.DELIVERED else None
        }
