# Communication Protocol - Unidirectional Mode (Figure 4)

## Overview
This document describes the implementation of the **unidirectional communication protocol** between nodes in the 2D Mesh NoC, based on Figure 4 from the research paper.

## Signal Description

### 1. **REQ (Request)**
- **Purpose**: Raised when a node wants to send a packet to an adjacent node
- **Direction**: Source → Destination
- **Color**: Red (🔴)
- **When Active**: When output buffer has packets to send

### 2. **ACK (Acknowledgement)**
- **Purpose**: Raised by receiving node to confirm readiness to accept packet
- **Direction**: Destination → Source  
- **Color**: Green (🟢)
- **When Active**: When input buffer has space available

### 3. **DATA**
- **Purpose**: Carries the actual packet data between interfaces
- **Transfer**: Serial transfer synchronized with CLK
- **Protocol**: Only transfers when both REQ and ACK are high

### 4. **CLK (Clock)**
- **Purpose**: Synchronizes data transfer between interfaces
- **Color**: Blue (🔵)
- **Pulse**: Generated during active transfer (REQ + ACK)

### 5. **Choke (C)**
- **Purpose**: Fairness mechanism for bidirectional communication
- **Color**: Yellow (⚠️)
- **Logic**: Set when receiving node's send buffer contains packets
- **Effect**: Prevents starvation by allowing alternate transmission

## Communication Flow

### Step-by-Step Protocol:

```
1. IDLE STATE
   ├── Node 1 has packet to send
   └── Node 2 ready to receive

2. REQUEST PHASE
   ├── Node 1 checks Choke signal from Node 2
   ├── If Choke = 0 (fair to send)
   │   ├── Node 1 raises REQ signal
   │   └── Node 1 places DATA on line
   └── If Choke = 1 (Node 2 wants to send)
       └── Wait for fairness

3. ACKNOWLEDGE PHASE
   ├── Node 2 receives REQ signal
   ├── Node 2 checks input buffer space
   ├── If space available:
   │   ├── Node 2 raises ACK signal
   │   └── Node 2 sets Choke = 1 if output buffer has packets
   └── If buffer full:
       └── No ACK (sender must wait)

4. TRANSFER PHASE
   ├── Both REQ and ACK are HIGH
   ├── CLK pulse generated
   ├── DATA transferred serially
   └── Packet moves from Node 1 → Node 2

5. COMPLETION
   ├── REQ signal lowered
   ├── ACK signal lowered
   ├── CLK pulse ends
   └── Both nodes return to IDLE
```

## Fairness Mechanism (Choke Signal)

The **Choke bit** provides fairness in bidirectional communication:

```
Scenario: Node A ↔ Node B

WITHOUT Choke:
- Node A continuously sends → Node B starved
- Node B never gets chance to send

WITH Choke:
- Node A sends Packet 1
- Node B sets Choke = 1 (has packets to send)
- Node A sees Choke, waits
- Node B sends its packet
- Node B sets Choke = 0
- Node A can send Packet 2
```

## Implementation Details

### Node Class (`node.py`)
```python
# Signal state per direction
self.signals = {
    Direction.NORTH: {'REQ': False, 'ACK': False, 'DATA': None, 'CLK': False, 'Choke': False},
    Direction.SOUTH: {'REQ': False, 'ACK': False, 'DATA': None, 'CLK': False, 'Choke': False},
    Direction.EAST: {'REQ': False, 'ACK': False, 'DATA': None, 'CLK': False, 'Choke': False},
    Direction.WEST: {'REQ': False, 'ACK': False, 'DATA': None, 'CLK': False, 'Choke': False},
}
```

### Key Methods:

1. **`initiate_transfer(direction, packet)`**
   - Checks Choke signal for fairness
   - Raises REQ signal
   - Places DATA on line

2. **`acknowledge_transfer(direction)`**
   - Checks buffer space
   - Raises ACK signal
   - Sets Choke if needed

3. **`complete_transfer(direction)`**
   - Verifies REQ-ACK handshake
   - Generates CLK pulse
   - Transfers DATA
   - Clears all signals

## Visualization

### In GUI (`mesh_gui.py`):

**Signal Indicators on Connections:**
- **REQ→** : Red arrow pointing forward
- **←ACK** : Green arrow pointing backward  
- **🔵** : Blue dot for CLK pulse
- **⚠️** : Yellow warning for Choke

**Example Display:**
```
Node(0,0) ----REQ→---- Node(0,1)
           ----←ACK----
           -----🔵-----
           -----⚠️----- (if Choke active)
```

## Timing Diagram

```
Time:  t0    t1    t2    t3    t4    t5
       │     │     │     │     │     │
REQ:   ──────┌─────┬─────┐─────────────
       │     │     │     │     │     │
ACK:   ──────────────┌─────┬────────────
       │     │     │     │     │     │
CLK:   ──────────────┌──┐──────────────
       │     │     │     │     │     │
DATA:  ──────XXXXXX[PKT]XXXXXX──────────
       │     │     │     │     │     │
Choke: ──────┌───────────────┐─────────
       │     │     │     │     │     │

Legend:
─── : Low signal
┌─┐ : High signal
XXX : Data present
[PKT]: Valid packet transfer
```

## Benefits

1. **Deadlock-Free**: REQ-ACK handshake prevents buffer overflow
2. **Fair**: Choke signal ensures both nodes get transmission opportunities
3. **Synchronized**: CLK ensures reliable data transfer
4. **Simple**: Minimal control signals (5 signals only)
5. **Scalable**: Works for any 2D mesh size

## Buffer Management

### Reception Buffer (Receive Buffer):
```
1. Receives incoming packets
2. FIFO queue structure
3. Triggers ACK when space available
4. Feeds Routing Logic
```

### Transmission Buffer (Send Buffer):
```
1. Holds packets for transmission
2. Triggers REQ when packets present
3. Triggers Choke when non-empty
4. Releases on successful transfer
```

## Test Scenarios

### Scenario 1: Simple Transfer
- Node A wants to send to Node B
- Both buffers have space
- Expected: REQ → ACK → CLK → DATA → Success

### Scenario 2: Buffer Full
- Node A wants to send to Node B
- Node B buffer full
- Expected: REQ → No ACK → Wait → Retry

### Scenario 3: Bidirectional with Fairness
- Node A sends to Node B
- Node B also has packet for Node A
- Expected: 
  - A→B (Packet 1)
  - B sets Choke
  - B→A (Packet 2)
  - A→B (Packet 3)

### Scenario 4: Multiple Parallel Transfers
- (0,0)→(0,1) and (1,0)→(1,1) simultaneously
- Independent REQ-ACK handshakes
- Expected: Both transfer in parallel

## Performance Metrics

- **Latency**: Time from REQ to DATA transfer complete
- **Throughput**: Packets transferred per clock cycle
- **Fairness**: Alternation ratio between bidirectional flows
- **Buffer Utilization**: Average occupancy percentage

## Future Enhancements

1. **Pipelined Transfer**: Overlap REQ-ACK with previous DATA
2. **Adaptive Choke**: Priority-based choke mechanism
3. **Multi-Flit Packets**: Header and payload separation
4. **Virtual Channels**: Multiple buffers per direction
5. **Credit-Based Flow Control**: Advance credits instead of ACK

---

**Reference**: Figure 4 - Interconnection of nodes in unidirectional mode
