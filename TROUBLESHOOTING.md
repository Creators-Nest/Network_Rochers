# Troubleshooting Guide

## 🐛 Common Issues and Solutions

### Issue 1: ImportError - Module not found

**Error:**
```
ImportError: No module named 'src'
ModuleNotFoundError: No module named 'gui'
```

**Solution:**
Make sure you're running from the project root directory:
```powershell
cd "C:\Users\girio\OneDrive - REVA University\Sem 5\Network on chips\project\Network_Rochers"
python run_simulator.py
```

---

### Issue 2: Circular import errors

**Error:**
```
ImportError: attempted relative import beyond top-level package
```

**Solution:**
✅ **FIXED** - Use the provided `run_simulator.py` launcher script instead of running files directly.

**Don't do:**
```powershell
python src/gui/main_window.py  ❌
```

**Do:**
```powershell
python run_simulator.py  ✅
```

---

### Issue 3: KeyError when drawing network

**Error:**
```
KeyError: (0, 0)
```

**Solution:**
✅ **FIXED** - The initialization order has been corrected. Network is created before visualization.

---

### Issue 4: GUI window doesn't appear

**Possible Causes:**
1. Python version incompatibility
2. Tkinter not installed

**Check Python version:**
```powershell
python --version
```
Should be Python 3.8 or higher

**Check Tkinter:**
```powershell
python -c "import tkinter; print('Tkinter OK')"
```

**If Tkinter missing on Windows:**
- Reinstall Python from python.org with "tcl/tk and IDLE" option checked

---

### Issue 5: Blank canvas / Network not visible

**Solutions:**
1. **Resize window** - Drag window edges to trigger redraw
2. **Click "Reset View"** - In View Controls section
3. **Reconfigure network** - Change rows/columns and click "Apply Configuration"

---

### Issue 6: Node selection not working

**Check:**
- Network must be created first (click "Apply Configuration")
- Click directly on node circles (blue circles)
- First click = Source (green), Second click = Destination (red)

---

### Issue 7: Simulation button disabled

**Requirements for simulation:**
- ✅ Network must be created
- ✅ Source node must be selected (green)
- ✅ Destination node must be selected (red)
- ✅ Source ≠ Destination

---

### Issue 8: Packet doesn't move

**Troubleshooting:**
1. Check source and destination are different nodes
2. Verify "Start Simulation" was clicked
3. Try "Step Forward" for manual control
4. Check Statistics panel for packet status
5. Try "Reset Simulation" and start again

---

### Issue 9: Buffer overflow warnings

**This is expected behavior!**
- Demonstrates congestion management
- Shows back-pressure (Choke signal)
- Part of the NoC simulation
- Can be observed in Statistics panel

---

### Issue 10: Slow animation

**Solutions:**
- Increase speed slider (higher ms = slower)
- Default: 500ms between hops
- Fast: 100-200ms
- Slow (detailed): 1000-2000ms

---

## 🔧 Debug Mode

If you encounter unexpected errors, run with full traceback:

```powershell
python run_simulator.py
```

The script already includes error handling and will display:
- Error message
- Full stack trace
- Line numbers

---

## 📝 Reporting Issues

When reporting issues, include:

1. **Error message** (full traceback)
2. **Steps to reproduce**
3. **Python version** (`python --version`)
4. **OS version** (Windows version)
5. **Screenshot** (if GUI issue)

---

## ✅ Verification Checklist

### Fresh Installation Test

1. **Navigate to project:**
   ```powershell
   cd "C:\Users\girio\OneDrive - REVA University\Sem 5\Network on chips\project\Network_Rochers"
   ```

2. **Launch simulator:**
   ```powershell
   python run_simulator.py
   ```

3. **Expected output:**
   ```
   ============================================================
   Starting Network-on-Chip Simulator
   ============================================================
   
   Loading GUI...
   ```

4. **GUI should appear** with:
   - Left control panel (dark blue background)
   - Right visualization area (light gray background)
   - 4×4 mesh network displayed
   - Blue node circles with coordinates

5. **Test basic functionality:**
   - ✓ Click any node → turns green (source)
   - ✓ Click another node → turns red (destination)
   - ✓ "Start Simulation" enables
   - ✓ Click "Start Simulation" → packet routes
   - ✓ Statistics update in real-time

---

## 🎯 Quick Fixes

### If simulation freezes:
```
Click "Reset Simulation"
```

### If network looks wrong:
```
Change grid size → Click "Apply Configuration"
```

### If zoom is weird:
```
Click "Reset View"
```

### If nothing works:
```
Close window → Restart: python run_simulator.py
```

---

## 🔍 File Integrity Check

Ensure all files exist:

```
Network_Rochers/
├── run_simulator.py          ✅ Main launcher
├── src/
│   ├── __init__.py           ✅ Package marker
│   ├── core/
│   │   ├── __init__.py       ✅
│   │   ├── packet.py         ✅
│   │   ├── buffer.py         ✅
│   │   └── node.py           ✅
│   ├── routing/
│   │   ├── __init__.py       ✅
│   │   ├── base_routing.py   ✅
│   │   └── xy_routing.py     ✅
│   └── gui/
│       ├── __init__.py       ✅
│       ├── main_window.py    ✅
│       └── mesh_gui.py       ✅
```

---

## 💡 Performance Tips

### For large networks (8×8, 10×10):
- Use slower animation speed (800-1000ms)
- Zoom in for better visibility
- Use step-by-step mode for detailed observation

### For demonstrations:
- Use 4×4 or 5×5 (optimal balance)
- Speed: 300-500ms
- Try diagonal routing: (0,0) → (3,3)

---

## 🚑 Emergency Reset

If everything breaks:

1. **Close the GUI window**
2. **Delete .pyc files:**
   ```powershell
   Remove-Item -Recurse -Force src\__pycache__
   Remove-Item -Recurse -Force src\*\__pycache__
   ```
3. **Restart:**
   ```powershell
   python run_simulator.py
   ```

---

## ✨ Success Indicators

**Your simulator is working correctly if:**

✅ GUI launches without errors  
✅ 4×4 mesh network visible  
✅ Nodes are clickable and change color  
✅ Simulation button becomes enabled  
✅ Packet animates along path  
✅ Statistics update in real-time  
✅ Buffer counts shown on active nodes  
✅ Zoom and view controls work  

**Congratulations! Your NoC Simulator is operational! 🎉**

---

**Last Updated:** October 24, 2025  
**Version:** 1.0.0  
**Status:** Production Ready
