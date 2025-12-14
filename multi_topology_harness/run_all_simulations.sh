#!/bin/bash
#
# Multi-Topology Network Simulation Launcher
# Runs MESH, RiCoBiT, and TORUS simulations in parallel
#
# Usage: ./run_all_simulations.sh [packets] [seed] [grid_size] [ricobit_levels] [buffer_size]
# Example: ./run_all_simulations.sh 100 42 8 7 16
#   - packets: Number of packets to send (default: 100)
#   - seed: Random seed (default: 42)
#   - grid_size: Size of mesh/torus grid, e.g., 8 for 8x8 (default: 8)
#   - ricobit_levels: Number of levels for RiCoBiT topology (default: 7, gives 56 nodes)
#   - buffer_size: Buffer capacity per interface (default: 16, larger prevents deadlock)
#

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Configuration
PACKETS=${1:-100}
SEED=${2:-42}
GRID_SIZE=${3:-8}         # Default 8x8 = 64 nodes for MESH/TORUS
RICOBIT_LEVELS=${4:-7}    # Default 7 levels = 56 nodes for RiCoBiT
BUFFER_SIZE=${5:-16}      # Default 16 (Intel-style larger buffers prevent deadlock)
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="/Users/darshanpr/Learning/AIU/Network_Rochers/.venv/bin/activate"
RESULTS_DIR="${SCRIPT_DIR}/results"
RUNNERS_DIR="${SCRIPT_DIR}/runners"

# Output files
MESH_OUTPUT="${RESULTS_DIR}/mesh_results_${TIMESTAMP}.json"
RICOBIT_OUTPUT="${RESULTS_DIR}/ricobit_results_${TIMESTAMP}.json"
TORUS_OUTPUT="${RESULTS_DIR}/torus_results_${TIMESTAMP}.json"

MESH_LOG="${RESULTS_DIR}/mesh_log_${TIMESTAMP}.txt"
RICOBIT_LOG="${RESULTS_DIR}/ricobit_log_${TIMESTAMP}.txt"
TORUS_LOG="${RESULTS_DIR}/torus_log_${TIMESTAMP}.txt"

# Ensure results directory exists
mkdir -p "${RESULTS_DIR}"

# Header
echo ""
echo -e "${BOLD}╔══════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║     ${CYAN}MULTI-TOPOLOGY NETWORK SIMULATION LAUNCHER${NC}${BOLD}                        ║${NC}"
echo -e "${BOLD}║                                                                      ║${NC}"
echo -e "${BOLD}║     Comparing: ${GREEN}MESH${NC}${BOLD}  |  ${YELLOW}RiCoBiT${NC}${BOLD}  |  ${BLUE}TORUS${NC}${BOLD}                            ║${NC}"
echo -e "${BOLD}╚══════════════════════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${BOLD}Configuration:${NC}"
echo -e "  Packets:        ${CYAN}${PACKETS}${NC}"
echo -e "  Seed:           ${CYAN}${SEED}${NC}"
echo -e "  MESH/TORUS:     ${CYAN}${GRID_SIZE}x${GRID_SIZE} ($((GRID_SIZE * GRID_SIZE)) nodes)${NC}"
echo -e "  RiCoBiT Levels: ${CYAN}${RICOBIT_LEVELS} ($((RICOBIT_LEVELS * 8)) nodes approx)${NC}"
echo -e "  Buffer Size:    ${CYAN}${BUFFER_SIZE}${NC}"
echo -e "  Timestamp:      ${CYAN}${TIMESTAMP}${NC}"
echo ""

# Activate virtual environment
source "${VENV_PATH}"

echo -e "${BOLD}═══════════════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}                    LAUNCHING PARALLEL SIMULATIONS${NC}"
echo -e "${BOLD}═══════════════════════════════════════════════════════════════════════${NC}"
echo ""

# Record start time
START_TIME=$(date +%s)

# Launch all three simulations in parallel
echo -e "${GREEN}[MESH]${NC}    Starting simulation (${GRID_SIZE}x${GRID_SIZE}, buffer=${BUFFER_SIZE})..."
python "${RUNNERS_DIR}/run_mesh.py" \
    --width "${GRID_SIZE}" \
    --height "${GRID_SIZE}" \
    --buffer "${BUFFER_SIZE}" \
    --packets "${PACKETS}" \
    --seed "${SEED}" \
    --output "mesh_results_${TIMESTAMP}.json" \
    > "${MESH_LOG}" 2>&1 &
MESH_PID=$!

echo -e "${YELLOW}[RICOBIT]${NC} Starting simulation (${RICOBIT_LEVELS} levels, buffer=${BUFFER_SIZE})..."
python "${RUNNERS_DIR}/run_ricobit.py" \
    --levels "${RICOBIT_LEVELS}" \
    --buffer "${BUFFER_SIZE}" \
    --packets "${PACKETS}" \
    --seed "${SEED}" \
    --output "ricobit_results_${TIMESTAMP}.json" \
    > "${RICOBIT_LOG}" 2>&1 &
RICOBIT_PID=$!

