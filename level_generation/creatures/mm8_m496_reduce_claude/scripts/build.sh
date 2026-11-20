#!/usr/bin/env bash
# Picked candidate (work/ladder_f75h.blend, Cand_55) -> export/mm8_m496.glb: body LOD0 swap (other nodes keep their
# installed LOD chains), body LOD1-3 with the eye outline protected, shadow chain = colour LOD1-3 (as installed),
# compaction, repaint of the bake's isolated black faces, body atlas gutter padding, the arm pose eased into and out
# of Fidget and Hit (boundary pops), checks.
set -euo pipefail
cd "$(dirname "$0")/.."
cp work/ladder_f75h.blend work/ladder.blend
REA_CAND=Cand_55 REA_NODE=Body blender -b -P scripts/export_cand.py 2>&1 | grep EXPORTED
python3 scripts/swap_lod0.py work/mm8_m496_source_pre_reduce.glb work/cand_export.glb work/r55_lod0.glb Body | tail -1
blender -b -P scripts/build_lods.py 2>&1 | grep -E "LOD tri|EYE"
python3 scripts/shadow_chain.py work/r55_lods.glb work/r55_shadow.glb Body
python3 scripts/compact_glb.py work/r55_shadow.glb work/r55_compact.glb | tail -1
python3 scripts/fix_dark_faces.py work/r55_compact.glb work/r55_fixed.glb | tail -1
python3 scripts/pad_body.py work/r55_fixed.glb work/r55_padded.glb
python3 scripts/fix_arm_boundaries.py work/r55_padded.glb export/mm8_m496.glb
ALLOW_IMAGES=m496_body ALLOW_CHANNELS=Fidget:LeftArm:rotation,Fidget:RightArm:rotation,Hit:LeftArm:rotation,Hit:RightArm:rotation \
    python3 scripts/effects_identical.py work/mm8_m496_source_pre_reduce.glb export/mm8_m496.glb
python3 ../../../level_generation/decorations/mm8_3d/animated/scripts/check_winding.py export/mm8_m496.glb | tail -1
