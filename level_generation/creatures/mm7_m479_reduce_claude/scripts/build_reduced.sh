#!/usr/bin/env bash
# Reduced runtime GLB from the picked ladder step (hp, Cand_76; piece weights): kept_normals (source GLB normals on unchanged faces) ->
# export_cand -> swap_lod0 (onto the production export: material, images, clips, Socket_Mouth byte for byte) -> LODs
# (protected extremes and Death/Dead floor contact) -> shadow LODs (the production project's step). One material and no
# colour variants, so there is no carry_variants step. Usage: TOKEN=<lease> scripts/build_reduced.sh [out.glb]
set -euo pipefail
cd "$(dirname "$0")/.."; out=${1:-export/mm7_m479.glb}; ROOT=$(cd ../../.. && pwd)
B() { local o; o=$("$ROOT/tools/run_creature_blender.sh" --token "$TOKEN" "level_generation/creatures/mm7_m479_reduce_claude/scripts/$@" 2>&1)
      local log; log=$(echo "$o" | grep -o '/tmp/openyamm-creature-blender-[A-Za-z0-9]*\.log' | head -1)
      grep -E "EXPORTED|KEPTNORMALS|PROTECTED|RATIOS|LOD triangles|Traceback|Error:" "$log" || true; }
REA_KEPT_NORMALS=1 scripts/cand_glb.sh hp Cand_76 kn
cp work/glb_hp_76kn.glb work/pick_lod0.glb
REA_LOD_RATIOS=${REA_LOD_RATIOS:-0.5,0.22,0.072} REA_FLOOR_M=0.006 B build_lods.py
python3 scripts/shrink_shadow_lods.py work/pick_lods.glb work/pick_lods_shadowfix.glb
cp work/pick_lods_shadowfix.glb "$out"; ls -la "$out"
