#!/usr/bin/env bash
# MM6 female peasant fix chain on the original install (work/orig_mm6_pfem.glb, the source before this project):
# new Standing, Fidget and Hit from the Mixamo library, shoulders held, arms hung straight 10 deg out beside the
# skirt, sleeves following the upper arms, arms thickened with a taper (upper arm most, wrist untouched).
# The dumps come from scripts/dump_fbx_clip.py (Standard Idle, Weight Shift, Standing React Large From Front).
set -euo pipefail
cd "$(dirname "$0")/.."
SRC=work/orig_mm6_pfem.glb
SH="L/mixamorig:LeftShoulder/mixamorig:LeftArm R/mixamorig:RightShoulder/mixamorig:RightArm"
python3 scripts/retarget_idle.py $SRC work/pf_1.glb work/standard_idle.npz Standing
python3 scripts/retarget_idle.py work/pf_1.glb work/pf_2.glb work/weight_shift.npz Fidget
python3 scripts/retarget_idle.py work/pf_2.glb work/pf_3.glb work/react_front.npz Hit
python3 scripts/shoulder_fix.py work/pf_3.glb work/pf_4.glb --bones $SH --clips Standing Fidget Hit
ARMS="L/mixamorig:LeftArm/mixamorig:LeftForeArm/mixamorig:LeftHand/mixamorig:LeftHandMiddle1
R/mixamorig:RightArm/mixamorig:RightForeArm/mixamorig:RightHand/mixamorig:RightHandMiddle1"
python3 scripts/arm_pose.py work/pf_4.glb work/pf_5.glb --arms $ARMS --lat 10 10 9 --flex 8 0 --clips Standing Fidget
python3 scripts/sleeve_weights.py work/pf_5.glb work/pf_6.glb
python3 scripts/arm_thicken.py work/pf_6.glb export/mm6_pfem.glb --add 14 6 2 0
