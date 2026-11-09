#!/usr/bin/env bash
# Rebuild the unreduced natf runtime from the installed GLB: new Attack/Cast (work/clips.blend, build_clips.py),
# retired cage keys stripped, skirt re-skinned to pelvis + swing helpers (skirt_skin.py, settings below), helper joints
# and keys added, body swapped, LODs rebuilt, variants carried, unused materials pruned.
# -> export/mm6_natf_v2_unreduced.glb   (run from anywhere)
set -euo pipefail
P="$(cd "$(dirname "$0")/.." && pwd)"; ROOT="$(cd "$P/../../.." && pwd)"; R="$P/../mm6_natf_reduce_claude/scripts"; cd "$P"
blender -b -P scripts/export_clips.py -- work/clips.blend work/clips_new.glb Attack Cast 2>&1 | grep EXPORTED
python3 scripts/merge_clips.py "$ROOT/assets_source/worlds/mm6/models/mm6_natf.glb" work/clips_new.glb work/natf_clips_merged.glb Attack Cast
python3 scripts/strip_channels.py work/natf_clips_merged.glb work/natf_clips_merged.glb
THIGH_MAX=1.0 CLEAR=0.03 TOP=0.98 BOTTOM=0.62 SPLIT=0.20 SMOOTH_SKIRT=0 \
    blender -b -P scripts/skirt_skin.py -- work/natf_clips_merged.glb work/skirt_final.blend 2>&1 | grep -E "^SKIRT"
blender -b -P scripts/export_rig_clips.py -- work/skirt_final.blend work/helpers_export.glb 2>&1 | grep EXPORTED
python3 scripts/add_helpers.py work/natf_clips_merged.glb work/helpers_export.glb work/natf_helpers.glb
blender -b -P scripts/export_body.py -- work/skirt_final.blend work/body_export.glb 2>&1 | grep EXPORTED
python3 "$R/swap_lod0.py" work/natf_helpers.glb work/body_export.glb work/natf_v2_lod0.glb Natf
blender -b -P "$ROOT/tools/build_actor_lods.py" -- work/natf_v2_lod0.glb work/natf_v2_lods.glb --mesh-node Natf 2>&1 | grep "LOD tri"
python3 "$R/carry_variants.py" work/natf_v2_lods.glb
python3 "$R/prune_materials.py" work/natf_v2_lods.glb export/mm6_natf_v2_unreduced.glb
