#!/usr/bin/env bash
# After the paint: export -> clips -> corrections -> finger pose -> half joints -> skirt -> prepare -> LODs -> shadow fix -> metal from class maps ->
# floor -> winding [-> install] -> viewer manifest. Project folder: scripts/rebuild.sh [--install]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; repo="$(cd -- "$here/../../.." && pwd)"; cd "$here"
G="$repo/level_generation/creatures/claude_shared/gltf_venv/bin/python"; N=Kira; IN=${IN:-uv_v1.blend}
export PYTHONPATH=/usr/lib/python3/dist-packages
if [[ -z "${SKIP_EXPORT:-}" ]]; then
F='^(EXPORTED)|Traceback|Error' scripts/run.sh export_kira.py "$here/work/$IN" "$here/work/kira_body.glb" | cut -c80-
fi
Q() { "$@" 2>&1 | grep -v "Unexpected value\|RuntimeWarning" ; }
Q "$G" scripts/clips_mm9.py work/kira_body.glb work/kira_clips0.glb scripts/roles_kira.json work/clips.json | tail -1 | cut -c1-120
cp work/kira_clips0.glb work/kira_clips1.glb
if [[ -s scripts/arm_const.txt ]]; then Q "$G" scripts/arm_const.py work/kira_clips1.glb work/kira_clips1b.glb $(cat scripts/arm_const.txt) | tail -2; mv work/kira_clips1b.glb work/kira_clips1.glb; fi
if [[ -s scripts/armout_jobs.txt ]]; then Q "$G" scripts/arm_out.py work/kira_clips1.glb work/kira_clips1b.glb $(cat scripts/armout_jobs.txt) | tail -2; mv work/kira_clips1b.glb work/kira_clips1.glb; fi
Q "$G" scripts/finger_pose.py work/kira_clips1.glb work/kira_clips1b.glb | tail -1 | cut -c1-160; mv work/kira_clips1b.glb work/kira_clips1.glb
Q "$G" scripts/half_keys.py work/kira_clips1.glb work/kira_clips2.glb | tail -1
Q "$G" scripts/skirt_keys.py work/kira_clips2.glb work/kira_clips3.glb work/skirt_report.json | tail -1
if [[ -s scripts/arm_jobs.txt ]]; then
  Q "$G" scripts/arm_bump.py work/kira_clips3.glb work/kira_final_clips.glb $(cat scripts/arm_jobs.txt) | grep -E "BUMP|Traceback|Error" | cut -c1-170
else cp work/kira_clips3.glb work/kira_final_clips.glb; fi
Q "$G" "$repo/tools/prepare_actor_glb.py" work/kira_final_clips.glb export/mm9_kira_runtime_lod0.glb | tail -1 | cut -c1-160
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/mm9_kira_runtime_lod0.glb" "$here/export/mm9_kira_lods.glb" --mesh-node $N --max-influences 4 2>&1 | grep -E "LOD triangles|Error" | cut -c1-200
Q "$G" scripts/shrink_shadow_lods.py export/mm9_kira_lods.glb export/mm9_kira_lods_shadowfix.glb $N | tail -1 | cut -c1-160
Q "$G" ../claude_shared/material_classes_to_orm.py export/mm9_kira_lods_shadowfix.glb export/mm9_kira_metal.glb \
  --classes textures/kira_body_material_classes.png --head-classes textures/kira_head_material_classes.png --report work/orm_report.json | tail -2 | cut -c1-200
Q "$G" ../claude_shared/floor/floor_fix.py export/mm9_kira_metal.glb export/mm9_kira.glb $(cat scripts/floor_ops.txt) --ground-death Death Dead | tail -2 | cut -c1-200
Q "$G" scripts/fix_winding.py export/mm9_kira.glb work/wound.glb | tail -1 | cut -c1-120; mv work/wound.glb export/mm9_kira.glb
if [[ -e export/mm9_kira_lods.geometry.glb ]]; then rm export/mm9_kira_lods.geometry.glb; fi
Q "$G" "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/mm9_kira.glb | tail -1
if [[ "${1:-}" == "--install" ]]; then python3 "$repo/tools/install_model.py" export/mm9_kira.glb --world mm9; fi
ls -la export/mm9_kira.glb
