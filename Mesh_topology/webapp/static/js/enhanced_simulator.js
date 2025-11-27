/**
 * Enhanced Mesh Topology NoC Simulator - Frontend
 * Implements interactive visualization with packet animation and interface monitoring
 */

// Global State
let canvas, ctx;
let topology = null;
let selectedSource = null;
let selectedDestinations = [];
let transferType = '1:1';
let scale = 1;
let offsetX = 0;
let offsetY = 0;
let isDragging = false;
let lastMouseX = 0;
let lastMouseY = 0;
let completedPath = []; // Track nodes in completed path for green coloring
let selectedNodeForInternal = null;  // Track selected node for internal view
let internalViewUpdateInterval = null;  // Interval for updating internal view

// Constants
const NODE_RADIUS = 25;
const NODE_SIZE = 50; // Size for square nodes
const NODE_SPACING = 100;
const PACKET_SIZE = 8;
const ANIMATION_SPEED = 20; // ms per frame

// Colors
const COLORS = {
    node: '#667eea',
    nodeSelected: '#f56565',
    nodeDestination: '#48bb78',
    nodeCompleted: '#90cdf4',
    pathGreen: '#48bb78',  // Green for completed path
    edge: '#cbd5e0',
    edgeActive: '#667eea',
    packet: '#f6ad55',
    signal: '#fc8181',
    background: '#ffffff'
};

// Initialize on page load
window.addEventListener('load', () => {
    canvas = document.getElementById('topology-canvas');
    ctx = canvas.getContext('2d');
    
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);
    
    // Setup canvas event listeners
    canvas.addEventListener('mousedown', handleMouseDown);
    canvas.addEventListener('mousemove', handleMouseMove);
    canvas.addEventListener('mouseup', handleMouseUp);
    canvas.addEventListener('wheel', handleWheel);
    canvas.addEventListener('click', handleCanvasClick);
    
    // Setup transfer type listeners
    document.getElementById('transfer1to1').addEventListener('change', handleTransferTypeChange);
    document.getElementById('transfer1toM').addEventListener('change', handleTransferTypeChange);
    
    // Initialize default topology
    initTopology();
});

function resizeCanvas() {
    const container = document.getElementById('canvas-container');
    canvas.width = container.clientWidth;
    canvas.height = container.clientHeight;
    drawTopology();
}

// =========================
// Topology Management
// =========================

async function initTopology() {
    const width = parseInt(document.getElementById('gridWidth').value);
    const height = parseInt(document.getElementById('gridHeight').value);
    
    showLoading(true);
    
    try {
        const response = await fetch('/api/init', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ width, height })
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            topology = data.topology_data;
            resetSelection();
            drawTopology();
            updateStats();
        } else {
            alert('Error: ' + data.message);
        }
    } catch (error) {
        console.error('Error initializing topology:', error);
        alert('Failed to initialize topology');
    } finally {
        showLoading(false);
    }
}

// =========================
// Drawing Functions
// =========================

function drawTopology() {
    if (!topology) return;
    
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.save();
    
    // Apply transformations
    ctx.translate(offsetX, offsetY);
    ctx.scale(scale, scale);
    
    // Center the topology
    const centerX = canvas.width / (2 * scale) - offsetX / scale;
    const centerY = canvas.height / (2 * scale) - offsetY / scale;
    const gridWidth = (topology.width - 1) * NODE_SPACING;
    const gridHeight = (topology.height - 1) * NODE_SPACING;
    const startX = centerX - gridWidth / 2;
    const startY = centerY - gridHeight / 2;
    
    // Draw edges
    topology.edges.forEach(edge => {
        const from = edge.from;
        const to = edge.to;
        const fromPos = getNodePosition(from, startX, startY);
        const toPos = getNodePosition(to, startX, startY);
        
        ctx.strokeStyle = COLORS.edge;
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(fromPos.x, fromPos.y);
        ctx.lineTo(toPos.x, toPos.y);
        ctx.stroke();
    });
    
    // Draw nodes
    topology.nodes.forEach(node => {
        const pos = getNodePosition(node.address, startX, startY);
        drawNode(node, pos);
    });
    
    ctx.restore();
}

