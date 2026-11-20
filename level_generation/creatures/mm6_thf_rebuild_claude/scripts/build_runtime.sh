#!/usr/bin/env bash
# Runtime GLB: weight passes -> textured export -> clips (MM9 roles, hands and daggers, helpers, skirt hinges, cloak chains) -> prepare -> LODs
# -> shadow fix -> tier variants (cloth region on the body set) -> floor -> winding [-> install].
# Usage (project folder): scripts/build_runtime.sh [--install]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; repo="$(cd -- "$here/../../.." && pwd)"; cd "$here"
export TOKEN=$(cat work/token); W=$here/work
G="$repo/level_generation/creatures/claude_shared/gltf_venv/bin/python"
Q() { "$@" 2>&1 | grep -v "Unexpected value\|RuntimeWarning" ; }
if [[ -z "${FROM_CLOAK:-}" ]]; then                # FROM_CLOAK=1: only the cloak keys again, on work/c5.glb of the last full run
scripts/B.sh smooth_band.py $W/final_v1.blend $W/final_s1.blend 14 0.2 0.50 0.74 8
scripts/B.sh smooth_band.py $W/final_s1.blend $W/final_v2.blend 1 0.2 0.52 0.64 4
scripts/B.sh export_thf.py $W/final_v2.blend $W/thf_body_tex.glb | grep -v LIFT
scripts/clips.sh work/thf_body_tex.glb work/thf_final_clips.glb > work/clips_log.txt
else
Q "$G" scripts/cloak_keys.py work/c5.glb work/thf_final_clips.glb work/rig_v1.blend.cloak.json work/cloak_report.json | grep -v "^lift\|^CAPS" | cut -c1-90 > work/clips_log_cloak.txt
fi
Q "$G" "$repo/tools/prepare_actor_glb.py" work/thf_final_clips.glb export/mm6_thf_runtime_lod0.glb | tail -1 | cut -c1-200
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/mm6_thf_runtime_lod0.glb" "$here/export/mm6_thf_lods.glb" --mesh-node Thief --max-influences 4 2>&1 | grep -E "LOD triangles|Error"
Q "$G" scripts/shrink_shadow_lods.py export/mm6_thf_lods.glb export/mm6_thf_lods_shadowfix.glb Thief | tail -1
Q "$G" ../claude_shared/region_variants.py export/mm6_thf_lods_shadowfix.glb work/tiers.glb textures/thf_ramps.json | tail -1
Q "$G" ../claude_shared/floor/floor_fix.py work/tiers.glb export/mm6_thf.glb $(cat scripts/floor_ops.txt) --ground-death Death Dead | tail -2 | cut -c1-200
Q "$G" scripts/shadow_tiny_parts.py export/mm6_thf.glb export/mm6_thf.glb | tail -1
Q "$G" "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/mm6_thf.glb | tail -1
if [[ "${1:-}" == "--install" ]]; then python3 "$repo/tools/install_model.py" export/mm6_thf.glb --world mm6 | tail -1; fi
ls -la export/mm6_thf.glb
