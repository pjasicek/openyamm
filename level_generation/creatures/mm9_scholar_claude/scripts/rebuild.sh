#!/usr/bin/env bash
# Mesh + textures -> GLB -> clips -> arms -> half joints -> runtime. Usage (project folder): scripts/rebuild.sh [--install]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; repo="$(cd -- "$here/../../.." && pwd)"; cd "$here"
n=mm9_monk; G="$repo/level_generation/creatures/claude_shared/gltf_venv/bin/python"; L=../claude_shared; M=work/uv_tex.npz
python3 scripts/finish_mk.py >/dev/null; python3 scripts/tweak.py | tail -1
"$G" -W ignore scripts/fit_rig.py work/asm2.npz source/mk1/mk1.glb work/rig.json 2>&1 | tail -1 | cut -c1-120
python3 scripts/weights.py work/asm2.npz work/mm9.npz work/rig.json work/weights.npz | tail -1 | cut -c1-160
"$G" -W ignore scripts/build_glb.py $M work/weights.npz work/body.glb 2>&1 | tail -1
"$G" -W ignore scripts/clips_mk.py work/body.glb work/clips.glb scripts/roles_mk.json work/clips.json 2>&1 | grep -E "Traceback|Error" || true
"$G" -W ignore scripts/finger_rest.py work/clips.glb work/clips_f.glb 2>&1 | grep -E "Traceback|Error" || true
"$G" -W ignore scripts/arm_out.py work/clips_f.glb work/clips_o.glb R:${ARMDEG:-3} L:${ARMDEG:-3} 2>&1 | grep -E "Traceback|Error" || true
prev=work/clips_o.glb; k=0
while read -r clips cap sig; do
  [ -z "$clips" ] && continue
  k=$((k + 1))
  "$G" -W ignore scripts/arm_clear.py work/clips_o.glb work/cl_c$k.glb --side L=' L ' --side R=' R ' --clips $clips --outer-only --max-deg $cap --sigma 2.0 --root Spine 2>&1 | grep -E "Traceback|Error" || true
  FADE=0.16 "$G" -W ignore scripts/arm_soft.py $prev work/cl_c$k.glb work/cl_a$k.glb $cap $sig $clips 2>&1 | grep -E "Traceback|Error" || true
  prev=work/cl_a$k.glb
done < scripts/arm_jobs.txt
cp $prev work/clips_arm.glb
"$G" -W ignore scripts/half_keys.py work/clips_arm.glb work/half.glb 2>&1 | grep -E "Traceback|Error|HALF"
cur=work/half.glb
if [ -f scripts/cloth_keys.py ] && [ -z "${NOCLOTH:-}" ]; then "$G" -W ignore scripts/cloth_keys.py work/half.glb work/cloth.glb 2>&1 | tail -1; cur=work/cloth.glb; fi
"$G" -W ignore "$repo/tools/prepare_actor_glb.py" $cur export/${n}_runtime_lod0.glb 2>&1 | tail -1
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/${n}_runtime_lod0.glb" "$here/export/${n}_lods.glb" --mesh-node Monk --max-influences 4 2>&1 | grep -E "LOD triangles|Error"
"$G" -W ignore ../mm9_skeletonwarrior_claude/scripts/shrink_shadow_lods.py export/${n}_lods.glb export/${n}_lods_shadowfix.glb Monk 2>&1 | tail -1
"$G" -W ignore $L/region_variants.py export/${n}_lods_shadowfix.glb work/${n}_rv.glb textures/mk_ramps.json --extra Monk openyamm_specular=0 --extra Monk pbr.metallicFactor=0 2>&1 | tail -1
"$G" -W ignore scripts/tier_images.py work/${n}_rv.glb export/${n}_skins.glb 2>&1 | tail -1
"$G" -W ignore scripts/fix_winding.py export/${n}_skins.glb export/${n}_skins2.glb 2>&1 | tail -1
"$G" -W ignore $L/floor/floor_fix.py export/${n}_skins2.glb export/${n}_floor.glb $(cat scripts/floor_ops.txt) --ground-death Death Dead 2>&1 | tail -2
"$G" -W ignore scripts/add_sockets.py export/${n}_floor.glb export/${n}_sock.glb 2>&1 | tail -1
"$G" -W ignore ../mm9_lich_claude/scripts/mirror_glb.py export/${n}_sock.glb export/${n}.glb 2>&1 | tail -1
rm -f export/${n}_lods.geometry.glb
"$G" -W ignore "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/${n}.glb | tail -1
if [[ "${1:-}" == "--install" ]]; then python3 "$repo/tools/install_model.py" export/${n}.glb --world mm9; fi
ls -la export/${n}.glb
