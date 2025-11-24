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
const destinationCandidateSelect = document.getElementById('destinationCandidateSelect');
const addMultiDestinationBtn = document.getElementById('addMultiDestinationBtn');
const pickDestinationMultiBtn = document.getElementById('pickDestinationMultiBtn');

const applyTopologyBtn = document.getElementById('applyTopologyBtn');
const levelInput = document.getElementById('levelInput');
const simulateBtn = document.getElementById('simulateBtn');
const animateBtn = document.getElementById('animateBtn');
const resetBtn = document.getElementById('resetBtn');
const simulationModeSelect = document.getElementById('simulationMode');
const clearMultiDestinationsBtn = document.getElementById('clearMultiDestinationsBtn');
const multiDestinationList = document.getElementById('multiDestinationList');
const multiRouteList = document.getElementById('multiRouteList');
const singleDestinationField = document.querySelector('[data-mode-area="single"]');
const multiDestinationField = document.querySelector('[data-mode-area="multi"]');

const zoomInBtn = document.getElementById('zoomInBtn');
const zoomOutBtn = document.getElementById('zoomOutBtn');
const resetViewBtn = document.getElementById('resetViewBtn');
const cursorModeBtn = document.getElementById('cursorModeBtn');
const pauseAnimationBtn = document.getElementById('pauseAnimationBtn');
const restartAnimationBtn = document.getElementById('restartAnimationBtn');
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
const nodePanelLogic = document.getElementById('nodePanelLogic');
const nodePanelInterfaces = document.getElementById('nodePanelInterfaces');
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
    tree: 'rgba(104, 104, 103, 0.23)',
    treeHighlight: '#2c2c2ce4',
    ringHighlight:  '#2c2c2ce4',
    previewTree: 'rgba(255, 157, 0, 1)',
    previewRing: 'rgba(255, 145, 0, 1)',
    node: '#016271ff',
    nodeHighlight: '#000000ff',
    nodeSelected: '#f97316',
    sourceNode: '#16a34a',
    destinationNode: '#b80000ff',
    sharedNode: '#01dfb7ea',
    phaseReq: '#cc6403ff',
    phaseAck: '#013b9fe5',
    phaseData: '#22c55e',
    phaseRelease: '#0271a4ff',
    text: '#454545ae',
    completedTree: '#70ed03e1',
    completedRing: '#70ed03e1',
};

const PREVIEW_STYLE_DEFAULTS = {
    active: {
        treeColor: colors.treeHighlight,
        ringColor: colors.ringHighlight,
        lineWidth: 4,
        strokeOpacity: 0.9,
    },
    pending: {
        treeColor: colors.previewTree,
        ringColor: colors.previewRing,
        lineWidth: 3,
        strokeOpacity: 0.45,
    },
    completed: {
        treeColor: colors.completedTree,
        ringColor: colors.completedRing,
        lineWidth: 4,
        strokeOpacity: 0.9,
    },
    default: {
        treeColor: colors.previewTree,
        ringColor: colors.previewRing,
        lineWidth: 3,
        strokeOpacity: 0.75,
    },
};

const PARALLEL_ROUTE_COLORS = ['#ff6a00ff', '#00aeffff', '#8400ffff', '#f60303ff', '#05faddff'];
const HANDSHAKE_PHASES = new Set(['req', 'ack']);
const HANDSHAKE_WITH_DATA_PHASES = new Set(['req', 'ack', 'data']);
const DEFAULT_SPEED_SLIDER = 0.6;
const SPEED_SCALE = 0.6;

const STAGE_INDICATOR_COLORS = {
    ready: colors.nodeSelected,
    req: colors.phaseReq,
    ack: colors.phaseAck,
    data: colors.phaseData,
    release: colors.phaseRelease,
};

function resolveSpeedSliderValue(rawValue, fallback = DEFAULT_SPEED_SLIDER) {
    const numeric = parseFloat(rawValue);
    return Number.isFinite(numeric) ? numeric : fallback;
}

function computeSpeedMultiplier(rawValue) {
    return resolveSpeedSliderValue(rawValue) * SPEED_SCALE;
}

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
let animationStep = null;
let flowCardElements = [];
let currentRouteInfo = null;
let speedMultiplier = computeSpeedMultiplier(speedControl ? speedControl.value : DEFAULT_SPEED_SLIDER);
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
let multiRunState = null;
const multiDestinations = [];
let animationOptions = null;
let animationPaused = false;
let animationPauseTimestamp = null;
let pickMode = null;
let currentSourceId = null;
let currentDestinationId = null;

if (animateBtn) {
    animateBtn.dataset.defaultLabel = animateBtn.textContent;
    animateBtn.dataset.currentLabel = animateBtn.textContent;
}

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

function defaultInterfaceRuntime(metaInterface = null) {
    const sendCapacity = Number(metaInterface?.sendBuffer?.capacity ?? 0) || 0;
    const receiveCapacity = Number(metaInterface?.receiveBuffer?.capacity ?? 0) || 0;
    const timeoutLimit = Number(metaInterface?.timeout?.limit ?? metaInterface?.timeout?.TIMEOUT_LIMIT ?? 0) || 0;
    return {
        sendBuffer: {
            used: 0,
            capacity: sendCapacity,
            head: null,
            state: 'idle',
        },
        receiveBuffer: {
            used: 0,
            capacity: receiveCapacity,
            head: null,
            state: 'idle',
        },
        statusBits: {
            busy: false,
            transfer: false,
            receive: false,
        },
        handshakePins: {
            req: false,
            ack: false,
            data: false,
            choke: false,
        },
        sendRegister: null,
        receiveRegister: null,
        dataLine: null,
        timeout: {
            value: 0,
            limit: timeoutLimit,
        },
        activePackets: new Map(),
    };
}

function defaultNodeRuntimeState(meta = null) {
    const interfaces = new Map();
    if (meta && Array.isArray(meta.interfaces)) {
        meta.interfaces.forEach((iface) => {
            if (!iface || !iface.neighbor) return;
            const neighborId = makeNodeId(iface.neighbor);
            interfaces.set(neighborId, defaultInterfaceRuntime(iface));
        });
    }
    return {
        sendBuffer: 'idle',
        receiveBuffer: 'idle',
        applicationBuffer: 0,
        handshake: 'idle',
        lastUpdated: 0,
        interfaces,
    };
}

function ensureNodeRuntimeState(nodeId) {
    if (!nodeRuntimeState.has(nodeId)) {
        const meta = nodeMeta.get(nodeId) || null;
        nodeRuntimeState.set(nodeId, defaultNodeRuntimeState(meta));
    }
    return nodeRuntimeState.get(nodeId);
}

function resetAllNodeRuntimeState() {
    nodeRuntimeState.forEach((_, nodeId) => {
        const meta = nodeMeta.get(nodeId) || null;
        nodeRuntimeState.set(nodeId, defaultNodeRuntimeState(meta));
    });
}

function ensureInterfaceRuntimeState(nodeId, neighbor) {
    if (!neighbor) return null;
    const runtime = ensureNodeRuntimeState(nodeId);
    if (!(runtime.interfaces instanceof Map)) {
        runtime.interfaces = new Map();
    }
    const neighborId = makeNodeId(neighbor);
    if (!runtime.interfaces.has(neighborId)) {
        const meta = nodeMeta.get(nodeId) || null;
        let metaInterface = null;
        if (meta && Array.isArray(meta.interfaces)) {
            metaInterface = meta.interfaces.find((iface) => iface?.neighbor && makeNodeId(iface.neighbor) === neighborId) || null;
        }
        runtime.interfaces.set(neighborId, defaultInterfaceRuntime(metaInterface));
    }
    return runtime.interfaces.get(neighborId);
}

