#!/usr/bin/env bash
# Mesh + textures -> GLB -> clips -> half joints -> panels -> runtime. Usage (project folder): TOKEN=<lease> scripts/rebuild.sh [--install]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; repo="$(cd -- "$here/../../.." && pwd)"; cd "$here"
n=mm9_evilsorcerer; G="$repo/level_generation/creatures/claude_shared/gltf_venv/bin/python"; L=../claude_shared; M=work/uv_tex.npz
python3 scripts/weights.py work/asm3.npz work/heat.npz work/rig.json work/finger_labels.npy work/weights.npz | tail -1 | cut -c1-160
"$G" -W ignore scripts/build_glb.py $M work/weights.npz work/body.glb 2>&1 | tail -1
"$G" -W ignore scripts/clips_es.py work/body.glb work/clips.glb scripts/roles_es.json work/clips.json 2>&1 | grep -E "Traceback|Error" || true
"$G" -W ignore scripts/arm_out.py work/clips.glb work/clips_o.glb R:7 2>&1 | grep -E "Traceback|Error" || true
# arm corrections, group by group: clips cap sigma
prev=work/clips_o.glb; k=0
while read -r clips cap sig; do
  k=$((k + 1))
  "$G" -W ignore scripts/arm_clear.py work/clips_o.glb work/cl_c$k.glb --side L=' L ' --side R=' R ' --clips $clips --outer-only --max-deg $cap --sigma 2.0 2>&1 | grep -E "Traceback|Error" || true
  FADE=0.16 "$G" -W ignore scripts/arm_soft.py $prev work/cl_c$k.glb work/cl_a$k.glb $cap $sig $clips 2>&1 | grep -E "Traceback|Error" || true
  prev=work/cl_a$k.glb
done <<'G_'
Fidget,Fidget2,Fidget3,Taunt,AttackMelee,Hit,Hit2,Death2,Backpedal 22 0.09
AttackRanged 14 0.13
AttackRanged2,ResurrectSpell 34 0.09
Death 30 0.11
G_
cp $prev work/clips_arm.glb
cur=work/clips_arm.glb
"$G" -W ignore scripts/half_keys.py $cur work/half.glb 2>&1 | grep -E "Traceback|Error|HALF"
"$G" -W ignore scripts/panel_keys.py work/half.glb work/panel.glb work/asm3.npz work/panel.json 2>&1 | grep -E "Traceback|Error" || true
"$G" -W ignore "$repo/tools/prepare_actor_glb.py" work/panel.glb export/${n}_runtime_lod0.glb 2>&1 | tail -1
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/${n}_runtime_lod0.glb" "$here/export/${n}_lods.glb" --mesh-node Sorcerer --max-influences 4 2>&1 | grep -E "LOD triangles|Error"
"$G" -W ignore ../mm9_skeletonwarrior_claude/scripts/shrink_shadow_lods.py export/${n}_lods.glb export/${n}_lods_shadowfix.glb Sorcerer 2>&1 | tail -1
"$G" -W ignore $L/region_variants.py export/${n}_lods_shadowfix.glb work/${n}_rv.glb textures/es_ramps.json --extra Sorcerer openyamm_specular=0 --extra Sorcerer pbr.metallicFactor=0 2>&1 | tail -1
"$G" -W ignore scripts/tier_images.py work/${n}_rv.glb export/${n}_skins.glb 2>&1 | tail -1
"$G" -W ignore scripts/fix_winding.py export/${n}_skins.glb export/${n}_skins2.glb 2>&1 | tail -1
"$G" -W ignore $L/floor/floor_fix.py export/${n}_skins2.glb export/${n}_floor.glb $(cat scripts/floor_ops.txt) --ground-death Death Dead 2>&1 | tail -2
"$G" -W ignore scripts/add_sockets.py export/${n}_floor.glb export/${n}_sock.glb 2>&1 | tail -1
"$G" -W ignore ../mm9_lich_claude/scripts/mirror_glb.py export/${n}_sock.glb export/${n}.glb 2>&1 | tail -1
rm -f export/${n}_lods.geometry.glb
"$G" -W ignore "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/${n}.glb | tail -1
if [[ "${1:-}" == "--install" ]]; then python3 "$repo/tools/install_model.py" export/${n}.glb --world mm9; fi
ls -la export/${n}.glb
