#!/usr/bin/env bash
# After the paid paints: export -> clips -> corrections -> prepare -> LODs -> shadow fix -> ramps -> torso tiers -> floor -> winding [-> install]. Usage: TOKEN=<lease> scripts/rebuild.sh [--install]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; repo="$(cd -- "$here/../../.." && pwd)"; cd "$here"
rel=level_generation/creatures/$(basename "$here"); G="$repo/level_generation/creatures/claude_shared/gltf_venv/bin/python"; n=mm9_zombie; N=Zombie
B() { local out log; out=$(cd "$repo" && tools/run_creature_blender.sh --token "$TOKEN" "$@" 2>&1) || true
      log=$(echo "$out" | grep -o '/tmp/openyamm-creature-blender-[A-Za-z0-9]*\.log' | head -1)
      if grep -q "Error: script failed\|Traceback" "$log"; then grep -A12 Traceback "$log" | tail -14; echo "STEP FAILED: $1"; exit 1; fi
      grep -E "^(TATTER|ARMPIT|REPACK|WELD|PLUG|LINING|LIFT|EXPORTED)" "$log" | cut -c1-200 || true; }
B "$rel/scripts/reweight_tatter.py" "$here/work/uv_v2.blend" "$here/work/uv_v3.blend"
B "$rel/scripts/export_zombie.py" "$here/work/uv_v3.blend" "$here/work/zombie_body_tex.glb" zombie_basecolor_final.png zombie_head_basecolor_final.png zombie_normal_soft.png zombie_orm_rp.png zombie_head_normal_1k.png zombie_head_metal_rough_1k.png
"$G" scripts/clips_mm9.py work/zombie_body_tex.glb work/zombie_clips.glb scripts/roles_zombie.json work/clips.json 2>&1 | grep -v Unexpected | cut -c1-200
"$G" scripts/clips_mm9.py work/zombie_body_tex.glb work/zombie_clips_raw.glb scripts/roles_zombie_raw.json work/clips_raw.json 2>&1 | grep -c CLIPS >/dev/null
"$G" scripts/arm_bump.py work/zombie_clips.glb work/zombie_final_clips.glb AttackMelee:R AttackMelee:L AttackMelee2:L AttackMelee2:R:0.2 AttackRanged:L:0.2 AttackRanged2:R AttackRanged2:L 2>&1 | grep -E "BUMP|DEPTH|SIGNS|Traceback|Error" | cut -c1-170
"$G" "$repo/tools/prepare_actor_glb.py" work/zombie_final_clips.glb export/${n}_runtime_lod0.glb 2>&1 | tail -2 | cut -c1-160
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/${n}_runtime_lod0.glb" "$here/export/${n}_lods.glb" --mesh-node $N --max-influences 4 2>&1 | grep -E "LOD triangles|Error"
"$G" scripts/shrink_shadow_lods.py export/${n}_lods.glb export/${n}_lods_shadowfix.glb $N 2>&1 | tail -1 | cut -c1-160
"$G" ../claude_shared/region_variants.py export/${n}_lods_shadowfix.glb export/${n}_skins0.glb textures/zombie_ramps.json \
  --extra Zombie openyamm_specular=0 --extra Zombie pbr.metallicFactor=0 2>&1 | tail -1 | cut -c1-160
"$G" scripts/torso_variants.py export/${n}_skins0.glb export/${n}_skins.glb 2>&1 | grep -v Unexpected | tail -2 | cut -c1-200
"$G" ../claude_shared/floor/floor_fix.py export/${n}_skins.glb export/${n}.glb $(cat scripts/floor_ops.txt) --ground-death Death Dead 2>&1 | tail -2 | cut -c1-200
"$G" scripts/fix_winding.py export/${n}.glb work/wound.glb 2>&1 | tail -1 | cut -c1-120; mv work/wound.glb export/${n}.glb
rm -f export/${n}_lods.geometry.glb
"$G" "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/${n}.glb | tail -1
if [[ "${1:-}" == "--install" ]]; then python3 "$repo/tools/install_model.py" export/${n}.glb --world mm9; fi
ls -la export/${n}.glb
