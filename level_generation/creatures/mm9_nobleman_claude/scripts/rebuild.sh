#!/usr/bin/env bash
# After the paints: finish -> export -> clips -> foot, arm corrections -> half joints -> skirt -> prepare -> LODs -> shadow fix -> ramps, tier images -> floor -> winding [-> install] -> viewer. Project folder: scripts/rebuild.sh [--install]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; repo="$(cd -- "$here/../../.." && pwd)"; cd "$here"
G="$repo/level_generation/creatures/claude_shared/gltf_venv/bin/python"; n=mm9_nobleman; N=Nobleman; IN=${IN:-uv_v2.blend}
if [[ -z "${SKIP_EXPORT:-}" ]]; then
F='^(FINISH|ERR)|Traceback|Error' scripts/run.sh finish_nb.py "$here/work/$IN" "$here/work/final_v1.blend"
F='^(EXPORTED)|Traceback|Error' scripts/run.sh export_nb.py "$here/work/final_v1.blend" "$here/work/nb_body.glb" | cut -c80-
fi
Q() { "$@" 2>&1 | grep -v "Unexpected value\|RuntimeWarning" ; }
Q "$G" scripts/clips_mm9.py work/nb_body.glb work/nb_clips0.glb scripts/roles_nb.json work/clips.json | tail -1 | cut -c1-120
cp work/nb_clips0.glb work/nb_clips1.glb
if [[ -s scripts/foot_jobs.txt ]]; then Q "$G" scripts/foot_clear.py work/nb_clips1.glb work/nb_clips1b.glb $(cat scripts/foot_jobs.txt) | tail -2; mv work/nb_clips1b.glb work/nb_clips1.glb; fi
if [[ -s scripts/lift_jobs.txt ]]; then Q "$G" scripts/leg_lift.py work/nb_clips1.glb work/nb_clips1b.glb $(cat scripts/lift_jobs.txt) | tail -2; mv work/nb_clips1b.glb work/nb_clips1.glb; fi
if [[ -s scripts/arm_const.txt ]]; then Q "$G" scripts/arm_const.py work/nb_clips1.glb work/nb_clips1b.glb $(cat scripts/arm_const.txt) | tail -2; mv work/nb_clips1b.glb work/nb_clips1.glb; fi
if [[ -s scripts/armout_jobs.txt ]]; then Q "$G" scripts/arm_out.py work/nb_clips1.glb work/nb_clips1b.glb $(cat scripts/armout_jobs.txt) | tail -2; mv work/nb_clips1b.glb work/nb_clips1.glb; fi
Q "$G" scripts/half_keys.py work/nb_clips1.glb work/nb_clips2.glb | tail -1
Q "$G" scripts/skirt_keys.py work/nb_clips2.glb work/nb_clips3.glb work/skirt_report.json | tail -1
if [[ -s scripts/arm_jobs.txt ]]; then
  Q "$G" scripts/arm_bump.py work/nb_clips3.glb work/nb_final_clips.glb $(cat scripts/arm_jobs.txt) | grep -E "BUMP|Traceback|Error" | cut -c1-170
else cp work/nb_clips3.glb work/nb_final_clips.glb; fi
Q "$G" "$repo/tools/prepare_actor_glb.py" work/nb_final_clips.glb export/${n}_runtime_lod0.glb | tail -1 | cut -c1-160
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/${n}_runtime_lod0.glb" "$here/export/${n}_lods.glb" --mesh-node $N --max-influences 4 2>&1 | grep -E "LOD triangles|Error" | cut -c1-200
Q "$G" scripts/shrink_shadow_lods.py export/${n}_lods.glb export/${n}_lods_shadowfix.glb $N | tail -1 | cut -c1-160
Q "$G" ../claude_shared/region_variants.py export/${n}_lods_shadowfix.glb work/${n}_rv.glb textures/nb_ramps.json --extra Nobleman openyamm_specular=0 --extra Nobleman pbr.metallicFactor=0 | tail -1 | cut -c1-160
Q "$G" scripts/tier_images.py work/${n}_rv.glb export/${n}_skins.glb | tail -1 | cut -c1-160
Q "$G" ../claude_shared/floor/floor_fix.py export/${n}_skins.glb export/${n}.glb $(cat scripts/floor_ops.txt) --ground-death Death Dead | tail -2 | cut -c1-200
Q "$G" scripts/fix_winding.py export/${n}.glb work/wound.glb | tail -1 | cut -c1-120; mv work/wound.glb export/${n}.glb
rm -f export/${n}_lods.geometry.glb
Q "$G" "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/${n}.glb | tail -1
if [[ "${1:-}" == "--install" ]]; then python3 "$repo/tools/install_model.py" export/${n}.glb --world mm9; fi
ls -la export/${n}.glb
Q "$G" scripts/viewer_tiers.py | grep -E "Error|Traceback" || true
python3 scripts/make_viewer_manifest.py ${REV:-r1} "nb_a=Baron=review/viewer/nb_a.glb" "nb_b=Viscount=review/viewer/nb_b.glb" "nb_c=Count=review/viewer/nb_c.glb" | cut -c1-80
