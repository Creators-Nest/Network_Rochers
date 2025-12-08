// Live interface update patch - append to app.js
(function() {
    let liveUpdateInterval = null;
    
    // Fetch and update interface state from backend
    async function fetchAndUpdateInterfaceState() {
        if (!selectedNodeId || !nodePanel || !nodePanel.classList.contains('is-visible')) {
            return;
        }
        
        const meta = nodeMeta.get(selectedNodeId);
        if (!meta) return;
        
        try {
            const response = await fetch('/api/node-state', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ address: [meta.x, meta.y] })
            });
            
            if (!response.ok) return;
            
            const liveState = await response.json();
            const runtime = ensureNodeRuntimeState(selectedNodeId);
            
            // Update runtime interfaces with live data
            if (liveState.interfaces && runtime.interfaces) {
                Object.entries(liveState.interfaces).forEach(([direction, ifaceData]) => {
                    const neighborId = makeNodeId(ifaceData.neighbor);
                    let ifaceRuntime = runtime.interfaces.get(neighborId);
                    
                    if (!ifaceRuntime) {
                        ifaceRuntime = defaultInterfaceRuntime();
                        runtime.interfaces.set(neighborId, ifaceRuntime);
                    }
                    
                    // Update all interface state
                    ifaceRuntime.handshakePins = {
                        req: Boolean(ifaceData.pins?.req),
                        ack: Boolean(ifaceData.pins?.ack),
                        data: Boolean(ifaceData.pins?.data),
                        choke: Boolean(ifaceData.pins?.choke)
                    };
                    
                    ifaceRuntime.statusBits = {
                        busy: Boolean(ifaceData.status_bits?.busy),
                        transfer: Boolean(ifaceData.status_bits?.transfer),
                        receive: Boolean(ifaceData.status_bits?.receive)
                    };
                    
                    ifaceRuntime.sendBuffer = {
                        used: ifaceData.send_buffer?.count || 0,
                        capacity: ifaceData.send_buffer?.capacity || 4,
                        state: (ifaceData.send_buffer?.count || 0) > 0 ? 'primed' : 'idle',
                        head: ifaceData.send_buffer?.packets?.[0] || null
                    };
                    
                    ifaceRuntime.receiveBuffer = {
                        used: ifaceData.receive_buffer?.count || 0,
                        capacity: ifaceData.receive_buffer?.capacity || 4,
                        state: (ifaceData.receive_buffer?.count || 0) > 0 ? 'ready' : 'idle',
                        head: ifaceData.receive_buffer?.packets?.[0] || null
                    };
                    
                    ifaceRuntime.sendRegister = ifaceData.send_register || null;
                    ifaceRuntime.receiveRegister = ifaceData.receive_register || null;
                });
            }
            
            // Update aggregate states
            runtime.sendBuffer = (liveState.send_buffer?.count || 0) > 0 ? 'primed' : 'idle';
            runtime.receiveBuffer = (liveState.receive_buffer?.count || 0) > 0 ? 'ready' : 'idle';
            
            // Re-render the interface section
            renderNodeInterfacesSection(meta, runtime);
            
        } catch (error) {
            console.warn('Failed to fetch live interface state:', error);
        }
    }
    
    // Start live updates
    function startLiveInterfaceUpdates() {
        if (liveUpdateInterval) return;
        liveUpdateInterval = setInterval(fetchAndUpdateInterfaceState, 500);
    }
    
    // Stop live updates
    function stopLiveInterfaceUpdates() {
        if (liveUpdateInterval) {
            clearInterval(liveUpdateInterval);
            liveUpdateInterval = null;
        }
    }
    
    // Hook into animation start/stop
    const originalStartAnimation = window.startAnimation;
    if (originalStartAnimation) {
        window.startAnimation = function(...args) {
            startLiveInterfaceUpdates();
            return originalStartAnimation.apply(this, args);
        };
    }
    
    const originalStopAnimation = window.stopAnimation;
    if (originalStopAnimation) {
        window.stopAnimation = function(...args) {
            stopLiveInterfaceUpdates();
            return originalStopAnimation.apply(this, args);
        };
    }
    
    // Hook into node panel open/close
    const originalOpenNodePanel = window.openNodePanel;
    if (originalOpenNodePanel) {
        window.openNodePanel = function(...args) {
            const result = originalOpenNodePanel.apply(this, args);
            if (animationState) {
                startLiveInterfaceUpdates();
            }
            return result;
        };
    }
    
    const originalCloseNodePanel = window.closeNodePanel;
    if (originalCloseNodePanel) {
        window.closeNodePanel = function(...args) {
            stopLiveInterfaceUpdates();
            return originalCloseNodePanel.apply(this, args);
        };
    }
    
    // Export functions
    window.startLiveInterfaceUpdates = startLiveInterfaceUpdates;
    window.stopLiveInterfaceUpdates = stopLiveInterfaceUpdates;
    window.fetchAndUpdateInterfaceState = fetchAndUpdateInterfaceState;
})();
