/* global window requestAnimationFrame cancelAnimationFrame fetch */

const canvas = document.getElementById('networkCanvas');
const ctx = canvas.getContext('2d');
const hudStatus = document.getElementById('hudStatus');

const sourceSelect = document.getElementById('sourceSelect');
const destinationSelect = document.getElementById('destinationSelect');
const flowLog = document.getElementById('flowLog');
const speedControl = document.getElementById('speedControl');
const summary = document.getElementById('routeSummary');
const pickSourceBtn = document.getElementById('pickSourceBtn');
const pickDestinationBtn = document.getElementById('pickDestinationBtn');

const applyTopologyBtn = document.getElementById('applyTopologyBtn');
const levelInput = document.getElementById('levelInput');
const simulateBtn = document.getElementById('simulateBtn');
const animateBtn = document.getElementById('animateBtn');
const resetBtn = document.getElementById('resetBtn');

const zoomInBtn = document.getElementById('zoomInBtn');
const zoomOutBtn = document.getElementById('zoomOutBtn');
const resetViewBtn = document.getElementById('resetViewBtn');
const cursorModeBtn = document.getElementById('cursorModeBtn');
const sidebarToggle = document.getElementById('sidebarToggle');
const sidebarCloseBtn = document.getElementById('sidebarClose');
const sidebarOverlay = document.getElementById('sidebarOverlay');
const layoutSidebar = document.getElementById('layoutSidebar');
const nodePanel = document.getElementById('nodeDetailsPanel');
const nodePanelClose = document.getElementById('nodePanelClose');
const nodePanelScrim = document.getElementById('nodePanelScrim');
const nodePanelTitle = document.getElementById('nodePanelTitle');
const nodePanelSubhead = document.getElementById('nodePanelSubhead');
const nodePanelRing = document.getElementById('nodePanelRing');
const nodePanelDegree = document.getElementById('nodePanelDegree');
const nodePanelRoutes = document.getElementById('nodePanelRoutes');
const nodePanelNeighbors = document.getElementById('nodePanelNeighbors');
const nodePanelSendBuffer = document.getElementById('nodePanelSendBuffer');
const nodePanelReceiveBuffer = document.getElementById('nodePanelReceiveBuffer');
const nodePanelAppBuffer = document.getElementById('nodePanelAppBuffer');
const nodePanelHandshake = document.getElementById('nodePanelHandshake');
const autoNodeDetailsBtn = document.getElementById('autoNodeDetailsBtn');
const phaseTimelineSteps = Array.from(document.querySelectorAll('[data-phase]'));

const statusElements = {
    hopValue: document.getElementById('statusHopValue'),
    hopNodes: document.getElementById('statusHopNodes'),
    phaseValue: document.getElementById('statusPhaseValue'),
    signalValue: document.getElementById('statusSignalValue'),
    routeValue: document.getElementById('statusRouteValue'),
    transferValue: document.getElementById('statusTransferValue'),
    progressPercent: document.getElementById('statusProgressPercent'),
    progressFill: document.getElementById('statusProgressFill'),
    timerValue: document.getElementById('statusTimerValue'),
};

const signalChips = {
    req: document.querySelector('[data-signal="req"]'),
    ack: document.querySelector('[data-signal="ack"]'),
    data: document.querySelector('[data-signal="data"]'),
};

const colors = {
    tree: 'rgba(82, 80, 80, 0.35)',
    treeHighlight: '#38bdf8',
    ringHighlight: '#38bdf8',
    previewTree: 'rgba(56, 189, 248, 0.45)',
    previewRing: 'rgba(56, 189, 248, 0.45)',
    node: '#1d4ed8',
    nodeHighlight: '#22d3ee',
    nodeSelected: '#f97316',
    sourceNode: '#16a34a',
    destinationNode: '#7c3aed',
    sharedNode: '#0ea5e9',
    phaseReq: '#f59e0b',
    phaseAck: '#6366f1',
    phaseData: '#22c55e',
    phaseRelease: '#0ea5e9',
    text: '#0f172a',
};

const STAGE_INDICATOR_COLORS = {
    ready: colors.nodeSelected,
    req: colors.phaseReq,
    ack: colors.phaseAck,
    data: colors.phaseData,
    release: colors.phaseRelease,
};

const viewState = {
    zoom: 1,
    panX: 0,
    panY: 0,
};

const PHASE_RANGES = {
    ready: [0, 0.2],
    req: [0.2, 0.4],
    ack: [0.4, 0.6],
    data: [0.6, 0.85],
    release: [0.85, 1],
};

const ZOOM_LIMITS = { min: 0.4, max: 3.2 };

let canvasScale = window.devicePixelRatio || 1;
let topologyData = null;
let layoutCache = null;
let animationState = null;
let animationFrame = null;
let flowCardElements = [];
let currentRouteInfo = null;
let speedMultiplier = parseFloat(speedControl.value) || 0.6;
const nodeMeta = new Map();
const nodeRuntimeState = new Map();
const nodePositions = new Map();
let selectedNodeId = null;
let scrollZoomEnabled = false;
let panMoved = false;
let nodePanelAutoTracking = false;
let autoNodeDetailsPreference = false;
let routePreview = null;
let lastRoutePayload = null;
let pickMode = null;
let currentSourceId = null;
let currentDestinationId = null;

const PHASE_SEQUENCE = ['ready', 'req', 'ack', 'data', 'release'];

const BUFFER_STATE_LABELS = {
    idle: 'Idle',
    primed: 'Primed',
    waiting: 'Awaiting ACK',
    transferring: 'In transfer',
    receiving: 'Receiving',
    delivered: 'Delivered',
    ready: 'Buffered',
    releasing: 'Releasing',
};

function levelToRingCount(numLevels) {
    const safeLevels = Number.isFinite(numLevels) ? numLevels : 0;
    return Math.max(1, safeLevels - 1);
}

function ringCountToLevels(ringCount) {
    const safeRings = Number.isFinite(ringCount) ? ringCount : 1;
    return Math.trunc(safeRings) + 1;
}

function makeNodeId(node) {
    return `${node.ring}-${node.index}`;
}

function defaultNodeRuntimeState() {
    return {
        sendBuffer: 'idle',
        receiveBuffer: 'idle',
        applicationBuffer: 0,
        handshake: 'idle',
        lastUpdated: 0,
    };
}

function ensureNodeRuntimeState(nodeId) {
    if (!nodeRuntimeState.has(nodeId)) {
        nodeRuntimeState.set(nodeId, defaultNodeRuntimeState());
    }
    return nodeRuntimeState.get(nodeId);
}

function resetAllNodeRuntimeState() {
    nodeRuntimeState.forEach((state) => {
        state.sendBuffer = 'idle';
        state.receiveBuffer = 'idle';
        state.applicationBuffer = 0;
        state.handshake = 'idle';
        state.lastUpdated = 0;
    });
}

function clamp(value, min, max) {
    return Math.max(min, Math.min(max, value));
}

function normalizeRange(value, start, end) {
    if (end <= start) {
        return 0;
    }
    return clamp((value - start) / (end - start), 0, 1);
}

function syncSelectionState() {
    currentSourceId = sourceSelect ? sourceSelect.value || null : null;
    currentDestinationId = destinationSelect ? destinationSelect.value || null : null;
}

function setPickMode(mode) {
    const normalized = mode === 'source' || mode === 'destination' ? mode : null;
    pickMode = normalized;
    if (pickSourceBtn) {
        const active = normalized === 'source';
        pickSourceBtn.setAttribute('aria-pressed', active ? 'true' : 'false');
        pickSourceBtn.classList.toggle('is-active', active);
    }
    if (pickDestinationBtn) {
        const active = normalized === 'destination';
        pickDestinationBtn.setAttribute('aria-pressed', active ? 'true' : 'false');
        pickDestinationBtn.classList.toggle('is-active', active);
    }
    if (canvas) {
        canvas.classList.toggle('is-picking', Boolean(normalized));
    }
    if (normalized && hudStatus) {
        hudStatus.textContent = normalized === 'source'
            ? 'Click a node to choose the source.'
            : 'Click a node to choose the destination.';
    }
}

function setSelectValue(select, nodeId) {
    if (!select || !nodeId) {
        return false;
    }
    const option = select.querySelector(`option[value="${nodeId}"]`);
    if (!option) {
        return false;
    }
    if (select.value !== nodeId) {
        select.value = nodeId;
    }
    return true;
}

