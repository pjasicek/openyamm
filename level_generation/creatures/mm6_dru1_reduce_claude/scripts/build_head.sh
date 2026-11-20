#!/usr/bin/env bash
# Candidate with the new head set: work/ladder_head.blend (head_atlas_uv.py) + textures/head_<tag>_*.png ->
# export/mm6_dru1_head<out>.glb (LODs, shadow LODs, variants) + viewer GLBs. Usage: build_head.sh <tag> [out, default tag]
# (round 3: REA_LADDER=ladder_head_panel.blend build_head.sh r66 r66p, the panel weights from panel_weights.py)
set -euo pipefail
tag=$1; out=${2:-$1}; P="$(cd "$(dirname "$0")/.." && pwd)"; R="$(cd "$P/../../.." && pwd)"; cd "$P"
REA_LADDER=${REA_LADDER:-ladder_head.blend} REA_CAND=Cand_66 REA_NODE=Druidess blender -b -P scripts/export_cand.py 2>&1 | grep -E "EXPORTED|Error"
python3 scripts/swap_lod0.py "$R/assets_source/worlds/mm6/models/mm6_dru1.glb" work/cand_export.glb export/mm6_dru1_head_lod0.glb Druidess
python3 scripts/replace_head_images.py export/mm6_dru1_head_lod0.glb export/mm6_dru1_head${out}_lod0.glb textures/head_${tag}_
blender -b -P "$R/tools/build_actor_lods.py" -- export/mm6_dru1_head${out}_lod0.glb export/mm6_dru1_head_lods.glb --mesh-node Druidess 2>&1 | grep "LOD tri"
python3 ../mm6_dru1_claude/scripts/shrink_shadow_lods.py export/mm6_dru1_head_lods.glb export/mm6_dru1_head$out.glb > /dev/null
rm -f export/mm6_dru1_head_lods.glb export/mm6_dru1_head_lods.geometry.glb export/mm6_dru1_head_lod0.glb
python3 scripts/carry_variants.py export/mm6_dru1_head$out.glb
python3 scripts/viewer_variants.py export/mm6_dru1_head$out.glb head$out > /dev/null
