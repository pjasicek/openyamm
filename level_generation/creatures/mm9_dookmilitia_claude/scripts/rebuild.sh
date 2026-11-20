#!/usr/bin/env bash
# After the paints: finish -> export -> clips -> fingers -> corrections -> helpers -> skirt -> arm bumps -> prepare -> LODs -> shadow fix -> tier materials -> floor -> winding [-> install] -> viewer. Project folder: scripts/rebuild.sh [--install]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; repo="$(cd -- "$here/../../.." && pwd)"; cd "$here"
G="$repo/level_generation/creatures/claude_shared/gltf_venv/bin/python"; n=mm9_dookmilitia; N=DookMilitia; IN=${IN:-uv_v1.blend}
if [[ -z "${SKIP_EXPORT:-}" ]]; then
F='^(FINISH|ERR|BAR)' scripts/run.sh finish_dook.py "$here/work/$IN" "$here/work/final_v1.blend" "$here/work/hand_poses.json"
F='^(EXPORTED)' scripts/run.sh export_dook.py "$here/work/final_v1.blend" "$here/work/dook_body.glb" | cut -c80-
fi
Q() { "$@" 2>&1 | grep -v "Unexpected value\|RuntimeWarning" ; }
# run 2: skin weights smoothed at the neck, hood seam and clavicles (collapse gate); zones in weight_zones.txt, one per line
mapfile -t WZ < scripts/weight_zones.txt
Q "$G" scripts/weight_smooth.py work/dook_body.glb work/dook_body_ws.glb $(cat scripts/weight_keep.txt) "${WZ[@]}" | grep -E "ZONE|WEIGHTS|Error|Traceback"
Q "$G" scripts/clips_mm9.py work/dook_body_ws.glb work/dook_clips0.glb scripts/roles_dook.json work/clips.json | tail -1 | cut -c1-120
Q "$G" scripts/finger_keys.py work/dook_clips0.glb work/dook_clips1.glb work/hand_poses.json | tail -1
cp work/dook_clips1.glb work/dook_clips1d.glb
if [[ -s scripts/arm_out.txt ]]; then Q "$G" scripts/arm_out.py work/dook_clips1.glb work/dook_clips1b.glb $(cat scripts/arm_out.txt) | tail -1; else cp work/dook_clips1.glb work/dook_clips1b.glb; fi
if [[ -s scripts/foot_clear.txt ]]; then Q "$G" scripts/foot_clear.py work/dook_clips1b.glb work/dook_clips1c.glb $(cat scripts/foot_clear.txt) | tail -4; else cp work/dook_clips1b.glb work/dook_clips1c.glb; fi
if [[ -s scripts/leg_lift.txt ]]; then Q "$G" scripts/leg_lift.py work/dook_clips1c.glb work/dook_clips1d.glb $(cat scripts/leg_lift.txt) | tail -4; else cp work/dook_clips1c.glb work/dook_clips1d.glb; fi
Q "$G" scripts/half_keys.py work/dook_clips1d.glb work/dook_clips2.glb | tail -1
Q "$G" scripts/skirt_keys.py work/dook_clips2.glb work/dook_clips4.glb work/skirt_report.json | tail -1
if [[ -s scripts/arm_jobs.txt ]]; then
  Q "$G" scripts/arm_bump.py work/dook_clips4.glb work/dook_final_clips.glb $(cat scripts/arm_jobs.txt) | grep -E "BUMP|Traceback|Error" | cut -c1-170
else cp work/dook_clips4.glb work/dook_final_clips.glb; fi
if [[ -s scripts/sword_jobs.txt ]]; then      # run 2: the sword and its hand off the head (Cower)
  Q "$G" scripts/sword_clear.py work/dook_final_clips.glb work/dook_final_clips_s.glb $(cat scripts/sword_jobs.txt) | grep -E "CLEAR|Traceback|Error" | cut -c1-170
  mv work/dook_final_clips_s.glb work/dook_final_clips.glb
fi
Q "$G" "$repo/tools/prepare_actor_glb.py" work/dook_final_clips.glb export/${n}_runtime_lod0.glb | tail -1 | cut -c1-160
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/${n}_runtime_lod0.glb" "$here/export/${n}_lods.glb" --mesh-node $N --max-influences 4 2>&1 | grep -E "LOD triangles|Error" | cut -c1-200
Q "$G" scripts/shrink_shadow_lods.py export/${n}_lods.glb export/${n}_lods_shadowfix.glb $N | tail -1 | cut -c1-160
Q "$G" scripts/tier_materials.py export/${n}_lods_shadowfix.glb export/${n}_skins.glb | tail -1 | cut -c1-160
Q "$G" ../claude_shared/floor/floor_fix.py export/${n}_skins.glb export/${n}.glb $(cat scripts/floor_ops.txt) --ground-death Death Dead | tail -2 | cut -c1-200
Q "$G" scripts/fix_winding.py export/${n}.glb work/wound.glb | tail -1 | cut -c1-120; mv work/wound.glb export/${n}.glb
rm -f export/${n}_lods.geometry.glb
Q "$G" "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/${n}.glb | tail -1
if [[ "${1:-}" == "--install" ]]; then python3 "$repo/tools/install_model.py" export/${n}.glb --world mm9; fi
ls -la export/${n}.glb
Q "$G" scripts/viewer_tiers.py | grep -E "Error|Traceback" || true
python3 scripts/make_viewer_manifest.py ${REV:-r1} "dook_a=Half Orc Recruit=review/viewer/dook_a.glb" "dook_b=Half Orc Soldier=review/viewer/dook_b.glb" "dook_c=Half Orc Captain=review/viewer/dook_c.glb" | cut -c1-80