function drawNode(node, pos) {
    const addr = node.address;
    
    // Determine node color
    let fillColor = COLORS.node;
    if (selectedSource && addr[0] === selectedSource[0] && addr[1] === selectedSource[1]) {
        fillColor = COLORS.nodeSelected;
    } else if (selectedDestinations.some(d => d[0] === addr[0] && d[1] === addr[1])) {
        fillColor = COLORS.nodeDestination;
    } else if (completedPath.some(p => p[0] === addr[0] && p[1] === addr[1])) {
        fillColor = COLORS.pathGreen; // Green for completed path nodes
    }
    
    // Draw square node
    const halfSize = NODE_SIZE / 2;
    ctx.fillStyle = fillColor;
    ctx.strokeStyle = '#333';
    ctx.lineWidth = 2;
    ctx.fillRect(pos.x - halfSize, pos.y - halfSize, NODE_SIZE, NODE_SIZE);
    ctx.strokeRect(pos.x - halfSize, pos.y - halfSize, NODE_SIZE, NODE_SIZE);
    
    // Draw address label
    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 12px Arial';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(`(${addr[0]},${addr[1]})`, pos.x, pos.y);
    
    // Draw interface count
    ctx.fillStyle = '#ffffff';
    ctx.font = '9px Arial';
    ctx.fillText(`${node.num_interfaces} if`, pos.x, pos.y + 15);
}

function getNodePosition(address, startX, startY) {
    return {
        x: startX + address[0] * NODE_SPACING,
        y: startY + address[1] * NODE_SPACING
    };
}

// =========================
// User Interaction
// =========================

function handleCanvasClick(e) {
    if (!topology) return;
    
    const rect = canvas.getBoundingClientRect();
    const mouseX = (e.clientX - rect.left - offsetX) / scale;
    const mouseY = (e.clientY - rect.top - offsetY) / scale;
    
    const centerX = canvas.width / (2 * scale) - offsetX / scale;
    const centerY = canvas.height / (2 * scale) - offsetY / scale;
    const gridWidth = (topology.width - 1) * NODE_SPACING;
    const gridHeight = (topology.height - 1) * NODE_SPACING;
    const startX = centerX - gridWidth / 2;
    const startY = centerY - gridHeight / 2;
    
    // Check if clicked on a node
    for (const node of topology.nodes) {
        const pos = getNodePosition(node.address, startX, startY);
        const halfSize = NODE_SIZE / 2;
        
        // Check if click is within square bounds
        if (mouseX >= pos.x - halfSize && mouseX <= pos.x + halfSize &&
            mouseY >= pos.y - halfSize && mouseY <= pos.y + halfSize) {
            handleNodeClick(node.address);
            // Also update internal view
            showNodeInternal(node.address);
            return;
        }
    }
}

function handleNodeClick(address) {
    if (transferType === '1:1') {
        // 1:1 mode - select source then destination
        if (!selectedSource) {
            selectedSource = address;
            document.getElementById('sourceNode').value = `${address[0]},${address[1]}`;
        } else if (!selectedDestinations.length) {
            if (address[0] === selectedSource[0] && address[1] === selectedSource[1]) {
                alert('Source and destination cannot be the same');
                return;
            }
            selectedDestinations = [address];
            document.getElementById('destNode').value = `${address[0]},${address[1]}`;
            document.getElementById('startBtn').disabled = false;
        } else {
            // Reset and start over
            resetSelection();
            selectedSource = address;
            document.getElementById('sourceNode').value = `${address[0]},${address[1]}`;
        }
    } else {
        // 1:M mode - select source then multiple destinations
        if (!selectedSource) {
            selectedSource = address;
            document.getElementById('sourceNode').value = `${address[0]},${address[1]}`;
            updateDestinationList();
        } else {
            if (address[0] === selectedSource[0] && address[1] === selectedSource[1]) {
                alert('Source cannot be a destination');
                return;
            }
            
            // Toggle destination
            const index = selectedDestinations.findIndex(d => d[0] === address[0] && d[1] === address[1]);
            if (index >= 0) {
                selectedDestinations.splice(index, 1);
            } else {
                selectedDestinations.push(address);
            }
            
            updateDestinationList();
            document.getElementById('startBtn').disabled = selectedDestinations.length === 0;
        }
    }
    
    drawTopology();
}