function syncAutoNodeDetailsControl() {
    if (!autoNodeDetailsBtn) return;
    const preferred = autoNodeDetailsPreference;
    const active = nodePanelAutoTracking;
    autoNodeDetailsBtn.classList.toggle('is-active', preferred);
    autoNodeDetailsBtn.setAttribute('aria-pressed', preferred ? 'true' : 'false');
    const stateLabel = autoNodeDetailsBtn.querySelector('.control-toggle__state');
    if (stateLabel) {
        if (!preferred) {
            stateLabel.textContent = 'Off';
        } else if (preferred && !active) {
            stateLabel.textContent = 'Paused';
        } else {
            stateLabel.textContent = 'On';
        }
    }
}

function setNodePanelAutoTracking(enabled, { persist = false, preferredValue } = {}) {
    nodePanelAutoTracking = Boolean(enabled);
    if (persist) {
        autoNodeDetailsPreference = typeof preferredValue === 'boolean'
            ? preferredValue
            : nodePanelAutoTracking;
    }
    syncAutoNodeDetailsControl();
    if (nodePanelAutoTracking && selectedNodeId) {
        openNodePanel();
        updateNodePanelContent();
    }
}

function applySignalState(states = {}) {
    const merged = {
        req: 'idle',
        ack: 'idle',
        data: 'idle',
        ...states,
    };

    Object.entries(signalChips).forEach(([key, element]) => {
        if (!element) return;
        element.classList.remove('is-active', 'is-sleep');
        const state = merged[key];
        if (state === 'active') {
            element.classList.add('is-active');
        } else if (state === 'sleep') {
            element.classList.add('is-sleep');
        }
        const labelPrefix = key.toUpperCase();
        const labelState = state === 'active' ? 'active' : 'idle';
        element.setAttribute('aria-label', `${labelPrefix} signal ${labelState}`);
    });
}

function updatePhaseTimeline(phaseKey) {
    if (!phaseTimelineSteps.length) return;
    phaseTimelineSteps.forEach((step) => {
        step.classList.remove('is-current', 'is-complete');
    });

    if (!phaseKey) {
        return;
    }

    if (phaseKey === 'completed') {
        phaseTimelineSteps.forEach((step) => {
            step.classList.add('is-complete');
        });
        return;
    }

    const currentIndex = PHASE_SEQUENCE.indexOf(phaseKey);
    if (currentIndex === -1) {
        return;
    }

    phaseTimelineSteps.forEach((step) => {
        const stepKey = step.dataset.phase;
        const stepIndex = PHASE_SEQUENCE.indexOf(stepKey);
        if (stepIndex === -1) return;
        if (stepIndex < currentIndex) {
            step.classList.add('is-complete');
        } else if (stepIndex === currentIndex) {
            step.classList.add('is-current');
        }
    });
}

function isMobileSidebar() {
    return window.innerWidth <= 1024;
}

function isNodePanelOverlayMode() {
    return true; // Node panel always overlays on the left side
}

function isSidebarVisible() {
    return layoutSidebar ? layoutSidebar.classList.contains('is-visible') : false;
}

function openSidebar() {
    if (!layoutSidebar || !isMobileSidebar()) return;
    layoutSidebar.classList.add('is-visible');
    if (sidebarOverlay) {
        sidebarOverlay.classList.add('is-active');
        sidebarOverlay.setAttribute('aria-hidden', 'false');
    }
    document.body.classList.add('sidebar-open');
    if (sidebarToggle) {
        sidebarToggle.setAttribute('aria-expanded', 'true');
    }
}

function closeSidebar(event) {
    if (event) {
        event.preventDefault();
    }
    if (!layoutSidebar) return;
    layoutSidebar.classList.remove('is-visible');
    document.body.classList.remove('sidebar-open');
    if (sidebarOverlay) {
        sidebarOverlay.classList.remove('is-active');
        sidebarOverlay.setAttribute('aria-hidden', 'true');
    }
    if (sidebarToggle) {
        sidebarToggle.setAttribute('aria-expanded', 'false');
    }
}

function toggleSidebar(event) {
    if (event) {
        event.preventDefault();
    }
    if (isSidebarVisible()) {
        closeSidebar();
    } else {
        openSidebar();
    }
}

function syncSidebarForViewport() {
    if (!layoutSidebar) return;
    if (!isMobileSidebar()) {
        layoutSidebar.classList.remove('is-visible');
        document.body.classList.remove('sidebar-open');
        if (sidebarOverlay) {
            sidebarOverlay.classList.remove('is-active');
            sidebarOverlay.setAttribute('aria-hidden', 'true');
        }
        if (sidebarToggle) {
            sidebarToggle.setAttribute('aria-expanded', 'false');
        }
        return;
    }

    if (!isSidebarVisible()) {
        if (sidebarOverlay) {
            sidebarOverlay.classList.remove('is-active');
            sidebarOverlay.setAttribute('aria-hidden', 'true');
        }
        document.body.classList.remove('sidebar-open');
        if (sidebarToggle) {
            sidebarToggle.setAttribute('aria-expanded', 'false');
        }
    }
}

function syncNodePanelMode() {
    if (!nodePanel) return;
    // Node panel always starts hidden in overlay mode
    nodePanel.classList.remove('is-visible');
    nodePanel.setAttribute('aria-hidden', 'true');
    if (nodePanelScrim) {
        nodePanelScrim.classList.remove('is-active');
        nodePanelScrim.setAttribute('aria-hidden', 'true');
    }
    document.body.classList.remove('node-panel-open');
}

function updateBufferChip(element, state, textOverride) {
    if (!element) return;
    const label = BUFFER_STATE_LABELS[state] || textOverride || state || 'Idle';
    element.dataset.state = state || 'idle';
    element.textContent = textOverride || label;
}

function openNodePanel() {
    if (!nodePanel) return;
    nodePanel.classList.add('is-visible');
    nodePanel.setAttribute('aria-hidden', 'false');
    if (isNodePanelOverlayMode()) {
        if (nodePanelScrim) {
            nodePanelScrim.classList.add('is-active');
            nodePanelScrim.setAttribute('aria-hidden', 'false');
        }
        document.body.classList.add('node-panel-open');
    } else if (nodePanelScrim) {
        nodePanelScrim.classList.remove('is-active');
        nodePanelScrim.setAttribute('aria-hidden', 'true');
        document.body.classList.remove('node-panel-open');
    }
}

function closeNodePanel() {
    if (!nodePanel) return;
    if (!isNodePanelOverlayMode()) {
        const hadSelection = Boolean(selectedNodeId);
        selectedNodeId = null;
        resetNodePanelContent();
        if (hadSelection) {
            renderTopology();
        }
        return;
    }

    const wasVisible = nodePanel.classList.contains('is-visible');
    nodePanel.classList.remove('is-visible');
    nodePanel.setAttribute('aria-hidden', 'true');
    if (nodePanelScrim) {
        nodePanelScrim.classList.remove('is-active');
        nodePanelScrim.setAttribute('aria-hidden', 'true');
    }
    document.body.classList.remove('node-panel-open');
    const hadSelection = Boolean(selectedNodeId);
    selectedNodeId = null;
    resetNodePanelContent();
    if (wasVisible && hadSelection) {
        renderTopology();
    }
}

function isNodePanelOpen() {
    if (!nodePanel) return false;
    if (!isNodePanelOverlayMode()) {
        return true;
    }
    return nodePanel.classList.contains('is-visible');
}

