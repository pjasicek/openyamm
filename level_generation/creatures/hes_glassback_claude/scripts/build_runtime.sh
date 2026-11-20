#!/usr/bin/env bash
# Glassback runtime GLBs, NOT installed (the Hesper stage integrates them):
# clips (anim.py on the reduced rig) -> export -> prepare -> LODs -> shadow fix -> A/B/C skins (region ramps) ->
# head material merged into the body -> export/hes_glassback.glb; then the crest attachments (crest.py, crest_export.py,
# crest_post.py) -> export/hes_glassback_crest_<size>_<bone>.glb. Usage: TOK=<lease token> scripts/build_runtime.sh
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
cd "$here"
S=scripts/run.sh
$S anim.py work/rig_v5.blend work/anim_v3.blend | grep "^CLIP"
$S crest.py work/anim_v3.blend work/crest_v3.blend | grep "CREST full\|crystals"
$S crest_check.py work/crest_v3.blend | cut -c1-150
$S export.py work/anim_v3.blend export/hes_glassback_lod0.glb
python3 "$repo/tools/prepare_actor_glb.py" export/hes_glassback_lod0.glb export/hes_glassback_runtime_lod0.glb
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/hes_glassback_runtime_lod0.glb" \
  "$here/export/hes_glassback_lods.glb" --mesh-node Glassback 2>&1 | grep "LOD triangles"
python3 scripts/shrink_shadow_lods.py export/hes_glassback_lods.glb export/hes_glassback_lods_shadowfix.glb
python3 ../claude_shared/region_variants.py export/hes_glassback_lods_shadowfix.glb export/hes_glassback.glb \
  textures/hgb_ramps.json --extra Glassback openyamm_specular=1 --extra Glassback openyamm_specular_mask=true \
  --extra Glassback pbr.metallicFactor=0
python3 "$repo/tools/merge_head_material.py" export/hes_glassback.glb export/hes_glassback.glb
rm -f export/hes_glassback_lods.geometry.glb
# corpse exactly on the floor (Blender's grounding left Dead 2.25 cm up in the exported mesh)
mkdir -p work/floor_fix_base && cp export/hes_glassback.glb work/floor_fix_base/hes_glassback.glb
python3 ../claude_shared/floor/floor_fix.py work/floor_fix_base/hes_glassback.glb export/hes_glassback.glb --ground-death Death Dead
python3 scripts/floor_gate.py export/hes_glassback.glb | grep "GATE\|STRIDE\|STAND"
$S crest_export.py work/crest_v3.blend
rm -f export/hes_glassback_crest_*.glb
python3 scripts/crest_post.py
python3 "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/hes_glassback.glb
for f in export/hes_glassback_crest_*.glb; do python3 "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" "$f" | tail -1; done
ls -la export/hes_glassback.glb