function updateDestinationList() {
    const list = document.getElementById('destList');
    
    if (selectedDestinations.length === 0) {
        list.innerHTML = '<em style="color: #999;">No destinations selected</em>';
    } else {
        list.innerHTML = selectedDestinations.map((dest, i) => `
            <div class="destination-item">
                <span>(${dest[0]}, ${dest[1]})</span>
                <button onclick="removeDestination(${i})">Remove</button>
            </div>
        `).join('');
    }
}

function removeDestination(index) {
    selectedDestinations.splice(index, 1);
    updateDestinationList();
    drawTopology();
    document.getElementById('startBtn').disabled = selectedDestinations.length === 0;
}

function handleTransferTypeChange() {
    transferType = document.querySelector('input[name="transferType"]:checked').value;
    
    if (transferType === '1:1') {
        document.getElementById('singleDestGroup').style.display = 'block';
        document.getElementById('multiDestGroup').style.display = 'none';
    } else {
        document.getElementById('singleDestGroup').style.display = 'none';
        document.getElementById('multiDestGroup').style.display = 'block';
    }
    
    resetSelection();
}

function resetSelection() {
    selectedSource = null;
    selectedDestinations = [];
    completedPath = []; // Clear completed path
    document.getElementById('sourceNode').value = '';
    document.getElementById('destNode').value = '';
    document.getElementById('startBtn').disabled = true;
    updateDestinationList();
    drawTopology();
}

// =========================
// Simulation
// =========================

async function startSimulation() {
    if (!selectedSource || selectedDestinations.length === 0) {
        alert('Please select source and destination(s)');
        return;
    }
    
    const packetData = document.getElementById('packetData').value || 'Test Data';
    
    // Clear previous completed path
    completedPath = [];
    
    // Don't show loading during animation
    
    try {
        if (transferType === '1:1') {
            await simulateSingleTransfer(selectedSource, selectedDestinations[0], packetData);
        } else {
            await simulateMulticast(selectedSource, selectedDestinations, packetData);
        }
    } catch (error) {
        console.error('Simulation error:', error);
        alert('Simulation failed: ' + error.message);
    }
}

async function simulateSingleTransfer(source, destination, data) {
    const response = await fetch('/api/simulate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ source, destination, data })
    });
    
    const result = await response.json();
    
    if (result.status === 'success') {
        await animateTransfer(result.simulation);
        // Keep live panel visible for 1 second before showing final results
        await delay(1000);
        closeLiveResults();
        showResults([result.simulation]);
        updateStats();
    } else {
        throw new Error(result.message);
    }
}

async function simulateMulticast(source, destinations, data) {
    const response = await fetch('/api/multicast', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ source, destinations, data })
    });
    
    const result = await response.json();
    
    if (result.status === 'success') {
        // Animate each destination sequentially
        for (const destResult of result.multicast.results) {
            if (destResult.status === 'success') {
                await animatePath(destResult.path);
                await delay(1000); // 1 second delay between destinations
            }
        }
        
        showMulticastResults(result.multicast);
        updateStats();
    } else {
        throw new Error(result.message);
    }
}

async function animateTransfer(simulation) {
    const path = simulation.path;
    // Show live results panel
    showLiveResults(simulation);
    await animatePath(path, simulation);
}

