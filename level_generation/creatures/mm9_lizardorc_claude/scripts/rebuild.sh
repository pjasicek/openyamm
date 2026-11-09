#!/usr/bin/env bash
# weights -> final mesh -> clips -> fist -> arm bumps -> half keys -> runtime GLB. Project folder. Usage: scripts/rebuild.sh [--install]. Env SKIPBUMP=1
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; repo="$(cd -- "$here/../../.." && pwd)"; cd "$here"
. scripts/env.sh
n=mm9_lizardorc; L=../claude_shared
BUMPS=${BUMPS:-$(cat scripts/bumps.txt 2>/dev/null || true)}
"$G" scripts/weights_liz.py work/heat2.npz work/w2.npz 2>&1 | grep -E 'influences|Error|Trace' | cut -c1-120
"$G" scripts/assemble.py work/joined.npz work/w2.npz work/uv.npz work/final.npz work/final_w.npz scripts/tex_final.json 2>&1 | tail -1
"$G" scripts/build_glb.py work/final.npz work/final_w.npz work/body.glb 2>&1 | tail -1
"$G" scripts/clips_mm9.py work/body.glb work/raw_clips.glb scripts/roles_liz.json work/clips.json 2>&1 | tail -1 | cut -c1-80
"$G" scripts/finger_keys.py work/raw_clips.glb work/fist_clips.glb 2>&1 | tail -1
"$G" scripts/half_keys.py work/fist_clips.glb work/ref_half.glb 2>&1 | tail -1 | cut -c1-100
if [[ -z "${SKIPBUMP:-}" && -n "$BUMPS" ]]; then
  "$G" scripts/half_keys.py work/fist_clips.glb work/raw_half.glb 2>&1 | tail -1 | cut -c1-140
  "$G" scripts/arm_bump.py work/raw_half.glb work/bump_clips.glb $BUMPS 2>&1 | grep -E 'BUMP|Traceback|Error' | cut -c1-140
else cp work/fist_clips.glb work/bump_clips.glb; fi
"$G" scripts/tip_lift.py work/bump_clips.glb work/tip_clips.glb AttackMelee:R 2>&1 | grep -E 'TIP|Traceback|Error' | cut -c1-160
"$G" scripts/half_keys.py work/tip_clips.glb work/half_clips.glb 2>&1 | grep -E 'HALF|Traceback|Error' | cut -c1-140
"$G" scripts/flap_solve.py work/half_clips.glb work/final_clips.glb 2>&1 | grep -E "^[A-Z]" | cut -c1-200
"$G" "$repo/tools/prepare_actor_glb.py" work/final_clips.glb export/${n}_runtime_lod0.glb 2>&1 | tail -2 | cut -c1-140
env -u PYTHONPATH /snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/${n}_runtime_lod0.glb" "$here/export/${n}_lods.glb" --mesh-node LizardOrc --max-influences 4 2>&1 | grep -E "LOD triangles|Error"
"$G" scripts/shrink_shadow_lods.py export/${n}_lods.glb export/${n}_lods_shadowfix.glb LizardOrc 2>&1 | tail -1 | cut -c1-140
cp export/${n}_lods_shadowfix.glb export/${n}_skins.glb
if [[ -f textures/liz_ramps.json ]]; then "$G" $L/region_variants.py export/${n}_lods_shadowfix.glb export/${n}_skins0.glb textures/liz_ramps.json --extra Liz openyamm_specular=0 --extra Liz pbr.metallicFactor=0 2>&1 | tail -1 | cut -c1-140
"$G" ../mm9_skeleton_claude/scripts/drop_tier_ramps.py export/${n}_skins0.glb export/${n}_skins.glb _A 2>&1 | tail -1 | cut -c1-140; fi
"$G" $L/floor/floor_fix.py export/${n}_skins.glb export/${n}_floor0.glb $(cat scripts/floor_ops.txt) 2>&1 | tail -2 | cut -c1-200
# run 2: the corpse lies on its left pauldron, 16 cm up; grounding Death per key stopped the fall in one frame (79 mm/f2). Its own pass holds the
# raise over +-0.12 s and low-passes it, so the fall settles without a pop and never dips under the floor (the hold 0 of the living clips let it dip 4.5)
"$G" $L/floor/floor_fix.py export/${n}_floor0.glb export/${n}_floor.glb --ground-death Death Dead --smooth-hold 1 --smooth Death 0.12 2>&1 | tail -2 | cut -c1-200
"$G" scripts/fix_winding.py export/${n}_floor.glb export/${n}.glb 2>&1 | tail -1 | cut -c1-120
rm -f export/${n}_lods.geometry.glb
"$G" "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/${n}.glb | tail -1
if [[ "${1:-}" == "--install" ]]; then python3 "$repo/tools/install_model.py" export/${n}.glb --world mm9; fi
ls -la export/${n}.glb
