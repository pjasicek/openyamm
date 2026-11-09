#!/usr/bin/env bash
# After the paid paints: reweight -> export -> clips -> flap keys -> helpers -> prepare -> LODs -> shadow fix -> ramps -> floor -> winding [-> install]. Usage: TOKEN=<lease> scripts/rebuild.sh [--install]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; repo="$(cd -- "$here/../../.." && pwd)"; cd "$here"
rel=level_generation/creatures/$(basename "$here"); G="$repo/level_generation/creatures/claude_shared/gltf_venv/bin/python"; n=mm9_ghoul; N=Ghoul
B() { local out log; out=$(cd "$repo" && tools/run_creature_blender.sh --token "$TOKEN" "$@" 2>&1) || true
      log=$(echo "$out" | grep -o '/tmp/openyamm-creature-blender-[A-Za-z0-9]*\.log' | head -1)
      if grep -q "Error: script failed\|Traceback" "$log"; then grep -A12 Traceback "$log" | tail -14; echo "STEP FAILED: $1"; exit 1; fi
      grep -E "^(FLAP|PLUG|LINING|LIFT|EXPORTED)" "$log" | cut -c1-200 || true; }
B "$rel/scripts/reweight_ghoul.py" "$here/work/uv_v2.blend" "$here/work/uv_v3.blend"
B "$rel/scripts/export_ghoul.py" "$here/work/uv_v3.blend" "$here/work/ghoul_body_tex.glb" ${BASEC:-ghoul_basecolor_final.png} ghoul_head_basecolor_final.png ${NORMC:-ghoul_normal_soft.png} ${ORMC:-ghoul_metal_rough_1k.png} ghoul_head_normal_soft.png ghoul_head_metal_rough_1k.png
"$G" scripts/clips_mm9.py work/ghoul_body_tex.glb work/ghoul_clips0.glb scripts/roles_ghoul.json work/clips.json 2>&1 | grep -v Unexpected | cut -c1-200 | tail -1
"$G" scripts/flap_keys.py work/ghoul_clips0.glb work/ghoul_flap.glb 2>&1 | grep -E "FLAPKEYS|Traceback|Error" | cut -c1-200
"$G" scripts/half_keys.py work/ghoul_flap.glb work/ghoul_clips1.glb 2>&1 | tail -1
if [ -f scripts/clip_fix.sh ]; then source scripts/clip_fix.sh; else cp work/ghoul_clips1.glb work/ghoul_final_clips.glb; fi
"$G" "$repo/tools/prepare_actor_glb.py" work/ghoul_final_clips.glb export/${n}_runtime_lod0.glb 2>&1 | tail -2 | cut -c1-160
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/${n}_runtime_lod0.glb" "$here/export/${n}_lods.glb" --mesh-node $N --max-influences 4 2>&1 | grep -E "LOD triangles|Error"
"$G" scripts/shrink_shadow_lods.py export/${n}_lods.glb export/${n}_lods_shadowfix.glb $N 2>&1 | tail -1 | cut -c1-160
"$G" ../claude_shared/region_variants.py export/${n}_lods_shadowfix.glb export/${n}_skins0.glb textures/ghoul_ramps.json \
  --extra Ghoul openyamm_specular=0 --extra Ghoul pbr.metallicFactor=0 2>&1 | tail -1 | cut -c1-160
"$G" ../claude_shared/floor/floor_fix.py export/${n}_skins0.glb work/floored.glb $(cat scripts/floor_ops.txt) --ground-death Death Dead 2>&1 | tail -2 | cut -c1-200
"$G" scripts/smooth_lift.py export/${n}_skins0.glb work/floored.glb export/${n}.glb Death Death2 Walking 2>&1 | grep -E "LIFT|Traceback|Error" | cut -c1-140
"$G" scripts/fix_winding.py export/${n}.glb work/wound.glb 2>&1 | tail -1 | cut -c1-120; mv work/wound.glb export/${n}.glb
rm -f export/${n}_lods.geometry.glb
"$G" "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/${n}.glb | tail -1
"$G" ../claude_shared/bone_length_audit.py export/${n}.glb 2>&1 | grep -v Unexpected | tail -3
if [[ "${1:-}" == "--install" ]]; then python3 "$repo/tools/install_model.py" export/${n}.glb --world mm9; fi
ls -la export/${n}.glb
