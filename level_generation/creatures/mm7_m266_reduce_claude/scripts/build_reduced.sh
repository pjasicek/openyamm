#!/usr/bin/env bash
# Reduced runtime GLB from the picked ladder step: head 5 fix (horns -> eyes) -> export_cand -> swap_lod0 (onto the batch I export) -> LODs
# (protected extremes and Death floor contact; the body material at 0.5/0.22/0.1, its ~60 spikes keep a few
# triangles each) -> shadow LODs -> colour variants carried to every LOD/shadow primitive -> head 5 eye paint in the free atlas tile.
# Blender steps run through scripts/b.sh (creature wrapper; lease token in REA_TOKEN).
# Usage: [REA_LADDER=ladder_n1 REA_PICK=Cand_78] scripts/build_reduced.sh <out.glb>
set -euo pipefail
cd "$(dirname "$0")/.."; out=${1:-export/mm7_m266.glb}
# user review 2026-10-20: head 5's eye horns and stray mouth horn removed, eye lenses added (head5_fix.py, head5_eyes.py)
python3 scripts/head5_eyes.py
REA_EYES=1 scripts/b.sh head5_fix.py ${REA_LADDER:-ladder_n1}.blend ${REA_PICK:-Cand_78} ladder.blend
REA_CAND=${REA_PICK:-Cand_78} REA_NODE=M266 scripts/b.sh export_cand.py
python3 scripts/swap_lod0.py work/mm7_m266_source_pre_reduce.glb work/cand_export.glb work/pick_lod0.glb M266
REA_MAT_RATIOS="Hydra_A:0.5,0.22,0.1" REA_FLOOR_M=0.006 scripts/b.sh build_lods.py
python3 scripts/shrink_shadow_lods.py work/pick_lods.glb work/pick_lods_shadowfix.glb
cp work/pick_lods_shadowfix.glb "$out"; python3 scripts/carry_variants.py "$out"
python3 scripts/head5_eye_paint.py "$out"; ls -la "$out"
