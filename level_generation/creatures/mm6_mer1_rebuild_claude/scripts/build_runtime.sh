#!/usr/bin/env bash
# Runtime GLB: neck weight ramp -> textured export -> clips (NOBLEMAN roles, FIGHTERBASE club blow, fist, helpers, robe chains) -> prepare -> LODs
# -> shadow fix -> tier variants (tunic region on the body set) -> floor -> winding -> club re-seated on Ybasesword [-> install both].
# Usage (project folder): scripts/build_runtime.sh [--install]     FROM_CLIPS=1: reuse work/mer_body_tex.glb
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; repo="$(cd -- "$here/../../.." && pwd)"; cd "$here"
export TOKEN=$(cat work/token); W=$here/work
G="$repo/level_generation/creatures/claude_shared/gltf_venv/bin/python"
Q() { "$@" 2>&1 | grep -v "Unexpected value\|RuntimeWarning\|Warn" ; }
if [[ -z "${FROM_CLIPS:-}" ]]; then
scripts/B.sh smooth_band.py $W/final_v1.blend $W/final_v2.blend 1,2 0.2 0.47 0.62 6
scripts/B.sh export_mer.py $W/final_v2.blend $W/mer_body_tex.glb | grep -v LIFT
fi
scripts/clips.sh work/mer_body_tex.glb work/mer_final_clips.glb > work/clips_log.txt 2>&1 || { cat work/clips_log.txt; exit 1; }; cut -c1-200 work/clips_log.txt
Q "$G" "$repo/tools/prepare_actor_glb.py" work/mer_final_clips.glb export/mm6_mer1_runtime_lod0.glb | tail -1 | cut -c1-200
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/mm6_mer1_runtime_lod0.glb" "$here/export/mm6_mer1_lods.glb" --mesh-node Merchant --max-influences 4 2>&1 | grep -E "LOD triangles|Error"
Q "$G" scripts/shrink_shadow_lods.py export/mm6_mer1_lods.glb export/mm6_mer1_lods_shadowfix.glb Merchant | tail -1
Q "$G" ../claude_shared/region_variants.py export/mm6_mer1_lods_shadowfix.glb work/tiers.glb textures/mer_ramps.json | tail -1
Q "$G" ../claude_shared/floor/floor_fix.py work/tiers.glb export/mm6_mer1.glb $(cat scripts/floor_ops.txt) --ground-death Death Dead | tail -2 | cut -c1-200
Q "$G" scripts/shadow_tiny_parts.py export/mm6_mer1.glb export/mm6_mer1.glb | tail -1
Q "$G" "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/mm6_mer1.glb | tail -1
Q "$G" scripts/place_club.py export/mm6_mer1.glb work/before_rebuild/mm6_mer1_club.glb export/mm6_mer1_club.glb | tail -2
Q "$G" "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/mm6_mer1_club.glb | tail -1
if [[ "${1:-}" == "--install" ]]; then
  python3 "$repo/tools/install_model.py" export/mm6_mer1.glb --world mm6 | tail -1
  python3 "$repo/tools/install_model.py" export/mm6_mer1_club.glb --world mm6 | tail -1
fi
ls -la export/mm6_mer1.glb export/mm6_mer1_club.glb
