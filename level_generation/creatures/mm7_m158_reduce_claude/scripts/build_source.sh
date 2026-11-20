#!/usr/bin/env bash
# Unreduced source GLB with the bat project's own chain: export (uv_master) -> material contract -> prepare -> LODs
# (0.5/0.25/0.125, 4 influences) -> shadow fix -> shared-skin tiers -> work/mm7_m158_source.glb
set -euo pipefail
cd "$(dirname "$0")/.."; B=../mm7_m158_claude; ROOT=../../..
blender -b --factory-startup -P scripts/export_source.py 2>&1 | grep EXPORTED
python3 $B/scripts/material_contract.py work/source_lod0.glb
python3 $ROOT/tools/prepare_actor_glb.py work/source_lod0.glb work/source_runtime_lod0.glb
blender -b --factory-startup --python-expr "import sys; sys.path.insert(0,'$ROOT/tools'); from pathlib import Path as Q; from build_actor_lods import generate; generate(Q('work/source_runtime_lod0.glb'),Q('work/source_lods.glb'),'Bat',ratios=(.5,.25,.125),max_influences=4)" 2>&1 | grep -i "lod tri"
python3 $B/scripts/shrink_shadow_lods.py work/source_lods.glb work/source_shadow.glb
python3 ../claude_shared/region_variants.py work/source_shadow.glb work/mm7_m158_source.glb $B/textures/bat_ramps.json \
  --extra Bat openyamm_specular=1 --extra Bat openyamm_specular_mask=true --extra Bat pbr.metallicFactor=0
rm -f work/source_lods.geometry.glb
