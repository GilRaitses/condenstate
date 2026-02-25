#!/bin/bash
#
# RUN SINGLE SIMULATION WITH OPTIMIZED PARAMETERS
#
# Usage: ./run_single_sim.sh <sim_id> <eps> <temp> <arch_a> <arch_b> <chain_len> <copies> <box_size>
#
# Example: ./run_single_sim.sh 001 8 300 4 20 24 500 35
#

set -e

if [[ $# -lt 8 ]]; then
    echo "Usage: $0 <sim_id> <eps> <temp> <arch_a> <arch_b> <chain_len> <copies> <box_size>"
    echo "Example: $0 001 8 300 4 20 24 500 35"
    exit 1
fi

SIM_ID=$1
EPS=$2
TEMP=$3
CONSECUTIVE_A=$4
CONSECUTIVE_B=$5
CHAIN_LENGTH=$6
COPIES=$7
BOX_SIZE=$8

# Stage 5: 1-1 sticker-sticker attraction (14 sims whose trajectories were lost)
STAGE5_SIMS="115 116 117 118 119 120 121 122 123 124 125 126 127 128 129 130"
if echo "$STAGE5_SIMS" | grep -qw "$SIM_ID"; then
    STAGE5_FLAG="--stage5"
    STAGE5_SUFFIX="_11attract"
else
    STAGE5_FLAG=""
    STAGE5_SUFFIX=""
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Beads audit (best-effort)
if [[ -x "$SCRIPT_DIR/bd_audit.sh" ]]; then
    "$SCRIPT_DIR/bd_audit.sh" "launch_sim" \
        "sim_id=${SIM_ID} eps=${EPS} temp=${TEMP} arch=A${CONSECUTIVE_A}B${CONSECUTIVE_B} chain_len=${CHAIN_LENGTH} copies=${COPIES} box_size=${BOX_SIZE}"
fi

# Optimized run parameters (literature-compliant)
RELAX_STEPS1=2000000    # 2M steps first relaxation
RELAX_STEPS2=5000000    # 5M steps second relaxation
RECORD_STEPS=20000000   # 20M steps production

# LAMMPS command - try different options
echo "[DEBUG] Detecting LAMMPS..."
if command -v lmp_mpi &> /dev/null; then
    echo "[DEBUG] Found lmp_mpi"
    LAMMPS_CMD="mpirun --oversubscribe --allow-run-as-root -np 2 lmp_mpi"
elif command -v lmp &> /dev/null; then
    # Check if lmp supports MPI by running a quick test
    echo "[DEBUG] Found lmp, testing if it works..."
    if lmp -help 2>&1 | grep -q "MPI"; then
        echo "[DEBUG] lmp has MPI support, using mpirun"
        LAMMPS_CMD="mpirun --oversubscribe --allow-run-as-root -np 2 lmp"
    else
        echo "[DEBUG] lmp without MPI, running directly"
        LAMMPS_CMD="lmp"
    fi
else
    echo "[ERROR] No LAMMPS found!"
    exit 1
fi
echo "[DEBUG] LAMMPS_CMD = $LAMMPS_CMD"

# Calculate density
TOTAL_BEADS=$((COPIES * CHAIN_LENGTH))
VOLUME=$((BOX_SIZE * BOX_SIZE * BOX_SIZE))
DENSITY=$(echo "scale=3; $TOTAL_BEADS / $VOLUME" | bc)

# Create run directory
RUN_DIR="runs/sim_${SIM_ID}_E${EPS}_T${TEMP}_A${CONSECUTIVE_A}B${CONSECUTIVE_B}${STAGE5_SUFFIX}"
mkdir -p "$RUN_DIR"

LOG_FILE="$RUN_DIR/simulation.log"
exec > >(tee -a "$LOG_FILE") 2>&1

echo "============================================================"
echo "SIMULATION ${SIM_ID}: ε=${EPS} T=${TEMP}K A${CONSECUTIVE_A}B${CONSECUTIVE_B}"
echo "Started: $(date)"
echo "============================================================"
echo ""
echo "Parameters:"
echo "  ε = $EPS kBT"
echo "  T = ${TEMP}K"
echo "  Architecture: A${CONSECUTIVE_A}B${CONSECUTIVE_B}"
echo "  Chain length: $CHAIN_LENGTH"
echo "  Chains: $COPIES"
echo "  Box: ${BOX_SIZE}³ nm³ (cubic)"
echo "  Bead density: $DENSITY σ⁻³"
echo "  LAMMPS: $LAMMPS_CMD"
echo ""

cd "$RUN_DIR"

# Generate configuration
echo "[$(date +%H:%M:%S)] Generating polymer configuration..."
python3 "$SCRIPT_DIR/S1_Parameter_StickerSpacer_Polymers.py" \
    -t "$TEMP" -n "$CHAIN_LENGTH" -a "$CONSECUTIVE_A" -b "$CONSECUTIVE_B" \
    -c "$COPIES" -x "$BOX_SIZE" -y "$BOX_SIZE" -z "$BOX_SIZE" -o Parameter

python3 "$SCRIPT_DIR/S2_Poly_Stickers_Generation_RandAB.py" \
    -p Parameter/Initial_Parameter_0.dat

python3 "$SCRIPT_DIR/S3_Relax_StickerSpacer_Polymers.py" \
    -p Parameter/Initial_Parameter_0.dat -e "$EPS" \
    --run-steps1 "$RELAX_STEPS1" --run-steps2 "$RELAX_STEPS2" \
    $STAGE5_FLAG

python3 "$SCRIPT_DIR/S4_Record_StickerSpacers_Polymers.py" \
    -p Parameter/Initial_Parameter_0.dat -e "$EPS" \
    --run-steps "$RECORD_STEPS" \
    $STAGE5_FLAG

# Enter simulation directory
SIM_DIR="Simulations_T${TEMP}"
cd "$SIM_DIR"

RELAX_FILE=$(ls Poly_Relax_*.in 2>/dev/null | head -1)
RECORD_FILE=$(ls Poly_Record_*.in 2>/dev/null | head -1)

# Patch neighbor list for efficiency
for f in "$RELAX_FILE" "$RECORD_FILE"; do
    if [[ -f "$f" ]]; then
        sed -i.bak 's/neigh_modify every 1 delay 0/neigh_modify every 10 delay 0 check yes/' "$f" 2>/dev/null || true
        rm -f "${f}.bak"
    fi
done

# Run relaxation
echo "[$(date +%H:%M:%S)] Running relaxation (${RELAX_STEPS1} + ${RELAX_STEPS2} steps)..."
echo "[DEBUG] LAMMPS command: $LAMMPS_CMD"
echo "[DEBUG] Input file: $RELAX_FILE"
echo "[DEBUG] Checking if input file exists..."
ls -la "$RELAX_FILE" || echo "[ERROR] Input file not found!"
echo "[DEBUG] First 20 lines of input file:"
head -20 "$RELAX_FILE" || true
START=$(date +%s)
# Run LAMMPS with output to both console and log file
$LAMMPS_CMD -in "$RELAX_FILE" 2>&1 | tee "Relax_E${EPS}.log" || {
    echo "[ERROR] LAMMPS relaxation failed with exit code $?"
    echo "[ERROR] Last 50 lines of LAMMPS output:"
    tail -50 "Relax_E${EPS}.log" 2>/dev/null || true
    exit 1
}
RELAX_TIME=$(($(date +%s) - START))
echo "[$(date +%H:%M:%S)] Relaxation done (${RELAX_TIME}s)"

# Run production
echo "[$(date +%H:%M:%S)] Running production (${RECORD_STEPS} steps)..."
START=$(date +%s)
$LAMMPS_CMD -in "$RECORD_FILE" > "Prd_E${EPS}.log" 2>&1
PROD_TIME=$(($(date +%s) - START))
echo "[$(date +%H:%M:%S)] Production done (${PROD_TIME}s)"

# Run analysis
echo "[$(date +%H:%M:%S)] Running analysis..."
cd "$SCRIPT_DIR"
python3 "$SCRIPT_DIR/quick_analysis.py" "$RUN_DIR" 2>/dev/null || echo "Analysis script not found or failed"

# Write completion marker
TOTAL_TIME=$((RELAX_TIME + PROD_TIME))
echo ""
echo "============================================================"
echo "SIMULATION ${SIM_ID} COMPLETE"
echo "Total time: ${TOTAL_TIME}s ($(echo "scale=1; $TOTAL_TIME / 3600" | bc)h)"
echo "Finished: $(date)"
echo "============================================================"

# Create completion flag
echo "$SIM_ID,$EPS,$TEMP,$CONSECUTIVE_A,$CONSECUTIVE_B,$CHAIN_LENGTH,$COPIES,$BOX_SIZE,$TOTAL_TIME,$(date +%s)" > "$RUN_DIR/COMPLETED"
