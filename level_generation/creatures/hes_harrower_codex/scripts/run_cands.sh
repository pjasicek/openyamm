#!/usr/bin/env bash
# Library attack chain (2026-10-24): retargeted clips (work/cand_raw.blend) -> fit -> foot lock -> arm clearance ->
# blade clearance -> polish -> last armour contacts -> cloth/tail/floor finish -> gates, for the clips in
# work/cand_config.json. Every Blender step runs through tools/run_creature_blender.sh, one at a time (the workspace
# lock is exclusive), with the lease token in CREATURE_3D_TOKEN. Logs in $LOG. BLADE_R / BLADE_PUSH (the crescents'
# collision capsules in cand_robe_sim.py) default to the installed run's 0.09 / 0.05 m. After the finish, a second
# blade clearance with the simulated cloth as an obstacle (CLOTH=1).
set -euo pipefail
cd "$(dirname "$0")/.."
W=$(pwd); R=$(cd ../../.. && pwd); LOG=${LOG:?set LOG to a log directory}; mkdir -p "$LOG"
: "${CREATURE_3D_TOKEN:?claim the creature first}"
export BLADE_R=${BLADE_R:-0.09} BLADE_PUSH=${BLADE_PUSH:-0.05}
blend() {
    local s=$1 name=$2; shift 2
    local out; out=$("$R/tools/run_creature_blender.sh" "level_generation/creatures/hes_harrower_codex/scripts/$s" "$@") \
        || { cp "${out#Blender log: }" "$LOG/$name.log" 2>/dev/null; echo "FAILED $s"; tail -20 "$LOG/$name.log"; exit 1; }
    cp "${out#Blender log: }" "$LOG/$name.log"
}
step() {
    echo "== $1"; blend "$1" "${LOGNAME_:-${1%.py}}" "${@:2}"
    grep -hE "^(CAND|FOOTLOCK|ARMCLEAR|CLEARED|POLISH|CONTACTS|CLOTH_FIT|ROOT_LIFT) " "$LOG/${LOGNAME_:-${1%.py}}.log" | cut -c1-400 || true
}
step cand_fit.py "$W/work/cand_raw.blend" "$W/work/cand_fit.blend" "$W/work/cand_config.json"
step cand_footlock.py "$W/work/cand_fit.blend" "$W/work/cand_lock.blend" "$W/work/cand_config.json"
step cand_armclear.py "$W/work/cand_lock.blend" "$W/work/cand_arm.blend"
step cand_blade_clear.py "$W/work/cand_arm.blend" "$W/work/cand_clear.blend"
step cand_polish.py "$W/work/cand_clear.blend" "$W/work/cand_polish.blend"
step cand_contacts.py "$W/work/cand_polish.blend" "$W/work/cand_contacts.blend" "$W/scripts/armour_harrower.json"
step cand_finish.py "$W/work/cand_contacts.blend" "$W/work/cand_finished.blend"
CLOTH=1 LOGNAME_=cand_blade_clear_cloth step cand_blade_clear.py "$W/work/cand_finished.blend" "$W/work/cand_final.blend"
"$W/scripts/run_cand_gates.sh"