async function animatePath(path, simulation) {
    // Animate packet moving along path
    for (let i = 0; i < path.length - 1; i++) {
        const from = path[i];
        const to = path[i + 1];
        // Update live display before each hop
        updateLiveProgress(i + 1, path.length, path, i + 1);
        await animatePacketHop(from, to);
    }
}

async function animatePacketHop(from, to, showHandshake = true) {
    const centerX = canvas.width / (2 * scale) - offsetX / scale;
    const centerY = canvas.height / (2 * scale) - offsetY / scale;
    const gridWidth = (topology.width - 1) * NODE_SPACING;
    const gridHeight = (topology.height - 1) * NODE_SPACING;
    const startX = centerX - gridWidth / 2;
    const startY = centerY - gridHeight / 2;
    
    const fromPos = getNodePosition(from, startX, startY);
    const toPos = getNodePosition(to, startX, startY);
    
    // Calculate midpoint for signal
    const midX = (fromPos.x + toPos.x) / 2;
    const midY = (fromPos.y + toPos.y) / 2;
    
    // Single signal for REQ-ACK-DATA transfer
    if (showHandshake) {
        // Phase 1: REQ signal travels from source to destination
        const reqSteps = 15;
        for (let step = 0; step <= reqSteps; step++) {
            const progress = step / reqSteps;
            const signalX = fromPos.x + (toPos.x - fromPos.x) * progress;
            const signalY = fromPos.y + (toPos.y - fromPos.y) * progress;
            
            drawTopology();
            ctx.save();
            ctx.translate(offsetX, offsetY);
            ctx.scale(scale, scale);
            
            // Draw REQ signal (small red circle)
            ctx.fillStyle = '#ff4444';
            ctx.beginPath();
            ctx.arc(signalX, signalY, 6, 0, 2 * Math.PI);
            ctx.fill();
            
            // Label
            ctx.fillStyle = '#ff4444';
            ctx.font = 'bold 10px Arial';
            ctx.textAlign = 'center';
            ctx.fillText('REQ', signalX, signalY - 12);
            
            ctx.restore();
            await delay(30);
        }
        
        // Small pause to check buffer/destination
        await delay(100);
        
        // Phase 2: ACK signal travels back from destination to source
        const ackSteps = 15;
        for (let step = 0; step <= ackSteps; step++) {
            const progress = step / ackSteps;
            const signalX = toPos.x + (fromPos.x - toPos.x) * progress;
            const signalY = toPos.y + (fromPos.y - toPos.y) * progress;
            
            drawTopology();
            ctx.save();
            ctx.translate(offsetX, offsetY);
            ctx.scale(scale, scale);
            
            // Draw ACK signal (small green circle)
            ctx.fillStyle = '#44ff44';
            ctx.beginPath();
            ctx.arc(signalX, signalY, 6, 0, 2 * Math.PI);
            ctx.fill();
            
            // Label
            ctx.fillStyle = '#44ff44';
            ctx.font = 'bold 10px Arial';
            ctx.textAlign = 'center';
            ctx.fillText('ACK', signalX, signalY - 12);
            
            ctx.restore();
            await delay(30);
        }
    }
    
    // Phase 3: DATA packet transfer
    const steps = 30;
    for (let step = 0; step <= steps; step++) {
        const progress = step / steps;
        const x = fromPos.x + (toPos.x - fromPos.x) * progress;
        const y = fromPos.y + (toPos.y - fromPos.y) * progress;
        
        drawTopology();
        
        ctx.save();
        ctx.translate(offsetX, offsetY);
        ctx.scale(scale, scale);
        
        // Draw DATA packet (orange circle)
        ctx.fillStyle = COLORS.packet;
        ctx.beginPath();
        ctx.arc(x, y, PACKET_SIZE, 0, 2 * Math.PI);
        ctx.fill();
        
        // Draw "DATA" label near packet
        ctx.fillStyle = '#333';
        ctx.font = 'bold 9px Arial';
        ctx.textAlign = 'center';
        ctx.fillText('DATA', x, y - 12);
        
        ctx.restore();
        
        await delay(ANIMATION_SPEED);
    }
    
    // Mark destination node as completed (green) after packet arrives
    if (!completedPath.some(p => p[0] === to[0] && p[1] === to[1])) {
        completedPath.push(to);
    }
    drawTopology();
}

