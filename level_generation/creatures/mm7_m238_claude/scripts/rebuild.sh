#!/usr/bin/env bash
# m238 replayable chain (the m150/m406 source-frame route, without legs). Gate outputs printed; aborts on the first
# failure. Every Blender step runs in a memory-capped scope (cap.sh, CAP default 8G).
#   STAGE=rig : step1 (parts) -> garments -> joints (Meshy auto-rig + ring wrists) -> rig (cloned frames, mesh hands,
#               fitted fingers) -> vortex chain (tail weights; Meshy's legs inside the vortex lose their weights)
#   STAGE=anim: retarget (humanoid set) -> twist bones -> weight rules -> finger weights -> reduction -> authored clips
#               (folded arms, hover, vortex sway, cast hold, death and lamp) -> twist re-bake
set -euo pipefail
cd "$(dirname "$0")/.."
P=$(pwd)
. scripts/libpath.sh
: "${TOKEN:?set TOKEN to the workspace lease token}"
export CAP=${CAP:-8G}
run() { local s=$1; shift; local out log
        out=$(cd "$P/../../.." && "$P/scripts/cap.sh" tools/run_creature_blender.sh --token "$TOKEN" "level_generation/creatures/$(basename "$P")/scripts/$s" "$@" 2>&1) || true
        log=$(echo "$out" | grep -o '/tmp/openyamm-creature-blender-[A-Za-z0-9]*\.log' | head -1)
        if [ -z "$log" ] || grep -q "Error: script failed\|Traceback" "$log"; then grep -A12 Traceback "$log" | tail -14; echo "STEP FAILED: $s"; exit 1; fi
        grep -E '^(CLEAN|GARMENT|RIG|HAND|WEIGHTS|RETARGET|TWIST|RULE|FINGERS|FINGERSMOOTH|REDUCE|FJ|FINGERFIT|THUMBCUT|HANDFRAME|KNUCKLE|VORTEX|AUTHOR|CLIP|LAMP|FOLD|IMPACT)' "$log" | cut -c1-240 || true; }
W=$P/work
STAGE=${STAGE:-all}
if [ "$STAGE" = all ] || [ "$STAGE" = rig ]; then
run step1_clean.py $W/st_v1_parts.blend $W/step1.blend
run garments.py $W/step1.blend $W/step1.blend
python3 scripts/compose_joints.py | grep ELBOW
rm -f work/finger_joints.json
run build_rig.py
run fit_fingers.py $W/rig_v1.blend
run finger_joints.py $W/rig_v1.blend
run build_rig.py
run hand_frame_check.py $W/rig_v1.blend
run vortex.py $W/rig_v1.blend $W/rig_v1v.blend
fi
if [ "$STAGE" = all ] || [ "$STAGE" = anim ]; then
mapfile -t SETC < <(sed -e "s|\$L|$L|" "${SET_LIST:-scripts/set_clips.txt}" | grep -v '^#' | grep .)
run retarget.py $W/rig_v1v.blend $W/rig_v2.blend "${SETC[@]}"
FA=0.6 FA_RAMP=0.15,0.85 run twist_bones.py $W/rig_v2.blend $W/rig_v2t.blend
run weights_fix.py $W/rig_v2t.blend $W/rig_v3.blend
SMOOTH_PASSES=${SMOOTH_PASSES:-3} run finger_weights.py $W/rig_v3.blend $W/rig_v4f.blend
run reduce_rigged.py $W/rig_v4f.blend $W/rig_v4.blend
run author_genie.py $W/rig_v4.blend $W/rig_v5a.blend
FA=0.6 run rebake_twist.py $W/rig_v5a.blend $W/rig_v5.blend Standing Walking Attack Hit Fidget Death
fi