function updateNodePanelContent() {
    if (!selectedNodeId || !nodePanel) return;
    const meta = nodeMeta.get(selectedNodeId);
    const runtime = ensureNodeRuntimeState(selectedNodeId);
    if (!meta) return;

    nodePanelTitle.textContent = `(${meta.ring}, ${meta.index})`;
    nodePanelSubhead.textContent = meta.ring === 0 ? 'Root controller node' : `Ring ${meta.ring} core`;
    nodePanelRing.textContent = `${meta.ring}`;
    nodePanelDegree.textContent = `${meta.degree ?? 0}`;
    const routingCount = Array.isArray(meta.routingTable) ? meta.routingTable.length : 0;
    nodePanelRoutes.textContent = routingCount ? `${routingCount}` : '0';

    if (nodePanelNeighbors) {
        nodePanelNeighbors.innerHTML = '';
        if (Array.isArray(meta.neighbors) && meta.neighbors.length) {
            meta.neighbors
                .slice()
                .sort((a, b) => makeNodeId(a).localeCompare(makeNodeId(b)))
                .forEach((neighbor) => {
                    const item = document.createElement('li');
                    const label = document.createElement('span');
                    label.textContent = `(${neighbor.ring}, ${neighbor.index})`;
                    const type = document.createElement('span');
                    const sendCap = Number.isFinite(neighbor.sendCapacity)
                        ? neighbor.sendCapacity
                        : '–';
                    const recvCap = Number.isFinite(neighbor.receiveCapacity)
                        ? neighbor.receiveCapacity
                        : '–';
                    const typeLabel = neighbor.type === 'ring' ? 'RING' : 'TREE';
                    type.textContent = `${typeLabel} · S:${sendCap} R:${recvCap}`;
                    item.appendChild(label);
                    item.appendChild(type);
                    nodePanelNeighbors.appendChild(item);
                });
        } else {
            const empty = document.createElement('li');
            const label = document.createElement('span');
            label.textContent = 'No active links';
            const type = document.createElement('span');
            type.textContent = '—';
            empty.appendChild(label);
            empty.appendChild(type);
            nodePanelNeighbors.appendChild(empty);
        }
    }

    updateBufferChip(nodePanelSendBuffer, runtime.sendBuffer);
    updateBufferChip(nodePanelReceiveBuffer, runtime.receiveBuffer);
    const appState = runtime.applicationBuffer > 0 ? 'ready' : 'idle';
    updateBufferChip(
        nodePanelAppBuffer,
        appState,
        `${runtime.applicationBuffer} ${runtime.applicationBuffer === 1 ? 'packet' : 'packets'}`,
    );
    updateBufferChip(nodePanelHandshake, runtime.handshake);
}

function resetNodePanelContent() {
    if (!nodePanel) return;
    nodePanelTitle.textContent = 'No node selected';
    nodePanelSubhead.textContent = 'Select a node to inspect';
    nodePanelRing.textContent = '—';
    nodePanelDegree.textContent = '—';
    nodePanelRoutes.textContent = '—';
    if (nodePanelNeighbors) {
        nodePanelNeighbors.innerHTML = '';
    }
    updateBufferChip(nodePanelSendBuffer, 'idle');
    updateBufferChip(nodePanelReceiveBuffer, 'idle');
    updateBufferChip(nodePanelAppBuffer, 'idle', '0 packets');
    updateBufferChip(nodePanelHandshake, 'idle');
}

function focusNode(nodeId, { auto = false, openPanelOnFocus = true } = {}) {
    if (!nodeId) return;
    selectedNodeId = nodeId;
    ensureNodeRuntimeState(nodeId);
    const shouldOpen = openPanelOnFocus && (nodePanelAutoTracking || !auto);
    if (shouldOpen || isNodePanelOpen()) {
        updateNodePanelContent();
    }
    if (shouldOpen) {
        openNodePanel();
    }
    if (!auto) {
        setNodePanelAutoTracking(false);
    }
}

function selectNode(nodeId) {
    focusNode(nodeId, { openPanelOnFocus: true });
    renderTopology();
}

function handleCanvasNodeClick(nodeId) {
    if (!nodeId) return;
    if (pickMode === 'source') {
        const meta = nodeMeta.get(nodeId) || parseSelectValue(nodeId);
        if (setSelectValue(sourceSelect, nodeId)) {
            handleSourceSelectChange({
                announce: true,
                message: `Source set to ${nodeLabel(meta)} via canvas.`,
            });
        } else {
            selectNode(nodeId);
        }
        setPickMode(null);
        return;
    }
    if (pickMode === 'destination') {
        const meta = nodeMeta.get(nodeId) || parseSelectValue(nodeId);
        if (setSelectValue(destinationSelect, nodeId)) {
            handleDestinationSelectChange({
                announce: true,
                message: `Destination set to ${nodeLabel(meta)} via canvas.`,
            });
        } else {
            selectNode(nodeId);
        }
        setPickMode(null);
        return;
    }
    selectNode(nodeId);
}

function resizeCanvas() {
    const rect = canvas.getBoundingClientRect();
    canvasScale = window.devicePixelRatio || 1;
    canvas.width = rect.width * canvasScale;
    canvas.height = rect.height * canvasScale;
    ctx.setTransform(canvasScale, 0, 0, canvasScale, 0, 0);
    renderTopology();
    syncSidebarForViewport();
    syncNodePanelMode();
}

window.addEventListener('resize', resizeCanvas);

function computeLayout(rect, numLevels) {
    const centerX = rect.width / 2;
    const centerY = rect.height / 2;
    const maxRadius = Math.min(rect.width, rect.height) * 0.45;
    const ringSpacing = numLevels > 1 ? maxRadius / (numLevels - 1) : maxRadius;
    return {
        width: rect.width,
        height: rect.height,
        centerX,
        centerY,
        ringSpacing,
        numLevels,
    };
}

function baseNodePosition(ring, index, layout) {
    if (ring === 0) {
        return { x: layout.centerX, y: layout.centerY };
    }
    const nodesInRing = Math.pow(2, ring);
    const radius = layout.ringSpacing * ring;
    const angle = (2 * Math.PI * index) / nodesInRing - Math.PI / 2;
    return {
        x: layout.centerX + radius * Math.cos(angle),
        y: layout.centerY + radius * Math.sin(angle),
    };
}

function applyTransform(point, layout) {
    const dx = point.x - layout.centerX;
    const dy = point.y - layout.centerY;
    return {
        x: layout.centerX + dx * viewState.zoom + viewState.panX,
        y: layout.centerY + dy * viewState.zoom + viewState.panY,
    };
}

function getNodePosition(ring, index, layout) {
    return applyTransform(baseNodePosition(ring, index, layout), layout);
}

function screenToBase(screenX, screenY, layout) {
    const baseX = layout.centerX + (screenX - layout.centerX - viewState.panX) / viewState.zoom;
    const baseY = layout.centerY + (screenY - layout.centerY - viewState.panY) / viewState.zoom;
    return { x: baseX, y: baseY };
}

function findNodeAtPosition(x, y) {
    let closestId = null;
    let minDistance = Number.POSITIVE_INFINITY;
    nodePositions.forEach((pos, nodeId) => {
        const dx = x - pos.x;
        const dy = y - pos.y;
        const distance = Math.sqrt(dx * dx + dy * dy);
        if (distance <= pos.radius + 8 && distance < minDistance) {
            minDistance = distance;
            closestId = nodeId;
        }
    });
    return closestId;
}

function nodeLabel({ ring, index }) {
    return `(${ring}, ${index})`;
}

function formatRouteText(path) {
    if (!path || !path.length) {
        return 'Awaiting route computation';
    }
    const text = path.map(nodeLabel).join(' → ');
    return text.length > 90 ? `${text.slice(0, 87)}…` : text;
}

function setStatusIdle(message = 'Select source & destination to begin') {
    statusElements.hopValue.textContent = '0 / 0';
    statusElements.hopNodes.textContent = message;
    statusElements.phaseValue.textContent = 'Idle';
    statusElements.signalValue.textContent = '';
    statusElements.transferValue.textContent = '';
    statusElements.progressPercent.textContent = '0%';
    statusElements.progressFill.style.width = '0%';
    statusElements.timerValue.textContent = 'Timer: 0s';
    applySignalState({ req: 'sleep', ack: 'sleep', data: 'sleep' });
    updatePhaseTimeline(null);
    if (currentRouteInfo) {
        statusElements.routeValue.textContent = currentRouteInfo.routeText;
    } else {
        statusElements.routeValue.textContent = 'Awaiting route computation';
    }
}

