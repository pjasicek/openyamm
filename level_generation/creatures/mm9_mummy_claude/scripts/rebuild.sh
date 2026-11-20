#!/usr/bin/env bash
# After the paints: weights + UVs -> GLB -> clips -> arm and band corrections -> runtime. Usage (project folder): TOKEN=<lease> scripts/rebuild.sh [--install]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; repo="$(cd -- "$here/../../.." && pwd)"; cd "$here"
n=mm9_mummy; G="$repo/level_generation/creatures/claude_shared/gltf_venv/bin/python"; L=../claude_shared
python3 scripts/weights.py work/joined.npz work/heat.npz work/rig.json work/finger_labels.npy work/weights.npz | tail -1
python3 scripts/assemble.py work/joined.npz work/weights.npz work/asm_final.npz --uv work/uv_final.npz --tex scripts/tex_a.json | tail -1
NOSTRIPS=1 python3 scripts/assemble.py work/joined.npz work/weights.npz work/asm_ns.npz | tail -1
"$G" scripts/build_glb.py work/asm_final.npz work/body.glb 2>&1 | tail -1
"$G" scripts/build_glb.py work/asm_ns.npz work/skin.glb 2>&1 | tail -1
"$G" scripts/clips_mummy.py work/skin.glb work/skin_raw_clips.glb scripts/roles_mummy.json work/clips.json 2>&1 | tail -1 | cut -c1-80
"$G" scripts/arm_clear.py work/skin_raw_clips.glb work/skin_clips.glb --side L=' L ' --side R=' R ' --clips AttackMelee,AttackMelee2,AttackRanged,Death --outer-only --max-deg 22 --sigma 2.0 2>&1 | grep ARMCLEAR | cut -c1-120
FADE=0.16 "$G" scripts/arm_soft.py work/skin_raw_clips.glb work/skin_clips.glb work/skin_soft.glb 22 0.09 AttackMelee,AttackMelee2,AttackRanged,Death 2>&1 | grep peak | cut -c1-80
"$G" scripts/copy_anim.py work/skin_soft.glb work/body.glb work/body_clips.glb 2>&1 | tail -1
"$G" scripts/band_sim.py work/body_clips.glb work/band_clips.glb 2>&1 | grep -E "BAND|Traceback|Error|band bind" | cut -c1-200
"$G" scripts/half_keys.py work/band_clips.glb work/final_clips.glb 2>&1 | grep -E "HALF|Traceback|Error" | cut -c1-200
"$G" "$repo/tools/prepare_actor_glb.py" work/final_clips.glb export/${n}_runtime_lod0.glb 2>&1 | tail -1
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/${n}_runtime_lod0.glb" "$here/export/${n}_lods.glb" --mesh-node Mummy --max-influences 4 2>&1 | grep -E "LOD triangles|Error"
"$G" ../mm9_skeletonwarrior_claude/scripts/shrink_shadow_lods.py export/${n}_lods.glb export/${n}_lods_shadowfix.glb Mummy 2>&1 | tail -1
"$G" scripts/tier_skins.py export/${n}_lods_shadowfix.glb export/${n}_skins.glb 2>&1 | tail -1
"$G" $L/floor/floor_fix.py export/${n}_skins.glb export/${n}_floor.glb $(cat scripts/floor_ops.txt) --ground-death Death Dead 2>&1 | tail -2
"$G" ../mm9_lich_claude/scripts/mirror_glb.py export/${n}_floor.glb export/${n}.glb 2>&1 | tail -1
rm -f export/${n}_lods.geometry.glb
"$G" "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/${n}.glb | tail -1
if [[ "${1:-}" == "--install" ]]; then python3 "$repo/tools/install_model.py" export/${n}.glb --world mm9; fi
ls -la export/${n}.glb
