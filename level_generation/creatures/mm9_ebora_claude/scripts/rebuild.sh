#!/usr/bin/env bash
# Mesh + textures -> GLB -> clips -> arm corrections -> half joints -> runtime (LODs, tiers, floor, sockets, mirror).
# Usage (project folder): scripts/rebuild.sh [--install]. Never re-runs the UV (work/uv_frozen.npz, paid paint).
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; repo="$(cd -- "$here/../../.." && pwd)"; cd "$here"
n=mm9_ebora; G="$repo/level_generation/creatures/claude_shared/gltf_venv/bin/python"; L=../claude_shared
"$G" -W ignore scripts/weights.py work/asm.npz work/heat.npz work/rig.json work/finger_labels.npy work/bodyw.npz | tail -1
"$G" -W ignore scripts/bind.py work/rig.json source/ebora/ebora.glb work/asm.npz work/bind.json | tail -1
"$G" -W ignore - <<'PY'
import json, numpy as np
B = json.load(open('work/bind.json')); json.dump({'joints': B['wing_heads']}, open('work/wing_rig.json', 'w'))
A = np.load('work/asm.npz'); Wb = np.load('work/bodyw.npz'); m = A['comp'] == 0
np.savez('work/wing_body.npz', co=A['co'][m], W=Wb['W'][m], names=Wb['names'])
PY
"$G" -W ignore scripts/build_wings.py work/wing_rig.json work/wing_body.npz work/wings.npz | cut -c1-60
"$G" -W ignore scripts/merge.py work/asm.npz work/bodyw.npz work/wings.npz work/mesh_tex.npz work/uv_tex.npz
"$G" -W ignore scripts/fringe_lift.py work/mesh_tex.npz work/mesh_fr.npz | tail -1
"$G" -W ignore scripts/subdiv_face.py work/mesh_fr.npz work/mesh_sub.npz | tail -1
# mouth wider and fuller, nose broader and shorter (head fixes 3; vertex moves only). project_head.py keeps projecting on the
# unshaped work/mesh_sub.npz (dump_head.py), so the paint rides on the moved skin through the frozen UVs
"$G" -W ignore scripts/face_shape.py work/mesh_sub.npz work/mesh_shp.npz | tail -1
# back sides for the hair shell, fringe and side locks where their inside is ever in view (Concubine face and hair fix,
# 2026-11-01 evening: holes in the hair at the temples, a floating strand by the cheek); copies only, nothing moves
"$G" -W ignore scripts/hair_backs.py work/mesh_shp.npz work/mesh_hb.npz | tail -1
"$G" -W ignore scripts/build_glb.py work/mesh_hb.npz work/bind.json work/body.glb work/textures.json
"$G" -W ignore scripts/clips_mm9.py work/body.glb work/clips.glb scripts/roles_ebora.json work/clips.json | cut -c1-80
# arm corrections, group by group: clips cap sigma
prev=work/clips.glb; k=0
while read -r clips cap sig; do
  k=$((k + 1))
  "$G" -W ignore scripts/arm_clear.py work/clips.glb work/cl_c$k.glb --side L=' L ' --side R=' R ' --clips $clips --outer-only --max-deg $cap --sigma 2.0 2>&1 | grep -E "Traceback|Error" || true
  FADE=0.16 "$G" -W ignore scripts/arm_soft.py $prev work/cl_c$k.glb work/cl_a$k.glb $cap $sig $clips 2>&1 | grep -E "Traceback|Error" || true
  prev=work/cl_a$k.glb
done < scripts/arm_groups.txt
# Death/Dead: MM9's die2 lays the left forearm through the raised left wing fan: lift the arm 18 deg, eased over the clip
# (larger lifts cleared the fall too but failed the jitter gate)
AXIS=key "$G" -W ignore scripts/arm_lay.py $prev work/clips_arm0.glb "Bip01 L UpperArm" 18 0.0 1.1 | tail -1
"$G" -W ignore scripts/pleat_keys.py work/clips_arm0.glb work/clips_arm.glb | cut -c1-300
"$G" -W ignore scripts/half_keys.py work/clips_arm.glb work/half.glb | tail -1
"$G" -W ignore scripts/pleat_keys.py work/clips.glb work/clips_ref.glb | tail -0
"$G" -W ignore scripts/half_keys.py work/clips_ref.glb work/ref_half.glb | tail -1
"$G" -W ignore "$repo/tools/prepare_actor_glb.py" work/half.glb export/${n}_runtime_lod0.glb | tail -1
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/${n}_runtime_lod0.glb" "$here/export/${n}_lods.glb" --mesh-node Ebora --max-influences 4 2>&1 | grep -E "LOD triangles|Error"
"$G" -W ignore ../mm9_skeletonwarrior_claude/scripts/shrink_shadow_lods.py export/${n}_lods.glb export/${n}_lods_shadowfix.glb Ebora | tail -1
"$G" -W ignore scripts/tier_glb.py export/${n}_lods_shadowfix.glb export/${n}_skins.glb | tail -1
"$G" -W ignore scripts/fix_winding.py export/${n}_skins.glb export/${n}_skins2.glb | tail -1
"$G" -W ignore $L/floor/floor_fix.py export/${n}_skins2.glb export/${n}_floor.glb $(cat scripts/floor_ops.txt) 2>&1 | tail -2
"$G" -W ignore scripts/add_sockets.py export/${n}_floor.glb export/${n}_sock.glb | tail -1
"$G" -W ignore ../mm9_lich_claude/scripts/mirror_glb.py export/${n}_sock.glb export/${n}.glb | tail -1
rm -f export/${n}_lods.geometry.glb
"$G" -W ignore "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/${n}.glb | tail -1
"$G" -W ignore $L/bone_length_audit.py export/${n}.glb | tail -1
if [[ "${1:-}" == "--install" ]]; then python3 "$repo/tools/install_model.py" export/${n}.glb --world mm9; fi
ls -la export/${n}.glb
