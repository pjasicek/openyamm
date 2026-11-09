#!/usr/bin/env bash
# Runtime GLB: work/skel_final_clips.glb -> prepare -> LODs -> shadow fix -> tier skins (region ramps, tier A = the paint) -> floor -> eye glow -> winding [-> install --world mm9].
# Usage (project folder): scripts/build_runtime.sh [--install]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; repo="$(cd -- "$here/../../.." && pwd)"; cd "$here"
n=mm9_skeleton; N=Skel; G="$repo/level_generation/creatures/claude_shared/gltf_venv/bin/python"
"$G" "$repo/tools/prepare_actor_glb.py" work/skel_final_clips.glb export/${n}_runtime_lod0.glb 2>&1 | tail -1
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/${n}_runtime_lod0.glb" "$here/export/${n}_lods.glb" --mesh-node $N --max-influences 4 2>&1 | grep -E "LOD triangles|Error"
"$G" scripts/shrink_shadow_lods.py export/${n}_lods.glb export/${n}_lods_shadowfix.glb $N 2>&1 | tail -1
"$G" scripts/fix_lod_winding.py export/${n}_lods_shadowfix.glb export/${n}_lods_wind.glb 2>&1 | tail -1
"$G" ../claude_shared/region_variants.py export/${n}_lods_wind.glb export/${n}_skins0.glb textures/skel_ramps.json \
  --extra Skel openyamm_specular=0 --extra Skel pbr.metallicFactor=0 2>&1 | tail -1
"$G" scripts/drop_tier_ramps.py export/${n}_skins0.glb export/${n}_skins.glb _A 2>&1 | tail -1
F=../claude_shared/floor/floor_fix.py
"$G" $F export/${n}_skins.glb export/${n}_floor.glb $(cat scripts/floor_ops.txt) --ground-death Death Dead 2>&1 | tail -2
"$G" ../claude_shared/emission.py export/${n}_floor.glb export/${n}_e1.glb --material SkelHead_A --mask textures/skel_eye_mask_a.png --color 0.25,1.0,0.1 --strength 1.1 --pulse 0.12,3.1 2>&1 | tail -1
"$G" ../claude_shared/emission.py export/${n}_e1.glb export/${n}.glb --material SkelHead_R --mask textures/skel_eye_mask_r.png --color 1.0,0.06,0.03 --strength 1.1 --pulse 0.12,3.1 2>&1 | tail -1
rm -f export/${n}_lods.geometry.glb
"$G" "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/${n}.glb | tail -6 || true
if [[ "${1:-}" == "--install" ]]; then python3 "$repo/tools/install_model.py" export/${n}.glb --world mm9; fi
ls -la export/${n}.glb
