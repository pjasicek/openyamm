#!/usr/bin/env bash
# reweight -> finish -> export -> clips -> fingers -> corrections -> helpers -> skirt legs -> skirt -> axe hide -> arm bumps -> head clear -> axe lift, no LODs. Project folder.
set -uo pipefail
here="$PWD"; G=../claude_shared/gltf_venv/bin/python
Q() { "$@" 2>&1 | grep -v "Unexpected value\|RuntimeWarning" ; }
if [[ -z "${SKIP_EXPORT:-}" ]]; then
F='^(REWEIGHT|SKIRT|ERR|Traceback)' W=170 scripts/run.sh reweight.py "$here/work/uv_v1.blend" "$here/work/rew_v1.blend"
F='^(FINISH|ERR)' W=170 scripts/run.sh finish_dwarf.py "$here/work/rew_v1.blend" "$here/work/final_v1.blend" "$here/work/hand_poses.json"
F='^(EXPORTED)' scripts/run.sh export_dwarf.py "$here/work/final_v1.blend" "$here/work/dwarf_body.glb" | cut -c1-120
fi
Q "$G" scripts/clips_mm9.py work/dwarf_body.glb work/dwarf_clips0.glb scripts/roles_dwarf.json work/clips.json | tail -1 | cut -c1-120
Q "$G" scripts/finger_keys.py work/dwarf_clips0.glb work/dwarf_clips1.glb work/hand_poses.json | tail -1
cp work/dwarf_clips1.glb work/dwarf_clips1d.glb
if [[ -f scripts/corrections.sh ]]; then source scripts/corrections.sh; fi
Q "$G" scripts/half_keys.py work/dwarf_clips1d.glb work/dwarf_clips2.glb | tail -1
Q "$G" scripts/skirt_leg_keys.py work/dwarf_clips2.glb work/dwarf_clips2l.glb | tail -1
Q "$G" scripts/skirt_keys.py work/dwarf_clips2l.glb work/dwarf_clips3.glb work/skirt_report.json | tail -1
Q "$G" scripts/axe_hide.py work/dwarf_clips3.glb work/dwarf_clips4.glb | tail -1
if [[ -s scripts/arm_jobs.txt ]]; then
  Q "$G" scripts/arm_bump.py work/dwarf_clips4.glb work/dwarf_clips5.glb $(cat scripts/arm_jobs.txt) | grep -E "BUMP|Traceback|Error" | cut -c1-170
else cp work/dwarf_clips4.glb work/dwarf_clips5.glb; fi
Q "$G" scripts/head_clear.py work/dwarf_clips5.glb work/dwarf_clips6.glb | grep -E "max_f': 0\.[1-9]|HEAD|Traceback|Error" | cut -c1-170
Q "$G" scripts/axe_lift.py work/dwarf_clips6.glb work/dwarf_final_clips.glb Fidget AttackMelee3 | grep -E "AXE|Traceback|Error" | cut -c1-170
