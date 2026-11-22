#!/usr/bin/env bash
# Killer Sprite runtime GLB: compose -> gutter fill -> export (rig_v6: rig_v6uv.blend with the gated clips) -> prepare
# -> LOD1 (build_actor_lods) -> shadow tuck -> tiers (region_variants: sprite_a/b/c, wings alpha-blended) ->
# far LODs and textures (lod_repair_claude/scripts/repair.py ladder) -> winding check. --install: tools/install_model.py.
# Usage: TOK=<lease> scripts/build_runtime.sh [--install]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; repo="$(cd -- "$here/../../.." && pwd)"
cd "$here"
CS=../claude_shared
[ "${SKIP_COMPOSE:-}" ] || python3 scripts/compose_sprite.py | grep -E "REGIONS|COMPOSED"
python3 $CS/gutter_fill.py texturing/sprite_body_upload.glb textures/sprite_basecolor_2k_graded.png textures/sprite_normal_1k.png \
    textures/sprite_orm_1k.png textures/sprite_region_mask.png --in-place | tail -1
[ -f work/rig_v6.blend ] || cp work/rig_v6uv.blend work/rig_v6.blend
[ "${SYNC:-}" ] && scripts/step.sh sync_actions.py work/rig_v5.blend work/rig_v6.blend
scripts/step.sh export_runtime.py | grep -E "SOCKETS|EXPORTED" | cut -c1-300
python3 "$repo/tools/prepare_actor_glb.py" export/xeen_sprite_lod0.glb export/xeen_sprite_runtime_lod0.glb
scripts/step.sh run_tool.py tools/build_actor_lods.py "$here/export/xeen_sprite_runtime_lod0.glb" \
  "$here/export/xeen_sprite_lods.glb" --mesh-node Sprite | grep "LOD triangles" || true
python3 scripts/shrink_shadow_lods.py export/xeen_sprite_lods.glb export/xeen_sprite_lods_shadowfix.glb
python3 $CS/region_variants.py export/xeen_sprite_lods_shadowfix.glb export/xeen_sprite_tiers.glb textures/sprite_ramps.json \
  --extra Sprite openyamm_specular=0 --extra Sprite pbr.metallicFactor=0 \
  --extra Wing openyamm_specular=0 --extra Wing pbr.metallicFactor=0 --extra Wing "material.alphaMode=\"BLEND\"" \
  --extra Wing material.doubleSided=true --extra Wing openyamm_edge_darkening=0
rm -f export/xeen_sprite_lods.geometry.glb
cp export/xeen_sprite_tiers.glb export/xeen_sprite.glb
# far LODs (LOD playbook: repair.py ladder, project copy in lodrepair/; Blender through the wrapper in audit.sh)
LV=$repo/level_generation/creatures/lod_repair_claude/venv/bin/python
LOD_REPAIR_PYTHON=$LV LOD_RENDER_CULL=1 $LV lodrepair/scripts/repair.py --source export/xeen_sprite.glb xeen_sprite | tail -1
cp export/xeen_sprite.glb export/xeen_sprite_prelod.glb && cp lodrepair/export/xeen_sprite.glb export/xeen_sprite.glb
python3 "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/xeen_sprite.glb | tail -3
if [[ "${1:-}" == "--install" ]]; then
  python3 "$repo/tools/install_model.py" export/xeen_sprite.glb --world xeen
fi
ls -la export/xeen_sprite.glb
