# Shared helpers of the run_*.sh scripts (sourced): Blender and Python steps one at a time under the creature lease
# (CREATURE_3D_TOKEN), logs in $LOG. Sets W (the project), R (the repository) and REL.
cd "$(dirname "${BASH_SOURCE[0]}")/.."
W=$(pwd); R=$(cd ../../.. && pwd); LOG=${LOG:?set LOG to a log directory}; mkdir -p "$LOG"
: "${CREATURE_3D_TOKEN:?claim the creature first}"
REL=level_generation/creatures/hes_harrower_codex/scripts
blend() {
    local name=$1 s=$2; shift 2; echo "== $name"
    local out; out=$("$R/tools/run_creature_blender.sh" "$REL/$s" "$@") \
        || { cp "${out#Blender log: }" "$LOG/$name.log" 2>/dev/null; echo "FAILED $s"; tail -20 "$LOG/$name.log"; exit 1; }
    cp "${out#Blender log: }" "$LOG/$name.log"
}
py() {
    local name=$1; shift; echo "== $name"
    python3 "$R/tools/creature_workspace.py" run --project "$W" -- python3 "$@" > "$LOG/$name.log" 2>&1 \
        || { echo "FAILED $name"; tail -20 "$LOG/$name.log"; exit 1; }
}
