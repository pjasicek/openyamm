#!/usr/bin/env bash
# After the paints: finish -> export -> clips -> fingers -> helpers -> skirt -> dagger -> arm bumps -> prepare -> LODs -> shadow fix -> tier materials -> floor -> winding [-> install] -> viewer. Project folder: scripts/rebuild.sh [--install]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; repo="$(cd -- "$here/../../.." && pwd)"; cd "$here"
G="$repo/level_generation/creatures/claude_shared/gltf_venv/bin/python"; n=mm9_highwayman; N=Highwayman; IN=${IN:-uv_v2.blend}
if [[ -z "${SKIP_EXPORT:-}" ]]; then
F='^(FINISH|ERR)' scripts/run.sh finish_hw.py "$here/work/$IN" "$here/work/final_v1.blend" "$here/work/hand_poses.json"
F='^(EXPORTED)' scripts/run.sh export_hw.py "$here/work/final_v1.blend" "$here/work/hw_body.glb" | cut -c80-
fi
Q() { "$@" 2>&1 | grep -v "Unexpected value\|RuntimeWarning" ; }
Q "$G" scripts/clips_mm9.py work/hw_body.glb work/hw_clips0.glb scripts/roles_hw.json work/clips.json | tail -1 | cut -c1-120
Q "$G" scripts/finger_keys.py work/hw_clips0.glb work/hw_clips1.glb work/hand_poses.json | tail -1
Q "$G" scripts/arm_out.py work/hw_clips1.glb work/hw_clips1b.glb AttackRanged:L:-0.08:0.36:14 Cower:L:0.5:1.7:-14 JumpingDown:L:-0.15:0.95:-14 Death:L:0.55:1.2:-9 | tail -1
Q "$G" scripts/foot_clear.py work/hw_clips1b.glb work/hw_clips1c.glb Running BackpedalRun | tail -4
Q "$G" scripts/leg_lift.py work/hw_clips1c.glb work/hw_clips1d.glb Walking Backpedal | tail -4
Q "$G" scripts/half_keys.py work/hw_clips1d.glb work/hw_clips2.glb | tail -1
Q "$G" scripts/skirt_keys.py work/hw_clips2.glb work/hw_clips3.glb work/skirt_report.json | tail -1
Q "$G" scripts/dagger_hide.py work/hw_clips3.glb work/hw_clips4.glb | tail -1
if [[ -s scripts/arm_jobs.txt ]]; then
  Q "$G" scripts/arm_bump.py work/hw_clips4.glb work/hw_final_clips.glb $(cat scripts/arm_jobs.txt) | grep -E "BUMP|Traceback|Error" | cut -c1-170
else cp work/hw_clips4.glb work/hw_final_clips.glb; fi
Q "$G" "$repo/tools/prepare_actor_glb.py" work/hw_final_clips.glb export/${n}_runtime_lod0.glb | tail -1 | cut -c1-160
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
python3 scripts/make_viewer_manifest.py ${REV:-r1} "hw_a=Cutpurse=review/viewer/hw_a.glb" "hw_b=Burglar=review/viewer/hw_b.glb" "hw_c=Bandit=review/viewer/hw_c.glb" | cut -c1-80
