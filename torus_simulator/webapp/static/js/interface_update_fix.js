// Minimal fix to update interface details from backend state
// Add this to the end of app.js or include it separately

// Override the updateNodePanelContent to fetch live state
const originalUpdateNodePanelContent = updateNodePanelContent;

async function updateNodePanelContentWithLiveData() {
    if (!selectedNodeId || !nodePanel) return;
    
    const meta = nodeMeta.get(selectedNodeId);
    if (!meta) return;
    
    // Fetch live state from backend
    try {
        const response = await fetch('/api/node-state', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ address: [meta.x, meta.y] })
        });
        
        if (!response.ok) {
            // Fallback to original if fetch fails
            originalUpdateNodePanelContent();
            return;
        }
        
        const liveState = await response.json();
        
        // Update runtime with live interface data
        const runtime = ensureNodeRuntimeState(selectedNodeId);
        
        if (liveState.interfaces && runtime.interfaces) {
            Object.entries(liveState.interfaces).forEach(([direction, ifaceData]) => {
                const neighborId = makeNodeId(ifaceData.neighbor);
                let ifaceRuntime = runtime.interfaces.get(neighborId);
                
                if (!ifaceRuntime) {
                    ifaceRuntime = defaultInterfaceRuntime();
                    runtime.interfaces.set(neighborId, ifaceRuntime);
                }
                
                // Update pins
                if (ifaceData.pins) {
                    ifaceRuntime.handshakePins = {
                        req: ifaceData.pins.req,
                        ack: ifaceData.pins.ack,
                        data: ifaceData.pins.data,
                        choke: ifaceData.pins.choke
                    };
                }
                
                // Update status bits
                if (ifaceData.status_bits) {
                    ifaceRuntime.statusBits = {
                        busy: ifaceData.status_bits.busy,
                        transfer: ifaceData.status_bits.transfer,
                        receive: ifaceData.status_bits.receive
                    };
                }
                
                // Update buffers
                if (ifaceData.send_buffer) {
                    ifaceRuntime.sendBuffer = {
                        used: ifaceData.send_buffer.count,
                        capacity: ifaceData.send_buffer.capacity,
                        state: ifaceData.send_buffer.count > 0 ? 'primed' : 'idle',
                        head: ifaceData.send_buffer.packets && ifaceData.send_buffer.packets.length > 0 
                            ? ifaceData.send_buffer.packets[0] : null
                    };
                }
                
                if (ifaceData.receive_buffer) {
                    ifaceRuntime.receiveBuffer = {
                        used: ifaceData.receive_buffer.count,
                        capacity: ifaceData.receive_buffer.capacity,
                        state: ifaceData.receive_buffer.count > 0 ? 'ready' : 'idle',
                        head: ifaceData.receive_buffer.packets && ifaceData.receive_buffer.packets.length > 0 
                            ? ifaceData.receive_buffer.packets[0] : null
                    };
                }
                
                // Update registers
                ifaceRuntime.sendRegister = ifaceData.send_register;
                ifaceRuntime.receiveRegister = ifaceData.receive_register;
            });
        }
        
        // Update aggregate buffer states
        if (liveState.send_buffer) {
            runtime.sendBuffer = liveState.send_buffer.count > 0 ? 'primed' : 'idle';
        }
        if (liveState.receive_buffer) {
            runtime.receiveBuffer = liveState.receive_buffer.count > 0 ? 'ready' : 'idle';
        }
        
    } catch (error) {
        console.warn('Failed to fetch live node state:', error);
    }
    
    // Call original function with updated runtime
    originalUpdateNodePanelContent();
}

// Replace the global function
if (typeof updateNodePanelContent !== 'undefined') {
    updateNodePanelContent = updateNodePanelContentWithLiveData;
}