function updateStatusBar(status) {
    if (!status) {
        setStatusIdle();
        return;
    }
    statusElements.hopValue.textContent = status.hopText;
    statusElements.hopNodes.textContent = status.nodesText;
    const phaseLabel = status.phaseLabel || 'Idle';
    statusElements.phaseValue.textContent = phaseLabel;
    const signalText = status.signalText || '—';
    statusElements.signalValue.textContent = `${signalText}`;
    statusElements.transferValue.textContent = status.transferText
        ? ` ${status.transferText}`
        : '';
    statusElements.progressPercent.textContent = `${status.progressPercent}%`;
    statusElements.progressFill.style.width = `${status.progressPercent}%`;
    statusElements.timerValue.textContent = `Timer: ${status.timer}s`;
    applySignalState(status.signalStates);
    updatePhaseTimeline(status.phaseKey || null);
    if (currentRouteInfo) {
        statusElements.routeValue.textContent = currentRouteInfo.routeText;
    } else {
        statusElements.routeValue.textContent = 'Awaiting route computation';
    }
}
function showRouteReadyStatus(payload) {
    const hopCount = payload?.hopCount ?? 0;
    const startNode = Array.isArray(payload?.path) && payload.path.length ? payload.path[0] : null;
    const endNode = Array.isArray(payload?.path) && payload.path.length ? payload.path[payload.path.length - 1] : null;
    const nodesText = startNode && endNode ? `${nodeLabel(startNode)} → ${nodeLabel(endNode)}` : 'Route prepared';
    updateStatusBar({
        hopText: `0 / ${hopCount}`,
        nodesText,
        phaseKey: 'ready',
        phaseLabel: 'Ready',
        signalText: 'Idle',
        signalStates: { req: 'sleep', ack: 'sleep', data: 'sleep' },
        transferText: 'Press Animate',
        progressPercent: 0,
        timer: 0,
    });
}


function setRouteInfo(payload) {
    if (!payload || !payload.path) {
        currentRouteInfo = null;
        statusElements.routeValue.textContent = 'Awaiting route computation';
        return;
    }
    currentRouteInfo = {
        path: payload.path.slice(),
        hopCount: payload.hopCount,
        routeText: formatRouteText(payload.path),
    };
    statusElements.routeValue.textContent = currentRouteInfo.routeText;
}

function updateAnimateButton({ disabled, busy = false } = {}) {
    if (!animateBtn) return;
    if (typeof disabled === 'boolean') {
        animateBtn.disabled = disabled;
    }
    animateBtn.textContent = busy ? 'Animating…' : 'Animate path';
}

function ingestTopologyPayload(data, { resetView = true } = {}) {
    topologyData = data;
    if (levelInput) {
        const ringCount = levelToRingCount(data?.numLevels);
        levelInput.value = `${ringCount}`;
    }
    nodeMeta.clear();
    if (Array.isArray(data?.nodes)) {
        data.nodes.forEach((node) => {
            if (node && node.id) {
                nodeMeta.set(node.id, node);
            }
        });
    }

    nodeRuntimeState.clear();
    nodeMeta.forEach((_, nodeId) => {
        nodeRuntimeState.set(nodeId, defaultNodeRuntimeState());
    });

    if (resetView) {
        viewState.zoom = 1;
        viewState.panX = 0;
        viewState.panY = 0;
    }

    selectedNodeId = null;
    setNodePanelAutoTracking(autoNodeDetailsPreference);
    routePreview = null;
    animationState = null;
    lastRoutePayload = null;
    currentRouteInfo = null;
    flowCardElements = [];
    if (flowLog) {
        flowLog.innerHTML = '';
    }
    if (summary) {
        summary.textContent = '';
    }

    if (isNodePanelOpen()) {
        closeNodePanel();
    } else {
        resetNodePanelContent();
    }

    updateAnimateButton({ disabled: true, busy: false });
    populateNodeSelects();
    syncSelectionState();
    renderTopology();
}

function populateNodeSelects() {
    if (!topologyData) return;
    const options = topologyData.nodes
        .map((node) => ({
            value: `${node.ring}-${node.index}`,
            label: `(${node.ring}, ${node.index})`,
        }))
        .sort((a, b) => a.value.localeCompare(b.value));

    [sourceSelect, destinationSelect].forEach((select, idx) => {
        select.innerHTML = '';
        options.forEach((opt) => {
            const optionEl = document.createElement('option');
            optionEl.value = opt.value;
            optionEl.textContent = opt.label;
            if (idx === 0 && opt.value === '0-0') {
                optionEl.selected = true;
            }
            if (idx === 1 && opt.value === '2-2') {
                optionEl.selected = true;
            }
            select.appendChild(optionEl);
        });
    });
}

function fetchTopology() {
    hudStatus.textContent = 'Loading topology…';
    return fetch('/api/topology')
        .then((res) => res.json())
        .then((data) => {
            ingestTopologyPayload(data);
            hudStatus.textContent = `Loaded ${levelToRingCount(data.numLevels)} rings`;
            setStatusIdle();
        })
        .catch((err) => {
            console.error(err);
            hudStatus.textContent = 'Error loading topology';
            setStatusIdle('Topology failed to load');
        });
}

function drawRings(layout) {
    const center = applyTransform({ x: layout.centerX, y: layout.centerY }, layout);
    ctx.save();
    ctx.strokeStyle = '#94a3b8';
    ctx.lineWidth = 1.2;
    for (let ring = 1; ring < layout.numLevels; ring += 1) {
        const radius = layout.ringSpacing * ring * viewState.zoom;
        ctx.beginPath();
        ctx.arc(center.x, center.y, radius, 0, Math.PI * 2);
        ctx.stroke();
    }
    ctx.restore();
}

function drawTreeEdges(layout) {
    if (!topologyData) return;
    ctx.save();
    ctx.strokeStyle = colors.tree;
    ctx.lineWidth = 1.5;
    topologyData.treeEdges.forEach(({ source, target }) => {
        const start = getNodePosition(source.ring, source.index, layout);
        const end = getNodePosition(target.ring, target.index, layout);
        ctx.beginPath();
        ctx.moveTo(start.x, start.y);
        ctx.lineTo(end.x, end.y);
        ctx.stroke();
    });
    ctx.restore();
}

function drawNodes(layout) {
    if (!topologyData) return;
    ctx.save();
    topologyData.nodes.forEach((node) => {
        const nodeId = makeNodeId(node);
        const pos = getNodePosition(node.ring, node.index, layout);
        const zoomRadius = clamp(viewState.zoom, 0.7, 1.6);
        const radius = (node.ring === 0 ? 10 : 6) * zoomRadius;
        nodePositions.set(nodeId, { x: pos.x, y: pos.y, radius });
        const isSelected = nodeId === selectedNodeId;
        const isSource = nodeId === currentSourceId;
        const isDestination = nodeId === currentDestinationId;
        let fillColor = colors.node;
        if (isSource && isDestination) {
            fillColor = colors.sharedNode;
        } else if (isSource) {
            fillColor = colors.sourceNode;
        } else if (isDestination) {
            fillColor = colors.destinationNode;
        }
        if (isSelected) {
            fillColor = colors.nodeSelected;
        }

        ctx.beginPath();
        ctx.arc(pos.x, pos.y, radius, 0, Math.PI * 2);
        ctx.fillStyle = fillColor;
        ctx.fill();

        ctx.beginPath();
        ctx.arc(pos.x, pos.y, radius, 0, Math.PI * 2);
        if (isSelected) {
            ctx.strokeStyle = colors.nodeHighlight;
            ctx.lineWidth = 3;
            ctx.stroke();
        } else if (isSource || isDestination) {
            ctx.strokeStyle = isSource && isDestination
                ? colors.nodeHighlight
                : isSource
                    ? colors.sourceNode
                    : colors.destinationNode;
            ctx.lineWidth = 2.4;
            ctx.stroke();
        }

        ctx.fillStyle = colors.text;
        const fontSize = clamp(12 * zoomRadius, 10, 18);
        ctx.font = `${fontSize}px Inter, sans-serif`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'top';
        ctx.fillText(nodeLabel(node), pos.x, pos.y + radius + 4);
    });
    ctx.restore();
}

function angleForNode(ring, index) {
    const nodesInRing = Math.pow(2, ring);
    return (2 * Math.PI * index) / nodesInRing - Math.PI / 2;
}

function ringDirection(ring, fromIndex, toIndex) {
    const nodesInRing = Math.max(1, Math.pow(2, ring));
    const diff = ((toIndex - fromIndex) % nodesInRing + nodesInRing) % nodesInRing;
    if (diff === 0) return 0;
    const threshold = nodesInRing / 2;
    return diff <= threshold ? 1 : -1;
}

