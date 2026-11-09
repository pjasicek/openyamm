#!/usr/bin/env bash
# After the paint: neck fix -> head pass (face sharpen, hair rim roll) -> finish (linings, cap) -> export -> clips -> corrections -> half joints -> skirt -> prepare -> LODs ->
# shadow fix -> material extras -> floor -> winding [-> install] -> viewer. Project folder: scripts/rebuild.sh [--install]
# IN = the UV blend or a re-rig carried onto it (carry_uv.py); default work/uv_v2.blend (step_b.sh re-rig + carry_uv.py onto uv_v1).
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; repo="$(cd -- "$here/../../.." && pwd)"; cd "$here"
G="$repo/level_generation/creatures/claude_shared/gltf_venv/bin/python"; n=mm9_njam; N=Njam; IN=${IN:-uv_v2.blend}
if [[ -z "${SKIP_EXPORT:-}" ]]; then
F='^(NECK|ERR)|Traceback|Error' scripts/run.sh neck_fix_nj.py "$here/work/$IN" "$here/work/neck_v1.blend"
F='^(HEADPOST|ERR)|Traceback|Error' scripts/run.sh head_post_nj.py "$here/work/neck_v1.blend" "$here/work/headpost_v1.blend" "$here/work/head_v1.blend"
F='^(FINISH|LINING|CAP|ERR)|Traceback|Error' scripts/run.sh finish_nj.py "$here/work/headpost_v1.blend" "$here/work/final_v1.blend"
F='^(EXPORTED)|Traceback|Error' scripts/run.sh export_nj.py "$here/work/final_v1.blend" "$here/work/nj_body.glb" | cut -c80-
fi
Q() { "$@" 2>&1 | grep -v "Unexpected value\|RuntimeWarning" ; }
Q "$G" scripts/clips_mm9.py work/nj_body.glb work/nj_clips0.glb scripts/roles_nj.json work/clips.json | tail -1 | cut -c1-120
cp work/nj_clips0.glb work/nj_clips1.glb
if [[ -s scripts/foot_jobs.txt ]]; then Q "$G" scripts/foot_clear.py work/nj_clips1.glb work/nj_clips1b.glb $(cat scripts/foot_jobs.txt) | tail -2; mv work/nj_clips1b.glb work/nj_clips1.glb; fi
if [[ -s scripts/lift_jobs.txt ]]; then Q "$G" scripts/leg_lift.py work/nj_clips1.glb work/nj_clips1b.glb $(cat scripts/lift_jobs.txt) | tail -2; mv work/nj_clips1b.glb work/nj_clips1.glb; fi
if [[ -s scripts/arm_const.txt ]]; then Q "$G" scripts/arm_const.py work/nj_clips1.glb work/nj_clips1b.glb $(cat scripts/arm_const.txt) | tail -2; mv work/nj_clips1b.glb work/nj_clips1.glb; fi
if [[ -s scripts/armout_jobs.txt ]]; then Q "$G" scripts/arm_out.py work/nj_clips1.glb work/nj_clips1b.glb $(cat scripts/armout_jobs.txt) | tail -2; mv work/nj_clips1b.glb work/nj_clips1.glb; fi
if [[ -s scripts/armhold_jobs.txt ]]; then Q "$G" scripts/arm_hold.py work/nj_clips1.glb work/nj_clips1b.glb $(cat scripts/armhold_jobs.txt) | tail -2; mv work/nj_clips1b.glb work/nj_clips1.glb; fi
Q "$G" scripts/half_keys.py work/nj_clips1.glb work/nj_clips2.glb | tail -1
Q "$G" scripts/skirt_keys.py work/nj_clips2.glb work/nj_clips3.glb work/skirt_report.json | tail -1
if [[ -s scripts/arm_jobs.txt ]]; then
  Q "$G" scripts/arm_bump.py work/nj_clips3.glb work/nj_final_clips.glb $(cat scripts/arm_jobs.txt) | grep -E "BUMP|Traceback|Error" | cut -c1-170
else cp work/nj_clips3.glb work/nj_final_clips.glb; fi
Q "$G" "$repo/tools/prepare_actor_glb.py" work/nj_final_clips.glb export/mm9_njam_runtime_lod0.glb | tail -1 | cut -c1-160
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/mm9_njam_runtime_lod0.glb" "$here/export/mm9_njam_lods.glb" --mesh-node $N --max-influences 4 2>&1 | grep -E "LOD triangles|Error" | cut -c1-200
Q "$G" scripts/shrink_shadow_lods.py export/mm9_njam_lods.glb export/mm9_njam_lods_shadowfix.glb $N | tail -1 | cut -c1-160
Q "$G" scripts/set_material_extras.py export/mm9_njam_lods_shadowfix.glb export/mm9_njam_skins.glb openyamm_specular=0 pbr.metallicFactor=0 | tail -1 | cut -c1-160
Q "$G" ../claude_shared/floor/floor_fix.py export/mm9_njam_skins.glb export/mm9_njam.glb $(cat scripts/floor_ops.txt) --ground-death Death Dead | tail -2 | cut -c1-200
Q "$G" scripts/fix_winding.py export/mm9_njam.glb work/wound.glb | tail -1 | cut -c1-120; mv work/wound.glb export/mm9_njam.glb
Q "$G" scripts/add_sockets_nj.py export/mm9_njam.glb work/sock.glb | tail -1; mv work/sock.glb export/mm9_njam.glb
if [[ -e export/mm9_njam_lods.geometry.glb ]]; then rm export/mm9_njam_lods.geometry.glb; fi
Q "$G" "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/mm9_njam.glb | tail -1
if [[ "${1:-}" == "--install" ]]; then python3 "$repo/tools/install_model.py" export/mm9_njam.glb --world mm9; fi
ls -la export/mm9_njam.glb
python3 scripts/make_viewer_manifest.py ${REV:-r1} "nj_a=Njam the Meddler=export/mm9_njam.glb" | cut -c1-80