echo -e "${BLUE}[TORUS]${NC}   Starting simulation (${GRID_SIZE}x${GRID_SIZE}, buffer=${BUFFER_SIZE})..."
python "${RUNNERS_DIR}/run_torus.py" \
    --width "${GRID_SIZE}" \
    --height "${GRID_SIZE}" \
    --buffer "${BUFFER_SIZE}" \
    --packets "${PACKETS}" \
    --seed "${SEED}" \
    --output "torus_results_${TIMESTAMP}.json" \
    > "${TORUS_LOG}" 2>&1 &
TORUS_PID=$!

echo ""
echo -e "PIDs: MESH=${MESH_PID}, RICOBIT=${RICOBIT_PID}, TORUS=${TORUS_PID}"
echo ""
echo -e "${BOLD}Waiting for simulations to complete...${NC}"
echo ""

# Wait for all processes and capture exit codes
wait $MESH_PID
MESH_EXIT=$?

wait $RICOBIT_PID
RICOBIT_EXIT=$?

wait $TORUS_PID
TORUS_EXIT=$?

# Record end time
END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))

echo ""
echo -e "${BOLD}═══════════════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}                       SIMULATION RESULTS${NC}"
echo -e "${BOLD}═══════════════════════════════════════════════════════════════════════${NC}"
echo ""

# Check results
if [ $MESH_EXIT -eq 0 ]; then
    echo -e "${GREEN}[MESH]${NC}    ✓ Completed successfully"
else
    echo -e "${RED}[MESH]${NC}    ✗ Failed (exit code: ${MESH_EXIT})"
fi

if [ $RICOBIT_EXIT -eq 0 ]; then
    echo -e "${YELLOW}[RICOBIT]${NC} ✓ Completed successfully"
else
    echo -e "${RED}[RICOBIT]${NC} ✗ Failed (exit code: ${RICOBIT_EXIT})"
fi

if [ $TORUS_EXIT -eq 0 ]; then
    echo -e "${BLUE}[TORUS]${NC}   ✓ Completed successfully"
else
    echo -e "${RED}[TORUS]${NC}   ✗ Failed (exit code: ${TORUS_EXIT})"
fi

echo ""
echo -e "Total execution time: ${CYAN}${ELAPSED} seconds${NC}"
echo ""

# Display comparison table using Python
echo -e "${BOLD}═══════════════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}                      METRICS COMPARISON${NC}"
echo -e "${BOLD}═══════════════════════════════════════════════════════════════════════${NC}"
echo ""

python3 << PYTHON_SCRIPT
import json
import os

results_dir = "${RESULTS_DIR}"
timestamp = "${TIMESTAMP}"

# Load results
results = {}
for topo in ['mesh', 'ricobit', 'torus']:
    filepath = os.path.join(results_dir, f'{topo}_results_{timestamp}.json')
    if os.path.exists(filepath):
        with open(filepath) as f:
            results[topo] = json.load(f)
    else:
        results[topo] = None

if not any(results.values()):
    print("No results found!")
    exit(1)

# Print comparison table
print("-" * 72)
print(f"{'Metric':<28} {'MESH':>12} {'RICOBIT':>12} {'TORUS':>12}")
print("-" * 72)

def get_val(r, *keys):
    if r is None:
        return 'N/A'
    for k in keys:
        if isinstance(r, dict):
            r = r.get(k)
        else:
            return 'N/A'
    return r if r is not None else 'N/A'

def fmt(val, fmt_str=None):
    if val == 'N/A' or val is None:
        return 'N/A'
    if fmt_str:
        return fmt_str.format(val)
    return str(val)

metrics = [
    ("Nodes", lambda r: get_val(r, 'metrics', 'nodes')),
    ("Packets Injected", lambda r: get_val(r, 'packets_injected')),
    ("Packets Delivered", lambda r: get_val(r, 'packets_delivered')),
    ("Delivery Rate (%)", lambda r: fmt(get_val(r, 'metrics', 'delivery_rate'), "{:.1f}")),
    ("Total Cycles", lambda r: get_val(r, 'total_cycles')),
    ("Avg Latency (cycles)", lambda r: fmt(get_val(r, 'metrics', 'avg_latency'), "{:.2f}")),
    ("Min Latency", lambda r: get_val(r, 'metrics', 'min_latency')),
    ("Max Latency", lambda r: get_val(r, 'metrics', 'max_latency')),
    ("Throughput (pkt/cycle)", lambda r: fmt(get_val(r, 'metrics', 'throughput'), "{:.4f}")),
    ("Avg Hops (RiCoBiT only)", lambda r: fmt(get_val(r, 'metrics', 'avg_hops'), "{:.2f}")),
    # Better metric: packets per average latency (how fast individual packets move)
    ("Packet Speed (1/latency)", lambda r: fmt(1.0 / get_val(r, 'metrics', 'avg_latency'), "{:.4f}") if get_val(r, 'metrics', 'avg_latency') not in ['N/A', None] and get_val(r, 'metrics', 'avg_latency') > 0 else 'N/A'),
]

