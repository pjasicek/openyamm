#!/usr/bin/env bash
# Gates on work/cand_final.blend for the clips in work/cand_config.json (or the clip names given), one Blender run at a
# time through tools/run_creature_blender.sh: geometry (blades, floor, cloth), arm and hand, grip, motion (cuts, feet,
# jerk at 48 fps), armour plates and the shell leak. Reports in review/*_cand.json. Env as run_cands.sh.
set -euo pipefail
cd "$(dirname "$0")/.."
W=$(pwd); R=$(cd ../../.. && pwd); LOG=${LOG:?set LOG to a log directory}; mkdir -p "$LOG"
: "${CREATURE_3D_TOKEN:?claim the creature first}"
BL=${BLEND:-$W/work/cand_final.blend}
CL=${*:-$(python3 -c "import json;print(' '.join('Harrower_'+c['name'] for c in json.load(open('work/cand_config.json'))))")}
gate() {
    local name=$1 s=$2; shift 2; echo "== $name"
    local out; out=$("$R/tools/run_creature_blender.sh" "level_generation/creatures/hes_harrower_codex/scripts/$s" "$@") || echo "FAILED $s"
    cp "${out#Blender log: }" "$LOG/$name.log"
}
gate g_geom cand_audit_geometry.py "$BL" cand .5
gate g_arm gates.py "$BL" cand $CL
gate g_grip cand_grip_gate.py "$BL"
gate g_motion cand_motion_gate.py "$BL" "$W/work/cand_config.json" "$W/review/motion_cand.json"
gate g_armour armour_gate.py "$BL" cand "$W/scripts/armour_harrower.json" $CL
gate g_shell shell_leak.py "$BL" "$W/scripts/armour_harrower.json" cand $CL
grep -h "ARMGATE" "$LOG/g_armour.log" | cut -c1-600 || true
echo "== gates done"
