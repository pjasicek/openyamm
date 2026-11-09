#!/usr/bin/env bash
# Reduced Griffin runtime GLB from the picked ladder candidate (work/ladder_s1b.blend, Cand_56 = ratio 0.57, 9,188
# triangles): export the candidate -> swap it into the pre-reduction export LOD0 (materials, clips, sockets unchanged)
# -> prepare_actor_glb -> LODs with protected points -> shadow-LOD shrink -> the Griffin's colour variants (same
# region_variants.py call as mm7_m258_claude/scripts/build_runtime.sh). Smooth shading by default; REA_FLAT=1 builds
# the flat-shaded alternative (source facets) as export/mm7_m258_flat.glb. Nothing is installed.
# Usage: [REA_FLAT=1] scripts/build_reduced.sh
set -euo pipefail
cd "$(dirname "$0")/.."
sfx=""; [ "${REA_FLAT:-}" = 1 ] && sfx="_flat"
cp work/ladder_s1b.blend work/ladder.blend
REA_CAND=Cand_56 REA_NODE=M258 REA_OUT=cand_export$sfx.glb blender -b -P scripts/export_cand.py 2>&1 | grep -E "SHADE|EXPORTED|Error"
python3 scripts/swap_lod0.py work/mm7_m258_lod0_pre_reduce.glb work/cand_export$sfx.glb work/pick_lod0_raw$sfx.glb M258
python3 ../../../tools/prepare_actor_glb.py work/pick_lod0_raw$sfx.glb work/pick_lod0.glb | tail -1
blender -b -P scripts/build_lods.py 2>&1 | grep -E "PROTECTED|LOD tri"
python3 scripts/shrink_shadow_lods.py work/pick_lods.glb work/pick_lods_shadowfix.glb > /dev/null
python3 ../claude_shared/region_variants.py work/pick_lods_shadowfix.glb export/mm7_m258$sfx.glb ../mm7_m258_claude/textures/m258_ramps.json \
  --extra M258 openyamm_specular=1 --extra M258 openyamm_specular_mask=true --extra M258 pbr.metallicFactor=0
rm -f work/pick_lods.glb work/pick_lods.geometry.glb work/pick_lods_shadowfix.glb
ls -la export/mm7_m258$sfx.glb