for name, extractor in metrics:
    vals = [str(extractor(results.get(t))) for t in ['mesh', 'ricobit', 'torus']]
    print(f"{name:<28} {vals[0]:>12} {vals[1]:>12} {vals[2]:>12}")

print("-" * 72)
print()

# Performance analysis
print("🏆 PERFORMANCE WINNERS:")
print()

valid_results = {k: v for k, v in results.items() if v and v.get('success')}

if valid_results:
    # Best latency (lowest)
    latencies = [(t, r['metrics']['avg_latency']) for t, r in valid_results.items() 
                 if r['metrics'].get('avg_latency', float('inf')) < 10000]
    if latencies:
        latencies.sort(key=lambda x: x[1])
        print(f"   🥇 Lowest Avg Latency:  {latencies[0][0].upper():>10} ({latencies[0][1]:.2f} cycles)")
        if len(latencies) > 1:
            print(f"   🥈 Second:              {latencies[1][0].upper():>10} ({latencies[1][1]:.2f} cycles)")
    
    # Best packet speed (highest 1/latency - how fast individual packets move)
    speeds = [(t, 1.0/r['metrics']['avg_latency']) for t, r in valid_results.items() 
              if r['metrics'].get('avg_latency', 0) > 0 and r['metrics'].get('avg_latency', float('inf')) < 10000]
    if speeds:
        speeds.sort(key=lambda x: x[1], reverse=True)
        print(f"   🥇 Fastest Packet Speed: {speeds[0][0].upper():>10} ({speeds[0][1]:.4f})")
    
    # Best throughput (highest)
    throughputs = [(t, r['metrics']['throughput']) for t, r in valid_results.items()]
    throughputs.sort(key=lambda x: x[1], reverse=True)
    print(f"   🥇 Highest Throughput:  {throughputs[0][0].upper():>10} ({throughputs[0][1]:.4f} pkt/cycle)")
    
    # Best delivery rate
    deliveries = [(t, r['metrics']['delivery_rate']) for t, r in valid_results.items()]
    deliveries.sort(key=lambda x: x[1], reverse=True)
    print(f"   🥇 Best Delivery Rate:  {deliveries[0][0].upper():>10} ({deliveries[0][1]:.1f}%)")

print()

# RiCoBiT specific analysis
if results.get('ricobit') and results['ricobit'].get('success'):
    ricobit = results['ricobit']
    mesh = results.get('mesh', {})
    
    print("📊 RiCoBiT vs MESH Analysis (per paper claims):")
    print()
    
    if mesh and mesh.get('metrics', {}).get('avg_latency'):
        ricobit_lat = ricobit['metrics']['avg_latency']
        mesh_lat = mesh['metrics']['avg_latency']
        if mesh_lat > 0:
            improvement = ((mesh_lat - ricobit_lat) / mesh_lat) * 100
            print(f"   Latency Improvement:    {improvement:.1f}% better than MESH")
    
    if ricobit['metrics'].get('avg_hops'):
        print(f"   Average Hop Count:      {ricobit['metrics']['avg_hops']:.2f} hops")

print()
PYTHON_SCRIPT

echo ""
echo -e "${BOLD}═══════════════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}                         OUTPUT FILES${NC}"
echo -e "${BOLD}═══════════════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "Results:"
echo -e "  ${GREEN}MESH${NC}:    ${RESULTS_DIR}/mesh_results_${TIMESTAMP}.json"
echo -e "  ${YELLOW}RICOBIT${NC}: ${RESULTS_DIR}/ricobit_results_${TIMESTAMP}.json"
echo -e "  ${BLUE}TORUS${NC}:   ${RESULTS_DIR}/torus_results_${TIMESTAMP}.json"
echo ""
echo -e "Logs:"
echo -e "  ${GREEN}MESH${NC}:    ${MESH_LOG}"
echo -e "  ${YELLOW}RICOBIT${NC}: ${RICOBIT_LOG}"
echo -e "  ${BLUE}TORUS${NC}:   ${TORUS_LOG}"
echo ""

# Save combined results
COMBINED_OUTPUT="${RESULTS_DIR}/comparison_${TIMESTAMP}.json"
python3 << SAVE_COMBINED
import json
import os

results_dir = "${RESULTS_DIR}"
timestamp = "${TIMESTAMP}"

combined = {
    "timestamp": timestamp,
    "config": {
        "packets": ${PACKETS},
        "seed": ${SEED}
    },
    "execution_time_seconds": ${ELAPSED},
    "results": {}
}

for topo in ['mesh', 'ricobit', 'torus']:
    filepath = os.path.join(results_dir, f'{topo}_results_{timestamp}.json')
    if os.path.exists(filepath):
        with open(filepath) as f:
            combined['results'][topo] = json.load(f)

with open("${COMBINED_OUTPUT}", 'w') as f:
    json.dump(combined, f, indent=2)

print(f"Combined results saved to: ${COMBINED_OUTPUT}")
SAVE_COMBINED

echo ""
echo -e "${BOLD}${GREEN}All simulations completed!${NC}"
echo ""