// =========================
// Results Display
// =========================

function showResults(simulations) {
    const content = document.getElementById('resultsContent');
    
    content.innerHTML = simulations.map((sim, i) => `
        <div class="result-item">
            <h3>Transfer ${i + 1}</h3>
            <p><strong>Packet ID:</strong> ${sim.packet.id}</p>
            <p><strong>Source:</strong> (${sim.packet.source[0]}, ${sim.packet.source[1]})</p>
            <p><strong>Destination:</strong> (${sim.packet.destination[0]}, ${sim.packet.destination[1]})</p>
            <p><strong>Hops:</strong> ${sim.total_hops}</p>
            <p><strong>Path:</strong> ${sim.path.map(p => `(${p[0]},${p[1]})`).join(' → ')}</p>
        </div>
    `).join('');
    
    document.getElementById('resultsModal').style.display = 'flex';
}

function showMulticastResults(multicast) {
    const content = document.getElementById('resultsContent');
    
    content.innerHTML = `
        <div class="result-item">
            <h3>Multicast Transfer Summary</h3>
            <p><strong>Source:</strong> (${multicast.source[0]}, ${multicast.source[1]})</p>
            <p><strong>Total Destinations:</strong> ${multicast.total_destinations}</p>
            <p><strong>Successful:</strong> ${multicast.successful}</p>
        </div>
        ${multicast.results.map((r, i) => `
            <div class="result-item">
                <h3>Destination ${i + 1}: (${r.destination[0]}, ${r.destination[1]})</h3>
                <p><strong>Status:</strong> ${r.status}</p>
                ${r.status === 'success' ? `
                    <p><strong>Hops:</strong> ${r.hops}</p>
                    <p><strong>Path:</strong> ${r.path.map(p => `(${p[0]},${p[1]})`).join(' → ')}</p>
                ` : `
                    <p><strong>Error:</strong> ${r.message}</p>
                `}
            </div>
        `).join('')}
    `;
    
    document.getElementById('resultsModal').style.display = 'flex';
}

function closeResultsModal() {
    document.getElementById('resultsModal').style.display = 'none';
}

// =========================
// Live Results Panel
// =========================

function showLiveResults(simulation) {
    const panel = document.getElementById('liveResultsPanel');
    const packet = simulation.packet;
    const path = simulation.path;
    
    // Update packet info
    document.getElementById('livePacketId').textContent = `Packet ID: ${packet.id}`;
    document.getElementById('liveSource').textContent = `Source: (${packet.source[0]}, ${packet.source[1]})`;
    document.getElementById('liveDest').textContent = `Destination: (${packet.destination[0]}, ${packet.destination[1]})`;
    
    // Initialize path display
    updateLiveProgress(0, path.length, path, 0);
    
    // Show panel with animation
    panel.style.display = 'block';
}

function updateLiveProgress(currentHop, totalHops, path, currentIndex) {
    document.getElementById('liveHops').textContent = `Hops: ${currentHop}/${totalHops - 1}`;
    
    const pathDisplay = document.getElementById('livePathDisplay');
    pathDisplay.innerHTML = '';
    
    for (let i = 0; i < path.length; i++) {
        const node = path[i];
        const nodeSpan = document.createElement('span');
        nodeSpan.className = 'path-node';
        nodeSpan.textContent = `(${node[0]},${node[1]})`;
        
        if (i < currentIndex) {
            nodeSpan.classList.add('completed');
        } else if (i === currentIndex) {
            nodeSpan.classList.add('current');
        }
        
        pathDisplay.appendChild(nodeSpan);
        
        if (i < path.length - 1) {
            const arrow = document.createElement('span');
            arrow.className = 'path-arrow';
            arrow.textContent = '→';
            pathDisplay.appendChild(arrow);
        }
    }
}