function resetMultiRunState({ clearList = true } = {}) {
    multiRunState = null;
    if (multiRouteList && clearList) {
        multiRouteList.innerHTML = '';
        multiRouteList.style.display = 'none';
    }
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
    if (pickDestinationMultiBtn) {
        const active = normalized === 'destination';
        pickDestinationMultiBtn.setAttribute('aria-pressed', active ? 'true' : 'false');
        pickDestinationMultiBtn.classList.toggle('is-active', active);
    }
    if (canvas) {
        canvas.classList.toggle('is-picking', Boolean(normalized));
    }
    if (normalized && hudStatus) {
        hudStatus.textContent = normalized === 'source'
            ? 'Click a node to choose the source.'
            : isMultiSimulationMode()
                ? 'Click a node to set the destination candidate.'
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

function setElementVisibility(element, visible) {
    if (!element) return;
    element.style.display = visible ? '' : 'none';
}

function getSimulationMode() {
    return simulationModeSelect ? simulationModeSelect.value : 'single';
}

function isMultiSimulationMode() {
    const mode = getSimulationMode();
    return mode === 'parallel';
}

function renderMultiDestinationList() {
    if (!multiDestinationList) return;
    multiDestinationList.innerHTML = '';

    if (!multiDestinations.length) {
        const emptyMessage = document.createElement('p');
        emptyMessage.className = 'destination-list__empty';
        emptyMessage.textContent = 'No destinations added yet.';
        multiDestinationList.appendChild(emptyMessage);
        if (topologyData && isMultiSimulationMode()) {
            renderTopology();
        }
        return;
    }

    const fragment = document.createDocumentFragment();
    multiDestinations.forEach((nodeId) => {
        const meta = nodeMeta.get(nodeId) || parseSelectValue(nodeId);
        const labelText = safeNodeLabel(meta);
        const item = document.createElement('div');
        item.className = 'destination-pill';
        item.setAttribute('role', 'listitem');

        const name = document.createElement('span');
        name.textContent = labelText;
        item.appendChild(name);

        const removeBtn = document.createElement('button');
        removeBtn.type = 'button';
        removeBtn.className = 'mini-btn destination-pill__remove';
        removeBtn.textContent = 'x';
        removeBtn.setAttribute('data-remove-destination', nodeId);
        removeBtn.setAttribute('aria-label', `Remove ${labelText} from destinations`);
        removeBtn.setAttribute('title', `Remove ${labelText}`);
        item.appendChild(removeBtn);

        fragment.appendChild(item);
    });

    multiDestinationList.appendChild(fragment);
    if (topologyData && isMultiSimulationMode()) {
        renderTopology();
    }
}

function addMultiDestination(nodeId, { announce = true } = {}) {
    if (!nodeId) {
        return false;
    }
    const sourceId = sourceSelect ? sourceSelect.value : null;
    if (nodeId === sourceId) {
        if (announce && hudStatus) {
            hudStatus.textContent = 'Destination cannot match the source node.';
        }
        return false;
    }
    if (multiDestinations.includes(nodeId)) {
        if (announce && hudStatus) {
            hudStatus.textContent = 'Destination already on the list.';
        }
        return false;
    }
    multiDestinations.push(nodeId);
    renderMultiDestinationList();
    if (announce && hudStatus) {
        const meta = nodeMeta.get(nodeId) || parseSelectValue(nodeId);
        hudStatus.textContent = `Added destination ${safeNodeLabel(meta)}.`;
    }
    return true;
}

function removeMultiDestination(nodeId, { announce = true } = {}) {
    const index = multiDestinations.indexOf(nodeId);
    if (index === -1) {
        return false;
    }
    const meta = nodeMeta.get(nodeId) || parseSelectValue(nodeId);
    multiDestinations.splice(index, 1);
    renderMultiDestinationList();
    if (announce && hudStatus) {
        hudStatus.textContent = `Removed ${safeNodeLabel(meta)} from destinations.`;
    }
    return true;
}

function clearMultiDestinationList({ announce = true } = {}) {
    if (!multiDestinations.length) {
        if (announce && hudStatus) {
            hudStatus.textContent = 'Destination list is already empty.';
        }
        renderMultiDestinationList();
        return;
    }
    multiDestinations.length = 0;
    renderMultiDestinationList();
    if (announce && hudStatus) {
        hudStatus.textContent = 'Destination list cleared.';
    }
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

function applyBufferRuntime(buffer, { used, state, head } = {}) {
    if (!buffer || typeof buffer !== 'object') return;
    if (Number.isFinite(used)) {
        if (Number.isFinite(buffer.capacity) && buffer.capacity > 0) {
            buffer.used = clamp(used, 0, buffer.capacity);
        } else {
            buffer.used = used;
            if (!Number.isFinite(buffer.capacity) || buffer.capacity < used) {
                buffer.capacity = used;
            }
        }
    }
    if (head !== undefined) {
        buffer.head = head;
    }
    if (state) {
        buffer.state = state;
    }
}

function setHandshakePins(ifaceRuntime, pins = {}) {
    if (!ifaceRuntime || typeof ifaceRuntime !== 'object') return;
    const { handshakePins } = ifaceRuntime;
    if (!handshakePins || typeof handshakePins !== 'object') return;
    handshakePins.req = Boolean(pins.req);
    handshakePins.ack = Boolean(pins.ack);
    handshakePins.data = Boolean(pins.data);
    handshakePins.choke = Boolean(pins.choke);
}

function setStatusBits(ifaceRuntime, bits = {}) {
    if (!ifaceRuntime || typeof ifaceRuntime !== 'object') return;
    const { statusBits } = ifaceRuntime;
    if (!statusBits || typeof statusBits !== 'object') return;
    statusBits.busy = Boolean(bits.busy);
    statusBits.transfer = Boolean(bits.transfer);
    statusBits.receive = Boolean(bits.receive);
}

function ensureActivePacketMap(ifaceRuntime) {
    if (!ifaceRuntime) return null;
    if (!(ifaceRuntime.activePackets instanceof Map)) {
        ifaceRuntime.activePackets = new Map();
    }
    return ifaceRuntime.activePackets;
}

const STAGE_PRIORITY = {
    ready: 1,
    req: 2,
    ack: 3,
    data: 4,
    release: 5,
    completed: 6,
};

const SEND_BUFFER_STATE_BY_STAGE = {
    ready: 'primed',
    req: 'waiting',
    ack: 'waiting',
    data: 'transferring',
    release: 'releasing',
    completed: 'idle',
};

const RECEIVE_BUFFER_STATE_BY_STAGE = {
    ready: 'idle',
    req: 'idle',
    ack: 'primed',
    data: 'receiving',
    release: 'delivered',
    completed: 'delivered',
};

function pickRepresentativePacket(entries) {
    if (!entries.length) return null;
    return entries
        .slice()
        .sort((a, b) => {
            const priorityDiff = (STAGE_PRIORITY[b.stage] || 0) - (STAGE_PRIORITY[a.stage] || 0);
            if (priorityDiff !== 0) return priorityDiff;
            return (b.lastUpdated || 0) - (a.lastUpdated || 0);
        })[0];
}

function summarizeInterfaceRuntime(ifaceRuntime) {
    if (!ifaceRuntime) return;
    const packets = ensureActivePacketMap(ifaceRuntime);
    if (!packets) return;

    if (!ifaceRuntime.sendBuffer) {
        ifaceRuntime.sendBuffer = { used: 0, capacity: 0, head: null, state: 'idle' };
    }
    if (!ifaceRuntime.receiveBuffer) {
        ifaceRuntime.receiveBuffer = { used: 0, capacity: 0, head: null, state: 'idle' };
    }
    if (!ifaceRuntime.statusBits) {
        ifaceRuntime.statusBits = { busy: false, transfer: false, receive: false };
    }
    if (!ifaceRuntime.handshakePins) {
        ifaceRuntime.handshakePins = { req: false, ack: false, data: false, choke: false };
    }

    const outbound = [];
    const inbound = [];
    packets.forEach((info, key) => {
        if (!info) return;
        const entry = {
            key,
            stage: info.stage,
            packet: info.packet || null,
            lastUpdated: info.lastUpdated || 0,
        };
        if (info.direction === 'inbound') {
            inbound.push(entry);
        } else {
            outbound.push(entry);
        }
    });

    const outboundRep = pickRepresentativePacket(outbound);
    const inboundRep = pickRepresentativePacket(inbound);

    ifaceRuntime.sendBuffer.used = outbound.length;
    ifaceRuntime.sendBuffer.state = outbound.length
        ? SEND_BUFFER_STATE_BY_STAGE[outboundRep?.stage] || 'transferring'
        : 'idle';
    ifaceRuntime.sendBuffer.head = outboundRep?.packet || null;

    ifaceRuntime.receiveBuffer.used = inbound.length;
    ifaceRuntime.receiveBuffer.state = inbound.length
        ? RECEIVE_BUFFER_STATE_BY_STAGE[inboundRep?.stage] || 'receiving'
        : 'idle';
    ifaceRuntime.receiveBuffer.head = inboundRep?.packet || null;

    const outboundStages = outbound.map((entry) => entry.stage);
    const inboundStages = inbound.map((entry) => entry.stage);

    const anyReq = outboundStages.some((stage) => ['req', 'ack', 'data'].includes(stage))
        || inboundStages.some((stage) => ['req', 'ack', 'data'].includes(stage));
    const anyAck = outboundStages.some((stage) => ['ack', 'data', 'release'].includes(stage))
        || inboundStages.some((stage) => ['ack', 'data', 'release'].includes(stage));
    const anyData = outboundStages.includes('data') || inboundStages.includes('data');

    ifaceRuntime.handshakePins.req = anyReq;
    ifaceRuntime.handshakePins.ack = anyAck;
    ifaceRuntime.handshakePins.data = anyData;
    ifaceRuntime.handshakePins.choke = false;

    ifaceRuntime.statusBits.busy = outbound.length > 0 || inbound.length > 0;
    ifaceRuntime.statusBits.transfer = outboundStages.includes('data');
    ifaceRuntime.statusBits.receive = inboundStages.includes('data');

    ifaceRuntime.sendRegister = outboundRep?.packet || null;
    ifaceRuntime.receiveRegister = inboundRep?.packet || null;
    const dataRep = outbound.find((entry) => entry.stage === 'data') || inbound.find((entry) => entry.stage === 'data');
    ifaceRuntime.dataLine = dataRep?.packet || null;

    if (ifaceRuntime.timeout) {
        ifaceRuntime.timeout.value = 0;
    }
}

function recordInterfacePacketStage(ifaceRuntime, packetKey, {
    direction = 'outbound',
    stage,
    packet = null,
    timestamp = performance.now(),
    remove = false,
} = {}) {
    if (!ifaceRuntime || !packetKey) return;
    const packets = ensureActivePacketMap(ifaceRuntime);
    if (!packets) return;

    if (remove || stage === 'completed') {
        packets.delete(packetKey);
    } else {
        const existing = packets.get(packetKey) || {};
        packets.set(packetKey, {
            direction: direction === 'inbound' ? 'inbound' : 'outbound',
            stage,
            packet: packet || existing.packet || null,
            lastUpdated: timestamp,
        });
    }

    summarizeInterfaceRuntime(ifaceRuntime);
}

function createPacketKey(status, animationContext, segment, fallbackDestination) {
    if (status?.packetIndex) {
        return `packet-${status.packetIndex}`;
    }
    if (animationContext?.packetIndex) {
        return `packet-${animationContext.packetIndex}`;
    }
    const destination = fallbackDestination
        ? makeNodeId(fallbackDestination)
        : segment?.to
            ? makeNodeId(segment.to)
            : 'unknown';
    const pathSignature = Array.isArray(animationContext?.path)
        ? routePathSignature(animationContext.path)
        : null;
    if (pathSignature) {
        return `${pathSignature}`;
    }
    return `pkt-${destination}`;
}

function derivePacketSummary(context, segment = null) {
    if (context && typeof context === 'object' && context.packetSummary) {
        return context.packetSummary;
    }
    const path = Array.isArray(context?.path) ? context.path : [];
    const fallbackPath = Array.isArray(segment?.path) ? segment.path : [];
    const resolvedPath = path.length ? path : fallbackPath;
    let source = resolvedPath.length ? resolvedPath[0] : segment?.from || null;
    let destination = resolvedPath.length
        ? resolvedPath[resolvedPath.length - 1]
        : segment?.to || null;
    const data = context?.packet?.data ?? context?.packetData ?? context?.data ?? null;
    if (!source && segment?.from) {
        source = segment.from;
    }
    if (!destination && segment?.to) {
        destination = segment.to;
    }
    if (!source && !destination && data == null) {
        return null;
    }
    return {
        source,
        destination,
        data,
    };
}

function resolveBufferSnapshot(metaSnapshot, runtimeSnapshot) {
    if (!metaSnapshot && !runtimeSnapshot) {
        return {
            used: 0,
            capacity: 0,
            head: null,
            state: null,
        };
    }
    const used = Number(runtimeSnapshot?.used ?? metaSnapshot?.used ?? 0) || 0;
    const capacity = Number(runtimeSnapshot?.capacity ?? metaSnapshot?.capacity ?? 0) || 0;
    const head = runtimeSnapshot?.head ?? metaSnapshot?.head ?? null;
    const state = runtimeSnapshot?.state ?? metaSnapshot?.state ?? null;
    return {
        used,
        capacity,
        head,
        state,
    };
}

function describeBufferSnapshot(snapshot) {
    if (!snapshot || typeof snapshot !== 'object') {
        return { primary: '—', secondary: null };
    }
    const used = Number(snapshot.used ?? 0);
    const capacity = Number(snapshot.capacity ?? 0);
    const primary = capacity
        ? `${used} / ${capacity} slot${capacity === 1 ? '' : 's'}`
        : `${used} slot${used === 1 ? '' : 's'}`;
    const stateKey = snapshot.state || null;
    const stateLabel = stateKey ? (BUFFER_STATE_LABELS[stateKey] || stateKey) : null;
    const headText = snapshot.head
        ? `Head: ${formatPacketSummary(snapshot.head)}`
        : 'Head: empty';
    const parts = [];
    if (stateLabel) {
        parts.push(`State: ${stateLabel}`);
    }
    parts.push(headText);
    const secondary = parts.filter(Boolean).join(' · ');
    return { primary, secondary };
}

function createMetricEntry(label, primary, secondary) {
    const wrapper = document.createElement('div');
    const dt = document.createElement('dt');
    dt.textContent = label;
    const dd = document.createElement('dd');
    dd.textContent = primary || '—';
    if (secondary) {
        const span = document.createElement('span');
        span.className = 'metric-secondary';
        span.textContent = secondary;
        dd.appendChild(document.createElement('br'));
        dd.appendChild(span);
    }
    wrapper.appendChild(dt);
    wrapper.appendChild(dd);
    return wrapper;
}

function formatPacketSummary(packet) {
    if (!packet || typeof packet !== 'object') {
        return 'Empty';
    }
    const source = safeNodeLabel(packet.source || packet.source_address || {});
    const destination = safeNodeLabel(packet.destination || packet.dest_address || {});
    const data = typeof packet.data === 'string' && packet.data.length ? ` · ${packet.data}` : '';
    return `${source} → ${destination}${data}`;
}

function createSignalChip(label, isHigh) {
    const chip = document.createElement('span');
    chip.className = 'signal-chip';
    chip.dataset.state = isHigh ? 'high' : 'low';
    chip.textContent = `${label}: ${isHigh ? 'High' : 'Low'}`;
    return chip;
}

function createBitChip(label, state) {
    const chip = document.createElement('span');
    chip.className = 'bit-chip';
    chip.dataset.state = state;
    const labels = {
        active: 'Active',
        idle: 'Idle',
        transfer: 'Transferring',
        receiving: 'Receiving',
    };
    chip.textContent = `${label}: ${labels[state] || 'Idle'}`;
    return chip;
}

function createRegisterRow(label, packet) {
    const row = document.createElement('p');
    row.textContent = `${label}: ${formatPacketSummary(packet)}`;
    return row;
}

function renderNodeLogicSection(meta, runtime) {
    if (!nodePanelLogic) return;
    nodePanelLogic.innerHTML = '';

    const logic = meta?.logic || {};
    const routingCount = typeof logic.routing?.entryCount === 'number'
        ? logic.routing.entryCount
        : Array.isArray(meta?.routingTable)
            ? meta.routingTable.length
            : 0;
    const runtimeInterfaces = runtime?.interfaces instanceof Map
        ? Array.from(runtime.interfaces.values())
        : [];
    const totalInterfacesRaw = typeof logic.control?.totalInterfaces === 'number'
        ? logic.control.totalInterfaces
        : Array.isArray(meta?.interfaces)
            ? meta.interfaces.length
            : runtimeInterfaces.length;
    const totalInterfaces = Number.isFinite(totalInterfacesRaw) ? totalInterfacesRaw : runtimeInterfaces.length;
    const activeInterfaces = runtimeInterfaces.reduce((count, iface) => {
        if (!iface) return count;
        const bits = iface.statusBits || {};
        return bits.busy || bits.transfer || bits.receive ? count + 1 : count;
    }, 0);
    const runtimeApp = Number(runtime?.applicationBuffer ?? 0);
    const logicApp = Number(logic.application?.bufferedPackets ?? 0);
    const metaApp = Number(meta?.applicationBuffer?.count ?? 0);
    const bufferedPackets = Math.max(
        Number.isFinite(runtimeApp) ? runtimeApp : 0,
        Number.isFinite(logicApp) ? logicApp : 0,
        Number.isFinite(metaApp) ? metaApp : 0,
    );

    const entries = [
        {
            label: 'Routing',
            primary: logic.routing?.description
                || `${routingCount} destination entries`,
            secondary: `Entries: ${routingCount}`,
        },
        {
            label: 'Application',
            primary: bufferedPackets > 0
                ? `${bufferedPackets} packet${bufferedPackets === 1 ? '' : 's'} staged`
                : 'Application buffer empty',
            secondary: `Buffered: ${bufferedPackets}`,
        },
        {
            label: 'Control',
            primary: activeInterfaces > 0
                ? `${activeInterfaces} interface${activeInterfaces === 1 ? '' : 's'} active`
                : 'All interfaces idle',
            secondary: `Active: ${activeInterfaces} / ${totalInterfaces}`,
        },
    ];

    entries.forEach((entry) => {
        nodePanelLogic.appendChild(createMetricEntry(entry.label, entry.primary, entry.secondary));
    });
}

function renderNodeInterfacesSection(meta, runtime) {
    if (!nodePanelInterfaces) return;
    nodePanelInterfaces.innerHTML = '';

    const interfaces = Array.isArray(meta?.interfaces) ? meta.interfaces.slice() : [];
    if (!interfaces.length) {
        const empty = document.createElement('p');
        empty.className = 'interface-empty';
        empty.textContent = 'No connected interfaces.';
        nodePanelInterfaces.appendChild(empty);
        return;
    }

    const keyForInterface = (iface) => {
        const neighbor = iface?.neighbor || {};
        if (typeof neighbor.ring === 'number' && typeof neighbor.index === 'number') {
            return `${neighbor.ring}-${neighbor.index}`;
        }
        return '0-0';
    };

    const runtimeInterfaces = runtime?.interfaces instanceof Map ? runtime.interfaces : null;
    const interfaceEntries = interfaces.map((iface) => {
        const neighborId = iface.neighbor ? makeNodeId(iface.neighbor) : null;
        const runtimeOverlay = neighborId && runtimeInterfaces?.get(neighborId)
            ? runtimeInterfaces.get(neighborId)
            : null;
        let activityScore = 0;
        if (runtimeOverlay) {
            const statusBits = runtimeOverlay.statusBits || {};
            if (statusBits.busy) activityScore += 8;
            if (statusBits.transfer) activityScore += 4;
            if (statusBits.receive) activityScore += 4;
            const sendUsed = Number(runtimeOverlay?.sendBuffer?.used || 0);
            const recvUsed = Number(runtimeOverlay?.receiveBuffer?.used || 0);
            if (sendUsed > 0) activityScore += 2;
            if (recvUsed > 0) activityScore += 2;
            const pins = runtimeOverlay.handshakePins || {};
            if (pins.req || pins.ack || pins.data || pins.choke) {
                activityScore += 1;
            }
        } else {
            const statusBits = iface.statusBits || {};
            if (statusBits.busy) activityScore += 4;
            if (statusBits.transfer) activityScore += 2;
            if (statusBits.receive) activityScore += 2;
            const pins = iface.handshakePins || {};
            if (pins.req || pins.ack || pins.data || pins.choke) {
                activityScore += 1;
            }
        }
        return {
            iface,
            runtimeOverlay,
            neighborId,
            key: keyForInterface(iface),
            activityScore,
        };
    });

    interfaceEntries
        .sort((a, b) => {
            if (b.activityScore !== a.activityScore) {
                return b.activityScore - a.activityScore;
            }
            return a.key.localeCompare(b.key);
        })
        .forEach(({ iface, runtimeOverlay, neighborId }) => {
            const card = document.createElement('article');
            card.className = 'interface-card';

            const header = document.createElement('div');
            header.className = 'interface-card__header';
            const title = document.createElement('h4');
            title.textContent = `Interface to ${safeNodeLabel(iface.neighbor || {})}`;
            const badge = document.createElement('span');
            badge.className = 'interface-card__badge';
            badge.dataset.variant = iface.linkType === 'ring' ? 'ring' : 'tree';
            badge.textContent = iface.linkType === 'ring' ? 'Ring link' : 'Tree link';
            header.appendChild(title);
            header.appendChild(badge);
            card.appendChild(header);

            const sendSnapshot = resolveBufferSnapshot(iface.sendBuffer, runtimeOverlay?.sendBuffer);
            const recvSnapshot = resolveBufferSnapshot(iface.receiveBuffer, runtimeOverlay?.receiveBuffer);
            if (runtimeOverlay?.sendBuffer?.state) {
                sendSnapshot.state = runtimeOverlay.sendBuffer.state;
            }
            if (runtimeOverlay?.receiveBuffer?.state) {
                recvSnapshot.state = runtimeOverlay.receiveBuffer.state;
            }
            const activePacketsMap = runtimeOverlay?.activePackets instanceof Map
                ? runtimeOverlay.activePackets
                : null;

            const metrics = document.createElement('dl');
            metrics.className = 'interface-metrics';
            const formattedSend = describeBufferSnapshot(sendSnapshot);
            metrics.appendChild(createMetricEntry('Send buffer', formattedSend.primary, formattedSend.secondary));
            const formattedRecv = describeBufferSnapshot(recvSnapshot);
            metrics.appendChild(createMetricEntry('Receive buffer', formattedRecv.primary, formattedRecv.secondary));
            if (activePacketsMap) {
                const totalActive = activePacketsMap.size;
                let outboundCount = 0;
                let inboundCount = 0;
                const stageCounts = new Map();
                activePacketsMap.forEach((info) => {
                    if (!info) return;
                    if (info.direction === 'inbound') {
                        inboundCount += 1;
                    } else {
                        outboundCount += 1;
                    }
                    if (typeof info.stage === 'string' && info.stage.length) {
                        const stageKey = info.stage;
                        stageCounts.set(stageKey, (stageCounts.get(stageKey) || 0) + 1);
                    }
                });
                const activePrimary = totalActive
                    ? `${totalActive} packet${totalActive === 1 ? '' : 's'} in flight`
                    : 'No packets in flight';
                const directionParts = [];
                if (outboundCount) {
                    directionParts.push(`${outboundCount} outbound`);
                }
                if (inboundCount) {
                    directionParts.push(`${inboundCount} inbound`);
                }
                const stageParts = Array.from(stageCounts.entries())
                    .sort((a, b) => (STAGE_PRIORITY[b[0]] || 0) - (STAGE_PRIORITY[a[0]] || 0))
                    .map(([stageKey, count]) => `${count} ${stageKey}`);
                const secondaryParts = [];
                if (directionParts.length) {
                    secondaryParts.push(directionParts.join(' · '));
                }
                if (stageParts.length) {
                    secondaryParts.push(`Stages: ${stageParts.join(', ')}`);
                }
                const activeSecondary = secondaryParts.join(' · ');
                metrics.appendChild(createMetricEntry('Active packets', activePrimary, activeSecondary || null));
            }
            const timeoutBase = runtimeOverlay?.timeout || iface.timeout || {};
            const timeoutText = Number.isFinite(timeoutBase.value) && Number.isFinite(timeoutBase.limit)
                ? `${timeoutBase.value} / ${timeoutBase.limit}`
                : '—';
            metrics.appendChild(createMetricEntry('Timeout', timeoutText));
            card.appendChild(metrics);

            const statusRow = document.createElement('div');
            statusRow.className = 'interface-status-row';
            const statusBits = {
                ...iface.statusBits,
                ...(runtimeOverlay?.statusBits || {}),
            };
            statusRow.appendChild(createBitChip('Busy', statusBits.busy ? 'active' : 'idle'));
            statusRow.appendChild(createBitChip('Transfer', statusBits.transfer ? 'transfer' : 'idle'));
            statusRow.appendChild(createBitChip('Receive', statusBits.receive ? 'receiving' : 'idle'));
            card.appendChild(statusRow);

            const signalRow = document.createElement('div');
            signalRow.className = 'interface-signal-row';
            const pins = {
                ...iface.handshakePins,
                ...(runtimeOverlay?.handshakePins || {}),
            };
            signalRow.appendChild(createSignalChip('REQ', Boolean(pins.req)));
            signalRow.appendChild(createSignalChip('ACK', Boolean(pins.ack)));
            signalRow.appendChild(createSignalChip('DATA', Boolean(pins.data)));
            signalRow.appendChild(createSignalChip('CHOKE', Boolean(pins.choke)));
            card.appendChild(signalRow);

            const registers = document.createElement('div');
            registers.className = 'interface-registers';
            registers.appendChild(createRegisterRow('Send register', runtimeOverlay?.sendRegister || iface.sendRegister));
            registers.appendChild(createRegisterRow('Receive register', runtimeOverlay?.receiveRegister || iface.receiveRegister));
            registers.appendChild(createRegisterRow('Data line', runtimeOverlay?.dataLine || iface.dataLine));
            card.appendChild(registers);

            nodePanelInterfaces.appendChild(card);
        });
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
    nodePanelSubhead.textContent = `Ring ${meta.ring} core`;
    nodePanelRing.textContent = `${meta.ring}`;
    nodePanelDegree.textContent = `${meta.degree ?? 0}`;
    const routingCount = Array.isArray(meta.routingTable) ? meta.routingTable.length : 0;
    nodePanelRoutes.textContent = routingCount ? `${routingCount}` : '0';

    renderNodeLogicSection(meta, runtime);
    renderNodeInterfacesSection(meta, runtime);

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
                    const sendUsage = Number.isFinite(neighbor.sendUsage)
                        ? neighbor.sendUsage
                        : null;
                    const recvUsage = Number.isFinite(neighbor.receiveUsage)
                        ? neighbor.receiveUsage
                        : null;
                    const typeLabel = neighbor.type === 'ring' ? 'RING' : 'TREE';
                    const sendDescriptor = sendUsage !== null && sendCap !== '–'
                        ? `${sendUsage}/${sendCap}`
                        : `${sendCap}`;
                    const recvDescriptor = recvUsage !== null && recvCap !== '–'
                        ? `${recvUsage}/${recvCap}`
                        : `${recvCap}`;
                    type.textContent = `${typeLabel} · S:${sendDescriptor} R:${recvDescriptor}`;
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

    const interfaces = Array.isArray(meta.interfaces) ? meta.interfaces : [];
    const runtimeInterfaces = runtime?.interfaces instanceof Map ? runtime.interfaces : null;
    const aggregateBuffers = (key) => interfaces.reduce((acc, iface) => {
        if (!iface) return acc;
        const neighborId = iface.neighbor ? makeNodeId(iface.neighbor) : null;
        const runtimeOverlay = neighborId && runtimeInterfaces?.get(neighborId) ? runtimeInterfaces.get(neighborId) : null;
        const snapshot = resolveBufferSnapshot(iface?.[key], runtimeOverlay?.[key]);
        acc.used += Number(snapshot.used || 0);
        acc.capacity += Number(snapshot.capacity || 0);
        return acc;
    }, { used: 0, capacity: 0 });

    const sendTotals = aggregateBuffers('sendBuffer');
    const recvTotals = aggregateBuffers('receiveBuffer');
    const formatTotal = (totals) => {
        const { used, capacity } = totals;
        if (capacity > 0) {
            return `${used} / ${capacity} slot${capacity === 1 ? '' : 's'}`;
        }
        return `${used} slot${used === 1 ? '' : 's'}`;
    };

    updateBufferChip(nodePanelSendBuffer, runtime.sendBuffer, formatTotal(sendTotals));
    updateBufferChip(nodePanelReceiveBuffer, runtime.receiveBuffer, formatTotal(recvTotals));

    const appBuffer = meta.applicationBuffer || {};
    const appCount = Number(appBuffer.count || 0);
    const runtimeAppCount = Number(runtime.applicationBuffer || 0);
    const appState = appCount > 0 || runtimeAppCount > 0 ? 'ready' : 'idle';
    const appDisplayCount = appCount > 0 ? appCount : runtimeAppCount;
    updateBufferChip(
        nodePanelAppBuffer,
        appState,
        `${appDisplayCount} ${appDisplayCount === 1 ? 'packet' : 'packets'}`,
    );

    let assertedSignals = 0;
    interfaces.forEach((iface) => {
        if (!iface) return;
        const neighborId = iface.neighbor ? makeNodeId(iface.neighbor) : null;
        const runtimeOverlay = neighborId && runtimeInterfaces?.get(neighborId) ? runtimeInterfaces.get(neighborId) : null;
        const pins = {
            ...iface.handshakePins,
            ...(runtimeOverlay?.handshakePins || {}),
        };
        assertedSignals += Number(Boolean(pins.req));
        assertedSignals += Number(Boolean(pins.ack));
        assertedSignals += Number(Boolean(pins.data));
        assertedSignals += Number(Boolean(pins.choke));
    });
    const handshakeActiveState = runtime.handshake !== 'idle'
        ? runtime.handshake
        : assertedSignals > 0
            ? 'primed'
            : 'idle';
    const handshakeText = runtime.handshake !== 'idle'
        ? BUFFER_STATE_LABELS[runtime.handshake] || runtime.handshake
        : assertedSignals > 0
            ? `${assertedSignals} signal${assertedSignals === 1 ? '' : 's'} asserted`
            : 'Idle';
    updateBufferChip(nodePanelHandshake, handshakeActiveState, handshakeText);
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
    if (nodePanelLogic) {
        nodePanelLogic.innerHTML = '';
    }
    if (nodePanelInterfaces) {
        nodePanelInterfaces.innerHTML = '';
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
    if (!pickMode && selectedNodeId === nodeId) {
        closeNodePanel();
        return;
    }
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
        const labelText = safeNodeLabel(meta);
        const mode = getSimulationMode();
        if (mode === 'parallel') {
            let applied = false;
            if (destinationCandidateSelect) {
                applied = setSelectValue(destinationCandidateSelect, nodeId);
            }
            if (!applied && destinationSelect) {
                applied = setSelectValue(destinationSelect, nodeId);
            }
            if (hudStatus) {
                hudStatus.textContent = applied
                    ? `Candidate destination set to ${labelText}. Press + to add to the list.`
                    : `Candidate destination ${labelText} ready.`;
            }
            focusNode(nodeId, {
                auto: nodePanelAutoTracking,
                openPanelOnFocus: true,
            });
            renderTopology();
        } else if (setSelectValue(destinationSelect, nodeId)) {
            handleDestinationSelectChange({
                announce: true,
                message: `Destination set to ${labelText} via canvas.`,
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

function safeNodeLabel(node) {
    if (!node || typeof node.ring !== 'number' || typeof node.index !== 'number') {
        return '(?, ?)';
    }
    return nodeLabel(node);
}

function routePathSignature(path) {
    if (!Array.isArray(path) || !path.length) {
        return null;
    }
    return path
        .map((node) => (node && typeof node.ring === 'number' && typeof node.index === 'number'
            ? `${node.ring}-${node.index}`
            : '∅'))
        .join('|');
}

function renderMultiRouteList() {
    if (!multiRouteList) return;
    if (!multiRunState || !Array.isArray(multiRunState.payloads) || !multiRunState.payloads.length) {
        multiRouteList.innerHTML = '';
        multiRouteList.style.display = 'none';
        return;
    }

    multiRouteList.innerHTML = '';
    multiRouteList.style.display = '';

    const title = document.createElement('p');
    title.className = 'flow-entry__phase';
    title.textContent = 'Parallel routes';
    multiRouteList.appendChild(title);

    const fragment = document.createDocumentFragment();
    const completedSet = multiRunState.completed instanceof Set ? multiRunState.completed : new Set();
    const activeIndex = typeof multiRunState.selectedIndex === 'number'
        ? multiRunState.selectedIndex
        : 0;

    multiRunState.payloads.forEach((payload, index) => {
        const card = document.createElement('article');
        card.className = 'flow-entry multi-route-entry';
        card.dataset.routeIndex = `${index}`;

        const isCompleted = completedSet.has(index);
        const isActive = typeof activeIndex === 'number' && activeIndex === index;

        if (isActive) {
            card.classList.add('flow-entry--active');
        }
        if (isCompleted) {
            card.style.opacity = '0.65';
        }

        if (multiRunState.mode === 'parallel') {
            card.setAttribute('role', 'button');
            card.tabIndex = 0;
            card.style.cursor = 'pointer';
        }

        const status = document.createElement('p');
        status.className = 'flow-entry__phase';
        status.textContent = isCompleted ? 'Completed' : 'Pending';
        card.appendChild(status);

        const titleEl = document.createElement('h3');
        titleEl.className = 'flow-entry__title';
        const pathArray = Array.isArray(payload.path) ? payload.path : [];
        const startNode = pathArray[0] || multiRunState.source || payload.source;
        const endNode = pathArray[pathArray.length - 1] || payload.destination || startNode;
        const packetLabel = payload.packetIndex ? `Packet ${payload.packetIndex}` : `Packet ${index + 1}`;
        titleEl.textContent = `${packetLabel}: ${safeNodeLabel(startNode)} → ${safeNodeLabel(endNode)}`;
        card.appendChild(titleEl);

        const details = document.createElement('ul');
        details.className = 'flow-entry__details';
        const packetCountItem = document.createElement('li');
        const packetCount = payload.packetCount || multiRunState.payloads.length;
        packetCountItem.textContent = `${packetLabel} of ${packetCount}`;
        details.appendChild(packetCountItem);
        const hopItem = document.createElement('li');
        hopItem.textContent = `Hop count: ${payload.hopCount ?? 0}`;
        details.appendChild(hopItem);

        if (multiRunState.mode === 'parallel' && !isCompleted) {
            const hintItem = document.createElement('li');
            hintItem.textContent = 'Click to preview';
            details.appendChild(hintItem);
        }

        card.appendChild(details);
        fragment.appendChild(card);
    });

    multiRouteList.appendChild(fragment);
    multiRouteList.scrollTop = 0;

}

function handleMultiRouteListClick(event) {
    const target = event.target.closest('.multi-route-entry');
    if (!target || !multiRunState) return;
    const index = parseInt(target.dataset.routeIndex, 10);
    if (Number.isNaN(index)) return;
    if (multiRunState.mode === 'parallel') {
        focusParallelRoute(index);
    }
}

function handleMultiRouteListKeydown(event) {
    if (event.key !== 'Enter' && event.key !== ' ') return;
    const target = event.target.closest('.multi-route-entry');
    if (!target || !multiRunState) return;
    event.preventDefault();
    const index = parseInt(target.dataset.routeIndex, 10);
    if (Number.isNaN(index)) return;
    if (multiRunState.mode === 'parallel') {
        focusParallelRoute(index);
    }
}

function ensureParallelCompletionSet() {
    if (!multiRunState || multiRunState.mode !== 'parallel') {
        return null;
    }
    if (!(multiRunState.completed instanceof Set)) {
        multiRunState.completed = new Set();
    }
    return multiRunState.completed;
}

function updateParallelRouteProgress(statuses = []) {
    const completedSet = ensureParallelCompletionSet();
    if (!completedSet) return;
    let changed = false;

    statuses.forEach((status, index) => {
        if (!status) return;
        const isCompleted = status.phaseKey === 'completed' || status.phaseLabel === 'Completed';
        if (isCompleted && !completedSet.has(index)) {
            completedSet.add(index);
            changed = true;
            if (!Array.isArray(multiRunState.completedRoutes)) {
                multiRunState.completedRoutes = [];
            }
            if (!Array.isArray(multiRunState.completedStatuses)) {
                multiRunState.completedStatuses = [];
            }
            multiRunState.completedStatuses[index] = {
                ...status,
                signalStates: {
                    ...(status.signalStates || {}),
                },
            };
            const payload = Array.isArray(multiRunState.payloads)
                ? multiRunState.payloads[index]
                : null;
            if (payload) {
                multiRunState.completedRoutes[index] = new RoutePreview(payload, {
                    renderStyle: 'completed',
                    strokeOpacity: 0.95,
                    lineWidth: 4,
                });
            }
            if (Array.isArray(multiRunState.previewRoutes) && multiRunState.previewRoutes[index]) {
                multiRunState.previewRoutes[index].renderStyle = 'completed';
                multiRunState.previewRoutes[index].strokeOpacity = Math.max(
                    multiRunState.previewRoutes[index].strokeOpacity || 0.85,
                    0.85,
                );
            }
        }
    });

    if (changed) {
        renderMultiRouteList();
    }
}

function buildCompletedStatusFromPayload(payload) {
    const segments = Array.isArray(payload?.segments) ? payload.segments : [];
    const path = Array.isArray(payload?.path) ? payload.path : [];
    const totalHops = segments.length || Number(payload?.hopCount ?? 0) || 0;
    const startNode = segments[0]?.from
        || path[0]
        || payload?.packet?.source
        || payload?.source
        || null;
    const endNode = segments.length
        ? segments[segments.length - 1]?.to
        : path[path.length - 1]
            || payload?.packet?.destination
            || payload?.destination
            || startNode;

    return {
        hopText: totalHops > 0 ? `${totalHops} / ${totalHops}` : '0 / 0',
        nodesText: startNode && endNode
            ? `${safeNodeLabel(startNode)} → ${safeNodeLabel(endNode)}`
            : 'Route complete',
        phaseKey: 'completed',
        phaseLabel: 'Completed',
        signalText: 'Idle',
        signalStates: { req: 'sleep', ack: 'sleep', data: 'sleep' },
        transferText: 'Packet delivered',
        progressPercent: 100,
        timer: 0,
    };
}

function focusParallelRoute(index) {
    if (!multiRunState || multiRunState.mode !== 'parallel') return;
    if (!Array.isArray(multiRunState.payloads) || index < 0 || index >= multiRunState.payloads.length) {
        return;
    }

    multiRunState.selectedIndex = index;
    renderMultiRouteList();
    highlightMultiRouteCard(index);

    const payload = multiRunState.payloads[index];
    const completedSet = ensureParallelCompletionSet();
    const previewEntry = Array.isArray(multiRunState.previewRoutes)
        ? multiRunState.previewRoutes[index]
        : null;
    const isCompleted = Boolean(completedSet?.has(index) || previewEntry?.renderStyle === 'completed');
    const storedStatus = Array.isArray(multiRunState.completedStatuses)
        ? multiRunState.completedStatuses[index]
        : null;
    const previewColors = !isCompleted && previewEntry
        ? {
            treeColor: previewEntry.treeColor,
            ringColor: previewEntry.ringColor,
            strokeOpacity: 0.9,
            lineWidth: 4,
        }
        : null;
    const initialStatus = isCompleted
        ? storedStatus
            ? {
                ...storedStatus,
                signalStates: {
                    ...(storedStatus.signalStates || {}),
                },
            }
            : buildCompletedStatusFromPayload(payload)
        : null;
    prepareRoute(payload, {
        contextLabel: `Packet ${payload.packetIndex || index + 1} of ${payload.packetCount || multiRunState.payloads.length}`,
        contextHint: isCompleted
            ? 'Packet delivered. Click "Animate all" to replay the batch.'
            : 'Preview loaded. Click "Animate all" to start simultaneous transfer.',
        buttonLabel: 'Animate all',
        previewColors,
        initialStatus,
        previewStyle: isCompleted ? 'completed' : 'active',
        isCompleted,
    });

    lastRoutePayload = payload;
    updateAnimateButton({
        disabled: !payload?.segments?.length,
        busy: false,
        label: 'Animate all',
    });
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
function showRouteReadyStatus(payload, { transferText } = {}) {
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
        transferText: transferText || 'Press Animate',
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

function updateAnimateButton({ disabled, busy = false, label } = {}) {
    if (!animateBtn) return;
    if (typeof disabled === 'boolean') {
        animateBtn.disabled = disabled;
    }
    if (label) {
        animateBtn.dataset.currentLabel = label;
    } else if (!animateBtn.dataset.currentLabel) {
        animateBtn.dataset.currentLabel = animateBtn.dataset.defaultLabel || 'Animate path';
    }
    const currentLabel = animateBtn.dataset.currentLabel || animateBtn.dataset.defaultLabel || 'Animate path';
    animateBtn.textContent = busy ? 'Animating…' : currentLabel;
}

function hasRouteReadyForRestart() {
    const parallelReady = Boolean(
        multiRunState
        && multiRunState.mode === 'parallel'
        && Array.isArray(multiRunState.payloads)
        && multiRunState.payloads.some((payload) => Array.isArray(payload?.segments) && payload.segments.length),
    );
    if (parallelReady) {
        return true;
    }
    return Boolean(
        lastRoutePayload
        && Array.isArray(lastRoutePayload.segments)
        && lastRoutePayload.segments.length,
    );
}

function updateAnimationControlState() {
    if (pauseAnimationBtn) {
        const isRunning = Boolean(animationState);
        const label = animationPaused ? 'Resume animation' : 'Pause animation';
        pauseAnimationBtn.disabled = !isRunning;
        pauseAnimationBtn.textContent = animationPaused ? '▶' : '⏸';
        pauseAnimationBtn.title = label;
        pauseAnimationBtn.setAttribute('aria-label', label);
        pauseAnimationBtn.setAttribute('aria-pressed', animationPaused ? 'true' : 'false');
    }
    if (restartAnimationBtn) {
        const routeReady = hasRouteReadyForRestart();
        restartAnimationBtn.disabled = !routeReady;
        restartAnimationBtn.title = routeReady ? 'Restart animation' : 'Restart animation (unavailable)';
        restartAnimationBtn.setAttribute('aria-label', 'Restart animation');
    }
}

function setAnimationPauseState(paused) {
    if (!animationState) {
        animationPaused = false;
        animationPauseTimestamp = null;
        updateAnimationControlState();
        return;
    }

    if (paused) {
        if (animationPaused) {
            return;
        }
        animationPaused = true;
        animationPauseTimestamp = performance.now();
        if (animationFrame) {
            cancelAnimationFrame(animationFrame);
            animationFrame = null;
        }
        if (hudStatus) {
            hudStatus.textContent = 'Animation paused';
        }
    } else {
        if (!animationPaused) {
            return;
        }
        const resumeTimestamp = performance.now();
        const delta = animationPauseTimestamp ? resumeTimestamp - animationPauseTimestamp : 0;
        animationPaused = false;
        animationPauseTimestamp = null;
        if (delta > 0 && animationState && typeof animationState.applyPauseOffset === 'function') {
            animationState.applyPauseOffset(delta);
        }
        if (typeof animationStep === 'function') {
            animationFrame = requestAnimationFrame(animationStep);
        }
        if (hudStatus) {
            hudStatus.textContent = 'Animation resumed';
        }
    }
    updateAnimationControlState();
}

function togglePauseAnimation() {
    if (!animationState) {
        return;
    }
    setAnimationPauseState(!animationPaused);
}

function restartAnimation() {
    if (!hasRouteReadyForRestart()) {
        if (hudStatus) {
            hudStatus.textContent = 'Nothing to restart yet. Run a simulation first.';
        }
        return;
    }
    stopAnimation();
    animationPaused = false;
    animationPauseTimestamp = null;
    playAnimation();
    updateAnimationControlState();
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
    nodeMeta.forEach((meta, nodeId) => {
        nodeRuntimeState.set(nodeId, defaultNodeRuntimeState(meta));
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
    updateAnimationControlState();
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
        if (!select) return;

        const previousValue = select.value;
        select.innerHTML = '';

        options.forEach((opt) => {
            const optionEl = document.createElement('option');
            optionEl.value = opt.value;
            optionEl.textContent = opt.label;
            select.appendChild(optionEl);
        });

        const hasPrevious = options.some((opt) => opt.value === previousValue);
        let fallbackValue = '';

        if (idx === 0) {
            fallbackValue = options.length ? options[0].value : '';
        } else if (idx === 1) {
            fallbackValue = options.length > 1 ? options[1].value : (options[0]?.value || '');
        }

        if (hasPrevious) {
            select.value = previousValue;
        } else if (fallbackValue) {
            select.value = fallbackValue;
        }
    });

    if (destinationCandidateSelect) {
        const previousValue = destinationCandidateSelect.value;
        destinationCandidateSelect.innerHTML = '';
        options.forEach((opt) => {
            const optionEl = document.createElement('option');
            optionEl.value = opt.value;
            optionEl.textContent = opt.label;
            destinationCandidateSelect.appendChild(optionEl);
        });

        if (options.length) {
            let fallback = previousValue;
            const hasPrevious = options.some((opt) => opt.value === fallback);
            if (!hasPrevious) {
                fallback = destinationSelect?.value || options[0].value;
            }
            destinationCandidateSelect.value = fallback;
        }
    }

    const validValues = new Set(options.map((opt) => opt.value));
    let removedAny = false;
    for (let i = multiDestinations.length - 1; i >= 0; i -= 1) {
        if (!validValues.has(multiDestinations[i])) {
            multiDestinations.splice(i, 1);
            removedAny = true;
        }
    }
    if (removedAny || (multiDestinationList && !multiDestinationList.children.length)) {
        renderMultiDestinationList();
    }
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
    const mode = getSimulationMode();
    const highlightMulti = mode === 'parallel';
    const multiDestinationSet = highlightMulti ? new Set(multiDestinations) : null;
    topologyData.nodes.forEach((node) => {
        const nodeId = makeNodeId(node);
        const pos = getNodePosition(node.ring, node.index, layout);
        const zoomRadius = clamp(viewState.zoom, 0.7, 1.6);
        const radius = (node.ring === 0 ? 10 : 6) * zoomRadius;
        nodePositions.set(nodeId, { x: pos.x, y: pos.y, radius });
        const isSelected = nodeId === selectedNodeId;
        const isSource = nodeId === currentSourceId;
        const isDestination = highlightMulti
            ? multiDestinationSet.has(nodeId)
            : nodeId === currentDestinationId;
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

function progressToSpatial(progress) {
    if (!Number.isFinite(progress)) {
        return 0;
    }
    const dataRange = PHASE_RANGES.data;
    if (progress <= dataRange[0]) {
        return 0;
    }
    if (progress < dataRange[1]) {
        const span = normalizeRange(progress, dataRange[0], dataRange[1]);
        return clamp(span * 0.85, 0, 0.85);
    }
    const releaseRange = PHASE_RANGES.release;
    if (progress <= releaseRange[0]) {
        return 0.85;
    }
    const releaseSpan = normalizeRange(progress, releaseRange[0], releaseRange[1] || 1);
    return clamp(0.85 + releaseSpan * 0.15, 0, 1);
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
        directionHint = false,
        suppressDirectionHintPhases = null,
        activePhaseKey = null,
        phaseIndicatorStages = null,
    } = options;

    const animationComplete = typeof state.isComplete === 'function' && state.isComplete();
    const previewComplete = state.renderStyle === 'completed' || options.forceCompleted === true;
    const isCompletedRoute = animationComplete || previewComplete;
    const activeTreeColor = isCompletedRoute ? colors.completedTree : treeColor;
    const activeRingColor = isCompletedRoute ? colors.completedRing : ringColor;
    const routeOpacity = isCompletedRoute ? Math.max(strokeOpacity, 0.9) : strokeOpacity;
    const directionHintSuppressed = Boolean(
        directionHint
        && !isCompletedRoute
        && suppressDirectionHintPhases
        && activePhaseKey
        && (
            typeof suppressDirectionHintPhases.has === 'function'
                ? suppressDirectionHintPhases.has(activePhaseKey)
                : Array.isArray(suppressDirectionHintPhases)
                    ? suppressDirectionHintPhases.includes(activePhaseKey)
                    : false
        ),
    );
    const allowDirectionHint = directionHint && !isCompletedRoute && !directionHintSuppressed;

    ctx.save();
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.lineWidth = lineWidth;
    const previousAlpha = ctx.globalAlpha;
    ctx.globalAlpha = routeOpacity;

    const currentInfoSnapshot = typeof state.currentSegment === 'function'
        ? state.currentSegment()
        : null;
    const currentIndex = currentInfoSnapshot ? currentInfoSnapshot.index : null;
    let currentArrowSample = null;
    state.segments.forEach((segment, idx) => {
        const progress = state.segmentProgress(idx);
        const completion = progressToSpatial(progress);
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
            ctx.strokeStyle = activeRingColor;
            ctx.arc(center.x, center.y, radius, startAngle, targetAngle, directionStep < 0);
            ctx.stroke();
        } else {
            const startPos = getNodePosition(from.ring, from.index, layout);
            const endPos = getNodePosition(to.ring, to.index, layout);
            ctx.beginPath();
            ctx.strokeStyle = activeTreeColor;
            const midX = startPos.x + (endPos.x - startPos.x) * clamp(completion, 0, 1);
            const midY = startPos.y + (endPos.y - startPos.y) * clamp(completion, 0, 1);
            ctx.moveTo(startPos.x, startPos.y);
            ctx.lineTo(midX, midY);
            ctx.stroke();
        }

        if (allowDirectionHint && completion > 0.1) {
            const baseProgress = completion;
            const arrowProgress = Math.min(Math.max(baseProgress, 0.2), 0.95);
            const arrowPoint = segmentPointWithAngle(segment, arrowProgress, layout, { allowClamp: true });
            const arrowColor = segment.type === 'ring' ? activeRingColor : activeTreeColor;
            drawFlowArrow(arrowPoint, arrowPoint.angle, arrowColor, { size: 12 });
            if (currentIndex === idx) {
                currentArrowSample = arrowPoint;
            }
        }
    });

    ctx.globalAlpha = previousAlpha;
    const current = currentInfoSnapshot;
    if (current) {
        const { segment, progress } = current;
        if (showPhaseIndicators) {
            const phaseOverrides = {
                dataPoint: currentArrowSample,
                allowFallback: Boolean(currentArrowSample),
            };
            drawPhaseIndicators(segment, progress, layout, phaseIndicatorStages, phaseOverrides);
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
        return { ...point, angle: tangent };        const alignedProgress = Math.min(Math.max(spatialProgress, 0.2), 0.95);
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

function drawFlowArrow(point, angle, color, { size = 12, style = 'solid' } = {}) {
    ctx.save();
    ctx.translate(point.x, point.y);
    ctx.rotate(angle);
    const tipLength = size;
    const halfBase = size * 0.55;
    ctx.beginPath();
    ctx.moveTo(0, 0);
    ctx.lineTo(-tipLength, halfBase);
    ctx.lineTo(-tipLength, -halfBase);
    ctx.closePath();
    if (style === 'outline') {
        ctx.lineWidth = 2.4;
        ctx.strokeStyle = color;
        ctx.stroke();
    } else {
        ctx.fillStyle = color;
        ctx.fill();
    }
    ctx.restore();
}

function drawDataMarker(point, angle, color) {
    ctx.save();
    ctx.translate(point.x, point.y);
    ctx.rotate(angle);
    // Offset slightly along the arrow direction so the circle sits at the tip.
    ctx.translate(4, 0);
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(0, 0, 7, 0, Math.PI * 2);
    ctx.fill();
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

function drawPhaseIndicators(segment, progress, layout, stageFilter = null, overrides = null) {
    const { req, ack, data, release } = PHASE_RANGES;
    const allowStage = (stageKey) => {
        if (!stageFilter) return true;
        if (stageFilter instanceof Set) {
            return stageFilter.has(stageKey);
        }
        if (Array.isArray(stageFilter)) {
            return stageFilter.includes(stageKey);
        }
        if (typeof stageFilter === 'function') {
            return stageFilter(stageKey);
        }
        return stageKey === stageFilter;
    };

    const dataPointOverride = overrides && typeof overrides === 'object' ? overrides.dataPoint || null : null;
    const allowDataFallback = overrides && typeof overrides === 'object'
        ? Boolean(overrides.allowFallback)
        : true;

    if (allowStage('req') && progress >= req[0] && progress < req[1]) {
        const t = normalizeRange(progress, req[0], req[1]);
        const point = segmentPointWithAngle(segment, t, layout, { allowClamp: true });
        drawFlowArrow(point, point.angle, colors.phaseReq, { size: 10 });
    }

    if (allowStage('ack') && progress >= ack[0] && progress < ack[1]) {
        const t = normalizeRange(progress, ack[0], ack[1]);
        const point = segmentPointWithAngle(segment, t, layout, { reverse: true, allowClamp: true });
        drawFlowArrow(point, point.angle, colors.phaseAck, { size: 10, style: 'outline' });
    }

    if (allowStage('data') && progress >= data[0] && progress < data[1]) {
        let point = dataPointOverride;
        if (!point) {
            if (!allowDataFallback) {
                point = null;
            } else {
                const spatialProgress = progressToSpatial(progress);
                const alignedProgress = Math.min(Math.max(spatialProgress, 0.2), 0.95);
                point = segmentPointWithAngle(segment, alignedProgress, layout, { allowClamp: true });
            }
        }
        if (point) {
            drawDataMarker(point, point.angle, colors.phaseData);
        }
    }

    if (allowStage('release') && progress >= release[0]) {
        const destPos = getNodePosition(segment.to.ring, segment.to.index, layout);
        drawReleasePulse(destPos, colors.phaseRelease);
    }
}

function resolvePreviewDrawOptions(preview) {
    if (!preview) return null;
    const styleKey = preview.renderStyle && PREVIEW_STYLE_DEFAULTS[preview.renderStyle]
        ? preview.renderStyle
        : 'default';
    const defaults = PREVIEW_STYLE_DEFAULTS[styleKey];
    return {
        treeColor: preview.treeColor || defaults.treeColor,
        ringColor: preview.ringColor || defaults.ringColor,
        lineWidth: typeof preview.lineWidth === 'number' ? preview.lineWidth : defaults.lineWidth,
        strokeOpacity: typeof preview.strokeOpacity === 'number'
            ? preview.strokeOpacity
            : defaults.strokeOpacity,
    };
}

function drawPreviewOverlay(preview, layout) {
    if (!preview || !layout) return;
    const drawOptions = resolvePreviewDrawOptions(preview);
    if (!drawOptions) return;
    drawRoute(preview, layout, {
        showIndicator: false,
        showPhaseIndicators: false,
        treeColor: drawOptions.treeColor,
        ringColor: drawOptions.ringColor,
        lineWidth: drawOptions.lineWidth,
        strokeOpacity: drawOptions.strokeOpacity,
        directionHint: preview.renderStyle !== 'completed',
    });
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
                point: segmentPointWithAngle(
                    segment,
                    progressToSpatial(progress),
                    layout,
                    { allowClamp: true },
                ),
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
                point: segmentPointWithAngle(
                    segment,
                    progressToSpatial(progress),
                    layout,
                    { allowClamp: true },
                ),
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
    const completedOverlays = Array.isArray(multiRunState?.completedRoutes)
        ? multiRunState.completedRoutes
        : [];
    completedOverlays.forEach((overlay) => {
        drawPreviewOverlay(overlay, layoutCache);
    });

    const previewOverlays = Array.isArray(multiRunState?.previewRoutes)
        ? multiRunState.previewRoutes
        : [];
    const activeSignature = routePathSignature(routePreview?.path);
    previewOverlays.forEach((overlay) => {
        if (!overlay) return;
        const overlaySignature = routePathSignature(overlay.path);
        if (activeSignature && overlaySignature && overlaySignature === activeSignature) {
            return;
        }
        drawPreviewOverlay(overlay, layoutCache);
    });

    if (routePreview) {
        drawPreviewOverlay(routePreview, layoutCache);
    }
    nodePositions.clear();
    drawNodes(layoutCache);
    if (animationState) {
        if (animationState.mode === 'parallel' && Array.isArray(animationState.animations)) {
            animationState.animations.forEach((animation, index) => {
                const color = PARALLEL_ROUTE_COLORS[index % PARALLEL_ROUTE_COLORS.length];
                const status = Array.isArray(animationState.latestStatuses)
                    ? animationState.latestStatuses[index]
                    : null;
                drawRoute(animation, layoutCache, {
                    showIndicator: false,
                    showPhaseIndicators: true,
                    phaseIndicatorStages: HANDSHAKE_WITH_DATA_PHASES,
                    treeColor: color,
                    ringColor: color,
                    lineWidth: 3,
                    strokeOpacity: 0.85,
                    directionHint: true,
                    suppressDirectionHintPhases: HANDSHAKE_PHASES,
                    activePhaseKey: status?.phaseKey || null,
                });
            });
        } else {
            const highlightStyle = PREVIEW_STYLE_DEFAULTS.active;
            drawRoute(animationState, layoutCache, {
                showIndicator: false,
                showPhaseIndicators: true,
                directionHint: true,
                treeColor: highlightStyle.treeColor,
                ringColor: highlightStyle.ringColor,
                lineWidth: highlightStyle.lineWidth,
                strokeOpacity: highlightStyle.strokeOpacity,
                suppressDirectionHintPhases: HANDSHAKE_PHASES,
                activePhaseKey: animationState.latestStatus?.phaseKey || null,
            });
        }
    }
}

// Replace the RouteAnimation class with this updated version
// that properly waits for each handshake phase

class RouteAnimation {
    constructor(payload, speed) {
        this.path = payload.path || [];
        this.segments = payload.segments || [];
        this.flow = payload.flow || [];
        this.speed = speed;
        this.packetIndex = payload?.packetIndex || 1;
        this.packetCount = payload?.packetCount || 1;
        this.lastStageKey = null;
        const pathNodes = Array.isArray(this.path) ? this.path : [];
        this.packetSummary = {
            source: pathNodes.length ? pathNodes[0] : null,
            destination: pathNodes.length ? pathNodes[pathNodes.length - 1] : null,
            data: payload?.packet?.data ?? payload?.data ?? null,
        };
        
        // Each segment has 5 phases with different durations
        // ready: 10%, req: 10%, ack: 10%, data: 50%, release: 20%
        this.phaseDurations = {
            ready: 200 / speed,    // Quick ready phase
            req: 300 / speed,      // REQ signal propagation
            ack: 300 / speed,      // Wait for ACK
            data: 800 / speed,     // Data transfer (longest)
            release: 200 / speed   // Release phase
        };
        
        this.totalSegmentDuration = Object.values(this.phaseDurations).reduce((a, b) => a + b, 0);
        this.startTimestamp = null;
        this.progress = 0;
        this.elapsedMs = 0;
        this.latestStatus = null;
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
        const totalDuration = this.totalSegmentDuration * this.segments.length;
        const normalized = Math.min(this.elapsedMs / totalDuration, 1);
        this.progress = normalized * this.segments.length;
    }

    segmentProgress(index) {
        const rawProgress = this.progress - index;
        if (rawProgress <= 0) return 0;
        if (rawProgress >= 1) return 1;
        
        // Map linear progress to phase-based progress
        const elapsed = rawProgress * this.totalSegmentDuration;
        let accumulatedTime = 0;
        
        // Calculate which phase we're in
        if (elapsed < (accumulatedTime += this.phaseDurations.ready)) {
            // Ready phase: 0 to 0.2
            return 0.2 * (elapsed / this.phaseDurations.ready);
        }
        if (elapsed < (accumulatedTime += this.phaseDurations.req)) {
            // REQ phase: 0.2 to 0.4
            const phaseProgress = (elapsed - (accumulatedTime - this.phaseDurations.req)) / this.phaseDurations.req;
            return 0.2 + (0.2 * phaseProgress);
        }
        if (elapsed < (accumulatedTime += this.phaseDurations.ack)) {
            // ACK phase: 0.4 to 0.6
            const phaseProgress = (elapsed - (accumulatedTime - this.phaseDurations.ack)) / this.phaseDurations.ack;
            return 0.4 + (0.2 * phaseProgress);
        }
        if (elapsed < (accumulatedTime += this.phaseDurations.data)) {
            // DATA phase: 0.6 to 0.85
            const phaseProgress = (elapsed - (accumulatedTime - this.phaseDurations.data)) / this.phaseDurations.data;
            return 0.6 + (0.25 * phaseProgress);
        }
        if (elapsed < (accumulatedTime += this.phaseDurations.release)) {
            // Release phase: 0.85 to 1.0
            const phaseProgress = (elapsed - (accumulatedTime - this.phaseDurations.release)) / this.phaseDurations.release;
            return 0.85 + (0.15 * phaseProgress);
        }
        
        return 1;
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
        const phaseChanged = this.lastStageKey !== stage.key;
        this.lastStageKey = stage.key;

        if (this.isComplete() && segmentProgress >= 1) {
            this.lastStageKey = 'completed';
            return {
                hopText: `${totalHops} / ${totalHops}`,
                nodesText: `${nodeLabel(segment.from)} → ${nodeLabel(segment.to)}`,
                phaseKey: 'completed',
                phaseLabel: 'Completed',
                signalText: 'Idle',
                signalStates: { req: 'sleep', ack: 'sleep', data: 'sleep' },
                transferText: 'Packet delivered',
                progressPercent: 100,
                timer: Math.round(this.elapsedMs / 1000),
                flowIndex: this.flow.length ? this.flow.length - 1 : hopNumber,
                segment,
                segmentProgress: 1,
                packetIndex: this.packetIndex,
                packetCount: this.packetCount,
                phaseChanged,
            };
        }
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
            packetIndex: this.packetIndex,
            packetCount: this.packetCount,
            phaseChanged,
        };
    }

}

class ParallelRouteController {
    constructor(payloads, speed) {
        this.mode = 'parallel';
        this.payloads = payloads;
        this.animations = payloads.map((payload) => new RouteAnimation(payload, speed));
        this.latestStatuses = [];
    }

    update(timestamp) {
        this.animations.forEach((animation) => {
            animation.update(timestamp);
        });
    }

    isComplete() {
        return this.animations.every((animation) => animation.isComplete());
    }

}

class RoutePreview {
    constructor(payload, options = {}) {
        this.path = payload?.path || [];
        this.segments = payload?.segments || [];
        this.flow = payload?.flow || [];
        this.renderStyle = options.renderStyle || 'default';
        this.treeColor = options.treeColor || null;
        this.ringColor = options.ringColor || null;
        this.lineWidth = typeof options.lineWidth === 'number' ? options.lineWidth : null;
        this.strokeOpacity = typeof options.strokeOpacity === 'number' ? options.strokeOpacity : null;
    }

    segmentProgress() {
        return 1;
    }

    currentSegment() {
        return null;
    }

    isComplete() {
        return this.renderStyle === 'completed';
    }
}

RouteAnimation.prototype.applyPauseOffset = function applyPauseOffset(delta) {
    if (!Number.isFinite(delta) || delta <= 0) {
        return;
    }
    if (typeof this.startTimestamp === 'number') {
        this.startTimestamp += delta;
    }
};

ParallelRouteController.prototype.applyPauseOffset = function applyPauseOffset(delta) {
    if (!Number.isFinite(delta) || delta <= 0) {
        return;
    }
    this.animations.forEach((animation) => {
        if (animation && typeof animation.applyPauseOffset === 'function') {
            animation.applyPauseOffset(delta);
        }
    });
};

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

function aggregateParallelStatuses(statuses, { timerOverride, forceComplete = false } = {}) {
    if (!Array.isArray(statuses) || !statuses.length) {
        return {
            hopText: '0 / 0',
            nodesText: 'No active routes',
            phaseKey: 'ready',
            phaseLabel: 'Parallel',
            signalText: 'Idle',
            signalStates: { req: 'sleep', ack: 'sleep', data: 'sleep' },
            transferText: '',
            progressPercent: 0,
            timer: 0,
        };
    }

    const total = statuses.length;
    let completed = 0;
    let progressSum = 0;
    let maxTimer = 0;

    statuses.forEach((status) => {
        if (!status) return;
        const isCompleted = forceComplete
            || status.phaseKey === 'completed'
            || status.phaseLabel === 'Completed';
        if (isCompleted) {
            completed += 1;
        }
        progressSum += Number(status.progressPercent ?? 0);
        maxTimer = Math.max(maxTimer, Number(status.timer ?? 0));
    });

    if (forceComplete) {
        completed = total;
    }

    const progressPercent = forceComplete
        ? 100
        : Math.round(progressSum / total);
    const allComplete = forceComplete || completed === total;
    const timer = typeof timerOverride === 'number' ? timerOverride : Math.round(maxTimer);
    const remaining = Math.max(total - completed, 0);
    return {
        hopText: `${completed} / ${total}`,
        nodesText: allComplete
            ? 'All packets delivered'
            : `${remaining} packet${remaining === 1 ? '' : 's'} still in flight`,
        phaseKey: allComplete ? 'completed' : 'data',
        phaseLabel: allComplete ? 'Completed' : 'Parallel',
        signalText: allComplete ? 'Idle' : 'Parallel active',
        signalStates: allComplete
            ? { req: 'sleep', ack: 'sleep', data: 'sleep' }
            : { req: 'active', ack: 'active', data: 'active' },
        transferText: allComplete ? 'Packets delivered' : 'Multiple packets transferring',
        progressPercent,
        timer,
    };
}

function updateNodeRuntimeFromStatus(status, animationContext = animationState) {
    if (!status || !animationContext) return;

    let finalNode = null;
    if (Array.isArray(animationContext.path) && animationContext.path.length) {
        finalNode = animationContext.path[animationContext.path.length - 1];
    } else if (Array.isArray(animationContext.segments) && animationContext.segments.length) {
        finalNode = animationContext.segments[animationContext.segments.length - 1]?.to || null;
    }
    const originNode = Array.isArray(animationContext.path) && animationContext.path.length
        ? animationContext.path[0]
        : null;
    const originId = originNode ? makeNodeId(originNode) : null;

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

    const sourceInterface = ensureInterfaceRuntimeState(sourceId, segment.to);
    const targetInterface = ensureInterfaceRuntimeState(targetId, segment.from);
    const packetSummary = derivePacketSummary(animationContext, segment) || null;
    const resolvedPacket = {
        source: packetSummary?.source || segment.from || null,
        destination: packetSummary?.destination || finalNode || segment.to || null,
        data: packetSummary?.data ?? null,
    };
    const hasPacket = Boolean(resolvedPacket.source || resolvedPacket.destination || resolvedPacket.data != null);
    const phaseChanged = Boolean(status.phaseChanged);

    const isFinalHop = Boolean(
        finalNode && segment.to.ring === finalNode.ring && segment.to.index === finalNode.index,
    );

    const phaseKeyRaw = status.phaseKey || status.phaseLabel;
    const fallbackStage = Number.isFinite(status.segmentProgress)
        ? stageFromProgress(status.segmentProgress).key
        : null;
    const phaseKey = (typeof phaseKeyRaw === 'string' && phaseKeyRaw.length)
        ? phaseKeyRaw.toLowerCase()
        : (typeof fallbackStage === 'string' ? fallbackStage : 'ready');

    const packetKey = createPacketKey(status, animationContext, segment, finalNode);

    switch (phaseKey) {
        case 'ready':
            sourceState.sendBuffer = 'primed';
            sourceState.handshake = 'primed';
            targetState.receiveBuffer = 'idle';
            targetState.handshake = 'idle';
            if (phaseChanged && originId && sourceId === originId && sourceState.applicationBuffer > 0) {
                sourceState.applicationBuffer = Math.max(0, sourceState.applicationBuffer - 1);
            }
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
            sourceState.sendBuffer = 'idle';
            sourceState.handshake = 'idle';
            if (isFinalHop) {
                targetState.receiveBuffer = 'delivered';
                targetState.applicationBuffer = 1;
                targetState.handshake = 'idle';
            }
            break;
        default:
            break;
    }

    const shouldRemoveSource = phaseKey === 'completed'
        || (phaseKey === 'release' && Number(status.segmentProgress ?? 0) >= 0.99)
        || (!hasPacket && phaseKey === 'ready');
    const shouldRemoveTarget = phaseKey === 'completed'
        || (phaseKey === 'release' && Number(status.segmentProgress ?? 0) >= 0.99)
        || (!hasPacket && phaseKey === 'ready' && !isFinalHop);

    if (sourceInterface) {
        recordInterfacePacketStage(sourceInterface, packetKey, {
            direction: 'outbound',
            stage: phaseKey,
            packet: hasPacket ? resolvedPacket : null,
            timestamp,
            remove: shouldRemoveSource,
        });
        if (sourceInterface.timeout) {
            sourceInterface.timeout.value = 0;
        }
    }

    if (targetInterface) {
        recordInterfacePacketStage(targetInterface, packetKey, {
            direction: 'inbound',
            stage: phaseKey,
            packet: hasPacket ? resolvedPacket : null,
            timestamp,
            remove: !isFinalHop && shouldRemoveTarget,
        });
        if (targetInterface.timeout) {
            targetInterface.timeout.value = 0;
        }
    }

    if (
        targetInterface
        && isFinalHop
        && phaseKey === 'release'
        && Number(status.segmentProgress ?? 0) >= 0.99
    ) {
        recordInterfacePacketStage(targetInterface, packetKey, {
            direction: 'inbound',
            stage: 'completed',
            packet: hasPacket ? resolvedPacket : null,
            timestamp,
            remove: true,
        });
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

function highlightMultiRouteCard(index) {
    if (!multiRouteList) return;
    const cards = multiRouteList.querySelectorAll('.multi-route-entry');
    cards.forEach((card, idx) => {
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

function collectSelectedDestinations() {
    return multiDestinations
        .map((nodeId) => parseSelectValue(nodeId))
        .filter((node) => Number.isFinite(node.ring) && Number.isFinite(node.index));
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

async function fetchRoutePayload(source, destination) {
    const response = await fetch('/api/route', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            source: { ring: source.ring, node: source.index },
            destination: { ring: destination.ring, node: destination.index },
        }),
    });

    const data = await response.json();
    if (!response.ok || data.error) {
        throw new Error(data.error || 'Routing failed');
    }
    return {
        ...data,
        source,
        destination,
    };
}

async function simulateSingleRoute() {
    if (!topologyData) return;
    setPickMode(null);
    resetMultiRunState();
    syncSelectionState();
    if (isMobileSidebar() && isSidebarVisible()) {
        closeSidebar();
    }
    stopAnimation();
    resetAllNodeRuntimeState();
    updateAnimateButton({ disabled: true, busy: false, label: animateBtn.dataset.defaultLabel });
    const source = parseSelectValue(sourceSelect.value);
    const destination = parseSelectValue(destinationSelect.value);
    hudStatus.textContent = `Preparing route ${nodeLabel(source)} → ${nodeLabel(destination)}…`;

    try {
        const payload = await fetchRoutePayload(source, destination);
        prepareRoute(payload);
        hudStatus.textContent = 'Route ready. Click "Animate path" to begin.';
    } catch (error) {
        console.error(error);
        const message = error.message || 'Routing failed';
        hudStatus.textContent = message;
        setStatusIdle(message);
        routePreview = null;
        lastRoutePayload = null;
        renderTopology();
        updateAnimateButton({ disabled: true, busy: false, label: animateBtn.dataset.defaultLabel });
        updateAnimationControlState();
    }
}

async function simulateParallelRoutes() {
    if (!topologyData) return;
    setPickMode(null);
    stopAnimation();
    resetAllNodeRuntimeState();
    resetMultiRunState();
    syncSelectionState();
    if (isMobileSidebar() && isSidebarVisible()) {
        closeSidebar();
    }

    const source = parseSelectValue(sourceSelect.value);
    const destinations = collectSelectedDestinations();
    const sourceKey = `${source.ring}-${source.index}`;
    const dedupe = new Map();
    destinations.forEach((dest) => {
        if (!dest || typeof dest.ring !== 'number' || typeof dest.index !== 'number') {
            return;
        }
        const key = `${dest.ring}-${dest.index}`;
        if (key === sourceKey) {
            return;
        }
        if (!dedupe.has(key)) {
            dedupe.set(key, dest);
        }
    });

    const uniqueDestinations = Array.from(dedupe.values());
    if (!uniqueDestinations.length) {
        hudStatus.textContent = 'Add one or more destination nodes for 1 → n parallel simulation.';
        setStatusIdle('Awaiting destination selection');
        updateAnimateButton({ disabled: true, busy: false, label: 'Animate all' });
        return;
    }

    hudStatus.textContent = `Computing ${uniqueDestinations.length} parallel route(s)…`;

    try {
        const rawPayloads = await Promise.all(
            uniqueDestinations.map((destination) => fetchRoutePayload(source, destination))
        );

        if (!rawPayloads.length) {
            hudStatus.textContent = 'No valid routes generated.';
            setStatusIdle('Awaiting destination selection');
            updateAnimateButton({ disabled: true, busy: false, label: 'Animate all' });
            return;
        }

        const packetCount = rawPayloads.length;
        const enrichedPayloads = rawPayloads.map((payload, index) => {
            const pathArray = Array.isArray(payload.path) ? payload.path : [];
            const computedDestination = pathArray.length
                ? pathArray[pathArray.length - 1]
                : payload.destination || uniqueDestinations[index] || null;
            const destinationAddress = computedDestination
                ? { ring: computedDestination.ring, index: computedDestination.index }
                : { ring: uniqueDestinations[index].ring, index: uniqueDestinations[index].index };
            return {
                ...payload,
                packetIndex: index + 1,
                packetCount,
                packet: {
                    source: { ring: source.ring, index: source.index },
                    destination: destinationAddress,
                    data: `Packet ${index + 1}`,
                },
            };
        });

        multiRunState = {
            mode: 'parallel',
            payloads: enrichedPayloads,
            currentIndex: null,
            selectedIndex: 0,
            completed: new Set(),
            completedRoutes: [],
            completedStatuses: [],
            previewRoutes: enrichedPayloads.map((payload, index) => {
                const color = PARALLEL_ROUTE_COLORS[index % PARALLEL_ROUTE_COLORS.length];
                return new RoutePreview(payload, {
                    renderStyle: 'pending',
                    treeColor: color,
                    ringColor: color,
                    strokeOpacity: 0.35,
                    lineWidth: 3,
                });
            }),
            source,
        };

        summary.textContent = `Parallel routes: ${packetCount} destination(s) · Packets: ${packetCount}`;
        renderMultiRouteList();

        const flowEntries = enrichedPayloads.map((payload, index) => {
            const pathArray = Array.isArray(payload.path) ? payload.path : [];
            const destination = pathArray[pathArray.length - 1] || payload.destination || source;
            return {
                phase: `Packet ${index + 1}`,
                title: `${safeNodeLabel(source)} → ${safeNodeLabel(destination)}`,
                details: [
                    `Hop count: ${payload.hopCount ?? 0}`,
                    `Segments: ${Array.isArray(payload.segments) ? payload.segments.length : 0}`,
                ],
            };
        });
        renderFlow(flowEntries);

        const firstPayload = enrichedPayloads[0];
        if (firstPayload) {
            const previewEntry = Array.isArray(multiRunState.previewRoutes)
                ? multiRunState.previewRoutes[0]
                : null;
            const previewColors = previewEntry
                ? {
                    treeColor: previewEntry.treeColor,
                    ringColor: previewEntry.ringColor,
                    strokeOpacity: 0.85,
                    lineWidth: 4,
                }
                : null;
            prepareRoute(firstPayload, {
                contextLabel: `Packet 1 of ${packetCount}`,
                previewColors,
                buttonLabel: 'Animate all',
            });
            lastRoutePayload = firstPayload;
        }

        hudStatus.textContent = `Parallel routes ready (${packetCount}). Press "Animate all" or pick a route to inspect.`;
        const hasSegments = enrichedPayloads.some((payload) => Array.isArray(payload.segments) && payload.segments.length);
        updateAnimateButton({ disabled: !hasSegments, busy: false, label: 'Animate all' });

        const sourceNodeId = makeNodeId(source);
        const sourceRuntime = ensureNodeRuntimeState(sourceNodeId);
        sourceRuntime.applicationBuffer = packetCount;
        sourceRuntime.handshake = packetCount > 0 ? 'primed' : 'idle';
        sourceRuntime.sendBuffer = packetCount > 0 ? 'primed' : 'idle';
        sourceRuntime.lastUpdated = performance.now();
        if (selectedNodeId === sourceNodeId) {
            updateNodePanelContent();
        }
    } catch (error) {
        console.error(error);
        const message = error.message || 'Routing failed';
        hudStatus.textContent = message;
        setStatusIdle(message);
        updateAnimateButton({ disabled: true, busy: false, label: 'Animate all' });
        resetMultiRunState();
        updateAnimationControlState();
    }
}

function prepareRoute(payload, options = {}) {
    resetAllNodeRuntimeState();
    setNodePanelAutoTracking(autoNodeDetailsPreference);
    lastRoutePayload = payload;
    const isCompleted = Boolean(options.isCompleted);
    const initialStatus = options.initialStatus || null;
    const previewColors = options.previewColors && typeof options.previewColors === 'object'
        ? options.previewColors
        : null;
    const previewStyle = options.previewStyle
        || (isCompleted ? 'completed' : (previewColors ? 'active' : 'pending'));
    routePreview = new RoutePreview(payload, {
        renderStyle: previewStyle,
        treeColor: previewColors?.treeColor,
        ringColor: previewColors?.ringColor,
        lineWidth: previewColors?.lineWidth,
        strokeOpacity: previewColors?.strokeOpacity,
    });
    animationState = null;
    setRouteInfo(payload);
    if (options.contextLabel) {
        summary.textContent = `${options.contextLabel} · Hops: ${payload.hopCount}`;
    } else {
        summary.textContent = `Hop count: ${payload.hopCount}`;
    }
    if (isCompleted) {
        summary.textContent += ' · Completed';
    }
    renderFlow(payload.flow);
    highlightFlowCard(0);
    const hasSegments = Array.isArray(payload.segments) && payload.segments.length > 0;
    const animateLabel = options.buttonLabel || options.contextLabel || animateBtn?.dataset?.defaultLabel;

    if (initialStatus) {
        updateStatusBar(initialStatus);
    } else if (!options.autoStart) {
        const transferPrompt = options.buttonLabel
            ? `Press ${options.buttonLabel}`
            : 'Press Animate';
        showRouteReadyStatus(payload, { transferText: transferPrompt });
    }

    if (options.autoStart) {
        updateAnimateButton({ disabled: true, busy: true, label: options.contextLabel || animateBtn?.dataset?.defaultLabel });
    } else {
        updateAnimateButton({
            disabled: !hasSegments,
            busy: false,
            label: animateLabel,
        });
        if (hudStatus) {
            if (options.contextHint) {
                hudStatus.textContent = options.contextHint;
            } else if (initialStatus) {
                hudStatus.textContent = 'Packet delivered. Click "Animate all" to replay.';
            } else if (hasSegments) {
                hudStatus.textContent = 'Route ready. Click "Animate path" to begin.';
            } else {
                hudStatus.textContent = 'Source and destination are identical.';
            }
        }
    }
    if (Array.isArray(payload.path) && payload.path.length) {
        focusNode(makeNodeId(payload.path[0]), {
            auto: true,
            openPanelOnFocus: nodePanelAutoTracking,
        });
    }
    renderTopology();
    updateAnimationControlState();
}

function playAnimation() {
    if (multiRunState) {
        if (
            multiRunState.mode === 'parallel'
            && Array.isArray(multiRunState.payloads)
            && multiRunState.payloads.length
        ) {
            startAnimation(multiRunState.payloads[0], {
                parallelPayloads: multiRunState.payloads,
                label: 'Animate all',
                onComplete: () => {
                    hudStatus.textContent = 'Parallel transmissions complete';
                },
            });
            return;
        }
    }

    if (!lastRoutePayload) {
        hudStatus.textContent = 'Simulate the route first.';
        return;
    }

    startAnimation(lastRoutePayload);
}

function startAnimation(payload, options = {}) {
    const opts = {
        onComplete: null,
        label: null,
        parallelPayloads: null,
        ...options,
    };

    const disableLabel = opts.label || animateBtn?.dataset?.currentLabel || animateBtn?.dataset?.defaultLabel;

    if (!payload || !Array.isArray(payload.segments) || !payload.segments.length) {
        updateAnimateButton({ disabled: true, busy: false, label: disableLabel });
        updateAnimationControlState();
        return;
    }
    cancelAnimationFrame(animationFrame);
    animationFrame = null;
    resetAllNodeRuntimeState();
    routePreview = null;
    if (Array.isArray(opts.parallelPayloads) && opts.parallelPayloads.length) {
        animationState = new ParallelRouteController(opts.parallelPayloads, speedMultiplier);
    } else {
        animationState = new RouteAnimation(payload, speedMultiplier);
    }
    animationOptions = opts;
    animationPaused = false;
    animationPauseTimestamp = null;
    setNodePanelAutoTracking(autoNodeDetailsPreference);
    updateAnimateButton({ disabled: true, busy: true, label: disableLabel });
    hudStatus.textContent = opts.parallelPayloads ? 'Animating parallel routes…' : 'Animating route…';
    const firstPath = Array.isArray(animationState.path) && animationState.path.length
        ? animationState.path
        : Array.isArray(routePreview?.path) ? routePreview.path : payload.path || [];
    const firstNode = Array.isArray(firstPath) && firstPath.length
        ? firstPath[0]
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

        if (animationState.mode === 'parallel' && Array.isArray(animationState.animations)) {
            const statuses = animationState.animations.map((animation) => animation.currentStatus());
            animationState.latestStatuses = statuses;
            const aggregate = aggregateParallelStatuses(statuses);
            updateStatusBar(aggregate);
            statuses.forEach((status, index) => updateNodeRuntimeFromStatus(status, animationState.animations[index]));
            updateParallelRouteProgress(statuses);
        } else {
            const status = animationState.currentStatus();
            animationState.latestStatus = status;
            updateStatusBar(status);
            if (status && typeof status.flowIndex === 'number') {
                highlightFlowCard(status.flowIndex);
            }
            updateNodeRuntimeFromStatus(status, animationState);
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
        }

        renderTopology();

        const isComplete = animationState.mode === 'parallel'
            ? animationState.isComplete()
            : animationState.isComplete();

        if (isComplete) {
            hudStatus.textContent = animationState.mode === 'parallel'
                ? 'Parallel transmissions complete'
                : 'Transmission complete';
            highlightFlowCard(flowCardElements.length - 1);
            const completedStatus = {
                phaseKey: 'completed',
                phaseLabel: 'Completed',
                signalText: 'Idle',
                signalStates: { req: 'sleep', ack: 'sleep', data: 'sleep' },
                transferText: animationState.mode === 'parallel' ? 'Packets delivered' : 'Packet delivered',
                progressPercent: 100,
                hopText: statusElements.hopValue.textContent,
                nodesText: statusElements.hopNodes.textContent,
                timer: parseInt(statusElements.timerValue.textContent.replace(/[^0-9]/g, ''), 10) || 0,
            };
            updateStatusBar(completedStatus);
            if (Array.isArray(opts.parallelPayloads) && opts.parallelPayloads.length) {
                opts.parallelPayloads.forEach((payloadItem, index) => {
                    const finalSegment = Array.isArray(payloadItem.segments) && payloadItem.segments.length
                        ? payloadItem.segments[payloadItem.segments.length - 1]
                        : null;
                    const status = {
                        ...completedStatus,
                        segment: finalSegment,
                        phaseKey: 'completed',
                        phaseLabel: 'Completed',
                    };
                    const context = Array.isArray(animationState?.animations)
                        ? animationState.animations[index]
                        : payloadItem;
                    updateNodeRuntimeFromStatus(status, context);
                });
            } else {
                updateNodeRuntimeFromStatus(completedStatus, animationState);
                if (nodePanelAutoTracking && Array.isArray(payload.path) && payload.path.length) {
                    const destinationNode = payload.path[payload.path.length - 1];
                    focusNode(makeNodeId(destinationNode), {
                        auto: true,
                        openPanelOnFocus: nodePanelAutoTracking,
                    });
                }
            }
            if (multiRunState && Array.isArray(multiRunState.previewRoutes)) {
                if (multiRunState.mode === 'parallel') {
                    multiRunState.previewRoutes.forEach((preview) => {
                        if (!preview) return;
                        preview.renderStyle = 'completed';
                        if (typeof preview.strokeOpacity !== 'number' || preview.strokeOpacity < 0.85) {
                            preview.strokeOpacity = 0.85;
                        }
                    });
                }
            }
            const completedSignature = routePathSignature(payload?.path);
            let completedPreviewColors = null;
            if (Array.isArray(multiRunState?.previewRoutes) && completedSignature) {
                const matchingPreview = multiRunState.previewRoutes.find((preview) => {
                    if (!preview) return false;
                    return routePathSignature(preview.path) === completedSignature;
                });
                if (matchingPreview) {
                    completedPreviewColors = {
                        treeColor: matchingPreview.treeColor,
                        ringColor: matchingPreview.ringColor,
                    };
                }
            }
            routePreview = new RoutePreview(payload, {
                renderStyle: 'completed',
                treeColor: completedPreviewColors?.treeColor,
                ringColor: completedPreviewColors?.ringColor,
            });
            const onComplete = typeof opts.onComplete === 'function' ? opts.onComplete : null;
            animationState = null;
            animationOptions = null;
            updateAnimateButton({ disabled: false, busy: false, label: disableLabel });
            renderTopology();
            animationFrame = null;
            if (onComplete) {
                onComplete();
            }
            animationPaused = false;
            animationPauseTimestamp = null;
            animationStep = null;
            updateAnimationControlState();
            return;
        }

        animationFrame = requestAnimationFrame(step);
    }
    animationStep = step;
    animationFrame = requestAnimationFrame(animationStep);
    updateAnimationControlState();
}

function stopAnimation() {
    if (animationFrame) {
        cancelAnimationFrame(animationFrame);
        animationFrame = null;
    }
    animationState = null;
    animationOptions = null;
    animationStep = null;
    animationPaused = false;
    animationPauseTimestamp = null;
    updateAnimationControlState();
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
    resetMultiRunState();
    if (selectedNodeId) {
        selectedNodeId = null;
        resetNodePanelContent();
    }
    renderTopology();
    updateAnimationControlState();
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

if (speedControl) {
    speedControl.addEventListener('input', (event) => {
        const sliderValue = resolveSpeedSliderValue(event.target.value);
        speedMultiplier = sliderValue * SPEED_SCALE;
        hudStatus.textContent = `Animation speed ×${speedMultiplier.toFixed(1)}`;
    });
}

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
    simulateBtn.addEventListener('click', () => {
        const mode = simulationModeSelect ? simulationModeSelect.value : 'single';
        switch (mode) {
            case 'parallel':
                simulateParallelRoutes();
                break;
            case 'single':
            default:
                simulateSingleRoute();
                break;
        }
    });
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

if (destinationCandidateSelect) {
    destinationCandidateSelect.addEventListener('change', () => {
        setPickMode(null);
        if (hudStatus) {
            const meta = parseSelectValue(destinationCandidateSelect.value);
            hudStatus.textContent = `Candidate destination: ${safeNodeLabel(meta)}.`;
        }
    });
}

if (addMultiDestinationBtn) {
    addMultiDestinationBtn.addEventListener('click', () => {
        if (!destinationCandidateSelect) return;
        addMultiDestination(destinationCandidateSelect.value);
    });
}

if (clearMultiDestinationsBtn) {
    clearMultiDestinationsBtn.addEventListener('click', () => {
        clearMultiDestinationList();
    });
}

if (multiDestinationList) {
    multiDestinationList.addEventListener('click', (event) => {
        const trigger = event.target.closest('[data-remove-destination]');
        if (!trigger) return;
        removeMultiDestination(trigger.dataset.removeDestination, { announce: true });
    });
    multiDestinationList.addEventListener('keydown', (event) => {
        if (event.key !== 'Enter' && event.key !== ' ') return;
        const trigger = event.target.closest('[data-remove-destination]');
        if (!trigger) return;
        event.preventDefault();
        removeMultiDestination(trigger.dataset.removeDestination, { announce: true });
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

if (pickDestinationMultiBtn) {
    pickDestinationMultiBtn.addEventListener('click', () => {
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

if (pauseAnimationBtn) {
    pauseAnimationBtn.addEventListener('click', togglePauseAnimation);
}

if (restartAnimationBtn) {
    restartAnimationBtn.addEventListener('click', restartAnimation);
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
renderMultiDestinationList();

function applySimulationModeUI(mode) {
    const normalizedMode = mode || (simulationModeSelect ? simulationModeSelect.value : 'single');
    const isParallel = normalizedMode === 'parallel';
    setElementVisibility(singleDestinationField, !isParallel);
    setElementVisibility(multiDestinationField, isParallel);
    if (multiRouteList) {
        multiRouteList.style.display = isParallel ? multiRouteList.style.display : 'none';
    }
    if (isParallel) {
        currentDestinationId = null;
        if (destinationCandidateSelect) {
            let fallback = destinationSelect?.value || destinationCandidateSelect.value;
            if (!fallback && destinationCandidateSelect.options.length) {
                fallback = destinationCandidateSelect.options[0].value;
            }
            if (fallback) {
                setSelectValue(destinationCandidateSelect, fallback);
            }
        }
        renderMultiDestinationList();
    } else {
        syncSelectionState();
    }
    if (isParallel) {
        updateAnimateButton({ disabled: true, busy: false, label: 'Animate all' });
    } else {
        updateAnimateButton({ disabled: true, busy: false, label: animateBtn?.dataset?.defaultLabel });
    }
    renderTopology();
}

if (simulationModeSelect) {
    applySimulationModeUI(simulationModeSelect.value);
    simulationModeSelect.addEventListener('change', () => {
        if (animateBtn) {
            animateBtn.dataset.currentLabel = animateBtn.dataset.defaultLabel;
        }
        applySimulationModeUI(simulationModeSelect.value);
        resetSimulation();
        summary.textContent = '';
        if (simulationModeSelect.value === 'parallel') {
            hudStatus.textContent = 'Parallel mode selected. Choose multiple destinations to animate together.';
        } else {
            hudStatus.textContent = '1 → 1 mode selected. Pick single destination to simulate.';
        }
    });
}

if (multiRouteList) {
    multiRouteList.addEventListener('click', handleMultiRouteListClick);
    multiRouteList.addEventListener('keydown', handleMultiRouteListKeydown);
}

applySignalState({ req: 'sleep', ack: 'sleep', data: 'sleep' });
syncSidebarForViewport();
syncNodePanelMode();
updateAnimateButton({ disabled: true, busy: false });
updateAnimationControlState();

fetchTopology()
    .then(() => {
        resizeCanvas();
    });
