#!/usr/bin/env bash
# master (rig weights + UVs) -> textured export -> MM9 clips -> half keys -> clip fixes -> prepare -> LODs -> shadow fix ->
# material extras -> floor -> winding -> bone audit [-> install]. Usage (project folder): TOKEN=<lease> scripts/rebuild.sh [--install]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; repo="$(cd -- "$here/../../.." && pwd)"; cd "$here"
rel=level_generation/creatures/$(basename "$here"); G="$repo/level_generation/creatures/claude_shared/gltf_venv/bin/python"; n=mm9_lesserdemon; N=LesserDemon
B() { local out log; out=$(cd "$repo" && tools/run_creature_blender.sh --token "$TOKEN" "$@" 2>&1) || true
      log=$(echo "$out" | grep -o '/tmp/openyamm-creature-blender-[A-Za-z0-9]*\.log' | head -1)
      if grep -q "Error: script failed\|Traceback" "$log"; then grep -A12 Traceback "$log" | tail -14; echo "STEP FAILED: $1"; exit 1; fi
      grep -E "^(LIFT|EXPORTED|REWEIGHT|SOLES|SUNK|CROTCH)" "$log" | cut -c1-200 || true; }
MASTER=${MASTER:-work/uv_v3.blend}
if [ -f scripts/reweight.py ] && [ -z "${SKIP_REWEIGHT:-}" ]; then B "$rel/scripts/reweight.py" "$here/$MASTER" "$here/work/master_w.blend"; fi; [ -f scripts/reweight.py ] && MASTER=work/master_w.blend
LIFT=1.368 B "$rel/scripts/export_demon.py" "$here/$MASTER" "$here/work/body_tex.glb" ldemon_basecolor_final.png ldemon_head_basecolor_final.png ldemon_normal_1k.png ldemon_metal_rough_1k.png ldemon_head_normal_1k.png ldemon_head_metal_rough_1k.png
"$G" scripts/clips_mm9.py work/body_tex.glb work/clips0.glb scripts/roles_demon.json work/clips.json 2>&1 | grep -v Unexpected | cut -c1-200 | tail -1
"$G" scripts/half_keys.py work/clips0.glb work/clips1.glb 2>&1 | tail -1
if [ -f scripts/clip_fix.sh ]; then source scripts/clip_fix.sh; else cp work/clips1.glb work/final_clips.glb; fi
"$G" "$repo/tools/prepare_actor_glb.py" work/final_clips.glb export/${n}_runtime_lod0.glb 2>&1 | tail -1 | cut -c1-160
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/${n}_runtime_lod0.glb" "$here/export/${n}_lods.glb" --mesh-node $N --max-influences 4 2>&1 | grep -E "LOD triangles|Error"
"$G" scripts/shrink_shadow_lods.py export/${n}_lods.glb export/${n}_lods_shadowfix.glb $N 2>&1 | tail -1 | cut -c1-160
"$G" scripts/set_material_extras.py export/${n}_lods_shadowfix.glb work/extras.glb openyamm_specular=0 pbr.metallicFactor=0
# the tail drags through the floor in MM9 (walk, run, ranged, hit): bent up from its own joints first, then the body
"$G" ../claude_shared/floor/floor_fix.py work/extras.glb work/floor_tail.glb --lift-joints Standing Walking Running Backpedal BackpedalRun Fidget Fidget2 Taunt Block AttackMelee AttackMelee2 AttackRanged DodgeLeft DodgeRight Hit Hit2 Death Dead --lift-only 'Xtail*,Bip01 ? Toe*' 2>&1 | grep -v Unexpected | tail -1 | cut -c1-120
"$G" ../claude_shared/floor/floor_fix.py work/floor_tail.glb export/${n}.glb $(cat scripts/floor_ops.txt) 2>&1 | grep -v Unexpected | tail -2 | cut -c1-200
"$G" scripts/fix_winding.py export/${n}.glb work/wound.glb 2>&1 | tail -1 | cut -c1-120; mv work/wound.glb export/${n}.glb
if [ -f export/${n}_lods.geometry.glb ]; then mv export/${n}_lods.geometry.glb work/; fi
"$G" "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/${n}.glb | tail -1
"$G" ../claude_shared/bone_length_audit.py export/${n}.glb 2>&1 | grep -v Unexpected | tail -2
if [[ "${1:-}" == "--install" ]]; then python3 "$repo/tools/install_model.py" export/${n}.glb --world mm9; fi
ls -la export/${n}.glb
