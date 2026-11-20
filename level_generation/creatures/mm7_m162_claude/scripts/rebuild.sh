#!/usr/bin/env bash
# Behemoth replayable chain (rig and clips): step1 -> joints (work/joints_final.json, measured) -> build_rig ->
# weights_heat -> retarget (Mixamo mutant family, relative to the idle's first frame) -> clip_finish -> twist_bones.
# Usage: scripts/rebuild.sh <creature lease token>   (STAGE=rig|anim|all)
set -euo pipefail
cd "$(dirname "$0")/../../../.."
P=level_generation/creatures/mm7_m162_claude
T=${1:?token}
. $P/scripts/libpath.sh
run() { local out log; out=$(tools/run_creature_blender.sh --token "$T" "$@" 2>&1) || { echo "$out"; log=$(echo "$out" | sed -n 's/^Blender log: //p'); tail -20 "$log"; echo "STEP FAILED: $1"; exit 1; }
        log=$(echo "$out" | sed -n 's/^Blender log: //p'); grep -E '^(CLEAN|RIG|HAND|WEIGHTS|RETARGET|CLIP|TWIST|BAKED|EXPORTED)|Error' "$log" | cut -c1-200 || true; }
STAGE=${STAGE:-all}
if [ "$STAGE" = all ] || [ "$STAGE" = rig ]; then
run $P/scripts/step1_clean.py $P/meshy/body_geometry_v1/model_urls_glb.glb $P/work/step1.blend
run $P/scripts/build_rig.py
run $P/scripts/weights_heat.py $P/work/rig_v1.blend $P/work/rig_v1w.blend
fi
if [ "$STAGE" = all ] || [ "$STAGE" = anim ]; then
mapfile -t MXC < <(sed -e "s|\$MX|$MX|" $P/scripts/mx_clips.txt | grep -v '^#' | grep .)
MX_REF="$MX/Mutant Breathing Idle.fbx:0" run $P/scripts/retarget_mixamo.py $P/work/rig_v1w.blend $P/work/rig_v2r.blend "${MXC[@]}"
run $P/scripts/clip_finish.py $P/work/rig_v2r.blend $P/work/rig_v2c.blend
FA=0.6 FA_RAMP=0.15,0.85 run $P/scripts/twist_bones.py $P/work/rig_v2c.blend $P/work/rig_v3.blend
fi