function ringPoint(ring, startIndex, direction, progress, layout) {
    const center = applyTransform({ x: layout.centerX, y: layout.centerY }, layout);
    const radius = layout.ringSpacing * ring * viewState.zoom;
    const nodesInRing = Math.max(1, Math.pow(2, ring));
    const span = (2 * Math.PI) / nodesInRing;
    const angle = angleForNode(ring, startIndex) + direction * span * clamp(progress, 0, 1);
    return {
        x: center.x + radius * Math.cos(angle),
        y: center.y + radius * Math.sin(angle),
    };
}

function drawRoute(state, layout, options = {}) {
    if (!state || !Array.isArray(state.segments) || !state.segments.length) return;
    const {
        showIndicator = true,
        showPhaseIndicators = true,
        treeColor = colors.treeHighlight,
        ringColor = colors.ringHighlight,
        lineWidth = 4,
        strokeOpacity = 1,
    } = options;

    ctx.save();
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.lineWidth = lineWidth;
    const previousAlpha = ctx.globalAlpha;
    ctx.globalAlpha = strokeOpacity;

    state.segments.forEach((segment, idx) => {
        const completion = state.segmentProgress(idx);
        if (completion <= 0) return;

        const from = segment.from;
        const to = segment.to;

        if (segment.type === 'ring') {
            const ring = from.ring;
            const directionStep = ringDirection(ring, from.index, to.index) || 1;
            const center = applyTransform({ x: layout.centerX, y: layout.centerY }, layout);
            const radius = layout.ringSpacing * ring * viewState.zoom;
            const nodesInRing = Math.max(1, Math.pow(2, ring));
            const span = (2 * Math.PI) / nodesInRing;
            const startAngle = angleForNode(ring, from.index);
            const targetAngle = startAngle + directionStep * span * clamp(completion, 0, 1);
            ctx.beginPath();
            ctx.strokeStyle = ringColor;
            ctx.arc(center.x, center.y, radius, startAngle, targetAngle, directionStep < 0);
            ctx.stroke();
        } else {
            const startPos = getNodePosition(from.ring, from.index, layout);
            const endPos = getNodePosition(to.ring, to.index, layout);
            ctx.beginPath();
            ctx.strokeStyle = treeColor;
            const midX = startPos.x + (endPos.x - startPos.x) * clamp(completion, 0, 1);
            const midY = startPos.y + (endPos.y - startPos.y) * clamp(completion, 0, 1);
            ctx.moveTo(startPos.x, startPos.y);
            ctx.lineTo(midX, midY);
            ctx.stroke();
        }
    });

    ctx.globalAlpha = previousAlpha;
    const current = state.currentSegment();
    if (current) {
        const { segment, progress } = current;
        if (showPhaseIndicators) {
            drawPhaseIndicators(segment, progress, layout);
        }

        if (showIndicator) {
            const indicator = indicatorInfoForProgress(segment, progress, layout);
            if (indicator?.point) {
                ctx.beginPath();
                ctx.fillStyle = indicator.color;
                ctx.arc(indicator.point.x, indicator.point.y, indicator.radius, 0, Math.PI * 2);
                ctx.fill();
            }
        }
    }

    ctx.restore();
}

function ringAngleAt(ring, startIndex, direction, progress) {
    const nodesInRing = Math.max(1, Math.pow(2, ring));
    const span = (2 * Math.PI) / nodesInRing;
    return angleForNode(ring, startIndex) + direction * span * clamp(progress, 0, 1);
}

function segmentPointWithAngle(segment, progress, layout, { reverse = false, allowClamp = false } = {}) {
    const clampedProgress = allowClamp ? clamp(progress, 0, 1) : progress;
    if (segment.type === 'ring') {
        const ring = segment.from.ring;
        const baseDirection = ringDirection(ring, segment.from.index, segment.to.index) || 1;
        const direction = reverse ? -baseDirection : baseDirection;
        const startIndex = reverse ? segment.to.index : segment.from.index;
        const theta = ringAngleAt(ring, startIndex, direction, clampedProgress);
        const point = ringPoint(ring, startIndex, direction, clampedProgress, layout);
        const tangent = theta + (direction >= 0 ? Math.PI / 2 : -Math.PI / 2);
        return { ...point, angle: tangent };
    }

    const fromNode = reverse ? segment.to : segment.from;
    const toNode = reverse ? segment.from : segment.to;
    const fromPos = getNodePosition(fromNode.ring, fromNode.index, layout);
    const toPos = getNodePosition(toNode.ring, toNode.index, layout);
    const x = fromPos.x + (toPos.x - fromPos.x) * clamp(clampedProgress, 0, 1);
    const y = fromPos.y + (toPos.y - fromPos.y) * clamp(clampedProgress, 0, 1);
    const angle = Math.atan2(toPos.y - fromPos.y, toPos.x - fromPos.x);
    return { x, y, angle };
}

function drawFlowArrow(point, angle, color, { length = 26, dashed = false } = {}) {
    ctx.save();
    ctx.translate(point.x, point.y);
    ctx.rotate(angle);
    ctx.strokeStyle = color;
    ctx.lineWidth = 3;
    ctx.lineCap = 'round';
    if (dashed) {
        ctx.setLineDash([8, 6]);
    }
    ctx.beginPath();
    ctx.moveTo(-length, 0);
    ctx.lineTo(0, 0);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.beginPath();
    ctx.moveTo(0, 0);
    ctx.lineTo(-12, 6.5);
    ctx.lineTo(-12, -6.5);
    ctx.closePath();
    ctx.fillStyle = color;
    ctx.fill();
    ctx.restore();
}