function closeLiveResults() {
    document.getElementById('liveResultsPanel').style.display = 'none';
}

// =========================
// Live Results Panel
// =========================

function showLiveResults(simulation) {
    const panel = document.getElementById('liveResultsPanel');
    const packet = simulation.packet;
    const path = simulation.path;
    
    // Update packet info
    document.getElementById('livePacketId').textContent = `Packet ID: ${packet.id}`;
    document.getElementById('liveSource').textContent = `Source: (${packet.source[0]}, ${packet.source[1]})`;
    document.getElementById('liveDest').textContent = `Destination: (${packet.destination[0]}, ${packet.destination[1]})`;
    
    // Initialize path display
    updateLiveProgress(0, path.length, path, 0);
    
    // Show panel
    panel.style.display = 'block';
}

function updateLiveProgress(currentHop, totalHops, path, currentIndex) {
    document.getElementById('liveHops').textContent = `Hops: ${currentHop}/${totalHops - 1}`;
    
    const pathDisplay = document.getElementById('livePathDisplay');
    pathDisplay.innerHTML = '';
    
    for (let i = 0; i < path.length; i++) {
        const node = path[i];
        const nodeSpan = document.createElement('span');
        nodeSpan.className = 'path-node';
        nodeSpan.textContent = `(${node[0]},${node[1]})`;
        
        if (i < currentIndex) {
            nodeSpan.classList.add('completed');
        } else if (i === currentIndex) {
            nodeSpan.classList.add('current');
        }
        
        pathDisplay.appendChild(nodeSpan);
        
        if (i < path.length - 1) {
            const arrow = document.createElement('span');
            arrow.className = 'path-arrow';
            arrow.textContent = '→';
            pathDisplay.appendChild(arrow);
        }
    }
}

function closeLiveResults() {
    document.getElementById('liveResultsPanel').style.display = 'none';
}

// =========================
// Statistics
// =========================

function updateStats() {
    if (!topology) return;
    
    document.getElementById('statNodes').textContent = topology.nodes.length;
    // Other stats would be updated based on simulation results
}

// =========================
// Zoom and Pan
// =========================

function handleMouseDown(e) {
    isDragging = true;
    lastMouseX = e.clientX;
    lastMouseY = e.clientY;
}

function handleMouseMove(e) {
    if (isDragging) {
        const dx = e.clientX - lastMouseX;
        const dy = e.clientY - lastMouseY;
        offsetX += dx;
        offsetY += dy;
        lastMouseX = e.clientX;
        lastMouseY = e.clientY;
        drawTopology();
    }
}

function handleMouseUp() {
    isDragging = false;
}

function handleWheel(e) {
    e.preventDefault();
    const delta = e.deltaY > 0 ? 0.9 : 1.1;
    scale *= delta;
    scale = Math.max(0.1, Math.min(5, scale)); // Clamp between 0.1 and 5
    drawTopology();
}

function zoomIn() {
    scale *= 1.2;
    scale = Math.min(5, scale);
    drawTopology();
}

function zoomOut() {
    scale *= 0.8;
    scale = Math.max(0.1, scale);
    drawTopology();
}

function resetZoom() {
    scale = 1;
    offsetX = 0;
    offsetY = 0;
    drawTopology();
}

// =========================
// Utilities
// =========================

function showLoading(show) {
    document.getElementById('loadingOverlay').style.display = show ? 'flex' : 'none';
}

function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function resetSimulation() {
    resetSelection();
    resetZoom();
    initTopology();
}

// =========================
// Node Internal View
// =========================

function showNodeInternal(address) {
    selectedNodeForInternal = address;
    const nodeInternal = document.getElementById('nodeInternal');
    const title = document.getElementById('nodeInternalTitle');
    
    title.textContent = `Node (${address[0]},${address[1]}) Internal View`;
    nodeInternal.classList.add('active');
    
    // Clear any existing interval
    if (internalViewUpdateInterval) {
        clearInterval(internalViewUpdateInterval);
    }
    
    // Update immediately
    updateNodeInternal();
    
    // Update every 500ms while displayed
    internalViewUpdateInterval = setInterval(updateNodeInternal, 500);
}

