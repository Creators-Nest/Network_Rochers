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
const pickDestinationMultiBtn = document.getElementById('pickDestinationMultiBtn');

const sourceField = sourceSelect ? sourceSelect.closest('.form-control') : null;

const applyTopologyBtn = document.getElementById('applyTopologyBtn');
const widthInput = document.getElementById('widthInput');
const heightInput = document.getElementById('heightInput');
const simulateBtn = document.getElementById('simulateBtn');
const animateBtn = document.getElementById('animateBtn');
const playPauseAnimationBtn = document.getElementById('playPauseAnimationBtn');
const canvasSimulateBtn = document.getElementById('canvasSimulateBtn');
const speedMenuBtn = document.getElementById('speedMenuBtn');
const speedMenuPopover = document.getElementById('speedMenuPopover');
const resetBtn = document.getElementById('resetBtn');
const simulationModeSelect = document.getElementById('simulationMode');
const clearMultiDestinationsBtn = document.getElementById('clearMultiDestinationsBtn');
const multiDestinationList = document.getElementById('multiDestinationList');
const multiRouteList = document.getElementById('multiRouteList');
const singleDestinationField = document.querySelector('[data-mode-area="single"]');
const multiDestinationField = document.querySelector('[data-mode-area="multi"]');
const nmRouteField = document.querySelector('[data-mode-area="nm"]');
const nmRouteTableBody = document.getElementById('nmRouteTableBody');
const addNmRouteBtn = document.getElementById('addNmRouteBtn');
const clearNmRoutesBtn = document.getElementById('clearNmRoutesBtn');
const openLogModalBtn = document.getElementById('openLogModalBtn');
const exportLogPdfBtn = document.getElementById('exportLogPdfBtn');

const zoomInBtn = document.getElementById('zoomInBtn');
const zoomOutBtn = document.getElementById('zoomOutBtn');
const resetViewBtn = document.getElementById('resetViewBtn');
const cursorModeBtn = document.getElementById('cursorModeBtn');
const interfaceModeBtn = document.getElementById('interfaceModeBtn');
const interfacePanel = document.getElementById('interfacePanel');
const interfacePanelClose = document.getElementById('interfacePanelClose');
const interfacePanelTitle = document.getElementById('interfacePanelTitle');
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
const nodePanelPosition = document.getElementById('nodePanelPosition');
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
const logModal = document.getElementById('logModal');
const logModalTitle = document.getElementById('logModalTitle');
const logModalBody = document.getElementById('logModalBody');
const logModalClose = document.getElementById('logModalClose');
const logModalOverlay = logModal ? logModal.querySelector('[data-close-modal="true"]') : null;

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

function formatSpeedDisplay(rawValue) {
    const sliderValue = resolveSpeedSliderValue(rawValue);
    if (DEFAULT_SPEED_SLIDER <= 0) {
        return `${sliderValue.toFixed(1)}×`;
    }
    const relative = sliderValue / DEFAULT_SPEED_SLIDER;
    return `${relative.toFixed(1)}×`;
}

function updateSpeedMenuLabel(rawValue) {
    if (!speedMenuBtn) {
        return;
    }
    const labelText = formatSpeedDisplay(rawValue);
    const textSpan = speedMenuBtn.querySelector('span');
    if (textSpan) {
        textSpan.textContent = labelText;
    }
    speedMenuBtn.dataset.speedLabel = labelText;
    speedMenuBtn.setAttribute('aria-label', `Speed ${labelText}`);
    speedMenuBtn.title = `Speed ${labelText}`;
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
let detailedLogEntries = [];
let detailedLogTitle = 'Detailed log';
const multiDestinations = [];
const nmRoutes = [];
let nmRouteCounter = 0;
let animationOptions = null;
let animationPaused = false;
let animationPauseTimestamp = null;
let pickMode = null;
let currentSourceId = null;
let currentDestinationId = null;
let nodeOptionsCache = [];
let suppressCandidateSelectChange = false;
let speedMenuOpen = false;

// Hover state for interface visualization
let hoverState = {
    nodeId: null,
    startTime: null,
    showInterfaces: false,
};

// Interface mode state
let interfaceMode = false;
let selectedInterfaceNode = null;

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
    return `${node.x}-${node.y}`;
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
            queue: 0,
            pendingDestinations: [],
        },
        receiveBuffer: {
            used: 0,
            capacity: receiveCapacity,
            head: null,
            state: 'idle',
            pendingDestinations: [],
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
        pendingOutbound: 0,
        handshake: 'idle',
        lastUpdated: 0,
        deliveredPackets: new Set(),
        interfaces,
        // Interface panel state
        signals: {
            req: false,
            ack: false,
            data: false
        },
        sendBuffers: [
            { state: 'empty', packet: null },
            { state: 'empty', packet: null },
            { state: 'empty', packet: null },
            { state: 'empty', packet: null }
        ],
        receiveBuffers: [
            { state: 'empty', packet: null },
            { state: 'empty', packet: null },
            { state: 'empty', packet: null },
            { state: 'empty', packet: null }
        ],
        activeInterface: null
    };
}