function drawDataMarker(point, angle, color) {
    ctx.save();
    ctx.translate(point.x, point.y);
    ctx.rotate(angle);
    ctx.fillStyle = color;
    ctx.strokeStyle = '#0f172a0f';
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.ellipse(0, 0, 9, 5, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();
    ctx.restore();
}

function drawReleasePulse(point, color) {
    ctx.save();
    ctx.beginPath();
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.globalAlpha = 0.8;
    ctx.arc(point.x, point.y, 12, 0, Math.PI * 2);
    ctx.stroke();
    ctx.restore();
}

function drawPhaseIndicators(segment, progress, layout) {
    const { req, ack, data, release } = PHASE_RANGES;

    if (progress >= req[0] && progress < req[1]) {
        const t = normalizeRange(progress, req[0], req[1]);
        const point = segmentPointWithAngle(segment, t, layout, { allowClamp: true });
        drawFlowArrow(point, point.angle, colors.phaseReq);
    }

    if (progress >= ack[0] && progress < ack[1]) {
        const t = normalizeRange(progress, ack[0], ack[1]);
        const point = segmentPointWithAngle(segment, t, layout, { reverse: true, allowClamp: true });
        drawFlowArrow(point, point.angle, colors.phaseAck, { dashed: true });
    }

    if (progress >= data[0] && progress < data[1]) {
        const t = normalizeRange(progress, data[0], data[1]);
        const point = segmentPointWithAngle(segment, t, layout);
        drawDataMarker(point, point.angle, colors.phaseData);
    }

    if (progress >= release[0]) {
        const destPos = getNodePosition(segment.to.ring, segment.to.index, layout);
        drawReleasePulse(destPos, colors.phaseRelease);
    }
}

function indicatorInfoForProgress(segment, progress, layout) {
    const stage = stageFromProgress(progress);
    const color = STAGE_INDICATOR_COLORS[stage.key] || colors.nodeHighlight;
    const samplePhasePoint = (phaseKey, options = {}) => {
        const bounds = PHASE_RANGES[phaseKey];
        const t = normalizeRange(progress, bounds[0], bounds[1]);
        return segmentPointWithAngle(segment, t, layout, { allowClamp: true, ...options });
    };

    switch (stage.key) {
        case 'ready':
            return {
                stage,
                point: getNodePosition(segment.from.ring, segment.from.index, layout),
                radius: 8,
                color,
            };
        case 'req':
            return null;
        case 'ack':
            return null;
        case 'data':
            return {
                stage,
                point: samplePhasePoint('data'),
                radius: 10,
                color,
            };
        case 'release':
            return {
                stage,
                point: getNodePosition(segment.to.ring, segment.to.index, layout),
                radius: 8,
                color,
            };
        default:
            return {
                stage,
                point: segmentPointWithAngle(segment, progress, layout, { allowClamp: true }),
                radius: 9,
                color,
            };
    }
}

function renderTopology() {
    if (!topologyData) return;
    const rect = canvas.getBoundingClientRect();
    layoutCache = computeLayout(rect, topologyData.numLevels);
    ctx.setTransform(canvasScale, 0, 0, canvasScale, 0, 0);
    ctx.clearRect(0, 0, canvas.width / canvasScale, canvas.height / canvasScale);
    drawRings(layoutCache);
    drawTreeEdges(layoutCache);
    if (routePreview) {
        drawRoute(routePreview, layoutCache, {
            showIndicator: false,
            showPhaseIndicators: false,
            treeColor: colors.previewTree,
            ringColor: colors.previewRing,
            lineWidth: 3,
            strokeOpacity: 0.75,
        });
    }
    nodePositions.clear();
    drawNodes(layoutCache);
    if (animationState) {
        drawRoute(animationState, layoutCache, { showIndicator: true, showPhaseIndicators: true });
    }
}

class RouteAnimation {
    constructor(payload, speed) {
        this.path = payload.path || [];
        this.segments = payload.segments || [];
        this.flow = payload.flow || [];
        this.speed = speed;
        this.durationPerSegment = 1800 / speed;
        this.startTimestamp = null;
        this.progress = 0;
        this.elapsedMs = 0;
    }

    update(timestamp) {
        if (!this.startTimestamp) {
            this.startTimestamp = timestamp;
        }
        this.elapsedMs = timestamp - this.startTimestamp;
        if (!this.segments.length) {
            this.progress = 1;
            return;
        }
        const totalDuration = this.durationPerSegment * this.segments.length;
        const normalized = Math.min(this.elapsedMs / totalDuration, 1);
        this.progress = normalized * this.segments.length;
    }

    segmentProgress(index) {
        return clamp(this.progress - index, 0, 1);
    }

    currentSegment() {
        if (!this.segments.length) return null;
        const index = Math.min(Math.floor(this.progress), this.segments.length - 1);
        const segmentProgress = this.segmentProgress(index);
        return {
            index,
            segment: this.segments[index],
            progress: segmentProgress,
        };
    }

    isComplete() {
        return !this.segments.length || this.progress >= this.segments.length;
    }

    overallPercent() {
        if (!this.segments.length) return 100;
        return clamp((this.progress / this.segments.length) * 100, 0, 100);
    }

    currentStatus() {
        const totalHops = this.segments.length;
        if (!totalHops) {
            return {
                hopText: '0 / 0',
                nodesText: 'Destination reached',
                phaseKey: 'completed',
                phaseLabel: 'Completed',
                signalText: 'Idle',
                signalStates: { req: 'sleep', ack: 'sleep', data: 'sleep' },
                transferText: 'Packet already at destination',
                progressPercent: 100,
                timer: Math.round(this.elapsedMs / 1000),
                flowIndex: this.flow.length - 1,
                segment: null,
                segmentProgress: 1,
            };
        }

        const rawIndex = clamp(Math.floor(this.progress), 0, totalHops - 1);
        const segmentProgress = this.segmentProgress(rawIndex);
        const segment = this.segments[rawIndex];
        const stage = stageFromProgress(segmentProgress);
        const hopNumber = Math.min(rawIndex + 1, totalHops);
        return {
            hopText: `${hopNumber} / ${totalHops}`,
            nodesText: `${nodeLabel(segment.from)} → ${nodeLabel(segment.to)}`,
            phaseKey: stage.key,
            phaseLabel: stage.label,
            signalText: stage.signalText,
            signalStates: stage.signals,
            transferText: stage.transfer,
            progressPercent: Math.round(this.overallPercent()),
            timer: Math.round(this.elapsedMs / 1000),
            flowIndex: Math.min(hopNumber, this.flow.length - 1),
            segment,
            segmentProgress,
        };
    }
}

class RoutePreview {
    constructor(payload) {
        this.path = payload?.path || [];
        this.segments = payload?.segments || [];
        this.flow = payload?.flow || [];
    }

    segmentProgress() {
        return 1;
    }

    currentSegment() {
        return null;
    }

    isComplete() {
        return true;
    }
}

function stageFromProgress(progress) {
    if (progress < 0.2) {
        return {
            key: 'ready',
            label: 'Ready',
            transfer: 'Buffers primed',
            signalText: 'Idle',
            signals: { req: 'sleep', ack: 'sleep', data: 'sleep' },
        };
    }
    if (progress < 0.4) {
        return {
            key: 'req',
            label: 'REQ',
            transfer: 'Source asserts REQ',
            signalText: 'REQ=1',
            signals: { req: 'active', ack: 'sleep', data: 'sleep' },
        };
    }
    if (progress < 0.6) {
        return {
            key: 'ack',
            label: 'ACK',
            transfer: 'Destination acknowledges',
            signalText: 'REQ=1, ACK=1',
            signals: { req: 'active', ack: 'active', data: 'sleep' },
        };
    }
    if (progress < 0.85) {
        return {
            key: 'data',
            label: 'DATA',
            transfer: 'Data moving',
            signalText: 'Transfer=1',
            signals: { req: 'active', ack: 'active', data: 'active' },
        };
    }
    return {
        key: 'release',
        label: 'Release',
        transfer: 'Lines releasing',
        signalText: 'Lines releasing',
        signals: { req: 'sleep', ack: 'sleep', data: 'sleep' },
    };
}

function updateNodeRuntimeFromStatus(status) {
    if (!status) return;
    if (!animationState) return;

    const finalNode = Array.isArray(animationState.path) && animationState.path.length
        ? animationState.path[animationState.path.length - 1]
        : null;

    if (!status.segment) {
        const isCompletedPhase = status.phaseKey === 'completed' || status.phaseLabel === 'Completed';
        if (isCompletedPhase && finalNode) {
            const destId = makeNodeId(finalNode);
            const destState = ensureNodeRuntimeState(destId);
            destState.receiveBuffer = 'delivered';
            destState.applicationBuffer = 1;
            destState.handshake = 'idle';
            destState.lastUpdated = performance.now();
            if (selectedNodeId === destId) {
                updateNodePanelContent();
            }
        }
        return;
    }

    const { segment } = status;
    const sourceId = makeNodeId(segment.from);
    const targetId = makeNodeId(segment.to);
    const sourceState = ensureNodeRuntimeState(sourceId);
    const targetState = ensureNodeRuntimeState(targetId);
    const timestamp = performance.now();
    sourceState.lastUpdated = timestamp;
    targetState.lastUpdated = timestamp;

    const isFinalHop = Boolean(
        finalNode && segment.to.ring === finalNode.ring && segment.to.index === finalNode.index,
    );

    const phaseKey = status.phaseKey || status.phaseLabel;

    switch (phaseKey) {
        case 'ready':
            sourceState.sendBuffer = 'primed';
            sourceState.handshake = 'primed';
            targetState.receiveBuffer = 'idle';
            targetState.handshake = 'idle';
            break;
        case 'req':
            sourceState.sendBuffer = 'waiting';
            sourceState.handshake = 'waiting';
            targetState.receiveBuffer = targetState.receiveBuffer === 'receiving' ? 'receiving' : 'idle';
            targetState.handshake = 'primed';
            break;
        case 'ack':
            sourceState.sendBuffer = 'waiting';
            sourceState.handshake = 'waiting';
            targetState.receiveBuffer = 'primed';
            targetState.handshake = 'receiving';
            break;
        case 'data':
            sourceState.sendBuffer = 'transferring';
            sourceState.handshake = 'transferring';
            targetState.receiveBuffer = 'receiving';
            targetState.handshake = 'receiving';
            break;
        case 'release':
            sourceState.sendBuffer = 'idle';
            sourceState.handshake = 'releasing';
            targetState.handshake = 'releasing';
            if (isFinalHop) {
                targetState.receiveBuffer = 'delivered';
                targetState.applicationBuffer = 1;
            } else {
                targetState.receiveBuffer = 'ready';
                targetState.applicationBuffer = 0;
            }
            break;
        case 'completed':
            if (isFinalHop) {
                targetState.receiveBuffer = 'delivered';
                targetState.applicationBuffer = 1;
                targetState.handshake = 'idle';
            }
            break;
        default:
            break;
    }

    if (selectedNodeId === sourceId || selectedNodeId === targetId) {
        updateNodePanelContent();
    }
}

function highlightFlowCard(index) {
    flowCardElements.forEach((card, idx) => {
        if (idx === index) {
            card.classList.add('flow-entry--active');
        } else {
            card.classList.remove('flow-entry--active');
        }
    });
}

function renderFlow(flowEntries) {
    flowLog.innerHTML = '';
    flowCardElements = [];
    flowEntries.forEach((entry) => {
        const card = document.createElement('article');
        card.className = 'flow-entry';

        const phase = document.createElement('p');
        phase.className = 'flow-entry__phase';
        phase.textContent = entry.phase;
        card.appendChild(phase);

        const title = document.createElement('h3');
        title.className = 'flow-entry__title';
        title.textContent = entry.title;
        card.appendChild(title);

        const list = document.createElement('ul');
        list.className = 'flow-entry__details';
        entry.details.forEach((detail) => {
            const item = document.createElement('li');
            item.textContent = detail;
            list.appendChild(item);
        });
        card.appendChild(list);

        flowLog.appendChild(card);
        flowCardElements.push(card);
    });
    if (flowLog) {
        flowLog.scrollTop = 0;
    }
}

function parseSelectValue(value) {
    if (typeof value !== 'string') {
        return { ring: 0, index: 0 };
    }
    const [ringStr, indexStr] = value.split('-');
    return {
        ring: parseInt(ringStr, 10),
        index: parseInt(indexStr, 10),
    };
}

function handleSourceSelectChange({ announce = false, message } = {}) {
    syncSelectionState();
    const nodeId = currentSourceId;
    if (!nodeId) return;
    const meta = nodeMeta.get(nodeId) || parseSelectValue(nodeId);
    focusNode(nodeId, {
        auto: nodePanelAutoTracking,
        openPanelOnFocus: true,
    });
    if (announce && hudStatus && meta) {
        hudStatus.textContent = message || `Source set to ${nodeLabel(meta)}.`;
    }
    renderTopology();
}

function handleDestinationSelectChange({ announce = false, message } = {}) {
    syncSelectionState();
    const nodeId = currentDestinationId;
    if (!nodeId) return;
    const meta = nodeMeta.get(nodeId) || parseSelectValue(nodeId);
    focusNode(nodeId, {
        auto: nodePanelAutoTracking,
        openPanelOnFocus: true,
    });
    if (announce && hudStatus && meta) {
        hudStatus.textContent = message || `Destination set to ${nodeLabel(meta)}.`;
    }
    renderTopology();
}

function simulateRoute() {
    if (!topologyData) return;
    setPickMode(null);
    syncSelectionState();
    if (isMobileSidebar() && isSidebarVisible()) {
        closeSidebar();
    }
    stopAnimation();
    updateAnimateButton({ disabled: true, busy: false });
    const source = parseSelectValue(sourceSelect.value);
    const destination = parseSelectValue(destinationSelect.value);
    hudStatus.textContent = `Preparing route ${nodeLabel(source)} → ${nodeLabel(destination)}…`;

    fetch('/api/route', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            source: { ring: source.ring, node: source.index },
            destination: { ring: destination.ring, node: destination.index },
        }),
    })
        .then((res) => res.json())
        .then((payload) => {
            if (payload.error) {
                hudStatus.textContent = payload.error;
                routePreview = null;
                lastRoutePayload = null;
                renderTopology();
                setStatusIdle(payload.error);
                updateAnimateButton({ disabled: true, busy: false });
                return;
            }
            prepareRoute(payload);
        })
        .catch((err) => {
            console.error(err);
            hudStatus.textContent = 'Routing failed';
            setStatusIdle('Routing failed');
            routePreview = null;
            lastRoutePayload = null;
            renderTopology();
            updateAnimateButton({ disabled: true, busy: false });
        });
}

