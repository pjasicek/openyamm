#!/usr/bin/env bash
# weights -> final mesh -> clips -> arm bumps -> half keys -> runtime GLB. Project folder. Usage: scripts/rebuild.sh [--install]. Env: BUMPS (clip:side list), SKIPBUMP=1
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; repo="$(cd -- "$here/../../.." && pwd)"; cd "$here"
. scripts/env.sh
n=mm9_troglodyte; L=../claude_shared
BUMPS=${BUMPS:-$(cat scripts/bumps.txt)}
"$G" scripts/weights.py work/joined.npz work/heat2.npz work/finger_labels.npy work/w2.npz 2>&1 | grep -E 'influences|Error|Trace' | cut -c1-120
"$G" scripts/assemble.py work/joined.npz work/w2.npz work/uv.npz work/final.npz work/final_w.npz scripts/tex_final.json 2>&1 | tail -1
"$G" scripts/build_glb.py work/final.npz work/final_w.npz work/body.glb 2>&1 | tail -1
"$G" scripts/clips_mm9.py work/body.glb work/raw_clips.glb scripts/roles_trog.json work/clips.json 2>&1 | tail -1 | cut -c1-80
if [[ -z "${SKIPBUMP:-}" ]]; then
  "$G" scripts/half_keys.py work/raw_clips.glb work/raw_half.glb 2>&1 | tail -1 | cut -c1-140
  "$G" scripts/arm_bump.py work/raw_half.glb work/bump_clips.glb $BUMPS 2>&1 | grep -E 'BUMP|Traceback|Error' | cut -c1-140
else cp work/raw_clips.glb work/bump_clips.glb; fi
"$G" scripts/half_keys.py work/bump_clips.glb work/final_clips.glb 2>&1 | grep -E 'HALF|Traceback|Error' | cut -c1-140
"$G" "$repo/tools/prepare_actor_glb.py" work/final_clips.glb export/${n}_runtime_lod0.glb 2>&1 | tail -2 | cut -c1-140
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/${n}_runtime_lod0.glb" "$here/export/${n}_lods.glb" --mesh-node Troglodyte --max-influences 4 2>&1 | grep -E "LOD triangles|Error"
"$G" scripts/shrink_shadow_lods.py export/${n}_lods.glb export/${n}_lods_shadowfix.glb Troglodyte 2>&1 | tail -1 | cut -c1-140
"$G" $L/region_variants.py export/${n}_lods_shadowfix.glb export/${n}_skins0.glb textures/trog_ramps.json --extra Trog openyamm_specular=0 --extra Trog pbr.metallicFactor=0 2>&1 | tail -1 | cut -c1-140
"$G" ../mm9_skeleton_claude/scripts/drop_tier_ramps.py export/${n}_skins0.glb export/${n}_skins1.glb _B 2>&1 | tail -1 | cut -c1-140
"$G" scripts/tier_c.py export/${n}_skins1.glb export/${n}_skins.glb 2>&1 | tail -1 | cut -c1-200
"$G" $L/floor/floor_fix.py export/${n}_skins.glb export/${n}_floor.glb $(cat scripts/floor_ops.txt) --ground-death Death Dead 2>&1 | tail -2 | cut -c1-200
"$G" scripts/fix_winding.py export/${n}_floor.glb export/${n}_w.glb 2>&1 | tail -1 | cut -c1-120
"$G" scripts/tone.py export/${n}_w.glb export/${n}.glb 2>&1 | tail -1
rm -f export/${n}_lods.geometry.glb
"$G" "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/${n}.glb | tail -1
if [[ "${1:-}" == "--install" ]]; then python3 "$repo/tools/install_model.py" export/${n}.glb --world mm9; fi
ls -la export/${n}.glb
