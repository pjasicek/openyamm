#!/usr/bin/env bash
# Invoke through creature_workspace.py run with this project's active lease.
set -euo pipefail
cd "$(dirname "$0")/../../.."
export PYTHONDONTWRITEBYTECODE=1
: "${LOD_REPAIR_PYTHON:?Set Python with pymeshlab, xatlas, scipy, Pillow}"
export BLENDER_BIN=${BLENDER_BIN:-blender}
p=level_generation/creatures/hes_drudge_codex
blender_step() { "$BLENDER_BIN" -b -noaudio --factory-startup --threads 4 --python-exit-code 1 -P "$p/scripts/$1" -- "${@:2}"; }
python3 "$p/scripts/build_drudges.py"
blender_step retarget_mixamo.py level_generation/creatures/hes_kreegan_claude/export/hes_kreegan.blend "$p/work/run_retarget.blend" 'anim_library/mixamo/Standard Run.fbx:Drudge_Running'
blender_step run_fit.py "$p/work/run_retarget.blend" "$p/work/run_fitted.blend"
blender_step finish_motion.py
python3 "$p/scripts/merge_motion.py"
blender_step gates.py "$p/work/drudge_before_lod.glb" gates_initial.json
for stem in drudge thrix; do
    python3 "$p/lodrep/repair_glb.py" "$p/work/${stem}_animated.glb" "$p/work/lod_${stem}" "$p/work/${stem}_after_lod.glb"
    python3 -c 'import json,sys; assert json.load(open(sys.argv[1]))["passed"]' "$p/work/lod_${stem}/result.json"
done
python3 "$p/scripts/finish_exports.py"
blender_step gates.py "$p/export/hes_drudge.glb" gates_final.json Drudge_Walking Drudge_Running Drudge_Death Drudge_Dead
python3 "$p/scripts/prepare_review.py"
python3 "$p/scripts/verify.py"
python3 "$p/scripts/jerk_probe.py"
python3 level_generation/decorations/mm8_3d/animated/scripts/check_winding.py "$p"/export/*.glb > "$p/review/winding.log"
blender_step editable_master.py
