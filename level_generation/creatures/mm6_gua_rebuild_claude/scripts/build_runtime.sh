#!/usr/bin/env bash
# Runtime GLBs: final master -> textured export -> MM9 clips -> fist -> skirt keys -> helpers -> arm rests -> prepare -> LODs -> shadow fix
# -> tier variants (body + head set) -> floor -> winding [-> install]; the approved MM6 halberd attachment is re-seated on Xbase (place_halberd.py).
# Usage (project folder): TOKEN=<lease> scripts/build_runtime.sh [--install]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; repo="$(cd -- "$here/../../.." && pwd)"; cd "$here"
G="$repo/level_generation/creatures/claude_shared/gltf_venv/bin/python"
Q() { "$@" 2>&1 | grep -v "Unexpected value\|RuntimeWarning" ; }
scripts/B.sh export_gua.py "$here/work/final_v2.blend" "$here/work/gua_body_tex.glb"
Q "$G" scripts/clips_mm9.py work/gua_body_tex.glb work/gua_clips.glb scripts/roles_gua.json work/clips.json | tail -1 | cut -c1-200
Q "$G" scripts/finger_keys.py work/gua_clips.glb work/gua_fingers.glb work/hand_poses.json | tail -1
Q "$G" scripts/helper_keys.py work/gua_fingers.glb work/gua_h1.glb | tail -1
Q "$G" scripts/skirt_keys.py work/gua_h1.glb work/gua_skirt.glb work/skirt_keys.json | tail -1
cur=work/gua_skirt.glb; k=0
if [[ -f scripts/hand_rest_gua.txt ]]; then
  while IFS= read -r line; do
    [[ -z "$line" || "$line" == \#* ]] && continue
    k=$((k + 1)); nxt=work/gua_rest${k}.glb
    eval "$G scripts/hand_rest.py $cur $nxt $line" 2>&1 | grep -v "Unexpected value\|RuntimeWarning" | cut -c1-200
    cur=$nxt
  done < scripts/hand_rest_gua.txt
fi
Q "$G" scripts/dead_hold.py "$cur" work/gua_dead.glb | tail -1
Q "$G" scripts/helper_keys.py work/gua_dead.glb work/gua_final_clips.glb | tail -1
Q "$G" "$repo/tools/prepare_actor_glb.py" work/gua_final_clips.glb export/mm6_gua_runtime_lod0.glb | tail -1
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/mm6_gua_runtime_lod0.glb" "$here/export/mm6_gua_lods.glb" --mesh-node Guard --max-influences 4 2>&1 | grep -E "LOD triangles|Error"
Q "$G" scripts/shrink_shadow_lods.py export/mm6_gua_lods.glb export/mm6_gua_lods_shadowfix.glb Guard | tail -1
Q "$G" ../claude_shared/region_variants.py export/mm6_gua_lods_shadowfix.glb work/tiers.glb textures/gua_ramps.json \
  --extra Guard openyamm_specular=0 --extra Guard pbr.metallicFactor=0 | tail -1
Q "$G" ../claude_shared/floor/floor_fix.py work/tiers.glb export/mm6_gua.glb $(cat scripts/floor_ops.txt) --ground-death Death Dead | tail -2 | cut -c1-200
Q "$G" scripts/shadow_tiny_parts.py export/mm6_gua.glb export/mm6_gua.glb | tail -1
Q "$G" scripts/place_halberd.py export/mm6_gua.glb "$here/work/before_rebuild/mm6_gua_halberd.glb" export/mm6_gua_halberd.glb | tail -2
for f in mm6_gua mm6_gua_halberd; do Q "$G" "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/$f.glb | tail -1; done
if [[ "${1:-}" == "--install" ]]; then for f in mm6_gua mm6_gua_halberd; do python3 "$repo/tools/install_model.py" export/$f.glb --world mm6 | tail -1; done; fi
ls -la export/mm6_gua.glb export/mm6_gua_halberd.glb