function prepareRoute(payload) {
    resetAllNodeRuntimeState();
    setNodePanelAutoTracking(autoNodeDetailsPreference);
    lastRoutePayload = payload;
    routePreview = new RoutePreview(payload);
    animationState = null;
    setRouteInfo(payload);
    summary.textContent = `Hop count: ${payload.hopCount}`;
    renderFlow(payload.flow);
    highlightFlowCard(0);
    showRouteReadyStatus(payload);
    const hasSegments = Array.isArray(payload.segments) && payload.segments.length > 0;
    updateAnimateButton({ disabled: !hasSegments, busy: false });
    if (hasSegments) {
        hudStatus.textContent = 'Route ready. Click "Animate path" to begin.';
    } else {
        hudStatus.textContent = 'Source and destination are identical.';
    }
    if (Array.isArray(payload.path) && payload.path.length) {
        focusNode(makeNodeId(payload.path[0]), {
            auto: true,
            openPanelOnFocus: nodePanelAutoTracking,
        });
    }
    renderTopology();
}

function playAnimation() {
    if (!lastRoutePayload) {
        hudStatus.textContent = 'Simulate the route first.';
        return;
    }
    startAnimation(lastRoutePayload);
}

function startAnimation(payload) {
    if (!payload || !Array.isArray(payload.segments) || !payload.segments.length) {
        updateAnimateButton({ disabled: true, busy: false });
        return;
    }
    cancelAnimationFrame(animationFrame);
    resetAllNodeRuntimeState();
    routePreview = null;
    animationState = new RouteAnimation(payload, speedMultiplier);
    setNodePanelAutoTracking(autoNodeDetailsPreference);
    updateAnimateButton({ disabled: true, busy: true });
    hudStatus.textContent = 'Animating route…';
    const firstNode = Array.isArray(animationState.path) && animationState.path.length
        ? animationState.path[0]
        : null;
    if (firstNode) {
        focusNode(makeNodeId(firstNode), {
            auto: true,
            openPanelOnFocus: nodePanelAutoTracking,
        });
    }
    highlightFlowCard(0);
    renderTopology();

    function step(timestamp) {
        if (!animationState) return;
        animationState.update(timestamp);
        const status = animationState.currentStatus();
        updateStatusBar(status);
        if (status && typeof status.flowIndex === 'number') {
            highlightFlowCard(status.flowIndex);
        }
        updateNodeRuntimeFromStatus(status);
        if (nodePanelAutoTracking && status && status.segment) {
            const autoNode = makeNodeId(status.segment.to);
            if (selectedNodeId !== autoNode) {
                focusNode(autoNode, {
                    auto: true,
                    openPanelOnFocus: nodePanelAutoTracking,
                });
            } else if (selectedNodeId) {
                updateNodePanelContent();
            }
        } else if (selectedNodeId) {
            updateNodePanelContent();
        }
        renderTopology();

        if (animationState.isComplete()) {
            hudStatus.textContent = 'Transmission complete';
            highlightFlowCard(flowCardElements.length - 1);
            const completedStatus = {
                ...status,
                phaseKey: 'completed',
                phaseLabel: 'Completed',
                signalText: 'Idle',
                signalStates: { req: 'sleep', ack: 'sleep', data: 'sleep' },
                transferText: 'Packet delivered',
                progressPercent: 100,
            };
            updateStatusBar(completedStatus);
            updateNodeRuntimeFromStatus(completedStatus);
            if (nodePanelAutoTracking && Array.isArray(payload.path) && payload.path.length) {
                const destinationNode = payload.path[payload.path.length - 1];
                focusNode(makeNodeId(destinationNode), {
                    auto: true,
                    openPanelOnFocus: nodePanelAutoTracking,
                });
            }
            routePreview = new RoutePreview(payload);
            animationState = null;
            updateAnimateButton({ disabled: false, busy: false });
            renderTopology();
            animationFrame = null;
            return;
        }

        animationFrame = requestAnimationFrame(step);
    }

    animationFrame = requestAnimationFrame(step);
}

function stopAnimation() {
    if (animationFrame) {
        cancelAnimationFrame(animationFrame);
        animationFrame = null;
    }
    animationState = null;
}

function resetSimulation() {
    stopAnimation();
    setPickMode(null);
    summary.textContent = '';
    flowLog.innerHTML = '';
    flowCardElements = [];
    resetAllNodeRuntimeState();
    setStatusIdle();
    hudStatus.textContent = 'Idle';
    setNodePanelAutoTracking(autoNodeDetailsPreference);
    routePreview = null;
    lastRoutePayload = null;
    updateAnimateButton({ disabled: true, busy: false });
    if (selectedNodeId) {
        selectedNodeId = null;
        resetNodePanelContent();
    }
    renderTopology();
}

