#!/usr/bin/env bash
# Sorceress runtime GLBs from the gated master: grade (body and head sets) -> tier ramps -> gutter fill (last step on
# every map) -> clips synced into the UV master (rig_v5 -> rig_v6) -> export -> prepare -> LODs -> shadow fix -> skins
# sorc_a/b/c/m (one region: the white cloth) -> head material merged into the body (one draw) -> winding check.
# --install: tools/install_model.py --world xeen. Far LODs: LOD playbook ladder afterwards (lodrepair/).
# Blender steps go through the lane wrapper (scripts/step.sh, or blender on PATH = xeen_tiers_claude/bin).
# Usage: TOK=<lease token> scripts/build_runtime.sh [--install]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
export PATH="$repo/level_generation/creatures/xeen_tiers_claude/bin:$PATH"
cd "$here"
for pre in sorc sorc_head; do
  python3 ../claude_shared/grade_basecolor.py --ao textures/${pre}_ao_1k.png --fine 1.0 --local 0.3 --ao-strength 0.5 \
    --contrast 1.06 --saturation 1.15 textures/${pre}_basecolor.png | tail -1
done
python3 scripts/tier_ramps_sorc.py | cut -c1-400
python3 ../claude_shared/gutter_fill.py work/uv_body.npz textures/sorc_basecolor_graded.png textures/sorc_region_mask.png \
  textures/sorc_normal_1k.png textures/sorc_mr_1k.png --in-place | tail -1
python3 ../claude_shared/gutter_fill.py work/uv_head.npz textures/sorc_head_basecolor_graded.png \
  textures/sorc_head_normal_1k.png textures/sorc_head_mr_1k.png --in-place | tail -1
scripts/step.sh sync_actions.py "$here/work/rig_v5.blend" "$here/work/rig_v6.blend"
scripts/step.sh export_runtime.py
python3 "$repo/tools/prepare_actor_glb.py" export/xeen_sorc_lod0.glb export/xeen_sorc_runtime_lod0.glb
blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/xeen_sorc_runtime_lod0.glb" \
  "$here/export/xeen_sorc_lods.glb" --mesh-node Sorc > logs/build_actor_lods.log 2>&1
grep "LOD triangles" logs/build_actor_lods.log
python3 scripts/shrink_shadow_lods.py export/xeen_sorc_lods.glb export/xeen_sorc_lods_shadowfix.glb
python3 ../claude_shared/region_variants.py export/xeen_sorc_lods_shadowfix.glb export/xeen_sorc_variants.glb \
  textures/sorc_ramps.json --extra Sorc openyamm_specular=0 --extra Sorc pbr.metallicFactor=0
python3 "$repo/tools/merge_head_material.py" export/xeen_sorc_variants.glb export/xeen_sorc.glb
python3 "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/xeen_sorc.glb | tail -1
if [[ "${1:-}" == "--install" ]]; then
  python3 "$repo/tools/install_model.py" export/xeen_sorc.glb --world xeen
fi
ls -la export/xeen_sorc.glb