function ensureNodeRuntimeState(nodeId) {
    if (!nodeRuntimeState.has(nodeId)) {
        const meta = nodeMeta.get(nodeId) || null;
        nodeRuntimeState.set(nodeId, defaultNodeRuntimeState(meta));
    }
    const runtime = nodeRuntimeState.get(nodeId);
    if (runtime && !(runtime.deliveredPackets instanceof Set)) {
        runtime.deliveredPackets = new Set();
    }
    if (runtime && typeof runtime.pendingOutbound !== 'number') {
        runtime.pendingOutbound = 0;
    }
    return runtime;
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

function normalizePickMode(mode) {
    if (!mode) {
        return null;
    }
    if (typeof mode === 'string') {
        return (mode === 'source' || mode === 'destination') ? { type: mode, rowId: null } : null;
    }
    if (typeof mode === 'object' && (mode.type === 'source' || mode.type === 'destination')) {
        return {
            type: mode.type,
            rowId: mode.rowId || null,
        };
    }
    return null;
}

function setPickMode(mode) {
    const normalized = normalizePickMode(mode);
    pickMode = normalized;

    const isSourceGlobal = normalized && normalized.type === 'source' && !normalized.rowId;
    const isDestGlobal = normalized && normalized.type === 'destination' && !normalized.rowId;

    if (pickSourceBtn) {
        pickSourceBtn.setAttribute('aria-pressed', isSourceGlobal ? 'true' : 'false');
        pickSourceBtn.classList.toggle('is-active', Boolean(isSourceGlobal));
    }
    if (pickDestinationBtn) {
        pickDestinationBtn.setAttribute('aria-pressed', isDestGlobal ? 'true' : 'false');
        pickDestinationBtn.classList.toggle('is-active', Boolean(isDestGlobal));
    }
    if (pickDestinationMultiBtn) {
        pickDestinationMultiBtn.setAttribute('aria-pressed', isDestGlobal ? 'true' : 'false');
        pickDestinationMultiBtn.classList.toggle('is-active', Boolean(isDestGlobal));
    }

    nmRoutes.forEach((route) => {
        if (!route.pickSourceBtn || !route.pickDestinationBtn) {
            return;
        }
        const sourceActive = normalized && normalized.type === 'source' && normalized.rowId === route.id;
        const destActive = normalized && normalized.type === 'destination' && normalized.rowId === route.id;
        route.pickSourceBtn.classList.toggle('is-active', Boolean(sourceActive));
        route.pickDestinationBtn.classList.toggle('is-active', Boolean(destActive));
        route.pickSourceBtn.setAttribute('aria-pressed', sourceActive ? 'true' : 'false');
        route.pickDestinationBtn.setAttribute('aria-pressed', destActive ? 'true' : 'false');
    });

    if (canvas) {
        canvas.classList.toggle('is-picking', Boolean(normalized));
    }

    if (hudStatus) {
        if (!normalized) {
            return;
        }
        const modeLabel = normalized.type === 'source' ? 'source' : 'destination';
        if (normalized.rowId) {
            const index = nmRoutes.findIndex((route) => route.id === normalized.rowId);
            const rowLabel = index >= 0 ? `route ${index + 1}` : 'route';
            hudStatus.textContent = normalized.type === 'source'
                ? `Click a node to set the ${modeLabel} for ${rowLabel}.`
                : `Click a node to set the ${modeLabel} for ${rowLabel}.`;
        } else if (normalized.type === 'source') {
            hudStatus.textContent = 'Click a node to choose the source.';
        } else {
            hudStatus.textContent = isMultiSimulationMode()
                ? 'Click a node to add it to the destination list.'
                : 'Click a node to choose the destination.';
        }
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

function populateSelectElementFromCache(select, selectedValue) {
    if (!select) return;
    const previous = typeof selectedValue === 'string' ? selectedValue : select.value;
    select.innerHTML = '';
    nodeOptionsCache.forEach((opt) => {
        const optionEl = document.createElement('option');
        optionEl.value = opt.value;
        optionEl.textContent = opt.label;
        select.appendChild(optionEl);
    });
    if (previous && nodeOptionsCache.some((opt) => opt.value === previous)) {
        select.value = previous;
    } else if (nodeOptionsCache.length) {
        select.value = nodeOptionsCache[0].value;
    }
}

function addNmRouteRow(initial = {}) {
    if (!nmRouteTableBody) return null;
    nmRouteCounter += 1;
    const id = initial.id || `nm-${nmRouteCounter}`;
    const row = document.createElement('tr');
    row.dataset.routeId = id;

    const sourceCell = document.createElement('td');
    const sourceSelect = document.createElement('select');
    sourceSelect.className = 'nm-node-select';
    populateSelectElementFromCache(sourceSelect, initial.sourceId);
    sourceCell.appendChild(sourceSelect);

    const destCell = document.createElement('td');
    const destSelect = document.createElement('select');
    destSelect.className = 'nm-node-select';
    populateSelectElementFromCache(destSelect, initial.destinationId);
    destCell.appendChild(destSelect);

    const packetCell = document.createElement('td');
    const packetsInput = document.createElement('input');
    packetsInput.type = 'number';
    packetsInput.min = '1';
    packetsInput.value = Math.max(1, parseInt(initial.packets ?? 1, 10) || 1);
    packetsInput.className = 'nm-packet-input';
    packetCell.appendChild(packetsInput);

    const actionsCell = document.createElement('td');
    actionsCell.className = 'nm-route-table__actions';
    const sourcePickBtn = document.createElement('button');
    sourcePickBtn.type = 'button';
    sourcePickBtn.className = 'mini-btn';
    sourcePickBtn.textContent = 'Src';
    sourcePickBtn.title = 'Pick source from canvas';
    sourcePickBtn.setAttribute('aria-label', 'Pick source from canvas');
    sourcePickBtn.dataset.routeId = id;
    const destPickBtn = document.createElement('button');
    destPickBtn.type = 'button';
    destPickBtn.className = 'mini-btn';
    destPickBtn.textContent = 'Des';
    destPickBtn.title = 'Pick destination from canvas';
    destPickBtn.setAttribute('aria-label', 'Pick destination from canvas');
    destPickBtn.dataset.routeId = id;
    const removeBtn = document.createElement('button');
    removeBtn.type = 'button';
    removeBtn.className = 'mini-btn';
    removeBtn.textContent = '✕';
    removeBtn.title = 'Remove route';
    actionsCell.appendChild(sourcePickBtn);
    actionsCell.appendChild(destPickBtn);
    actionsCell.appendChild(removeBtn);

    row.appendChild(sourceCell);
    row.appendChild(destCell);
    row.appendChild(packetCell);
    row.appendChild(actionsCell);
    nmRouteTableBody.appendChild(row);

    const routeRecord = {
        id,
        element: row,
        sourceSelect,
        destSelect,
        packetsInput,
        pickSourceBtn: sourcePickBtn,
        pickDestinationBtn: destPickBtn,
        removeBtn,
        get sourceId() {
            return this.sourceSelect.value;
        },
        get destinationId() {
            return this.destSelect.value;
        },
        get packetCount() {
            return Math.max(1, parseInt(this.packetsInput.value, 10) || 1);
        },
    };

    sourceSelect.addEventListener('change', () => {
        setPickMode(null);
        renderTopology();
    });
    destSelect.addEventListener('change', () => {
        setPickMode(null);
        renderTopology();
    });
    packetsInput.addEventListener('change', () => {
        const sanitized = Math.max(1, parseInt(packetsInput.value, 10) || 1);
        packetsInput.value = sanitized;
    });
    sourcePickBtn.addEventListener('click', () => {
        const active = pickMode && pickMode.type === 'source' && pickMode.rowId === id;
        setPickMode(active ? null : { type: 'source', rowId: id });
    });
    destPickBtn.addEventListener('click', () => {
        const active = pickMode && pickMode.type === 'destination' && pickMode.rowId === id;
        setPickMode(active ? null : { type: 'destination', rowId: id });
    });
    removeBtn.addEventListener('click', () => {
        removeNmRouteRow(id);
    });

    nmRoutes.push(routeRecord);
    renderTopology();
    return routeRecord;
}

function removeNmRouteRow(routeId) {
    const index = nmRoutes.findIndex((route) => route.id === routeId);
    if (index === -1) {
        return;
    }
    const [route] = nmRoutes.splice(index, 1);
    if (route?.element?.parentNode) {
        route.element.parentNode.removeChild(route.element);
    }
    if (pickMode && pickMode.rowId === routeId) {
        setPickMode(null);
    }
    renderTopology();
}

function clearNmRoutes({ announce = true } = {}) {
    while (nmRoutes.length) {
        const route = nmRoutes.pop();
        if (route?.element?.parentNode) {
            route.element.parentNode.removeChild(route.element);
        }
    }
    if (announce && hudStatus) {
        hudStatus.textContent = 'Route plan cleared.';
    }
    setPickMode(null);
    renderTopology();
}

function refreshNmRouteOptions() {
    if (!nmRoutes.length) {
        return;
    }
    nmRoutes.forEach((route) => {
        populateSelectElementFromCache(route.sourceSelect, route.sourceId);
        populateSelectElementFromCache(route.destSelect, route.destinationId);
    });
    renderTopology();
}

function collectNmRoutes() {
    return nmRoutes
        .map((route) => ({
            id: route.id,
            sourceId: route.sourceId,
            destinationId: route.destinationId,
            packets: route.packetCount,
            source: parseSelectValue(route.sourceId),
            destination: parseSelectValue(route.destinationId),
        }))
        .filter((entry) => Number.isFinite(entry.source.x)
            && Number.isFinite(entry.source.y)
            && Number.isFinite(entry.destination.x)
            && Number.isFinite(entry.destination.y));
}

function resolveSendBufferCapacity(sourceId, nextHop) {
    if (!sourceId) {
        return 4;
    }
    const sourceMeta = nodeMeta.get(sourceId);
    if (!sourceMeta || !Array.isArray(sourceMeta.interfaces)) {
        return 4;
    }
    if (!nextHop) {
        const fallback = sourceMeta.interfaces[0]?.sendBuffer?.capacity
            ?? sourceMeta.interfaces[0]?.sendCapacity;
        const numeric = Number(fallback);
        return Number.isFinite(numeric) && numeric > 0 ? numeric : 4;
    }
    const neighborId = makeNodeId(nextHop);
    const iface = sourceMeta.interfaces.find((entry) => entry?.neighbor && makeNodeId(entry.neighbor) === neighborId);
    if (!iface) {
        return 4;
    }
    const capacity = Number(iface.sendBuffer?.capacity ?? iface.sendCapacity);
    return Number.isFinite(capacity) && capacity > 0 ? capacity : 4;
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

function applyBufferRuntime(buffer, { used, state, head, pendingDestinations } = {}) {
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
    if (Array.isArray(pendingDestinations)) {
        buffer.pendingDestinations = pendingDestinations.slice();
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

    const capacity = Number(ifaceRuntime.sendBuffer.capacity || 0);
    ifaceRuntime.sendBuffer.used = outbound.length;
    ifaceRuntime.sendBuffer.state = outbound.length
        ? SEND_BUFFER_STATE_BY_STAGE[outboundRep?.stage] || 'transferring'
        : 'idle';
    ifaceRuntime.sendBuffer.head = outboundRep?.packet || null;
    const overflow = Math.max(outbound.length - capacity, 0);
    const existingQueue = Number(ifaceRuntime.sendBuffer.queue || 0);
    ifaceRuntime.sendBuffer.queue = Math.max(existingQueue, overflow);

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
            queue: 0,
            pendingDestinations: [],
        };
    }
    const used = Number(runtimeSnapshot?.used ?? metaSnapshot?.used ?? 0) || 0;
    const capacity = Number(runtimeSnapshot?.capacity ?? metaSnapshot?.capacity ?? 0) || 0;
    const head = runtimeSnapshot?.head ?? metaSnapshot?.head ?? null;
    const state = runtimeSnapshot?.state ?? metaSnapshot?.state ?? null;
    const queue = Number(runtimeSnapshot?.queue ?? metaSnapshot?.queue ?? 0) || 0;
    const pending = Array.isArray(runtimeSnapshot?.pendingDestinations)
        ? runtimeSnapshot.pendingDestinations
        : Array.isArray(metaSnapshot?.pendingDestinations)
            ? metaSnapshot.pendingDestinations
            : [];
    return {
        used,
        capacity,
        head,
        state,
        queue,
        pendingDestinations: pending,
    };
}

function describeBufferSnapshot(snapshot) {
    if (!snapshot || typeof snapshot !== 'object') {
        return { primary: '—', secondary: null };
    }
    const used = Number(snapshot.used ?? 0);
    const capacity = Number(snapshot.capacity ?? 0);
    const queue = Number(snapshot.queue ?? 0);
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
    if (queue > 0) {
        parts.push(`Queued: ${queue}`);
    }
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
    const queueStats = runtimeInterfaces.reduce((acc, ifaceRuntime) => {
        if (!ifaceRuntime) {
            return acc;
        }
        const sendBuffer = ifaceRuntime.sendBuffer || {};
        acc.waiting += Number(sendBuffer.queue || 0);
        acc.active += Number(sendBuffer.used || 0);
        return acc;
    }, { waiting: 0, active: 0 });
    const totalQueued = queueStats.waiting;
    const totalActive = queueStats.active;

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
            label: 'Queues',
            primary: totalQueued > 0
                ? `${totalQueued} packet${totalQueued === 1 ? '' : 's'} waiting`
                : (totalActive > 0
                    ? `${totalActive} packet${totalActive === 1 ? '' : 's'} in transfer`
                    : 'Queues empty'),
            secondary: (totalQueued > 0 && totalActive > 0)
                ? `Waiting: ${totalQueued} · Active: ${totalActive}`
                : totalActive > 0
                    ? `Active: ${totalActive}`
                    : (totalQueued > 0 ? `Waiting: ${totalQueued}` : null),
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
        if (typeof neighbor.x === 'number' && typeof neighbor.y === 'number') {
            return `${neighbor.x}-${neighbor.y}`;
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

    nodePanelTitle.textContent = `(${meta.x}, ${meta.y})`;
    nodePanelSubhead.textContent = `Grid position (${meta.x}, ${meta.y})`;
    nodePanelPosition.textContent = `(${meta.x}, ${meta.y})`;
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
                    label.textContent = `(${neighbor.x}, ${neighbor.y})`;
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

    const activeNeighborIds = new Set();
    if (currentRouteInfo && Array.isArray(currentRouteInfo.path) && currentRouteInfo.path.length) {
        const pathIndex = currentRouteInfo.path.findIndex((node) => makeNodeId(node) === selectedNodeId);
        if (pathIndex !== -1) {
            if (pathIndex > 0) {
                const previous = currentRouteInfo.path[pathIndex - 1];
                activeNeighborIds.add(makeNodeId(previous));
            }
            if (pathIndex < currentRouteInfo.path.length - 1) {
                const next = currentRouteInfo.path[pathIndex + 1];
                activeNeighborIds.add(makeNodeId(next));
            }
        }
    }

    const sendTotals = { used: 0, capacity: 0, queue: 0 };
    const recvTotals = { used: 0, capacity: 0, queue: 0 };
    const activeSendTotals = { used: 0, capacity: 0, queue: 0 };
    const activeRecvTotals = { used: 0, capacity: 0, queue: 0 };
    const activeSendDetails = [];
    const activeRecvDetails = [];
    const aggregatePending = new Map();

    interfaces.forEach((iface) => {
        if (!iface) return;
        const neighbor = iface.neighbor || null;
        const neighborId = neighbor ? makeNodeId(neighbor) : null;
        const runtimeOverlay = neighborId && runtimeInterfaces?.get(neighborId) ? runtimeInterfaces.get(neighborId) : null;

        const sendSnapshot = resolveBufferSnapshot(iface.sendBuffer, runtimeOverlay?.sendBuffer);
        sendTotals.used += Number(sendSnapshot.used || 0);
        sendTotals.capacity += Number(sendSnapshot.capacity || 0);
        sendTotals.queue += Number(sendSnapshot.queue || 0);
        const pendingList = Array.isArray(sendSnapshot.pendingDestinations)
            ? sendSnapshot.pendingDestinations
            : [];
        pendingList.forEach((item) => {
            if (!item || !item.destination) return;
            const { destination, count } = item;
            if (!Number.isFinite(destination?.x) || !Number.isFinite(destination?.y)) {
                return;
            }
            const key = makeNodeId(destination);
            const existing = aggregatePending.get(key) || { destination, count: 0 };
            existing.count += Number(count || 0);
            aggregatePending.set(key, existing);
        });
        if (neighborId && activeNeighborIds.has(neighborId)) {
            activeSendTotals.used += Number(sendSnapshot.used || 0);
            activeSendTotals.capacity += Number(sendSnapshot.capacity || 0);
            activeSendTotals.queue += Number(sendSnapshot.queue || 0);
            activeSendDetails.push({
                label: neighbor ? nodeLabel(neighbor) : neighborId,
                used: Number(sendSnapshot.used || 0),
                capacity: Number(sendSnapshot.capacity || 0),
                queue: Number(sendSnapshot.queue || 0),
                pendingDestinations: pendingList,
            });
        }

        const recvSnapshot = resolveBufferSnapshot(iface.receiveBuffer, runtimeOverlay?.receiveBuffer);
        recvTotals.used += Number(recvSnapshot.used || 0);
        recvTotals.capacity += Number(recvSnapshot.capacity || 0);
        recvTotals.queue += Number(recvSnapshot.queue || 0);
        if (neighborId && activeNeighborIds.has(neighborId)) {
            activeRecvTotals.used += Number(recvSnapshot.used || 0);
            activeRecvTotals.capacity += Number(recvSnapshot.capacity || 0);
            activeRecvTotals.queue += Number(recvSnapshot.queue || 0);
            activeRecvDetails.push({
                label: neighbor ? nodeLabel(neighbor) : neighborId,
                used: Number(recvSnapshot.used || 0),
                capacity: Number(recvSnapshot.capacity || 0),
                queue: Number(recvSnapshot.queue || 0),
            });
        }
    });

    const formatTotal = (totals) => {
        const { used, capacity, queue } = totals;
        if (capacity > 0) {
            const queueText = queue > 0 ? ` · Queue: ${queue}` : '';
            return `${used} / ${capacity} slot${capacity === 1 ? '' : 's'}${queueText}`;
        }
        const queueText = queue > 0 ? ` · Queue: ${queue}` : '';
        return `${used} slot${used === 1 ? '' : 's'}${queueText}`;
    };

    const formatPendingList = (pendingList, limit = 3) => {
        if (!Array.isArray(pendingList) || !pendingList.length) {
            return '';
        }
        const trimmed = pendingList
            .filter((item) => item && item.destination && Number.isFinite(item.count))
            .slice(0, limit);
        if (!trimmed.length) {
            return '';
        }
        const parts = trimmed.map((item) => {
            const { destination, count } = item;
            return `${nodeLabel(destination)}×${count}`;
        });
        if (pendingList.length > limit) {
            parts.push('…');
        }
        return parts.join(', ');
    };

    const formatActiveDetails = (details, totals) => {
        if (!details.length) {
            return totals.used > 0 || totals.queue > 0 ? formatTotal(totals) : 'Idle';
        }
        return details
            .map((entry) => {
                const { used, capacity, queue, label, pendingDestinations } = entry;
                const base = capacity > 0
                    ? `${used} / ${capacity}`
                    : `${used}`;
                const queueText = queue > 0 ? ` (queue ${queue})` : '';
                const pendingText = formatPendingList(pendingDestinations, 3);
                const pendingInfo = pendingText ? ` · Pending ${pendingText}` : '';
                return `${label}: ${base}${queueText}${pendingInfo}`;
            })
            .join(', ');
    };

    // Keep all the logic but only display simplified slots count
    let sendDisplay = formatTotal(sendTotals);
    // Logic kept for internal state but not shown in UI
    if (activeNeighborIds.size) {
        // Calculate active route details for diagnostics without surfacing them in the UI
        formatActiveDetails(activeSendDetails, activeSendTotals);
    }
    const aggregatePendingList = Array.from(aggregatePending.values())
        .filter((item) => item && item.destination && Number.isFinite(item.count) && item.count > 0)
        .sort((a, b) => (b.count - a.count) || makeNodeId(a.destination).localeCompare(makeNodeId(b.destination)));
    if (aggregatePendingList.length) {
        // Generate pending summary for potential telemetry but keep the UI focused on totals
        formatPendingList(aggregatePendingList, 4);
    }

    let receiveDisplay = formatTotal(recvTotals);
    if (activeNeighborIds.size) {
        formatActiveDetails(activeRecvDetails, activeRecvTotals);
        
    }

    updateBufferChip(nodePanelSendBuffer, runtime.sendBuffer, sendDisplay);
    updateBufferChip(nodePanelReceiveBuffer, runtime.receiveBuffer, receiveDisplay);

    const appBuffer = meta.applicationBuffer || {};
    const appCount = Number(appBuffer.count || 0);
    const runtimeAppCount = Number(runtime.applicationBuffer || 0);
    const appState = appCount > 0 || runtimeAppCount > 0 ? 'ready' : 'idle';
    const appDisplayCount = Math.max(appCount, runtimeAppCount);
    const queueTotal = Number(sendTotals.queue || 0);
    const appText = queueTotal > 0
        ? `${appDisplayCount} ${appDisplayCount === 1 ? 'packet' : 'packets'} · Queue: ${queueTotal}`
        : `${appDisplayCount} ${appDisplayCount === 1 ? 'packet' : 'packets'}`;
    updateBufferChip(
        nodePanelAppBuffer,
        appState,
        appText,
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
    nodePanelPosition.textContent = '—';
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
    if (pickMode) {
        const meta = nodeMeta.get(nodeId) || parseSelectValue(nodeId);
        const labelText = safeNodeLabel(meta);
        if (pickMode.rowId) {
            const route = nmRoutes.find((entry) => entry.id === pickMode.rowId);
            if (route) {
                const targetSelect = pickMode.type === 'source' ? route.sourceSelect : route.destSelect;
                if (targetSelect) {
                    populateSelectElementFromCache(targetSelect, nodeId);
                    setSelectValue(targetSelect, nodeId);
                    if (hudStatus) {
                        hudStatus.textContent = `${pickMode.type === 'source' ? 'Source' : 'Destination'} set to ${labelText}.`;
                    }
                    focusNode(nodeId, {
                        auto: nodePanelAutoTracking,
                        openPanelOnFocus: false,
                    });
                    renderTopology();
                }
            }
            setPickMode(null);
            return;
        }
        if (pickMode.type === 'source') {
            if (setSelectValue(sourceSelect, nodeId)) {
                handleSourceSelectChange({
                    announce: true,
                    message: `Source set to ${nodeLabel(meta)} via canvas.`,
                    openNodeDetails: false,
                });
            } else {
                focusNode(nodeId, {
                    auto: nodePanelAutoTracking,
                    openPanelOnFocus: false,
                });
                renderTopology();
            }
            setPickMode(null);
            return;
        }
        if (pickMode.type === 'destination') {
            const mode = getSimulationMode();
            if (mode === 'parallel') {
                if (destinationCandidateSelect) {
                    const needsChange = destinationCandidateSelect.value !== nodeId;
                    const updated = setSelectValue(destinationCandidateSelect, nodeId);
                    suppressCandidateSelectChange = Boolean(updated && needsChange);
                }
                const added = addMultiDestination(nodeId);
                if (!added && hudStatus && !hudStatus.textContent) {
                    hudStatus.textContent = `Destination ${labelText} could not be added.`;
                }
                return;
            }
            if (setSelectValue(destinationSelect, nodeId)) {
                handleDestinationSelectChange({
                    announce: true,
                    message: `Destination set to ${labelText} via canvas.`,
                    openNodeDetails: false,
                });
            } else {
                focusNode(nodeId, {
                    auto: nodePanelAutoTracking,
                    openPanelOnFocus: false,
                });
                renderTopology();
            }
            setPickMode(null);
            return;
        }
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

function computeLayout(rect, width, height) {
    const padding = 80;
    const availableWidth = rect.width - 2 * padding;
    const availableHeight = rect.height - 2 * padding;
    
    const cellWidth = width > 1 ? availableWidth / (width - 1) : availableWidth;
    const cellHeight = height > 1 ? availableHeight / (height - 1) : availableHeight;
    
    return {
        width: rect.width,
        height: rect.height,
        gridWidth: width,
        gridHeight: height,
        cellWidth,
        cellHeight,
        offsetX: padding,
        offsetY: padding,
    };
}

function baseNodePosition(x, y, layout) {
    return {
        x: layout.offsetX + x * layout.cellWidth,
        y: layout.offsetY + y * layout.cellHeight,
    };
}

function applyTransform(point, layout) {
    const centerX = layout.width / 2;
    const centerY = layout.height / 2;
    const dx = point.x - centerX;
    const dy = point.y - centerY;
    return {
        x: centerX + dx * viewState.zoom + viewState.panX,
        y: centerY + dy * viewState.zoom + viewState.panY,
    };
}

function getNodePosition(x, y, layout) {
    return applyTransform(baseNodePosition(x, y, layout), layout);
}

function screenToBase(screenX, screenY, layout) {
    const centerX = layout.width / 2;
    const centerY = layout.height / 2;
    const baseX = centerX + (screenX - centerX - viewState.panX) / viewState.zoom;
    const baseY = centerY + (screenY - centerY - viewState.panY) / viewState.zoom;
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

function nodeLabel({ x, y }) {
    return `(${x}, ${y})`;
}

function safeNodeLabel(node) {
    if (!node || typeof node.x !== 'number' || typeof node.y !== 'number') {
        return '(?, ?)';
    }
    return nodeLabel(node);
}

function routePathSignature(path) {
    if (!Array.isArray(path) || !path.length) {
        return null;
    }
    return path
        .map((node) => (node && typeof node.x === 'number' && typeof node.y === 'number'
            ? `${node.x}-${node.y}`
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
    title.textContent = multiRunState.mode === 'nm' ? 'n → m routes' : 'Parallel routes';
    multiRouteList.appendChild(title);

    const fragment = document.createDocumentFragment();
    const completedSet = multiRunState.completed instanceof Set ? multiRunState.completed : new Set();
    const activeIndex = typeof multiRunState.selectedIndex === 'number'
        ? multiRunState.selectedIndex
        : 0;
    const isNmMode = multiRunState.mode === 'nm';

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

        if (payload.color) {
            card.style.borderLeft = `4px solid ${payload.color}`;
        }

        if (multiRunState.mode === 'parallel' || multiRunState.mode === 'nm') {
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
        const labelPrefix = isNmMode
            ? `Route ${payload.routeIndex != null ? payload.routeIndex + 1 : index + 1}`
            : `Packet ${payload.packetIndex || index + 1}`;
        titleEl.textContent = `${labelPrefix}: ${safeNodeLabel(startNode)} → ${safeNodeLabel(endNode)}`;
        card.appendChild(titleEl);

        const details = document.createElement('ul');
        details.className = 'flow-entry__details';
        if (!isNmMode) {
            const packetCountItem = document.createElement('li');
            const packetCount = payload.packetCount || multiRunState.payloads.length;
            packetCountItem.textContent = `${labelPrefix} of ${packetCount}`;
            details.appendChild(packetCountItem);
        } else {
            const summaryEntry = multiRunState.routeQueueSummary instanceof Map
                ? multiRunState.routeQueueSummary.get(payload.routeIndex)
                : multiRunState.routeQueueSummary?.[payload.routeIndex] || null;
            const totalPackets = payload.packetBatches || 1;
            const activeCount = summaryEntry ? summaryEntry.active : Math.min(payload.bufferCapacity || totalPackets, totalPackets);
            const waitingCount = summaryEntry ? summaryEntry.waiting : Math.max(totalPackets - activeCount, 0);
            const deliveredCount = summaryEntry ? summaryEntry.delivered : 0;

            const totalItem = document.createElement('li');
            totalItem.textContent = `Total packets: ${totalPackets}`;
            details.appendChild(totalItem);

            const activeItem = document.createElement('li');
            activeItem.textContent = `In buffer: ${activeCount}`;
            details.appendChild(activeItem);

            const queueItem = document.createElement('li');
            queueItem.textContent = `Queue: ${waitingCount}`;
            details.appendChild(queueItem);

            const deliveredItem = document.createElement('li');
            deliveredItem.textContent = `Delivered: ${deliveredCount}`;
            details.appendChild(deliveredItem);

            if (Number.isFinite(payload.bufferCapacity)) {
                const bufferItem = document.createElement('li');
                bufferItem.textContent = `Send buffer capacity: ${payload.bufferCapacity}`;
                details.appendChild(bufferItem);
            }
        }
        const hopItem = document.createElement('li');
        hopItem.textContent = `Hop count: ${payload.hopCount ?? 0}`;
        details.appendChild(hopItem);

        if ((multiRunState.mode === 'parallel' || multiRunState.mode === 'nm') && !isCompleted) {
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
    } else if (multiRunState.mode === 'nm') {
        focusNmRoute(index);
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
    } else if (multiRunState.mode === 'nm') {
        focusNmRoute(index);
    }
}

function ensureParallelCompletionSet() {
    if (!multiRunState || (multiRunState.mode !== 'parallel' && multiRunState.mode !== 'nm')) {
        return null;
    }
    if (!(multiRunState.completed instanceof Set)) {
        multiRunState.completed = new Set();
    }
    return multiRunState.completed;
}

function updateParallelRouteProgress(statuses = [], contexts = []) {
    const completedSet = ensureParallelCompletionSet();
    if (!completedSet || !multiRunState) return;

    if (!Array.isArray(multiRunState.completedRoutes)) {
        multiRunState.completedRoutes = [];
    }
    if (!Array.isArray(multiRunState.completedStatuses)) {
        multiRunState.completedStatuses = [];
    }

    const isNmMode = multiRunState.mode === 'nm';
    const routeSummary = multiRunState.routeQueueSummary || null;
    let changed = false;

    function markRouteComplete(routeIndex, statusOverride = null) {
        if (!Number.isFinite(routeIndex) || completedSet.has(routeIndex)) {
            return false;
        }

        const payload = Array.isArray(multiRunState.payloads)
            ? multiRunState.payloads[routeIndex]
            : null;
        let completedStatus = statusOverride;
        if (!completedStatus && payload) {
            completedStatus = buildCompletedStatusFromPayload(payload);
        }
        if (!completedStatus) {
            completedStatus = {
                hopText: '0 / 0',
                nodesText: 'Route delivered',
                phaseKey: 'completed',
                phaseLabel: 'Completed',
                signalText: 'Idle',
                signalStates: { req: 'sleep', ack: 'sleep', data: 'sleep' },
                transferText: isNmMode ? 'Route delivered' : 'Packet delivered',
                progressPercent: 100,
                timer: 0,
            };
        }

        completedSet.add(routeIndex);
        multiRunState.completedStatuses[routeIndex] = {
            ...completedStatus,
            signalStates: {
                ...(completedStatus.signalStates || {}),
            },
        };

        if (payload) {
            multiRunState.completedRoutes[routeIndex] = new RoutePreview(payload, {
                renderStyle: 'completed',
                strokeOpacity: 0.95,
                lineWidth: 4,
            });
        }

        if (Array.isArray(multiRunState.previewRoutes) && multiRunState.previewRoutes[routeIndex]) {
            multiRunState.previewRoutes[routeIndex].renderStyle = 'completed';
            multiRunState.previewRoutes[routeIndex].strokeOpacity = Math.max(
                multiRunState.previewRoutes[routeIndex].strokeOpacity || 0.85,
                0.85,
            );
        }
        return true;
    }

    statuses.forEach((status, index) => {
        if (!status) return;
        const context = Array.isArray(contexts) ? contexts[index] || {} : {};
        const contextIndex = Number.isFinite(context.routeIndex) ? context.routeIndex : index;
        const routeIndex = Number.isFinite(contextIndex) ? contextIndex : index;

        if (isNmMode) {
            const summaryEntry = routeSummary instanceof Map
                ? routeSummary.get(routeIndex)
                : routeSummary?.[routeIndex];
            const totalPackets = Number(summaryEntry?.total || 0);
            const deliveredPackets = Number(summaryEntry?.delivered || 0);
            if (totalPackets > 0 && deliveredPackets >= totalPackets) {
                if (markRouteComplete(routeIndex)) {
                    changed = true;
                }
            }
        } else {
            const isCompleted = status.phaseKey === 'completed' || status.phaseLabel === 'Completed';
            if (isCompleted && markRouteComplete(routeIndex, status)) {
                changed = true;
            }
        }
    });

    if (isNmMode && routeSummary) {
        const entries = routeSummary instanceof Map
            ? Array.from(routeSummary.entries())
            : Object.entries(routeSummary);
        entries.forEach(([key, summary]) => {
            const routeIndex = Number(key);
            if (!Number.isFinite(routeIndex)) return;
            const totalPackets = Number(summary?.total || 0);
            const deliveredPackets = Number(summary?.delivered || 0);
            if (totalPackets > 0 && deliveredPackets >= totalPackets) {
                if (markRouteComplete(routeIndex)) {
                    changed = true;
                }
            }
        });
    }

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
    const transferText = multiRunState?.mode === 'nm' ? 'Route delivered' : 'Packet delivered';

    return {
        hopText: totalHops > 0 ? `${totalHops} / ${totalHops}` : '0 / 0',
        nodesText: startNode && endNode
            ? `${safeNodeLabel(startNode)} → ${safeNodeLabel(endNode)}`
            : 'Route complete',
        phaseKey: 'completed',
        phaseLabel: 'Completed',
        signalText: 'Idle',
        signalStates: { req: 'sleep', ack: 'sleep', data: 'sleep' },
        transferText,
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

function focusNmRoute(index) {
    if (!multiRunState || multiRunState.mode !== 'nm') return;
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
    const previewColors = previewEntry
        ? {
            treeColor: previewEntry.treeColor || payload.color,
            ringColor: previewEntry.ringColor || payload.color,
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
        contextLabel: `Route ${index + 1} of ${multiRunState.payloads.length}`,
        contextHint: isCompleted
            ? 'Route delivered. Click "Animate all" to replay the plan.'
            : 'Preview loaded. Click "Animate all" to execute the full n → m plan.',
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
    const defaultLabel = animateBtn?.dataset?.defaultLabel || 'Animate path';
    const startDefaultLabel = 'Start animation';
    const currentAnimateLabel = animateBtn?.dataset?.currentLabel;
    let startLabel = label;
    if (!startLabel) {
        if (currentAnimateLabel && currentAnimateLabel !== defaultLabel) {
            startLabel = currentAnimateLabel;
        } else {
            startLabel = startDefaultLabel;
        }
    }

    if (animateBtn) {
        if (typeof disabled === 'boolean') {
            animateBtn.disabled = disabled;
        }
        if (label) {
            animateBtn.dataset.currentLabel = label;
        } else if (!animateBtn.dataset.currentLabel) {
            animateBtn.dataset.currentLabel = defaultLabel;
        }
        const currentLabel = animateBtn.dataset.currentLabel || defaultLabel;
        animateBtn.textContent = busy ? 'Animating…' : currentLabel;
    }

    if (playPauseAnimationBtn) {
        if (typeof disabled === 'boolean' && !animationState) {
            playPauseAnimationBtn.disabled = disabled;
        }
        if (!animationState) {
            const ariaLabel = busy ? 'Preparing animation' : (startLabel || startDefaultLabel);
            playPauseAnimationBtn.setAttribute('aria-label', ariaLabel);
            playPauseAnimationBtn.title = ariaLabel;
            playPauseAnimationBtn.dataset.state = 'play';
        }
    }
}

function openSpeedMenu() {
    if (!speedMenuBtn || !speedMenuPopover) {
        return;
    }
    speedMenuPopover.hidden = false;
    speedMenuBtn.setAttribute('aria-expanded', 'true');
    speedMenuOpen = true;
    if (speedControl) {
        requestAnimationFrame(() => {
            speedControl.focus();
        });
    }
}

function closeSpeedMenu({ focusButton = false } = {}) {
    if (!speedMenuBtn || !speedMenuPopover) {
        return;
    }
    if (speedMenuPopover.hidden) {
        if (speedMenuBtn.getAttribute('aria-expanded') !== 'false') {
            speedMenuBtn.setAttribute('aria-expanded', 'false');
        }
        speedMenuOpen = false;
        return;
    }
    speedMenuPopover.hidden = true;
    speedMenuBtn.setAttribute('aria-expanded', 'false');
    speedMenuOpen = false;
    if (focusButton) {
        speedMenuBtn.focus();
    }
}

function toggleSpeedMenu() {
    if (!speedMenuBtn || !speedMenuPopover) {
        return;
    }
    if (speedMenuPopover.hidden) {
        openSpeedMenu();
    } else {
        closeSpeedMenu();
    }
}

function updateAnimationControlState() {
    if (playPauseAnimationBtn) {
        const isRunning = Boolean(animationState);
        const isActive = isRunning && !animationPaused;
        const label = !isRunning
            ? 'Start animation'
            : animationPaused
                ? 'Resume animation'
                : 'Pause animation';
        const state = isActive ? 'pause' : 'play';
        playPauseAnimationBtn.dataset.state = state;
        playPauseAnimationBtn.title = label;
        playPauseAnimationBtn.setAttribute('aria-label', label);
        playPauseAnimationBtn.setAttribute('aria-pressed', isActive ? 'true' : 'false');
        if (isRunning) {
            playPauseAnimationBtn.disabled = false;
        }
        playPauseAnimationBtn.classList.toggle('is-active', isActive);
        if (!isRunning) {
            playPauseAnimationBtn.dataset.state = 'play';
        }
    }
    if (restartAnimationBtn) {
        restartAnimationBtn.disabled = false;
        restartAnimationBtn.title = 'Reset simulation';
        restartAnimationBtn.setAttribute('aria-label', 'Reset simulation');
        const srRestartLabel = restartAnimationBtn.querySelector('.sr-only');
        if (srRestartLabel) {
            srRestartLabel.textContent = 'Reset simulation';
        }
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
    resetSimulation();
    if (hudStatus) {
        hudStatus.textContent = 'Simulation reset';
    }
}

function ingestTopologyPayload(data, { resetView = true } = {}) {
    topologyData = data;
    if (widthInput && data?.width) {
        widthInput.value = `${data.width}`;
    }
    if (heightInput && data?.height) {
        heightInput.value = `${data.height}`;
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
            value: `${node.x}-${node.y}`,
            label: `(${node.x}, ${node.y})`,
        }))
        .sort((a, b) => a.value.localeCompare(b.value));

    nodeOptionsCache = options;

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

    refreshNmRouteOptions();
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

function drawMeshGrid(layout) {
    if (!topologyData) return;
    ctx.save();
    ctx.strokeStyle = '#94a3b8';
    ctx.lineWidth = 1.2;
    ctx.globalAlpha = 0.3;
    
    // Draw vertical lines
    for (let x = 0; x < layout.gridWidth; x++) {
        const top = getNodePosition(x, 0, layout);
        const bottom = getNodePosition(x, layout.gridHeight - 1, layout);
        ctx.beginPath();
        ctx.moveTo(top.x, top.y);
        ctx.lineTo(bottom.x, bottom.y);
        ctx.stroke();
    }
    
    // Draw horizontal lines
    for (let y = 0; y < layout.gridHeight; y++) {
        const left = getNodePosition(0, y, layout);
        const right = getNodePosition(layout.gridWidth - 1, y, layout);
        ctx.beginPath();
        ctx.moveTo(left.x, left.y);
        ctx.lineTo(right.x, right.y);
        ctx.stroke();
    }
    
    ctx.restore();
}

function drawMeshEdges(layout) {
    if (!topologyData) return;
    ctx.save();
    ctx.strokeStyle = colors.tree;
    ctx.lineWidth = 1.5;
    
    // Draw horizontal edges
    if (Array.isArray(topologyData.horizontalEdges)) {
        topologyData.horizontalEdges.forEach(({ source, target }) => {
            const start = getNodePosition(source.x, source.y, layout);
            const end = getNodePosition(target.x, target.y, layout);
            ctx.beginPath();
            ctx.moveTo(start.x, start.y);
            ctx.lineTo(end.x, end.y);
            ctx.stroke();
        });
    }
    
    // Draw vertical edges
    if (Array.isArray(topologyData.verticalEdges)) {
        topologyData.verticalEdges.forEach(({ source, target }) => {
            const start = getNodePosition(source.x, source.y, layout);
            const end = getNodePosition(target.x, target.y, layout);
            ctx.beginPath();
            ctx.moveTo(start.x, start.y);
            ctx.lineTo(end.x, end.y);
            ctx.stroke();
        });
    }
    
    ctx.restore();
}

function drawNodes(layout) {
    if (!topologyData) return;
    ctx.save();
    const mode = getSimulationMode();
    const highlightMulti = mode === 'parallel';
    const multiDestinationSet = highlightMulti ? new Set(multiDestinations) : null;
    const highlightNm = mode === 'nm';
    const nmSourceSet = highlightNm
        ? new Set(nmRoutes.map((route) => route.sourceId).filter(Boolean))
        : null;
    const nmDestinationSet = highlightNm
        ? new Set(nmRoutes.map((route) => route.destinationId).filter(Boolean))
        : null;
    topologyData.nodes.forEach((node) => {
        const nodeId = makeNodeId(node);
        const pos = getNodePosition(node.x, node.y, layout);
        const zoomRadius = clamp(viewState.zoom, 0.7, 1.6);
        const radius = 8 * zoomRadius;
        nodePositions.set(nodeId, { x: pos.x, y: pos.y, radius });
        const isSelected = nodeId === selectedNodeId;
        const isSource = nodeId === currentSourceId;
        const isDestination = highlightMulti
            ? multiDestinationSet.has(nodeId)
            : nodeId === currentDestinationId;
        const isNmSource = highlightNm && nmSourceSet?.has(nodeId);
        const isNmDestination = highlightNm && nmDestinationSet?.has(nodeId);
        let fillColor = colors.node;
        const combinedSource = (isSource || isNmSource) && (isDestination || isNmDestination);
        if (combinedSource) {
            fillColor = colors.sharedNode;
        } else if (isSource || isNmSource) {
            fillColor = colors.sourceNode;
        } else if (isDestination || isNmDestination) {
            fillColor = colors.destinationNode;
        }
        if (isSelected) {
            fillColor = colors.nodeSelected;
        }

        // Draw square instead of circle
        const size = radius * 1.6; // Make squares slightly larger for visibility
        ctx.beginPath();
        ctx.rect(pos.x - size/2, pos.y - size/2, size, size);
        ctx.fillStyle = fillColor;
        ctx.fill();

        ctx.beginPath();
        ctx.rect(pos.x - size/2, pos.y - size/2, size, size);
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
        ctx.fillText(nodeLabel(node), pos.x, pos.y + size/2 + 4);
        
        // Draw active interfaces on hover after 2 seconds
        if (hoverState.showInterfaces && hoverState.nodeId === nodeId) {
            drawActiveInterfaces(node, pos, size);
        }
    });
    ctx.restore();
}

function drawActiveInterfaces(node, pos, nodeSize) {
    if (!currentSimulation || !currentSimulation.nodeStates) return;
    
    const nodeId = makeNodeId(node);
    const nodeState = currentSimulation.nodeStates.get(nodeId);
    if (!nodeState) return;
    
    // Get node metadata to find interfaces
    const meta = topologyData.nodes.find(n => makeNodeId(n) === nodeId);
    if (!meta || !meta.neighbors) return;
    
    const interfaceSize = 12;
    const offset = nodeSize/2 + 8;
    
    // Draw interfaces for each neighbor (N, E, S, W)
    meta.neighbors.forEach((neighbor, idx) => {
        const neighborId = makeNodeId(neighbor);
        const interfaceState = nodeState.interfaces?.get(neighborId);
        
        // Only show active interfaces (not idle)
        if (!interfaceState || 
            (interfaceState.sendBuffer === 'idle' && 
             interfaceState.receiveBuffer === 'idle' && 
             interfaceState.handshake === 'idle')) {
            return;
        }
        
        // Determine direction based on neighbor position
        let dx = neighbor.x - node.x;
        let dy = neighbor.y - node.y;
        let ifaceX = pos.x;
        let ifaceY = pos.y;
        
        if (dx > 0) { // East
            ifaceX = pos.x + offset;
        } else if (dx < 0) { // West
            ifaceX = pos.x - offset;
        }
        
        if (dy > 0) { // South
            ifaceY = pos.y + offset;
        } else if (dy < 0) { // North
            ifaceY = pos.y - offset;
        }
        
        // Draw interface indicator
        ctx.save();
        
        // Background
        ctx.fillStyle = 'rgba(30, 41, 59, 0.95)';
        ctx.fillRect(ifaceX - interfaceSize/2, ifaceY - interfaceSize/2, interfaceSize, interfaceSize);
        
        // Border based on state
        let borderColor = colors.node;
        if (interfaceState.sendBuffer === 'transferring' || 
            interfaceState.receiveBuffer === 'receiving') {
            borderColor = '#10b981'; // Green for active transfer
        } else if (interfaceState.handshake === 'waiting' || 
                   interfaceState.handshake === 'primed') {
            borderColor = '#f59e0b'; // Orange for handshake
        }
        
        ctx.strokeStyle = borderColor;
        ctx.lineWidth = 2;
        ctx.strokeRect(ifaceX - interfaceSize/2, ifaceY - interfaceSize/2, interfaceSize, interfaceSize);
        
        // Draw buffer state indicators (small colored dots)
        const dotSize = 3;
        if (interfaceState.sendBuffer !== 'idle') {
            ctx.fillStyle = interfaceState.sendBuffer === 'transferring' ? '#10b981' : '#f59e0b';
            ctx.beginPath();
            ctx.arc(ifaceX - 3, ifaceY, dotSize/2, 0, Math.PI * 2);
            ctx.fill();
        }
        if (interfaceState.receiveBuffer !== 'idle') {
            ctx.fillStyle = interfaceState.receiveBuffer === 'receiving' ? '#10b981' : '#f59e0b';
            ctx.beginPath();
            ctx.arc(ifaceX + 3, ifaceY, dotSize/2, 0, Math.PI * 2);
            ctx.fill();
        }
        
        ctx.restore();
    });
}

function meshGridPoint(fromNode, toNode, progress, layout) {
    const startPos = getNodePosition(fromNode.x, fromNode.y, layout);
    const endPos = getNodePosition(toNode.x, toNode.y, layout);
    const t = clamp(progress, 0, 1);
    return {
        x: startPos.x + (endPos.x - startPos.x) * t,
        y: startPos.y + (endPos.y - startPos.y) * t,
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

        // For mesh, we draw straight lines (either horizontal or vertical)
        const startPos = getNodePosition(from.x, from.y, layout);
        const endPos = getNodePosition(to.x, to.y, layout);
        ctx.beginPath();
        ctx.strokeStyle = activeTreeColor;
        const midX = startPos.x + (endPos.x - startPos.x) * clamp(completion, 0, 1);
        const midY = startPos.y + (endPos.y - startPos.y) * clamp(completion, 0, 1);
        ctx.moveTo(startPos.x, startPos.y);
        ctx.lineTo(midX, midY);
        ctx.stroke();

        if (allowDirectionHint && completion > 0.1) {
            const baseProgress = completion;
            const arrowProgress = Math.min(Math.max(baseProgress, 0.2), 0.95);
            const arrowPoint = segmentPointWithAngle(segment, arrowProgress, layout, { allowClamp: true });
            const arrowColor = activeTreeColor;
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

function segmentPointWithAngle(segment, progress, layout, { reverse = false, allowClamp = false } = {}) {
    const clampedProgress = allowClamp ? clamp(progress, 0, 1) : progress;
    
    // For mesh, all segments are straight lines
    const fromNode = reverse ? segment.to : segment.from;
    const toNode = reverse ? segment.from : segment.to;
    const fromPos = getNodePosition(fromNode.x, fromNode.y, layout);
    const toPos = getNodePosition(toNode.x, toNode.y, layout);
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
        const destPos = getNodePosition(segment.to.x, segment.to.y, layout);
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
                point: getNodePosition(segment.from.x, segment.from.y, layout),
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
                point: getNodePosition(segment.to.x, segment.to.y, layout),
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
    layoutCache = computeLayout(rect, topologyData.width, topologyData.height);
    ctx.setTransform(canvasScale, 0, 0, canvasScale, 0, 0);
    ctx.clearRect(0, 0, canvas.width / canvasScale, canvas.height / canvasScale);
    drawMeshGrid(layoutCache);
    drawMeshEdges(layoutCache);
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
        if ((animationState.mode === 'parallel' || animationState.mode === 'nm') && Array.isArray(animationState.animations)) {
            animationState.animations.forEach((animation, index) => {
                const routeIndex = Number.isFinite(animation?.routeIndex)
                    ? animation.routeIndex
                    : index;
                const routePayload = Array.isArray(multiRunState?.payloads)
                    ? multiRunState.payloads[routeIndex]
                    : null;
                const color = routePayload?.color
                    || PARALLEL_ROUTE_COLORS[index % PARALLEL_ROUTE_COLORS.length];
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
    
    // Update interface panel if visible
    updateInterfacePanel();
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
    constructor(payloads, speed, options = {}) {
        this.mode = options.mode === 'nm' ? 'nm' : 'parallel';
        this.speed = speed;
        this.payloads = Array.isArray(payloads) ? payloads : [];
        this.queueConfig = options.queueConfig instanceof Map
            ? new Map(options.queueConfig)
            : options.queueConfig && typeof options.queueConfig === 'object'
                ? new Map(Object.entries(options.queueConfig))
                : new Map();
        this.routeSummary = options.routeSummary instanceof Map
            ? options.routeSummary
            : options.routeSummary && typeof options.routeSummary === 'object'
                ? new Map(Object.entries(options.routeSummary))
                : null;
        this.latestStatuses = [];
        this.activeEntries = [];
        this.queueState = new Map();
        this.allEntries = [];
        this.sourceQueues = new Map();

        this.queueConfig.forEach((config, key) => {
            if (!config || !config.sourceId) return;
            if (!this.sourceQueues.has(config.sourceId)) {
                this.sourceQueues.set(config.sourceId, new Set());
            }
            this.sourceQueues.get(config.sourceId).add(key);
        });

        this.payloads.forEach((payload, index) => {
            this.registerPayload(payload, index);
        });
    }

    get animations() {
        return this.activeEntries.map((entry) => entry.animation);
    }

    getActiveEntries() {
        return this.activeEntries.slice();
    }

    resolveQueueKey(payload, index) {
        if (payload && typeof payload.queueKey === 'string') {
            return payload.queueKey;
        }
        if (payload && Number.isFinite(payload.routeIndex)) {
            return `route-${payload.routeIndex}`;
        }
        return `payload-${index}`;
    }

    ensureQueueState(queueKey, payload) {
        if (!this.queueState.has(queueKey)) {
            const config = this.queueConfig.get(queueKey) || {};
            let capacity = Number.isFinite(config.capacity) ? config.capacity : null;
            if (!Number.isFinite(capacity) || capacity <= 0) {
                capacity = Number.isFinite(payload?.bufferCapacity) && payload.bufferCapacity > 0
                    ? payload.bufferCapacity
                    : 1;
            }
            this.queueState.set(queueKey, {
                capacity: Math.max(1, Math.trunc(capacity)),
                active: [],
                waiting: [],
                routeIndex: Number.isFinite(payload?.routeIndex) ? payload.routeIndex : null,
            });
        }
        return this.queueState.get(queueKey);
    }

    registerPayload(payload, index) {
        const queueKey = this.resolveQueueKey(payload, index);
        const animation = new RouteAnimation(payload, this.speed);
        const routeIndex = Number.isFinite(payload?.routeIndex) ? payload.routeIndex : index;
        animation.routeIndex = routeIndex;
        animation.queueKey = queueKey;
        const entry = {
            animation,
            payload,
            queueKey,
            routeIndex,
            active: false,
        };
        this.allEntries.push(entry);

        const shouldQueue = this.mode === 'nm' || this.queueConfig.has(queueKey);
        if (shouldQueue) {
            const state = this.ensureQueueState(queueKey, payload);
            if (state.active.length < state.capacity) {
                this.startEntry(entry, { initial: true });
            } else {
                this.queueEntry(entry);
            }
            this.applyQueueState(queueKey);
        } else {
            this.activateDirect(entry);
        }
    }

    activateDirect(entry) {
        entry.active = true;
        this.activeEntries.push(entry);
    }

    queueEntry(entry) {
        const state = this.ensureQueueState(entry.queueKey, entry.payload);
        state.waiting.push(entry);
        entry.active = false;
    }

    startEntry(entry, { initial = false } = {}) {
        const state = this.ensureQueueState(entry.queueKey, entry.payload);
        if (!state.active.includes(entry)) {
            state.active.push(entry);
        }
        if (!this.activeEntries.includes(entry)) {
            this.activeEntries.push(entry);
        }
        entry.active = true;
        entry.animation.startTimestamp = null;
        entry.animation.elapsedMs = 0;
        entry.animation.progress = 0;
        entry.animation.lastStageKey = null;
        entry.animation.latestStatus = null;

        if (!initial) {
            this.updateRouteSummary(entry.routeIndex, (summary) => {
                summary.active = Math.min(summary.total, summary.active + 1);
                summary.waiting = Math.max(0, summary.waiting - 1);
            });
            this.applyQueueState(entry.queueKey);
            this.notifyQueueChange(entry.queueKey);
        }
    }

    update(timestamp) {
        const useQueueExecution = this.mode === 'nm' || this.queueConfig.size > 0;
        if (useQueueExecution) {
            const snapshot = this.activeEntries.slice();
            const completed = [];
            snapshot.forEach((entry) => {
                entry.animation.update(timestamp);
                if (entry.animation.isComplete()) {
                    completed.push(entry);
                }
            });
            if (completed.length) {
                completed.forEach((entry) => this.completeEntry(entry));
            }
        } else {
            this.activeEntries.forEach((entry) => entry.animation.update(timestamp));
        }
    }

    completeEntry(entry) {
        const state = this.queueState.get(entry.queueKey);
        if (state) {
            state.active = state.active.filter((item) => item !== entry);
        }
        this.activeEntries = this.activeEntries.filter((item) => item !== entry);
        entry.active = false;

        this.updateRouteSummary(entry.routeIndex, (summary) => {
            summary.active = Math.max(0, summary.active - 1);
            summary.delivered = Math.min(summary.total, summary.delivered + 1);
        });
        this.applyQueueState(entry.queueKey);

        const next = this.dequeueNext(entry.queueKey);
        if (next) {
            this.startEntry(next, { initial: false });
        } else {
            this.notifyQueueChange(entry.queueKey);
        }
    }

    dequeueNext(queueKey) {
        const state = this.queueState.get(queueKey);
        if (!state || !state.waiting.length) return null;
        return state.waiting.shift();
    }

    updateRouteSummary(routeIndex, mutator) {
        if (!Number.isFinite(routeIndex) || !this.routeSummary) return;
        const current = this.routeSummary instanceof Map
            ? this.routeSummary.get(routeIndex)
            : this.routeSummary[routeIndex];
        const base = current ? { ...current } : { total: 0, active: 0, waiting: 0, delivered: 0 };
        mutator(base);
        const total = Number.isFinite(base.total) ? base.total : Number(current?.total ?? 0) || 0;
        base.total = total;
        base.active = clamp(Number(base.active) || 0, 0, total);
        base.delivered = clamp(Number(base.delivered) || 0, 0, total);
        const remaining = Math.max(total - base.delivered, 0);
        const waitingCandidate = Number(base.waiting) || Number(current?.waiting ?? 0) || 0;
        base.waiting = clamp(waitingCandidate, 0, remaining);

        if (this.routeSummary instanceof Map) {
            this.routeSummary.set(routeIndex, base);
        } else {
            this.routeSummary[routeIndex] = base;
        }
    }

    applyQueueState(queueKey) {
        const config = this.queueConfig.get(queueKey) || null;
        const state = this.queueState.get(queueKey) || null;
        if (!config || !state) return;

        const ifaceRuntime = ensureInterfaceRuntimeState(config.sourceId, config.neighborNode);
        if (ifaceRuntime && ifaceRuntime.sendBuffer) {
            if (Number.isFinite(config.capacity) && config.capacity > 0) {
                ifaceRuntime.sendBuffer.capacity = config.capacity;
            }
            ifaceRuntime.sendBuffer.used = state.active.length;
            ifaceRuntime.sendBuffer.queue = Math.max(state.waiting.length, 0);
            ifaceRuntime.sendBuffer.state = state.active.length > 0
                ? 'transferring'
                : (state.waiting.length > 0 ? 'primed' : 'idle');
        }

        this.updateSourceRuntime(config.sourceId);
    }

    updateSourceRuntime(sourceId) {
        if (!sourceId) return;
        const queues = this.sourceQueues.get(sourceId);
        const runtime = ensureNodeRuntimeState(sourceId);
        if (!runtime) return;

        let active = 0;
        let waiting = 0;
        if (queues instanceof Set) {
            queues.forEach((key) => {
                const state = this.queueState.get(key);
                if (state) {
                    active += state.active.length;
                    waiting += state.waiting.length;
                }
            });
        }

        runtime.pendingOutbound = active + waiting;
        if (active > 0) {
            runtime.sendBuffer = 'transferring';
            runtime.handshake = 'transferring';
        } else if (waiting > 0) {
            runtime.sendBuffer = 'primed';
            runtime.handshake = 'primed';
        } else {
            runtime.sendBuffer = 'idle';
            runtime.handshake = 'idle';
            runtime.pendingOutbound = 0;
        }
        runtime.lastUpdated = performance.now();

        if (
            typeof isNodePanelOpen === 'function'
            && isNodePanelOpen()
            && typeof updateNodePanelContent === 'function'
            && selectedNodeId === sourceId
        ) {
            updateNodePanelContent();
        }
    }

    notifyQueueChange(queueKey) {
        if (typeof renderMultiRouteList === 'function') {
            renderMultiRouteList();
        }
        const config = this.queueConfig.get(queueKey);
        if (
            config
            && typeof isNodePanelOpen === 'function'
            && isNodePanelOpen()
            && typeof updateNodePanelContent === 'function'
            && selectedNodeId === config.sourceId
        ) {
            updateNodePanelContent();
        }
    }

    isComplete() {
        if (this.mode === 'nm' || this.queueConfig.size > 0) {
            return this.allEntries.every((entry) => entry.animation.isComplete());
        }
        return this.activeEntries.every((entry) => entry.animation.isComplete());
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

function aggregateParallelStatuses(statuses, {
    timerOverride,
    forceComplete = false,
    mode = null,
    routeSummary = null,
} = {}) {
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

    const statusCount = statuses.length;
    let total = statusCount;
    let completed = 0;
    let progressSum = 0;
    let maxTimer = 0;

    const summaryEntries = mode === 'nm'
        ? routeSummary instanceof Map
            ? Array.from(routeSummary.values())
            : routeSummary && typeof routeSummary === 'object'
                ? Object.values(routeSummary)
                : []
        : [];

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

    let progressPercent = forceComplete
        ? 100
        : Math.round(progressSum / Math.max(statusCount, 1));
    let allComplete = forceComplete || completed === total;
    const timer = typeof timerOverride === 'number' ? timerOverride : Math.round(maxTimer);
    let remaining = Math.max(total - completed, 0);
    const isNmMode = mode === 'nm';

    if (isNmMode && summaryEntries.length) {
        const validEntries = summaryEntries.filter((entry) => entry && Number.isFinite(entry.total));
        if (validEntries.length) {
            total = validEntries.length;
            const completedRoutes = validEntries.filter((entry) => entry.delivered >= entry.total).length;
            completed = completedRoutes;
            remaining = Math.max(total - completedRoutes, 0);
            const deliveredPortion = validEntries.reduce((sum, entry) => {
                if (!entry.total) return sum + 1;
                const ratio = entry.delivered / entry.total;
                return sum + clamp(ratio, 0, 1);
            }, 0);
            progressPercent = forceComplete
                ? 100
                : Math.round((deliveredPortion / validEntries.length) * 100);
            allComplete = forceComplete || completedRoutes === validEntries.length;
        }
    }

    return {
        hopText: `${completed} / ${total}`,
        nodesText: allComplete
            ? (isNmMode ? 'All routes delivered' : 'All packets delivered')
            : `${remaining} ${isNmMode ? 'route' : 'packet'}${remaining === 1 ? '' : 's'} still in flight`,
        phaseKey: allComplete ? 'completed' : 'data',
        phaseLabel: allComplete ? 'Completed' : (isNmMode ? 'n → m' : 'Parallel'),
        signalText: allComplete ? 'Idle' : (isNmMode ? 'n → m active' : 'Parallel active'),
        signalStates: allComplete
            ? { req: 'sleep', ack: 'sleep', data: 'sleep' }
            : { req: 'active', ack: 'active', data: 'active' },
        transferText: allComplete
            ? (isNmMode ? 'Routes delivered' : 'Packets delivered')
            : (isNmMode ? 'Multiple routes transferring' : 'Multiple packets transferring'),
        progressPercent,
        timer,
    };
}

function registerDeliveredPacket(nodeState, nodeId, packetKey) {
    if (!nodeState || !packetKey) {
        return false;
    }
    if (!(nodeState.deliveredPackets instanceof Set)) {
        nodeState.deliveredPackets = new Set();
    }
    if (nodeState.deliveredPackets.has(packetKey)) {
        return false;
    }
    nodeState.deliveredPackets.add(packetKey);
    nodeState.applicationBuffer = Math.max(0, Number(nodeState.applicationBuffer || 0)) + 1;
    nodeState.lastUpdated = performance.now();

    if (multiRunState) {
        if (!(multiRunState.deliveredCounts instanceof Map)) {
            multiRunState.deliveredCounts = new Map();
        }
        const existing = multiRunState.deliveredCounts.get(nodeId) || 0;
        multiRunState.deliveredCounts.set(nodeId, existing + 1);
        if (!(multiRunState.deliveredPacketKeys instanceof Set)) {
            multiRunState.deliveredPacketKeys = new Set();
        }
        multiRunState.deliveredPacketKeys.add(`${nodeId}:${packetKey}`);
    }

    if (
        typeof isNodePanelOpen === 'function'
        && isNodePanelOpen()
        && typeof updateNodePanelContent === 'function'
        && selectedNodeId === nodeId
    ) {
        updateNodePanelContent();
    }

    return true;
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
    const isNmMode = multiRunState?.mode === 'nm';

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
        finalNode && segment.to.x === finalNode.x && segment.to.y === finalNode.y,
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
            if (
                phaseChanged
                && originId
                && sourceId === originId
                && sourceState.pendingOutbound > 0
            ) {
                sourceState.pendingOutbound = Math.max(0, sourceState.pendingOutbound - 1);
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
            } else {
                targetState.receiveBuffer = 'ready';
            }
            break;
        case 'completed':
            sourceState.sendBuffer = 'idle';
            sourceState.handshake = 'idle';
            if (isFinalHop) {
                targetState.receiveBuffer = 'delivered';
                targetState.handshake = 'idle';
                registerDeliveredPacket(targetState, targetId, packetKey);
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
        registerDeliveredPacket(targetState, targetId, packetKey);
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

function resolveNodeLabel(node) {
    if (typeof node === 'string') {
        return node;
    }
    return safeNodeLabel(node || {});
}

function createLogEntry(context, stage, description, metadata = []) {
    return {
        context,
        stage,
        description,
        metadata: Array.isArray(metadata) ? metadata.filter(Boolean) : [],
    };
}

function buildDetailedLogForPayload(payload, options = {}) {
    const entries = [];
    if (!payload) {
        return entries;
    }

    const {
        label = 'Packet',
        bufferCapacity = null,
        activeCount = null,
        waitingCount = null,
        queuedInitially = false,
        sourceLabel: providedSource = null,
        destinationLabel: providedDestination = null,
        neighborLabel = null,
        packetCount = 1,
    } = options;

    const pathArray = Array.isArray(payload.path) ? payload.path : [];
    const hopCount = Number.isFinite(payload.hopCount)
        ? payload.hopCount
        : Math.max(pathArray.length - 1, 0);
    const sourceLabel = typeof providedSource === 'string' && providedSource.length
        ? providedSource
        : resolveNodeLabel(payload.source || payload.sourceNode || pathArray[0] || null);
    const destinationLabel = typeof providedDestination === 'string' && providedDestination.length
        ? providedDestination
        : resolveNodeLabel(payload.destination || payload.destinationNode || pathArray[pathArray.length - 1] || null);

    const initialDetails = [
        `Destination: ${destinationLabel}`,
        `Hop count: ${hopCount}`,
        packetCount > 1 ? `Packets scheduled: ${packetCount}` : null,
    ].filter(Boolean);

    entries.push(createLogEntry(label, 'Init', `Source ${sourceLabel} prepares transmission`, initialDetails));

    if (bufferCapacity !== null || activeCount !== null || waitingCount !== null) {
        const bufferDetails = [
            Number.isFinite(bufferCapacity) ? `Capacity: ${bufferCapacity}` : null,
            Number.isFinite(activeCount) ? `Active: ${activeCount}` : null,
            Number.isFinite(waitingCount) ? `Queued: ${waitingCount}` : null,
        ].filter(Boolean);
        const bufferLabel = neighborLabel
            ? `Send buffer toward ${neighborLabel}`
            : 'Send buffer status';
        entries.push(createLogEntry(label, 'Buffer', bufferLabel, bufferDetails));
        if (queuedInitially) {
            entries.push(createLogEntry(label, 'Queue', 'Packet queued until slot frees', []));
        }
    }

    const segments = Array.isArray(payload.segments) ? payload.segments : [];
    segments.forEach((segment, segmentIndex) => {
        const hop = segmentIndex + 1;
        const fromNode = segment?.from || pathArray[segmentIndex] || null;
        const toNode = segment?.to || pathArray[segmentIndex + 1] || null;
        const fromLabel = resolveNodeLabel(fromNode);
        const toLabel = resolveNodeLabel(toNode);
        const hopType = segment?.type === 'ring' ? 'Ring' : 'Tree';

        entries.push(createLogEntry(label, `Hop ${hop} · REQ`, `${fromLabel} asserts REQ`, [
            `Target: ${toLabel}`,
            `Link: ${hopType}`,
        ]));
        entries.push(createLogEntry(label, `Hop ${hop} · ACK`, `${toLabel} raises ACK`, [
            `Source: ${fromLabel}`,
        ]));
        entries.push(createLogEntry(label, `Hop ${hop} · DATA`, `Transfer ${fromLabel} → ${toLabel}`, [
            'Handshake lines released',
        ]));
    });

    entries.push(createLogEntry(label, 'Complete', `Packet delivered to ${destinationLabel}`, []));
    return entries;
}

function buildDetailedLogForParallelPayloads(payloads, options = {}) {
    const entries = [];
    if (!Array.isArray(payloads)) {
        return entries;
    }

    const mode = options.mode === 'nm' ? 'nm' : 'parallel';
    const queueConfig = options.queueConfig instanceof Map
        ? options.queueConfig
        : options.queueConfig && typeof options.queueConfig === 'object'
            ? new Map(Object.entries(options.queueConfig))
            : null;
    const routeSummary = options.routeSummary instanceof Map
        ? options.routeSummary
        : options.routeSummary && typeof options.routeSummary === 'object'
            ? new Map(Object.entries(options.routeSummary))
            : null;

    payloads.forEach((payload, index) => {
        if (!payload) {
            return;
        }
        const label = mode === 'nm' ? `Route ${index + 1}` : `Packet ${index + 1}`;
        const routeIndex = Number.isFinite(payload.routeIndex) ? payload.routeIndex : index;
        const summary = routeSummary ? routeSummary.get(routeIndex) : null;
        const queueKey = payload.queueKey || null;
        const config = queueKey && queueConfig ? queueConfig.get(queueKey) : null;
        const neighborLabel = options.neighborLabelOverride || (config?.neighborNode
            ? resolveNodeLabel(config.neighborNode)
            : payload.firstHopNode
                ? resolveNodeLabel(payload.firstHopNode)
                : null);
        const sourceLabel = resolveNodeLabel(payload.sourceNode || payload.source || null);
        const destinationLabel = resolveNodeLabel(payload.destinationNode || payload.destination || null);
        const packetCount = Number.isFinite(payload.packetBatches)
            ? payload.packetBatches
            : Number.isFinite(payload.packetCount)
                ? payload.packetCount
                : 1;

        entries.push(
            ...buildDetailedLogForPayload(payload, {
                label,
                bufferCapacity: config?.capacity ?? payload.bufferCapacity ?? null,
                activeCount: summary?.active ?? null,
                waitingCount: summary?.waiting ?? null,
                queuedInitially: Boolean(payload.initialQueueState === 'waiting'),
                sourceLabel,
                destinationLabel,
                neighborLabel,
                packetCount,
            }),
        );
    });

    return entries;
}

function escapeHtml(value) {
    if (value === null || value === undefined) {
        return '';
    }
    return String(value).replace(/[&<>"']/g, (char) => {
        const lookup = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;',
        };
        return lookup[char] || char;
    });
}

function renderLogModal() {
    if (!logModalBody) {
        return;
    }
    logModalBody.innerHTML = '';
    if (!detailedLogEntries.length) {
        const empty = document.createElement('p');
        empty.className = 'log-modal__empty';
        empty.textContent = 'No log entries available.';
        logModalBody.appendChild(empty);
        return;
    }

    const table = document.createElement('table');
    table.className = 'log-table';
    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');
    ['Context', 'Stage', 'Description', 'Details'].forEach((label) => {
        const th = document.createElement('th');
        th.textContent = label;
        headerRow.appendChild(th);
    });
    thead.appendChild(headerRow);
    table.appendChild(thead);

    const tbody = document.createElement('tbody');
    detailedLogEntries.forEach((entry) => {
        if (!entry) {
            return;
        }
        const row = document.createElement('tr');

        const contextCell = document.createElement('td');
        contextCell.className = 'log-table__context';
        contextCell.textContent = entry.context || '';
        row.appendChild(contextCell);

        const stageCell = document.createElement('td');
        stageCell.textContent = entry.stage || '';
        row.appendChild(stageCell);

        const descriptionCell = document.createElement('td');
        descriptionCell.textContent = entry.description || '';
        row.appendChild(descriptionCell);

        const detailsCell = document.createElement('td');
        if (Array.isArray(entry.metadata) && entry.metadata.length) {
            entry.metadata.forEach((detail) => {
                const metaLine = document.createElement('span');
                metaLine.className = 'log-table__metadata';
                metaLine.textContent = detail;
                detailsCell.appendChild(metaLine);
            });
        } else {
            detailsCell.textContent = '—';
        }
        row.appendChild(detailsCell);

        tbody.appendChild(row);
    });
    table.appendChild(tbody);
    logModalBody.appendChild(table);
    logModalBody.scrollTop = 0;
}

function setDetailedLog(entries, { title } = {}) {
    detailedLogEntries = Array.isArray(entries) ? entries.filter(Boolean) : [];
    detailedLogTitle = title || 'Detailed log';
    const hasEntries = detailedLogEntries.length > 0;

    if (openLogModalBtn) {
        openLogModalBtn.disabled = !hasEntries;
        openLogModalBtn.setAttribute('aria-disabled', hasEntries ? 'false' : 'true');
        openLogModalBtn.title = hasEntries
            ? 'View detailed log'
            : 'Run a simulation to generate log entries';
    }

    if (exportLogPdfBtn) {
        exportLogPdfBtn.disabled = !hasEntries;
        exportLogPdfBtn.setAttribute('aria-disabled', hasEntries ? 'false' : 'true');
        exportLogPdfBtn.title = hasEntries
            ? 'Export detailed log as PDF'
            : 'Run a simulation to export the log as PDF';
    }

    if (isLogModalOpen()) {
        renderLogModal();
        if (logModalTitle) {
            logModalTitle.textContent = detailedLogTitle;
        }
    }
}

function isLogModalOpen() {
    return Boolean(logModal && logModal.classList.contains('is-visible'));
}

function openLogModal() {
    if (!logModal || !detailedLogEntries.length) {
        return;
    }
    logModal.classList.add('is-visible');
    logModal.setAttribute('aria-hidden', 'false');
    document.body.classList.add('modal-open');
    if (logModalTitle) {
        logModalTitle.textContent = detailedLogTitle;
    }
    renderLogModal();
    if (logModalClose) {
        logModalClose.focus();
    }
}

function closeLogModal() {
    if (!isLogModalOpen()) {
        return;
    }
    logModal.classList.remove('is-visible');
    logModal.setAttribute('aria-hidden', 'true');
    document.body.classList.remove('modal-open');
    if (openLogModalBtn) {
        openLogModalBtn.focus();
    }
}

function exportLogAsPdf() {
    if (!detailedLogEntries.length) {
        window.alert('Run a simulation to generate log entries before exporting.');
        return;
    }

    const docTitle = detailedLogTitle || 'Detailed log';

    const generatedAt = new Date().toLocaleString();
    const styles = `
        :root {
            color-scheme: only light;
        }
        body {
            font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            margin: 32px;
            color: #0f172a;
            background: #f8fafc;
        }
        h1 {
            margin: 0 0 8px 0;
            font-size: 1.85rem;
            letter-spacing: -0.01em;
        }
        .subtitle {
            margin: 0 0 24px 0;
            color: #475569;
            font-size: 0.95rem;
        }
        table {
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            border-radius: 14px;
            overflow: hidden;
            box-shadow: inset 0 0 0 1px rgba(148, 163, 184, 0.3);
        }
        thead {
            background: linear-gradient(135deg, rgba(59, 130, 246, 0.18), rgba(14, 165, 233, 0.18));
        }
        th, td {
            padding: 16px 18px;
            text-align: left;
            vertical-align: top;
            font-size: 0.95rem;
        }
        th {
            font-weight: 600;
            color: #1e293b;
            border-bottom: 1px solid rgba(148, 163, 184, 0.35);
        }
        tbody tr:nth-child(odd) {
            background: rgba(226, 232, 240, 0.28);
        }
        tbody tr:nth-child(even) {
            background: #ffffff;
        }
        tbody tr:hover {
            background: rgba(59, 130, 246, 0.12);
        }
        .context {
            font-weight: 600;
            color: #1d4ed8;
            min-width: 110px;
        }
        .metadata {
            display: inline-block;
            padding: 4px 10px;
            margin: 0 6px 6px 0;
            font-size: 0.85rem;
            color: #334155;
            background: rgba(148, 163, 184, 0.26);
            border-radius: 10px;
        }
        footer {
            margin-top: 32px;
            text-align: right;
            color: #475569;
            font-size: 0.9rem;
        }
    `;

    const rowsHtml = detailedLogEntries
        .map((entry) => {
            if (!entry) {
                return '';
            }
            const metadataHtml = Array.isArray(entry.metadata) && entry.metadata.length
                ? entry.metadata.map((detail) => `<span class="metadata">${escapeHtml(detail)}</span>`).join('')
                : '—';

            return `
                <tr>
                    <td class="context">${escapeHtml(entry.context || '')}</td>
                    <td>${escapeHtml(entry.stage || '')}</td>
                    <td>${escapeHtml(entry.description || '')}</td>
                    <td>${metadataHtml}</td>
                </tr>
            `;
        })
        .join('');

    const html = `
        <!DOCTYPE html>
        <html lang="en">
            <head>
                <meta charset="UTF-8">
                <title>${escapeHtml(docTitle)}</title>
                <style>${styles}</style>
            </head>
            <body>
                <h1>${escapeHtml(docTitle)}</h1>
                <p class="subtitle">Generated on ${escapeHtml(generatedAt)}</p>
                <table>
                    <thead>
                        <tr>
                            <th>Context</th>
                            <th>Stage</th>
                            <th>Description</th>
                            <th>Details</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${rowsHtml}
                    </tbody>
                </table>
                <footer>© RicoBit Simulator. All rights reserved.</footer>
            </body>
        </html>
    `;

    const printFrame = document.createElement('iframe');
    printFrame.title = 'RicoBit detailed log export';
    printFrame.style.position = 'fixed';
    printFrame.style.right = '0';
    printFrame.style.bottom = '0';
    printFrame.style.width = '0';
    printFrame.style.height = '0';
    printFrame.style.border = '0';
    printFrame.setAttribute('aria-hidden', 'true');

    document.body.appendChild(printFrame);

    const finalizePrint = () => {
        try {
            const frameWindow = printFrame.contentWindow;
            if (!frameWindow) {
                throw new Error('No frame window available');
            }
            frameWindow.focus();
            frameWindow.print();
        } catch (error) {
            console.error('Failed to trigger PDF export', error);
            window.alert('Unable to open the print dialog. Use your browser\'s print option as a fallback.');
        } finally {
            setTimeout(() => {
                if (printFrame.parentNode) {
                    printFrame.parentNode.removeChild(printFrame);
                }
            }, 750);
        }
    };

    const frameDoc = printFrame.contentDocument || (printFrame.contentWindow && printFrame.contentWindow.document);
    if (!frameDoc) {
        window.alert('Export frame could not be prepared.');
        if (printFrame.parentNode) {
            printFrame.parentNode.removeChild(printFrame);
        }
        return;
    }

    frameDoc.open();
    frameDoc.write(html);
    frameDoc.close();

    if (printFrame.contentWindow && printFrame.contentWindow.document.readyState === 'complete') {
        setTimeout(finalizePrint, 100);
    } else {
        printFrame.addEventListener('load', () => setTimeout(finalizePrint, 75), { once: true });
    }
}

function parseSelectValue(value) {
    if (typeof value !== 'string') {
        return { x: 0, y: 0 };
    }
    const [xStr, yStr] = value.split('-');
    return {
        x: parseInt(xStr, 10),
        y: parseInt(yStr, 10),
    };
}

function collectSelectedDestinations() {
    return multiDestinations
        .map((nodeId) => parseSelectValue(nodeId))
        .filter((node) => Number.isFinite(node.x) && Number.isFinite(node.y));
}

function handleSourceSelectChange({ announce = false, message, openNodeDetails = true } = {}) {
    syncSelectionState();
    const nodeId = currentSourceId;
    if (!nodeId) return;
    const meta = nodeMeta.get(nodeId) || parseSelectValue(nodeId);
    focusNode(nodeId, {
        auto: nodePanelAutoTracking,
        openPanelOnFocus: openNodeDetails,
    });
    if (announce && hudStatus && meta) {
        hudStatus.textContent = message || `Source set to ${nodeLabel(meta)}.`;
    }
    renderTopology();
}

function handleDestinationSelectChange({ announce = false, message, openNodeDetails = true } = {}) {
    syncSelectionState();
    const nodeId = currentDestinationId;
    if (!nodeId) return;
    const meta = nodeMeta.get(nodeId) || parseSelectValue(nodeId);
    focusNode(nodeId, {
        auto: nodePanelAutoTracking,
        openPanelOnFocus: openNodeDetails,
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
            source: { x: source.x, y: source.y },
            destination: { x: destination.x, y: destination.y },
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
        const sourceId = makeNodeId(source);
        const sourceRuntime = ensureNodeRuntimeState(sourceId);
        sourceRuntime.pendingOutbound = 1;
        sourceRuntime.sendBuffer = 'primed';
        sourceRuntime.handshake = 'primed';
        sourceRuntime.lastUpdated = performance.now();
        if (isNodePanelOpen() && selectedNodeId === sourceId) {
            updateNodePanelContent();
        }
        setDetailedLog(
            buildDetailedLogForPayload(payload, {
                label: 'Packet 1',
                sourceLabel: nodeLabel(source),
                destinationLabel: nodeLabel(destination),
            }),
            {
                title: `1 → 1 log · ${nodeLabel(source)} → ${nodeLabel(destination)}`,
            },
        );
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
        setDetailedLog([]);
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
    const sourceKey = `${source.x}-${source.y}`;
    const dedupe = new Map();
    destinations.forEach((dest) => {
        if (!dest || typeof dest.x !== 'number' || typeof dest.y !== 'number') {
            return;
        }
        const key = `${dest.x}-${dest.y}`;
        if (key === sourceKey) {
            return;
        }
        if (!dedupe.has(key)) {
            dedupe.set(key, dest);
        }
    });

    const uniqueDestinations = Array.from(dedupe.values());
    const destinationTotal = uniqueDestinations.length;
    if (!destinationTotal) {
        hudStatus.textContent = 'Add one or more destination nodes for 1 → n parallel simulation.';
        setStatusIdle('Awaiting destination selection');
        updateAnimateButton({ disabled: true, busy: false, label: 'Animate all' });
        return;
    }

    hudStatus.textContent = `Computing ${destinationTotal} parallel route(s)…`;

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
        const sourceNodeId = makeNodeId(source);
        const enrichedPayloads = rawPayloads.map((payload, index) => {
            const pathArray = Array.isArray(payload.path) ? payload.path : [];
            const computedDestination = pathArray.length
                ? pathArray[pathArray.length - 1]
                : payload.destination || uniqueDestinations[index] || null;
            const destinationAddress = computedDestination
                ? { x: computedDestination.x, y: computedDestination.y }
                : { x: uniqueDestinations[index].x, y: uniqueDestinations[index].y };
            return {
                ...payload,
                packetIndex: index + 1,
                packetCount,
                packet: {
                    source: { x: source.x, y: source.y },
                    destination: destinationAddress,
                    data: `Packet ${index + 1}`,
                },
            };
        });

        const queueConfig = new Map();
        const routeQueueSummary = new Map();
        const queueStats = new Map();
        let totalActive = 0;
        let totalWaiting = 0;

        enrichedPayloads.forEach((payload, index) => {
            const pathArray = Array.isArray(payload.path) ? payload.path : [];
            const neighborNode = pathArray.length > 1
                ? pathArray[1]
                : (payload.destination || pathArray[pathArray.length - 1] || null);
            const neighborId = neighborNode ? makeNodeId(neighborNode) : `${payload.packetIndex}`;
            const queueKey = `${sourceNodeId}->${neighborId}`;
            const capacity = resolveSendBufferCapacity(sourceNodeId, neighborNode);

            if (!queueConfig.has(queueKey)) {
                queueConfig.set(queueKey, {
                    capacity,
                    sourceId: sourceNodeId,
                    sourceNode: source,
                    neighborNode,
                });
            } else {
                const config = queueConfig.get(queueKey);
                config.capacity = capacity;
            }

            const stats = queueStats.get(queueKey) || { capacity, active: 0, waiting: 0 };
            stats.capacity = capacity;
            const slotAvailable = stats.active < Math.max(1, stats.capacity);
            if (slotAvailable) {
                stats.active += 1;
                totalActive += 1;
            } else {
                stats.waiting += 1;
                totalWaiting += 1;
            }
            queueStats.set(queueKey, stats);

            payload.routeIndex = index;
            payload.queueKey = queueKey;
            payload.bufferCapacity = capacity;
            payload.firstHopNode = neighborNode;
            payload.firstHopId = neighborId;
            payload.sourceNode = source;
            payload.sourceNodeId = sourceNodeId;
            payload.initialQueueState = slotAvailable ? 'active' : 'waiting';

            routeQueueSummary.set(index, {
                total: 1,
                active: slotAvailable ? 1 : 0,
                waiting: slotAvailable ? 0 : 1,
                delivered: 0,
            });
        });

        const previewRoutes = enrichedPayloads.map((payload, index) => {
            const color = PARALLEL_ROUTE_COLORS[index % PARALLEL_ROUTE_COLORS.length];
            return new RoutePreview(payload, {
                renderStyle: 'pending',
                treeColor: color,
                ringColor: color,
                strokeOpacity: 0.35,
                lineWidth: 3,
            });
        });

        multiRunState = {
            mode: 'parallel',
            payloads: enrichedPayloads,
            currentIndex: null,
            selectedIndex: 0,
            completed: new Set(),
            completedRoutes: [],
            completedStatuses: [],
            previewRoutes,
            source,
            queueConfig,
            routeQueueSummary,
            totalPackets: packetCount,
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
        setDetailedLog(
            buildDetailedLogForParallelPayloads(enrichedPayloads, {
                mode: 'parallel',
                queueConfig,
                routeSummary: routeQueueSummary,
            }),
            {
                title: `1 → n log · ${nodeLabel(source)} → ${destinationTotal} destination${destinationTotal === 1 ? '' : 's'}`,
            },
        );

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

        const snapshotTimestamp = performance.now();
        queueConfig.forEach((config, key) => {
            const stats = queueStats.get(key) || { active: 0, waiting: 0 };
            const ifaceRuntime = ensureInterfaceRuntimeState(config.sourceId, config.neighborNode);
            if (ifaceRuntime && ifaceRuntime.sendBuffer) {
                ifaceRuntime.sendBuffer.capacity = config.capacity;
                ifaceRuntime.sendBuffer.used = stats.active;
                ifaceRuntime.sendBuffer.queue = stats.waiting;
                ifaceRuntime.sendBuffer.state = stats.active > 0
                    ? 'primed'
                    : (stats.waiting > 0 ? 'primed' : 'idle');
            }
        });
        const sourceRuntime = ensureNodeRuntimeState(sourceNodeId);
        sourceRuntime.pendingOutbound = enrichedPayloads.length;
        if (totalActive > 0) {
            sourceRuntime.sendBuffer = 'primed';
            sourceRuntime.handshake = 'primed';
        } else if (totalWaiting > 0) {
            sourceRuntime.sendBuffer = 'primed';
            sourceRuntime.handshake = 'primed';
        } else {
            sourceRuntime.sendBuffer = 'idle';
            sourceRuntime.handshake = 'idle';
        }
        sourceRuntime.lastUpdated = snapshotTimestamp;
        if (isNodePanelOpen() && selectedNodeId === sourceNodeId) {
            updateNodePanelContent();
        }

    } catch (error) {
        console.error(error);
        const message = error.message || 'Routing failed';
        hudStatus.textContent = message;
        setStatusIdle(message);
        updateAnimateButton({ disabled: true, busy: false, label: 'Animate all' });
        setDetailedLog([]);
        resetMultiRunState();
        updateAnimationControlState();
    }
}

async function simulateNmRoutes() {
    if (!topologyData) return;
    setPickMode(null);
    stopAnimation();
    resetAllNodeRuntimeState();
    resetMultiRunState();
    currentSourceId = null;
    currentDestinationId = null;
    if (isMobileSidebar() && isSidebarVisible()) {
        closeSidebar();
    }

    const plan = collectNmRoutes();
    if (!plan.length) {
        hudStatus.textContent = 'Add at least one route row to run n → m simulation.';
        setStatusIdle('Awaiting route plan');
        updateAnimateButton({ disabled: true, busy: false, label: 'Animate all' });
        setDetailedLog([]);
        return;
    }

    const invalidEntry = plan.find((entry) => entry.sourceId === entry.destinationId);
    if (invalidEntry) {
        hudStatus.textContent = 'Source and destination must differ for each route row.';
        setStatusIdle('Invalid route plan');
        updateAnimateButton({ disabled: true, busy: false, label: 'Animate all' });
        setDetailedLog([]);
        return;
    }

    hudStatus.textContent = `Resolving ${plan.length} route${plan.length === 1 ? '' : 's'}…`;

    const pairMap = new Map();
    const fetchTasks = [];
    plan.forEach((entry) => {
        const key = `${entry.sourceId}->${entry.destinationId}`;
        if (!pairMap.has(key)) {
            pairMap.set(key, null);
            fetchTasks.push(
                fetchRoutePayload(entry.source, entry.destination)
                    .then((payload) => {
                        pairMap.set(key, payload);
                    })
            );
        }
    });

    try {
        await Promise.all(fetchTasks);
    } catch (error) {
        console.error(error);
        const message = error.message || 'Routing failed';
        hudStatus.textContent = message;
        setStatusIdle(message);
        updateAnimateButton({ disabled: true, busy: false, label: 'Animate all' });
        setDetailedLog([]);
        return;
    }

    const routePayloads = [];
    const flowEntries = [];
    let totalPackets = 0;

    plan.forEach((entry, index) => {
        const key = `${entry.sourceId}->${entry.destinationId}`;
        const payload = pairMap.get(key);
        if (!payload) {
            return;
        }
        const pathArray = Array.isArray(payload.path) ? payload.path : [];
        const firstHop = pathArray.length > 1 ? pathArray[1] : null;
        const firstHopNode = firstHop || entry.destination;
        const firstHopId = makeNodeId(firstHopNode);
        const bufferCapacity = resolveSendBufferCapacity(entry.sourceId, firstHop);
        const color = PARALLEL_ROUTE_COLORS[index % PARALLEL_ROUTE_COLORS.length];
        const batches = Math.max(1, entry.packets);
        totalPackets += batches;
        const packetTemplate = (payload.packet && typeof payload.packet === 'object') ? payload.packet : {};
        const packetPreview = {
            ...packetTemplate,
            source: entry.source,
            destination: entry.destination,
            data: packetTemplate.data || `Route ${index + 1}`,
        };

        routePayloads.push({
            ...payload,
            routeId: entry.id,
            routeIndex: index,
            packetBatches: batches,
            bufferCapacity,
            routeLabel: `${safeNodeLabel(entry.source)} → ${safeNodeLabel(entry.destination)}`,
            color,
            packet: packetPreview,
            packetIndex: index + 1,
            packetCount: plan.length,
            sourceNode: entry.source,
            destinationNode: entry.destination,
            sourceNodeId: entry.sourceId,
            destinationNodeId: entry.destinationId,
            firstHopNode,
            firstHopId,
            queueKey: `${entry.sourceId}->${firstHopId}`,
        });

        flowEntries.push({
            phase: `Route ${index + 1}`,
            title: `${safeNodeLabel(entry.source)} → ${safeNodeLabel(entry.destination)}`,
            details: [
                `Hop count: ${payload.hopCount ?? 0}`,
                `Packets: ${batches}`,
                `Segments: ${Array.isArray(payload.segments) ? payload.segments.length : 0}`,
            ],
        });
    });

    if (!routePayloads.length) {
        hudStatus.textContent = 'No valid routes generated from plan.';
        setStatusIdle('Route plan invalid');
        updateAnimateButton({ disabled: true, busy: false, label: 'Animate all' });
        setDetailedLog([]);
        return;
    }

    const packetPayloads = [];
    const queueConfig = new Map();
    const routeQueueSummary = new Map();
    const sourceTotals = new Map();
    const interfaceTotals = new Map();
    let globalPacketIndex = 1;

    routePayloads.forEach((payload) => {
        const queueKey = payload.queueKey;
        const configEntry = queueConfig.get(queueKey) || {
            capacity: payload.bufferCapacity,
            sourceId: payload.sourceNodeId,
            sourceNode: payload.sourceNode,
            neighborNode: payload.firstHopNode,
            routeIndex: payload.routeIndex,
            color: payload.color,
        };
        configEntry.capacity = payload.bufferCapacity;
        queueConfig.set(queueKey, configEntry);

        const initialActive = Math.min(payload.bufferCapacity, payload.packetBatches);
        const initialWaiting = Math.max(payload.packetBatches - initialActive, 0);
        routeQueueSummary.set(payload.routeIndex, {
            total: payload.packetBatches,
            active: initialActive,
            waiting: initialWaiting,
            delivered: 0,
        });

        const prevSourceTotal = sourceTotals.get(payload.sourceNodeId) || 0;
        sourceTotals.set(payload.sourceNodeId, prevSourceTotal + payload.packetBatches);

        const ifaceTotals = interfaceTotals.get(queueKey) || {
            active: 0,
            waiting: 0,
            capacity: payload.bufferCapacity,
            sourceId: payload.sourceNodeId,
            sourceNode: payload.sourceNode,
            neighborNode: payload.firstHopNode,
        };
        ifaceTotals.active += initialActive;
        ifaceTotals.waiting += initialWaiting;
        ifaceTotals.capacity = payload.bufferCapacity;
        interfaceTotals.set(queueKey, ifaceTotals);

        for (let packetIdx = 0; packetIdx < payload.packetBatches; packetIdx += 1) {
            const packetClone = {
                ...payload,
                packetIndex: globalPacketIndex,
                packetCount: totalPackets,
                routePacketIndex: packetIdx + 1,
                routePacketCount: payload.packetBatches,
                packet: {
                    ...payload.packet,
                    data: `${payload.packet.data || payload.routeLabel} · Packet ${packetIdx + 1}`,
                },
                queueKey,
            };
            packetPayloads.push(packetClone);
            globalPacketIndex += 1;
        }
    });

    multiRunState = {
        mode: 'nm',
        payloads: routePayloads,
        selectedIndex: 0,
        completed: new Set(),
        completedRoutes: [],
        completedStatuses: [],
        deliveredCounts: new Map(),
        deliveredPacketKeys: new Set(),
        previewRoutes: routePayloads.map((payload) => new RoutePreview(payload, {
            renderStyle: 'pending',
            treeColor: payload.color,
            ringColor: payload.color,
            strokeOpacity: 0.35,
            lineWidth: 3,
        })),
        packetPayloads,
        queueConfig,
        routeQueueSummary,
        totalPackets,
    };

    setDetailedLog(
        buildDetailedLogForParallelPayloads(routePayloads, {
            mode: 'nm',
            queueConfig,
            routeSummary: routeQueueSummary,
        }),
        {
            title: `n → m log · ${routePayloads.length} route${routePayloads.length === 1 ? '' : 's'} (${totalPackets} packet${totalPackets === 1 ? '' : 's'})`,
        },
    );

    summary.textContent = `Routes: ${routePayloads.length} · Packets: ${totalPackets}`;
    renderMultiRouteList();
    renderFlow(flowEntries);

    const firstPayload = routePayloads[0];
    if (firstPayload) {
        prepareRoute(firstPayload, {
            contextLabel: `Route 1 of ${routePayloads.length}`,
            previewColors: {
                treeColor: firstPayload.color,
                ringColor: firstPayload.color,
                strokeOpacity: 0.9,
                lineWidth: 4,
            },
            buttonLabel: 'Animate all',
        });
        lastRoutePayload = firstPayload;
    }

    hudStatus.textContent = `Parallel plan ready: ${routePayloads.length} route${routePayloads.length === 1 ? '' : 's'}, ${totalPackets} packet${totalPackets === 1 ? '' : 's'}.`;
    updateAnimateButton({ disabled: false, busy: false, label: 'Animate all' });

    const nmSnapshotTimestamp = performance.now();
    interfaceTotals.forEach((info) => {
        const ifaceRuntime = ensureInterfaceRuntimeState(info.sourceId, info.neighborNode);
        if (ifaceRuntime && ifaceRuntime.sendBuffer) {
            ifaceRuntime.sendBuffer.capacity = info.capacity;
            ifaceRuntime.sendBuffer.used = Math.min(info.capacity, info.active);
            ifaceRuntime.sendBuffer.queue = Math.max(info.waiting, 0);
            ifaceRuntime.sendBuffer.state = info.active > 0 ? 'primed' : (info.waiting > 0 ? 'primed' : 'idle');
        }
        const sourceRuntime = ensureNodeRuntimeState(info.sourceId);
        if (info.active > 0) {
            sourceRuntime.sendBuffer = 'primed';
            sourceRuntime.handshake = 'primed';
        } else if (info.waiting > 0) {
            sourceRuntime.sendBuffer = 'primed';
            sourceRuntime.handshake = 'primed';
        }
    });
    sourceTotals.forEach((total, sourceId) => {
        const sourceRuntime = ensureNodeRuntimeState(sourceId);
        sourceRuntime.pendingOutbound = total;
        if (total > 0) {
            sourceRuntime.sendBuffer = 'primed';
            sourceRuntime.handshake = 'primed';
        } else {
            sourceRuntime.sendBuffer = 'idle';
            sourceRuntime.handshake = 'idle';
        }
        sourceRuntime.lastUpdated = nmSnapshotTimestamp;
    });
    if (isNodePanelOpen()) {
        updateNodePanelContent();
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
    if (
        multiRunState
        && (multiRunState.mode === 'parallel' || multiRunState.mode === 'nm')
    ) {
        const payloadList = multiRunState.mode === 'nm'
            ? multiRunState.packetPayloads || []
            : multiRunState.payloads || [];
        if (!Array.isArray(payloadList) || !payloadList.length) {
            hudStatus.textContent = 'Simulate the route first.';
            return;
        }
        const completionMessage = multiRunState.mode === 'nm'
            ? 'n → m plan complete'
            : 'Parallel transmissions complete';
        startAnimation(payloadList[0], {
            parallelPayloads: payloadList,
            parallelOptions: {
                mode: multiRunState.mode,
                queueConfig: multiRunState.queueConfig || null,
                routeSummary: multiRunState.routeQueueSummary || null,
            },
            label: 'Animate all',
            onComplete: () => {
                hudStatus.textContent = completionMessage;
            },
        });
        return;
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
        parallelOptions: null,
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
        animationState = new ParallelRouteController(opts.parallelPayloads, speedMultiplier, opts.parallelOptions || {});
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

        if (animationState.mode === 'parallel' || animationState.mode === 'nm') {
            const activeEntries = typeof animationState.getActiveEntries === 'function'
                ? animationState.getActiveEntries()
                : Array.isArray(animationState.animations)
                    ? animationState.animations.map((animation, index) => ({ animation, routeIndex: index }))
                    : [];
            const animations = activeEntries.map((entry) => entry.animation).filter(Boolean);
            const statuses = animations.map((animation) => animation.currentStatus());
            animationState.latestStatuses = statuses;
            const aggregate = aggregateParallelStatuses(statuses, {
                mode: multiRunState?.mode || null,
                routeSummary: multiRunState?.routeQueueSummary || null,
            });
            updateStatusBar(aggregate);
            statuses.forEach((status, index) => updateNodeRuntimeFromStatus(status, animations[index]));
            updateParallelRouteProgress(statuses, activeEntries);
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
            const multiMode = multiRunState?.mode || null;
            const completionMessage = multiMode === 'nm'
                ? 'n → m plan complete'
                : animationState.mode === 'parallel'
                    ? 'Parallel transmissions complete'
                    : 'Transmission complete';
            const transferLabel = multiMode === 'nm'
                ? 'Routes delivered'
                : animationState.mode === 'parallel'
                    ? 'Packets delivered'
                    : 'Packet delivered';

            hudStatus.textContent = completionMessage;
            highlightFlowCard(flowCardElements.length - 1);
            const completedStatus = {
                phaseKey: 'completed',
                phaseLabel: 'Completed',
                signalText: 'Idle',
                signalStates: { req: 'sleep', ack: 'sleep', data: 'sleep' },
                transferText: transferLabel,
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
                        transferText: transferLabel,
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
                if (multiRunState.mode === 'parallel' || multiRunState.mode === 'nm') {
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
            // Reset all node handshake states to idle after transfer completes
            nodeRuntimeState.forEach((runtime) => {
                if (runtime) {
                    runtime.handshake = 'idle';
                    runtime.sendBuffer = 'idle';
                    runtime.receiveBuffer = 'idle';
                }
            });
            // Update node panel to reflect idle state
            if (selectedNodeId) {
                updateNodePanelContent();
            }
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
    closeLogModal();
    setDetailedLog([]);
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
    if (isPanning && event.pointerId === panPointerId) {
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
        return;
    }
    
    // Handle hover for interface visualization
    const nodeId = findNodeAtPosition(event.offsetX, event.offsetY);
    
    if (nodeId) {
        if (hoverState.nodeId !== nodeId) {
            // New node, reset timer
            hoverState.nodeId = nodeId;
            hoverState.startTime = Date.now();
            hoverState.showInterfaces = false;
        } else if (!hoverState.showInterfaces) {
            // Same node, check if 2 seconds elapsed
            const elapsed = Date.now() - hoverState.startTime;
            if (elapsed >= 2000) {
                hoverState.showInterfaces = true;
                renderTopology();
            }
        }
    } else {
        // No node hovered, reset
        if (hoverState.nodeId !== null || hoverState.showInterfaces) {
            hoverState.nodeId = null;
            hoverState.startTime = null;
            hoverState.showInterfaces = false;
            renderTopology();
        }
    }
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
        // Interface mode takes priority
        if (interfaceMode) {
            drawNodeInterface(nodeId);
            return;
        }
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
        updateSpeedMenuLabel(event.target.value);
    });
    updateSpeedMenuLabel(speedControl.value);
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
        if (isLogModalOpen()) {
            closeLogModal();
            return;
        }
        if (speedMenuOpen) {
            closeSpeedMenu({ focusButton: true });
            return;
        }
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

document.addEventListener('click', (event) => {
    if (!speedMenuOpen) {
        return;
    }
    if (!speedMenuPopover) {
        speedMenuOpen = false;
        return;
    }
    const withinPopover = speedMenuPopover.contains(event.target);
    const onButton = speedMenuBtn && speedMenuBtn.contains(event.target);
    if (!withinPopover && !onButton) {
        closeSpeedMenu();
    }
});

function runSimulationByMode() {
    const mode = simulationModeSelect ? simulationModeSelect.value : 'single';
    switch (mode) {
        case 'parallel':
            simulateParallelRoutes();
            break;
        case 'nm':
            simulateNmRoutes();
            break;
        case 'single':
        default:
            simulateSingleRoute();
            break;
    }
}

if (simulateBtn) {
    simulateBtn.addEventListener('click', runSimulationByMode);
}
if (canvasSimulateBtn) {
    canvasSimulateBtn.addEventListener('click', () => {
        runSimulationByMode();
        closeSpeedMenu();
    });
}
if (animateBtn) {
    animateBtn.addEventListener('click', playAnimation);
}
if (playPauseAnimationBtn) {
    playPauseAnimationBtn.addEventListener('click', () => {
        if (animationState) {
            togglePauseAnimation();
        } else {
            playAnimation();
        }
    });
}
if (speedMenuBtn) {
    speedMenuBtn.addEventListener('click', (event) => {
        event.preventDefault();
        toggleSpeedMenu();
    });
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
        if (suppressCandidateSelectChange) {
            suppressCandidateSelectChange = false;
            return;
        }
        const value = destinationCandidateSelect.value;
        if (!value) return;
        addMultiDestination(value);
    });
}

if (clearMultiDestinationsBtn) {
    clearMultiDestinationsBtn.addEventListener('click', () => {
        clearMultiDestinationList();
    });
}

if (addNmRouteBtn) {
    addNmRouteBtn.addEventListener('click', () => {
        const route = addNmRouteRow();
        if (route && hudStatus) {
            hudStatus.textContent = 'Route row added. Use Src/Des to choose nodes from the canvas.';
        }
    });
}

if (clearNmRoutesBtn) {
    clearNmRoutesBtn.addEventListener('click', () => {
        clearNmRoutes({ announce: true });
    });
}

if (openLogModalBtn) {
    openLogModalBtn.addEventListener('click', openLogModal);
}
if (exportLogPdfBtn) {
    exportLogPdfBtn.addEventListener('click', exportLogAsPdf);
}
if (logModalClose) {
    logModalClose.addEventListener('click', closeLogModal);
}
if (logModalOverlay) {
    logModalOverlay.addEventListener('click', closeLogModal);
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
    const requestedWidth = parseInt(widthInput.value, 10);
    const requestedHeight = parseInt(heightInput.value, 10);
    if (!Number.isInteger(requestedWidth) || requestedWidth < 2 || requestedWidth > 12) {
        hudStatus.textContent = 'Width must be between 2 and 12';
        return;
    }
    if (!Number.isInteger(requestedHeight) || requestedHeight < 2 || requestedHeight > 12) {
        hudStatus.textContent = 'Height must be between 2 and 12';
        return;
    }

    hudStatus.textContent = 'Updating topology…';
    fetch('/api/topology', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ width: requestedWidth, height: requestedHeight }),
    })
        .then((res) => res.json())
        .then((data) => {
            if (data.error) {
                hudStatus.textContent = data.error;
                return;
            }
            ingestTopologyPayload(data);
            setStatusIdle('Topology updated');
            hudStatus.textContent = `Topology updated to ${requestedWidth}×${requestedHeight} grid`;
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
    const isNm = normalizedMode === 'nm';

    setPickMode(null);

    if (sourceField) {
        setElementVisibility(sourceField, !isNm);
    }
    setElementVisibility(singleDestinationField, normalizedMode === 'single');
    setElementVisibility(multiDestinationField, isParallel);
    setElementVisibility(nmRouteField, isNm);

    if (multiRouteList) {
        multiRouteList.style.display = 'none';
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
        syncSelectionState();
    } else if (isNm) {
        currentSourceId = null;
        currentDestinationId = null;
        if (!nmRoutes.length) {
            addNmRouteRow();
        } else {
            refreshNmRouteOptions();
        }
    } else {
        syncSelectionState();
    }

    if (isParallel || isNm) {
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
        } else if (simulationModeSelect.value === 'nm') {
            hudStatus.textContent = 'n → m mode selected. Add rows to the route plan table to define transmissions.';
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

setDetailedLog([]);

// Check hover timer periodically to trigger interface display
setInterval(() => {
    if (hoverState.nodeId && !hoverState.showInterfaces && hoverState.startTime) {
        const elapsed = Date.now() - hoverState.startTime;
        if (elapsed >= 2000) {
            hoverState.showInterfaces = true;
            renderTopology();
        }
    }
}, 100); // Check every 100ms

fetchTopology()
    .then(() => {
        resizeCanvas();
    });

// Interface Mode Functions
function toggleInterfaceMode() {
    interfaceMode = !interfaceMode;
    console.log('Interface mode toggled:', interfaceMode);
    
    if (interfaceModeBtn) {
        interfaceModeBtn.setAttribute('aria-pressed', interfaceMode ? 'true' : 'false');
        interfaceModeBtn.classList.toggle('is-active', interfaceMode);
        interfaceModeBtn.style.backgroundColor = interfaceMode ? '#3b82f6' : '';
        interfaceModeBtn.style.color = interfaceMode ? '#ffffff' : '';
    }
    if (interfaceMode) {
        if (hudStatus) {
            hudStatus.textContent = 'Interface mode: Click any node to view its interface';
        }
    } else {
        if (hudStatus) {
            hudStatus.textContent = 'Interface mode disabled';
        }
        // Close interface panel when mode is disabled
        if (interfacePanel) {
            interfacePanel.classList.remove('is-visible');
        }
    }
}

function drawNodeInterface(nodeId) {
    const meta = nodeMeta.get(nodeId);
    if (!meta) {
        console.log('Node metadata not found for:', nodeId);
        return;
    }
    
    const node = topologyData.nodes.find(n => makeNodeId(n) === nodeId);
    if (!node) {
        console.log('Node not found in topology:', nodeId);
        return;
    }
    
    selectedInterfaceNode = nodeId;
    
    console.log('Opening interface panel for node:', nodeId, 'Node coords:', node.x, node.y);
    
    // Update panel title
    if (interfacePanelTitle) {
        interfacePanelTitle.textContent = `Node (${node.x}, ${node.y}) Interface`;
    }
    
    // Get runtime state
    const runtimeState = nodeRuntimeState.get(nodeId);
    console.log('Runtime state:', runtimeState);
    
    // Update signal indicators
    updateSignalIndicator('interfaceReq', runtimeState?.signals?.req || false);
    updateSignalIndicator('interfaceAck', runtimeState?.signals?.ack || false);
    updateSignalIndicator('interfaceData', runtimeState?.signals?.data || false);
    
    // Update send buffers
    for (let i = 0; i < 4; i++) {
        const bufferId = `sendBuffer${i}`;
        const buffer = runtimeState?.sendBuffers?.[i];
        updateBufferSlot(bufferId, buffer);
    }
    
    // Update receive buffers
    for (let i = 0; i < 4; i++) {
        const bufferId = `recvBuffer${i}`;
        const buffer = runtimeState?.receiveBuffers?.[i];
        updateBufferSlot(bufferId, buffer);
    }
    
    // Update active interface direction
    const directionDisplay = document.getElementById('interfaceDirection');
    if (directionDisplay && runtimeState?.activeInterface) {
        directionDisplay.textContent = runtimeState.activeInterface;
        directionDisplay.parentElement.setAttribute('data-active', 'true');
    } else if (directionDisplay) {
        directionDisplay.textContent = 'None';
        directionDisplay.parentElement.setAttribute('data-active', 'false');
    }
    
    // Show panel
    if (interfacePanel) {
        console.log('Adding is-visible class to panel');
        interfacePanel.classList.add('is-visible');
    } else {
        console.error('Interface panel element not found!');
    }
}

function updateSignalIndicator(elementId, isActive) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    element.setAttribute('data-active', isActive ? 'true' : 'false');
    const valueSpan = element.querySelector('.signal-status__value');
    if (valueSpan) {
        valueSpan.textContent = isActive ? 'HIGH' : 'LOW';
    }
}

function updateBufferSlot(bufferId, bufferData) {
    const slotElement = document.getElementById(bufferId);
    if (!slotElement) return;
    
    const contentElement = slotElement.querySelector('.buffer-slot__content');
    if (!contentElement) return;
    
    if (!bufferData || bufferData.state === 'empty') {
        slotElement.setAttribute('data-state', 'empty');
        contentElement.textContent = '—';
    } else if (bufferData.state === 'active') {
        slotElement.setAttribute('data-state', 'active');
        contentElement.textContent = bufferData.packet ? 
            `P${bufferData.packet.id} → (${bufferData.packet.dest.x},${bufferData.packet.dest.y})` : 
            'Active';
    } else if (bufferData.state === 'filled') {
        slotElement.setAttribute('data-state', 'filled');
        contentElement.textContent = bufferData.packet ? 
            `P${bufferData.packet.id} → (${bufferData.packet.dest.x},${bufferData.packet.dest.y})` : 
            'Filled';
    }
}

// Update interface panel during simulation
function updateInterfacePanel() {
    if (!interfacePanel || !interfacePanel.classList.contains('is-visible')) {
        return;
    }
    
    if (!selectedInterfaceNode) {
        return;
    }
    
    const runtimeState = nodeRuntimeState.get(selectedInterfaceNode);
    if (!runtimeState) return;
    
    // Update signals
    updateSignalIndicator('interfaceReq', runtimeState.signals?.req || false);
    updateSignalIndicator('interfaceAck', runtimeState.signals?.ack || false);
    updateSignalIndicator('interfaceData', runtimeState.signals?.data || false);
    
    // Update send buffers
    for (let i = 0; i < 4; i++) {
        const bufferId = `sendBuffer${i}`;
        const buffer = runtimeState.sendBuffers?.[i];
        updateBufferSlot(bufferId, buffer);
    }
    
    // Update receive buffers
    for (let i = 0; i < 4; i++) {
        const bufferId = `recvBuffer${i}`;
        const buffer = runtimeState.receiveBuffers?.[i];
        updateBufferSlot(bufferId, buffer);
    }
    
    // Update active interface
    const directionDisplay = document.getElementById('interfaceDirection');
    if (directionDisplay && runtimeState.activeInterface) {
        directionDisplay.textContent = runtimeState.activeInterface;
        directionDisplay.parentElement.setAttribute('data-active', 'true');
    } else if (directionDisplay) {
        directionDisplay.textContent = 'None';
        directionDisplay.parentElement.setAttribute('data-active', 'false');
    }
}

// Event listeners for interface mode
console.log('Setting up interface mode listeners...');
console.log('interfaceModeBtn:', interfaceModeBtn);
console.log('interfacePanel:', interfacePanel);
console.log('interfacePanelClose:', interfacePanelClose);

if (interfaceModeBtn) {
    interfaceModeBtn.addEventListener('click', toggleInterfaceMode);
    console.log('Interface mode button listener added');
}

if (interfacePanelClose) {
    interfacePanelClose.addEventListener('click', () => {
        console.log('Close button clicked');
        if (interfacePanel) {
            interfacePanel.classList.remove('is-visible');
        }
    });
    console.log('Interface panel close listener added');
}