function applyZoom(factor, originX, originY) {
    if (!topologyData) return;
    const rect = canvas.getBoundingClientRect();
    const layout = layoutCache || computeLayout(rect, topologyData.numLevels);
    const newZoom = clamp(viewState.zoom * factor, ZOOM_LIMITS.min, ZOOM_LIMITS.max);
    const basePoint = screenToBase(originX, originY, layout);
    viewState.zoom = newZoom;
    viewState.panX = originX - (basePoint.x - layout.centerX) * newZoom - layout.centerX;
    viewState.panY = originY - (basePoint.y - layout.centerY) * newZoom - layout.centerY;
    renderTopology();
}

function resetView() {
    viewState.zoom = 1;
    viewState.panX = 0;
    viewState.panY = 0;
    renderTopology();
}

let isPanning = false;
let panPointerId = null;
const panState = { x: 0, y: 0 };

canvas.addEventListener('pointerdown', (event) => {
    isPanning = true;
    panPointerId = event.pointerId;
    panState.x = event.clientX;
    panState.y = event.clientY;
    panMoved = false;
    canvas.setPointerCapture(event.pointerId);
    if (!pickMode) {
        canvas.classList.add('is-panning');
    }
});

canvas.addEventListener('pointermove', (event) => {
    if (!isPanning || event.pointerId !== panPointerId) return;
    const dx = event.clientX - panState.x;
    const dy = event.clientY - panState.y;
    panState.x = event.clientX;
    panState.y = event.clientY;
    if (Math.abs(dx) > 2 || Math.abs(dy) > 2) {
        panMoved = true;
    }
    viewState.panX += dx;
    viewState.panY += dy;
    renderTopology();
});

function endPan(event) {
    if (event.pointerId !== panPointerId) return;
    isPanning = false;
    canvas.classList.remove('is-panning');
    canvas.releasePointerCapture(event.pointerId);
}

canvas.addEventListener('pointerup', endPan);
canvas.addEventListener('pointercancel', endPan);

canvas.addEventListener('click', (event) => {
    if (panMoved) {
        panMoved = false;
        return;
    }
    const nodeId = findNodeAtPosition(event.offsetX, event.offsetY);
    if (nodeId) {
        handleCanvasNodeClick(nodeId);
        return;
    } else if (isNodePanelOverlayMode() && isNodePanelOpen()) {
        closeNodePanel();
    } else if (selectedNodeId) {
        selectedNodeId = null;
        resetNodePanelContent();
        renderTopology();
    }
    if (pickMode) {
        setPickMode(null);
    }
});

canvas.addEventListener(
    'wheel',
    (event) => {
        if (!topologyData) return;
        if (!scrollZoomEnabled) {
            return;
        }
        event.preventDefault();
        const factor = event.deltaY < 0 ? 1.1 : 0.9;
        applyZoom(factor, event.offsetX, event.offsetY);
    },
    { passive: false },
);

speedControl.addEventListener('input', (event) => {
    speedMultiplier = parseFloat(event.target.value) || 0.6;
    hudStatus.textContent = `Animation speed ×${speedMultiplier.toFixed(1)}`;
});

if (sidebarToggle) {
    sidebarToggle.addEventListener('click', toggleSidebar);
}

if (sidebarCloseBtn) {
    sidebarCloseBtn.addEventListener('click', closeSidebar);
}

if (sidebarOverlay) {
    sidebarOverlay.addEventListener('click', closeSidebar);
}

if (nodePanelClose) {
    nodePanelClose.addEventListener('click', closeNodePanel);
}

if (nodePanelScrim) {
    nodePanelScrim.addEventListener('click', closeNodePanel);
}

document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') {
        if (isNodePanelOverlayMode() && isNodePanelOpen()) {
            closeNodePanel();
            return;
        }
        if (!isNodePanelOverlayMode() && selectedNodeId) {
            selectedNodeId = null;
            resetNodePanelContent();
            renderTopology();
            return;
        }
        if (isSidebarVisible()) {
            closeSidebar(event);
        }
    }
});

if (simulateBtn) {
    simulateBtn.addEventListener('click', simulateRoute);
}
if (animateBtn) {
    animateBtn.addEventListener('click', playAnimation);
}
resetBtn.addEventListener('click', resetSimulation);

if (sourceSelect) {
    sourceSelect.addEventListener('change', () => {
        setPickMode(null);
        handleSourceSelectChange({ announce: true });
    });
}

if (destinationSelect) {
    destinationSelect.addEventListener('change', () => {
        setPickMode(null);
        handleDestinationSelectChange({ announce: true });
    });
}

if (pickSourceBtn) {
    pickSourceBtn.addEventListener('click', () => {
        setPickMode(pickMode === 'source' ? null : 'source');
    });
}

if (pickDestinationBtn) {
    pickDestinationBtn.addEventListener('click', () => {
        setPickMode(pickMode === 'destination' ? null : 'destination');
    });
}

applyTopologyBtn.addEventListener('click', () => {
    const requestedRings = parseInt(levelInput.value, 10);
    if (!Number.isInteger(requestedRings) || requestedRings < 2 || requestedRings > 11) {
        hudStatus.textContent = 'Ring count must be between 2 and 11';
        return;
    }

    hudStatus.textContent = 'Updating topology…';
    const numLevels = ringCountToLevels(requestedRings);
    fetch('/api/topology', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ numLevels }),
    })
        .then((res) => res.json())
        .then((data) => {
            if (data.error) {
                hudStatus.textContent = data.error;
                return;
            }
            ingestTopologyPayload(data);
            setStatusIdle('Topology updated');
            hudStatus.textContent = `Topology updated to ${requestedRings} rings`;
        })
        .catch((err) => {
            console.error(err);
            hudStatus.textContent = 'Failed to update topology';
        });
});

zoomInBtn.addEventListener('click', () => {
    const rect = canvas.getBoundingClientRect();
    applyZoom(1.2, rect.width / 2, rect.height / 2);
});

zoomOutBtn.addEventListener('click', () => {
    const rect = canvas.getBoundingClientRect();
    applyZoom(1 / 1.2, rect.width / 2, rect.height / 2);
});

resetViewBtn.addEventListener('click', resetView);

if (cursorModeBtn) {
    cursorModeBtn.addEventListener('click', () => {
        scrollZoomEnabled = !scrollZoomEnabled;
        cursorModeBtn.setAttribute('aria-pressed', scrollZoomEnabled ? 'true' : 'false');
        cursorModeBtn.classList.toggle('is-active', scrollZoomEnabled);
        hudStatus.textContent = scrollZoomEnabled ? 'Scroll zoom enabled' : 'Scroll zoom locked';
    });
    cursorModeBtn.classList.toggle('is-active', scrollZoomEnabled);
}

if (autoNodeDetailsBtn) {
    autoNodeDetailsBtn.addEventListener('click', () => {
        const isPaused = autoNodeDetailsPreference && !nodePanelAutoTracking;
        let nextPreferred = autoNodeDetailsPreference;
        let nextActive = nodePanelAutoTracking;

        if (isPaused) {
            nextPreferred = true;
            nextActive = true;
        } else {
            nextPreferred = !autoNodeDetailsPreference;
            nextActive = nextPreferred;
        }

        setNodePanelAutoTracking(nextActive, { persist: true, preferredValue: nextPreferred });

        if (nextActive) {
            let focusTarget = selectedNodeId;
            if (animationState) {
                const current = animationState.currentSegment();
                if (current && current.segment) {
                    focusTarget = makeNodeId(current.segment.to);
                }
            }
            if (!focusTarget && routePreview && Array.isArray(routePreview.path) && routePreview.path.length) {
                focusTarget = makeNodeId(routePreview.path[0]);
            }
            if (!focusTarget && lastRoutePayload && Array.isArray(lastRoutePayload.path) && lastRoutePayload.path.length) {
                focusTarget = makeNodeId(lastRoutePayload.path[0]);
            }
            if (focusTarget) {
                focusNode(focusTarget, { auto: true, openPanelOnFocus: true });
            }
        }
    });
}

syncAutoNodeDetailsControl();
setPickMode(null);

applySignalState({ req: 'sleep', ack: 'sleep', data: 'sleep' });
syncSidebarForViewport();
syncNodePanelMode();
updateAnimateButton({ disabled: true, busy: false });

fetchTopology()
    .then(() => {
        resizeCanvas();
    });