function updateNodeInternal() {
    if (!selectedNodeForInternal || !topology) return;
    
    const address = selectedNodeForInternal;
    const node = topology.nodes.find(n => n.address[0] === address[0] && n.address[1] === address[1]);
    
    if (!node) return;
    
    // Fetch current node state from backend
    fetch('/api/node-state', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ address: address })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            console.error('Error fetching node state:', data.error);
            return;
        }
        
        updateInternalViewUI(data);
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

function updateInternalViewUI(nodeState) {
    // Update Pins
    const pins = ['req', 'ack', 'data', 'clk', 'choke'];
    pins.forEach(pin => {
        const pinEl = document.getElementById(`pin-${pin}`);
        const isActive = nodeState.pins && nodeState.pins[pin];
        pinEl.className = `pin ${isActive ? 'active' : 'inactive'}`;
    });
    
    // Update Registers
    const sendReg = document.getElementById('send-register');
    const receiveReg = document.getElementById('receive-register');
    
    if (nodeState.send_register && nodeState.send_register.packet_id !== null) {
        sendReg.textContent = `Send: Packet ${nodeState.send_register.packet_id}`;
        sendReg.style.background = '#c3dafe';
    } else {
        sendReg.textContent = 'Send Register: Empty';
        sendReg.style.background = 'white';
    }
    
    if (nodeState.receive_register && nodeState.receive_register.packet_id !== null) {
        receiveReg.textContent = `Receive: Packet ${nodeState.receive_register.packet_id}`;
        receiveReg.style.background = '#c3dafe';
    } else {
        receiveReg.textContent = 'Receive Register: Empty';
        receiveReg.style.background = 'white';
    }
    
    // Update Buffers
    const sendBufferCount = nodeState.send_buffer ? nodeState.send_buffer.count : 0;
    const receiveBufferCount = nodeState.receive_buffer ? nodeState.receive_buffer.count : 0;
    const bufferCapacity = nodeState.send_buffer ? nodeState.send_buffer.capacity : 4;
    
    document.getElementById('send-buffer-count').textContent = `${sendBufferCount}/${bufferCapacity}`;
    document.getElementById('receive-buffer-count').textContent = `${receiveBufferCount}/${bufferCapacity}`;
    
    // Visual buffer fill
    const sendBufferVis = document.getElementById('send-buffer-vis');
    const receiveBufferVis = document.getElementById('receive-buffer-vis');
    
    if (sendBufferCount > 0) {
        sendBufferVis.classList.add('filled');
        sendBufferVis.style.opacity = (sendBufferCount / bufferCapacity);
    } else {
        sendBufferVis.classList.remove('filled');
    }
    
    if (receiveBufferCount > 0) {
        receiveBufferVis.classList.add('filled');
        receiveBufferVis.style.opacity = (receiveBufferCount / bufferCapacity);
    } else {
        receiveBufferVis.classList.remove('filled');
    }
    
    // Update Status Bits
    const receiveBit = document.getElementById('bit-receive');
    const transferBit = document.getElementById('bit-transfer');
    const busyBit = document.getElementById('bit-busy');
    
    receiveBit.className = `indicator ${nodeState.receive_bit ? 'on' : 'off'}`;
    transferBit.className = `indicator ${nodeState.transfer_bit ? 'on' : 'off'}`;
    busyBit.className = `indicator ${nodeState.busy_bit ? 'on' : 'off'}`;
}

function hideNodeInternal() {
    const nodeInternal = document.getElementById('nodeInternal');
    nodeInternal.classList.remove('active');
    selectedNodeForInternal = null;
    
    if (internalViewUpdateInterval) {
        clearInterval(internalViewUpdateInterval);
        internalViewUpdateInterval = null;
    }
}
