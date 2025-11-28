"""
Enhanced Flask Web Application for Mesh Topology NoC Simulator
Implements complete interface design with pins, registers, buffers, and control logic
"""

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from topology.enhanced_mesh_topology import EnhancedMeshTopology
from simulation.simulator import Simulator
from core.packet import Packet

app = Flask(__name__)
CORS(app)

# Global topology and simulator
topology = None
simulator = None
packet_counter = 0  # Global packet counter

@app.route('/')
def index():
    """Main page"""
    return render_template('enhanced_simulator.html')

@app.route('/api/init', methods=['POST'])
def init_topology():
    """Initialize topology with given dimensions"""
    global topology, simulator
    
    data = request.json
    width = data.get('width', 6)
    height = data.get('height', 6)
    
    try:
        topology = EnhancedMeshTopology(width=width, height=height)
        simulator = Simulator(topology)
        
        return jsonify({
            'status': 'success',
            'message': f'Initialized {width}x{height} mesh topology',
            'nodes': topology.width * topology.height,
            'topology_data': get_topology_data()
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/topology')
def get_topology():
    """Get current topology structure"""
    if topology is None:
        return jsonify({'status': 'error', 'message': 'Topology not initialized'}), 400
    
    return jsonify({
        'status': 'success',
        'data': get_topology_data()
    })

@app.route('/api/node/<int:x>/<int:y>')
def get_node_info(x, y):
    """Get detailed information about a specific node"""
    if topology is None:
        return jsonify({'status': 'error', 'message': 'Topology not initialized'}), 400
    
    addr = (x, y)
    if addr not in topology.nodes:
        return jsonify({'status': 'error', 'message': 'Node not found'}), 404
    
    node = topology.nodes[addr]
    
    # Get interface information
    interfaces_info = {}
    for neighbor_addr, interface in node.interfaces.items():
        interfaces_info[str(neighbor_addr)] = {
            'neighbor': neighbor_addr,
            'pins': {
                'REQ': interface.pin_REQ,
                'ACK': interface.pin_ACK,
                'DATA': str(interface.pin_DATA) if interface.pin_DATA else None,
                'CLK': interface.pin_CLK,
                'CHOKE': interface.pin_CHOKE
            },
            'registers': {
                'send': str(interface.send_register) if interface.send_register else None,
                'receive': str(interface.receive_register) if interface.receive_register else None
            },
            'buffers': {
                'send': {
                    'size': len(interface.send_buffer.buffer),
                    'capacity': interface.send_buffer.buffer.maxlen,
                    'packets': [str(p) for p in interface.send_buffer.buffer]
                },
                'receive': {
                    'size': len(interface.receive_buffer.buffer),
                    'capacity': interface.receive_buffer.buffer.maxlen,
                    'packets': [str(p) for p in interface.receive_buffer.buffer]
                }
            },
            'status_bits': {
                'busy': interface.bit_Busy,
                'transfer': interface.bit_Transfer,
                'receive': interface.bit_Receive
            }
        }
    
    return jsonify({
        'status': 'success',
        'node': {
            'address': addr,
            'num_interfaces': len(node.interfaces),
            'interfaces': interfaces_info
        }
    })

@app.route('/api/route', methods=['POST'])
def find_route():
    """Find route between source and destination"""
    if topology is None:
        return jsonify({'status': 'error', 'message': 'Topology not initialized'}), 400
    
    data = request.json
    source = tuple(data.get('source'))
    destination = tuple(data.get('destination'))
    
    if source not in topology.nodes or destination not in topology.nodes:
        return jsonify({'status': 'error', 'message': 'Invalid source or destination'}), 400
    
    source_node = topology.nodes[source]
    path = source_node.get_route(destination)
    
    if not path:
        return jsonify({'status': 'error', 'message': 'No route found'}), 404
    
    return jsonify({
        'status': 'success',
        'route': {
            'source': source,
            'destination': destination,
            'path': path,
            'hops': len(path) - 1
        }
    })

@app.route('/api/simulate', methods=['POST'])
def simulate_transfer():
    """Simulate packet transfer from source to destination"""
    global packet_counter
    
    if topology is None or simulator is None:
        return jsonify({'status': 'error', 'message': 'Simulator not initialized'}), 400
    
    data = request.json
    source = tuple(data.get('source'))
    destination = tuple(data.get('destination'))
    packet_data = data.get('data', 'Test Data')
    
    if source not in topology.nodes or destination not in topology.nodes:
        return jsonify({'status': 'error', 'message': 'Invalid source or destination'}), 400
    
    # Create packet
    packet = Packet(
        source_address=source,
        dest_address=destination,
        data=packet_data,
        sim_clock=simulator.global_clock
    )
    packet_counter += 1
    
    # Get route
    source_node = topology.nodes[source]
    path = source_node.get_route(destination)
    
    if not path:
        return jsonify({'status': 'error', 'message': 'No route found'}), 404
    
    # Simulate hop-by-hop transfer with REQ-ACK handshake
    transfer_log = []
    current_packet = packet
    
    for i in range(len(path) - 1):
        current_addr = path[i]
        next_addr = path[i + 1]
        current_node = topology.nodes[current_addr]
        next_node = topology.nodes[next_addr]
        
        # Get interface to next hop
        if next_addr not in current_node.interfaces:
            return jsonify({
                'status': 'error',
                'message': f'No interface from {current_addr} to {next_addr}'
            }), 500
        
        interface = current_node.interfaces[next_addr]
        
        # REQ-ACK Handshake Protocol
        # Step 1: Send REQ signal
        interface.pin_REQ = True
        
        # Step 2: Check if next node can accept (ACK conditions)
        # Condition 1: Next node is destination (always accepts)
        # Condition 2: Next node has space in receive buffer (else wait)
        can_accept = False
        ack_reason = ""
        wait_cycles = 0
        
        if next_addr == destination:
            # Destination node always accepts
            can_accept = True
            ack_reason = "Destination node - packet will be consumed"
        else:
            # Intermediate node - check receive buffer space
            if next_addr in current_node.interfaces:
                next_interface = current_node.interfaces[next_addr]
                
                # Wait until receive buffer has space
                max_wait = 10  # Maximum wait cycles
                while next_interface.receive_buffer.is_full() and wait_cycles < max_wait:
                    wait_cycles += 1
                    # Simulate waiting for buffer space
                    ack_reason = f"Waiting for receive buffer space (cycle {wait_cycles})"
                
                if not next_interface.receive_buffer.is_full():
                    can_accept = True
                    ack_reason = f"Receive buffer has space (waited {wait_cycles} cycles)" if wait_cycles > 0 else "Receive buffer has space"
                else:
                    # Buffer still full after max wait
                    ack_reason = f"Receive buffer full after {max_wait} wait cycles - CHOKE asserted"
                    interface.pin_CHOKE = True
        
        # Step 3: Send ACK if conditions met
        if can_accept:
            interface.pin_ACK = True
        else:
            interface.pin_ACK = False
        
        # Log hop details with handshake info
        hop_info = {
            'hop': i + 1,
            'from': current_addr,
            'to': next_addr,
            'action': 'consuming' if next_addr == destination else 'forwarding',
            'handshake': {
                'REQ': interface.pin_REQ,
                'ACK': interface.pin_ACK,
                'ACK_reason': ack_reason,
                'wait_cycles': wait_cycles,
                'CHOKE': interface.pin_CHOKE
            },
            'interface_state': {
                'pins': {
                    'REQ': interface.pin_REQ,
                    'ACK': interface.pin_ACK,
                    'CLK': interface.pin_CLK,
                    'CHOKE': interface.pin_CHOKE
                },
                'status': {
                    'busy': interface.bit_Busy,
                    'transfer': interface.bit_Transfer,
                    'receive': interface.bit_Receive
                },
                'buffers': {
                    'send': len(interface.send_buffer.buffer),
                    'receive': len(interface.receive_buffer.buffer)
                }
            }
        }
        
        # Simulate transfer only if ACK received
        if can_accept:
            if next_addr == destination:
                # Final hop - destination consumes packet
                hop_info['consumed'] = True
                hop_info['message'] = f'Packet consumed by destination {destination}'
            else:
                # Intermediate hop - store in receive buffer, transfer to send buffer
                hop_info['buffered'] = True
                hop_info['message'] = f'Packet stored in receive buffer at {next_addr}, then moved to send buffer for next hop'
        else:
            hop_info['blocked'] = True
            hop_info['message'] = f'Transfer blocked: {ack_reason}'
        
        # Clear handshake signals after transfer
        interface.pin_REQ = False
        interface.pin_ACK = False
        
        transfer_log.append(hop_info)
    
    return jsonify({
        'status': 'success',
        'simulation': {
            'packet': {
                'id': packet_counter - 1,
                'source': packet.source_address,
                'destination': packet.dest_address,
                'data': packet.data
            },
            'path': path,
            'total_hops': len(path) - 1,
            'transfer_log': transfer_log
        }
    })

@app.route('/api/multicast', methods=['POST'])
def simulate_multicast():
    """Simulate 1:M multicast transfer"""
    global packet_counter
    
    if topology is None or simulator is None:
        return jsonify({'status': 'error', 'message': 'Simulator not initialized'}), 400
    
    data = request.json
    source = tuple(data.get('source'))
    destinations = [tuple(d) for d in data.get('destinations', [])]
    packet_data = data.get('data', 'Multicast Data')
    
    if not destinations:
        return jsonify({'status': 'error', 'message': 'No destinations provided'}), 400
    
    results = []
    
    for dest in destinations:
        # Create packet for this destination
        packet = Packet(
            source_address=source,
            dest_address=dest,
            data=packet_data,
            sim_clock=simulator.global_clock
        )
        packet_counter += 1
        
        # Get route
        source_node = topology.nodes[source]
        path = source_node.get_route(dest)
        
        if path:
            results.append({
                'destination': dest,
                'path': path,
                'hops': len(path) - 1,
                'status': 'success'
            })
        else:
            results.append({
                'destination': dest,
                'status': 'failed',
                'message': 'No route found'
            })
    
    return jsonify({
        'status': 'success',
        'multicast': {
            'source': source,
            'total_destinations': len(destinations),
            'successful': sum(1 for r in results if r.get('status') == 'success'),
            'results': results
        }
    })

def get_topology_data():
    """Helper function to extract topology data"""
    nodes_data = []
    edges_data = []
    
    for addr, node in topology.nodes.items():
        nodes_data.append({
            'address': addr,
            'x': addr[0],
            'y': addr[1],
            'num_interfaces': len(node.interfaces)
        })
        
        for neighbor_addr in node.interfaces.keys():
            # Add edge only once (from lower to higher address)
            if addr < neighbor_addr:
                edges_data.append({
                    'from': addr,
                    'to': neighbor_addr
                })
    
    return {
        'width': topology.width,
        'height': topology.height,
        'nodes': nodes_data,
        'edges': edges_data
    }

@app.route('/api/node-state', methods=['POST'])
def get_node_state():
    """Get current state of a specific node's interfaces"""
    if topology is None:
        return jsonify({'error': 'Topology not initialized'}), 400
    
    data = request.json
    address = tuple(data.get('address'))
    
    if address not in topology.nodes:
        return jsonify({'error': 'Node not found'}), 404
    
    node = topology.nodes[address]
    
    # Map neighbor addresses to directions
    x, y = address
    direction_map = {
        (x, y-1): 'north',
        (x, y+1): 'south',
        (x+1, y): 'east',
        (x-1, y): 'west'
    }
    
    # Collect interface-specific states
    interfaces = {}
    
    for neighbor_addr, interface in node.interfaces.items():
        direction = direction_map.get(neighbor_addr)
        if not direction:
            continue
            
        # Get register states
        send_reg_state = None
        if interface.send_register is not None:
            send_reg_state = {
                'packet_id': getattr(interface.send_register, 'packet_id', None),
                'source': getattr(interface.send_register, 'source_address', None),
                'dest': getattr(interface.send_register, 'dest_address', None)
            }
        
        recv_reg_state = None
        if interface.receive_register is not None:
            recv_reg_state = {
                'packet_id': getattr(interface.receive_register, 'packet_id', None),
                'source': getattr(interface.receive_register, 'source_address', None),
                'dest': getattr(interface.receive_register, 'dest_address', None)
            }
        
        # Get buffer contents
        send_buffer_packets = []
        for pkt in list(interface.send_buffer.buffer):
            send_buffer_packets.append({
                'packet_id': getattr(pkt, 'packet_id', None),
                'source': getattr(pkt, 'source_address', None),
                'dest': getattr(pkt, 'dest_address', None)
            })
        
        recv_buffer_packets = []
        for pkt in list(interface.receive_buffer.buffer):
            recv_buffer_packets.append({
                'packet_id': getattr(pkt, 'packet_id', None),
                'source': getattr(pkt, 'source_address', None),
                'dest': getattr(pkt, 'dest_address', None)
            })
        
        interfaces[direction] = {
            'neighbor': neighbor_addr,
            'pins': {
                'req': interface.pin_REQ,
                'ack': interface.pin_ACK,
                'data': interface.pin_DATA is not None,
                'clk': interface.pin_CLK,
                'choke': interface.pin_CHOKE
            },
            'send_register': send_reg_state,
            'receive_register': recv_reg_state,
            'send_buffer': {
                'count': interface.send_buffer.size(),
                'capacity': interface.send_buffer.capacity,
                'packets': send_buffer_packets
            },
            'receive_buffer': {
                'count': interface.receive_buffer.size(),
                'capacity': interface.receive_buffer.capacity,
                'packets': recv_buffer_packets
            },
            'status_bits': {
                'receive': interface.bit_Receive,
                'transfer': interface.bit_Transfer,
                'busy': interface.bit_Busy
            }
        }
    
    # Also provide aggregate state for backward compatibility
    pins_aggregate = {
        'req': False,
        'ack': False,
        'data': False,
        'clk': False,
        'choke': False
    }
    
    send_buffer_count = 0
    receive_buffer_count = 0
    buffer_capacity = 4
    
    if node.interfaces:
        first_interface = list(node.interfaces.values())[0]
        pins_aggregate['req'] = first_interface.pin_REQ
        pins_aggregate['ack'] = first_interface.pin_ACK
        pins_aggregate['data'] = first_interface.pin_DATA is not None
        pins_aggregate['clk'] = first_interface.pin_CLK
        pins_aggregate['choke'] = first_interface.pin_CHOKE
        send_buffer_count = first_interface.send_buffer.size()
        receive_buffer_count = first_interface.receive_buffer.size()
        buffer_capacity = first_interface.send_buffer.capacity
    
    return jsonify({
        'address': address,
        'interfaces': interfaces,
        'pins': pins_aggregate,
        'send_buffer': {
            'count': send_buffer_count,
            'capacity': buffer_capacity
        },
        'receive_buffer': {
            'count': receive_buffer_count,
            'capacity': buffer_capacity
        }
    })

if __name__ == '__main__':
    # Initialize default 6x6 topology
    topology = EnhancedMeshTopology(width=6, height=6)
    simulator = Simulator(topology)
    
    print("="*60)
    print("Enhanced Mesh Topology NoC Simulator - Flask Web Application")
    print("="*60)
    print(f"Topology: {topology.width}x{topology.height} mesh")
    print(f"Total Nodes: {len(topology.nodes)}")
    print(f"Starting server on http://localhost:5000")
    print("="*60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
