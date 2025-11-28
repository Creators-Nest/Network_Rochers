# Quick Start Guide - Torus Simulator Web App

## Installation & Running

### Step 1: Install Dependencies
```powershell
cd torus_simulator
pip install -r webapp\requirements.txt
```

### Step 2: Run the Application
```powershell
python run_webapp.py
```

### Step 3: Open Browser
Navigate to: **http://localhost:5000**

---

## Quick Test

1. **Initialize**: Default 4x4 torus should load automatically
2. **Select Nodes**:
   - Source: (0, 0)
   - Destination: (3, 0)
3. **Simulate**: Click "Simulate route" button
4. **Observe**: Notice it uses wraparound (1 hop via West) instead of direct (3 hops via East)
5. **Animate**: Click "Animate path" to see packet flow

---

## Example Wraparound Routes (4x4 Torus)

| From | To | Direct Path | Wraparound Path | Chosen |
|------|-----|-------------|-----------------|---------|
| (0,0) | (3,0) | East 3 hops | West 1 hop | Wraparound ✓ |
| (0,0) | (0,3) | South 3 hops | North 1 hop | Wraparound ✓ |
| (1,1) | (3,3) | East 2, South 2 | Direct (same cost) | Direct ✓ |

---

## Troubleshooting

### Port 5000 Already in Use
```powershell
# Edit webapp/enhanced_app.py, change last line:
app.run(debug=True, host='0.0.0.0', port=5001)  # Use 5001 instead
```

### Flask Not Found
```powershell
pip install Flask Flask-CORS
```

### Import Errors
Make sure you're running from the `torus_simulator` directory:
```powershell
cd torus_simulator
python run_webapp.py
```

---

## Key Features to Explore

✅ **Wraparound Visualization**: See edges that wrap around grid edges  
✅ **Interface Details**: Click nodes to view 4 interfaces (N, S, E, W)  
✅ **Handshake Phases**: Watch REQ→ACK→DATA→Release animation  
✅ **Buffer Status**: Monitor send/receive buffer occupancy  
✅ **Multi-route**: Test 1:n and n:m parallel simulations  

---

## File Structure
```
torus_simulator/
├── run_webapp.py          # <-- Run this file
├── core/
│   ├── enhanced_interface.py
│   └── enhanced_node.py
├── topology/
│   └── enhanced_torus_topology.py
├── routing/
│   └── xy_router.py
├── simulation/
│   └── simulator.py
└── webapp/
    ├── enhanced_app.py    # Flask application
    ├── requirements.txt
    ├── templates/
    │   └── simulator.html
    └── static/
        ├── css/
        │   ├── style.css
        │   └── index.css
        └── js/
            └── app.js
```

---

## Comparison with Mesh Topology

**Same:**
- UI/UX design and layout
- Frontend functionality
- Simulation features
- Interface architecture

**Different:**
- Torus has wraparound connections
- Default 4x4 grid (vs 6x6 mesh)
- All nodes have 4 neighbors
- Shorter average path lengths
- XY routing considers wraparound

---

## Next Steps

1. ✅ Run the application
2. ✅ Test basic 1:1 routing
3. ✅ Verify wraparound works
4. ✅ Explore node interface details
5. ✅ Try multicast (1:n) mode
6. ✅ Test parallel routing (n:m)
7. ✅ Experiment with different grid sizes

---

## Support

See detailed documentation:
- `webapp/README.md` - Full webapp documentation
- `WEBAPP_IMPLEMENTATION.md` - Implementation details
- `README.md` - Project overview

---

**Enjoy simulating your Torus NoC!** 🎉
