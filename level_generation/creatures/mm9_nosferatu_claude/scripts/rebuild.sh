#!/usr/bin/env bash
# Mesh + textures -> GLB -> clips -> half joints -> fingers -> arm bumps -> robe -> runtime. Usage (project folder): scripts/rebuild.sh [--install]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; repo="$(cd -- "$here/../../.." && pwd)"; cd "$here"
. scripts/env.sh
n=mm9_nosferatu; G=$PYG; L=../claude_shared; M=work/uv_tex.npz; A=work/asm_final.npz
"$G" scripts/fit_rig.py $A source/n1/n1.glb work/rig.json 2>&1 | grep -E "Traceback|Error" || true
python3 -c "1" ; "$G" scripts/weights.py $A work/rig.json work/finger_labels.npy work/weights.npz | tail -1 | cut -c1-160
"$G" -W ignore scripts/build_glb.py $M work/weights.npz work/body.glb 2>&1 | tail -1
"$G" -W ignore scripts/clips_mm9.py work/body.glb work/clips.glb scripts/roles.json work/clips.json 2>&1 | grep -E "Traceback|Error" || true
cp work/clips.glb work/ref_clips.glb
"$G" -W ignore scripts/half_keys.py work/clips.glb work/half.glb 2>&1 | grep -E "Traceback|Error" || true
"$G" -W ignore scripts/finger_keys.py work/half.glb work/fing.glb 2>&1 | grep -E "Traceback|Error" || true
"$G" -W ignore scripts/robe_keys.py work/fing.glb work/robe.glb 2>&1 | grep -E "Traceback|Error" || true
cur=work/robe.glb
if [ -s scripts/arm_jobs.txt ]; then
  "$G" -W ignore scripts/arm_bump.py work/robe.glb work/arm.glb $(cat scripts/arm_jobs.txt) 2>&1 | grep -E "Traceback|Error|BUMP" | cut -c1-160 || true
  "$G" -W ignore scripts/half_keys.py work/arm.glb work/arm2.glb 2>&1 | grep -E "Traceback|Error" || true
  cur=work/arm2.glb
fi
"$G" -W ignore "$repo/tools/prepare_actor_glb.py" $cur export/${n}_runtime_lod0.glb 2>&1 | tail -1 | cut -c1-160
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/${n}_runtime_lod0.glb" "$here/export/${n}_lods.glb" --mesh-node Nosferatu --max-influences 4 2>&1 | grep -E "LOD triangles|Error"
"$G" -W ignore ../mm9_skeletonwarrior_claude/scripts/shrink_shadow_lods.py export/${n}_lods.glb export/${n}_lods_shadowfix.glb Nosferatu 2>&1 | tail -1 | cut -c1-160
"$G" -W ignore $L/region_variants.py export/${n}_lods_shadowfix.glb work/${n}_rv.glb textures/nos_ramps.json --extra Nosferatu openyamm_specular=0 --extra Nosferatu pbr.metallicFactor=0 2>&1 | tail -1 | cut -c1-160
"$G" -W ignore scripts/fix_winding.py work/${n}_rv.glb export/${n}_skins.glb 2>&1 | tail -1 | cut -c1-160
"$G" -W ignore $L/floor/floor_fix.py export/${n}_skins.glb export/${n}_floor.glb $(cat scripts/floor_ops.txt) 2>&1 | tail -2 | cut -c1-200
"$G" -W ignore scripts/robe_keys.py export/${n}_floor.glb export/${n}_robe2.glb 2>&1 | grep -E "Traceback|Error|ROBE"
"$G" -W ignore scripts/add_sockets.py export/${n}_robe2.glb export/${n}.glb 2>&1 | tail -1 | cut -c1-160
rm -f export/${n}_lods.geometry.glb
"$G" -W ignore "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/${n}.glb | tail -1
"$G" -W ignore $L/bone_length_audit.py export/${n}.glb | tail -3
if [[ "${1:-}" == "--install" ]]; then python3 "$repo/tools/install_model.py" export/${n}.glb --world mm9; fi
ls -la export/${n}.glb
