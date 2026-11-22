#!/usr/bin/env bash
# Killer Sprite replayable chain (rig-first humanoid route of mm6_dru1_claude / mm6_natm_claude + flyer clips).
#   st_v1_parts -> step1 (cleanup) -> add_pinky -> arm rings + composed joints -> build_rig -> fingers -> rig_v1
#   -> retarget (Mixamo Floating/Swipe/2H cast/Taunt/Death fwd, set GetHit F1) -> flyer_clips -> twist -> weights
#   -> finger weights -> reduce -> open fingers -> wings -> wing flap + floor pass -> gates
# One-off prerequisites in work/: meshy_joints.json (meshy_joints.py on the Meshy rig), source_rest.json, proportions.json.
# Usage: TOK=<lease token> scripts/rebuild.sh   (STAGE=rig | anim | all)
set -euo pipefail
cd "$(dirname "$0")/.."
S=scripts/step.sh
MX=/home/pjasicek/github/OpenYAMM/anim_library/mixamo
L=/home/pjasicek/github/OpenYAMM/anim_library/humanoid_set
STAGE=${STAGE:-all}
if [ "$STAGE" = all ] || [ "$STAGE" = rig ]; then
$S step1_clean.py work/st_v1_parts.blend work/step1_raw.blend
EDGE_IN=-0.5 SPREAD=24 PINKY_LEN=0.72 $S add_pinky.py work/step1_raw.blend work/step1.blend
$S arm_rings.py work/step1.blend | grep -E "^(ARM|ANKLE)"
python3 scripts/compose_joints_sprite.py
rm -f work/finger_joints.json
$S build_rig.py | grep -E "^RIG"
$S fit_fingers.py work/rig_v1.blend | grep FINGERFIT
$S finger_joints.py work/rig_v1.blend >/dev/null
$S build_rig.py | grep -E "^(RIG|HAND)"
$S hand_frame_check.py work/rig_v1.blend
fi
if [ "$STAGE" = all ] || [ "$STAGE" = anim ]; then
$S retarget_mixamo.py work/rig_v1.blend work/rig_v2r.blend "$MX/Floating.fbx:Standing" "$MX/Mutant Swiping.fbx:SrcSwipe:turn" \
   "$MX/Standing 2H Magic Attack 01.fbx:SrcCast:turn" "$MX/Taunt Gesture.fbx:SrcFidget:turn" \
   "$MX/Standing Death Forward 01.fbx:SrcDeath:turn" | cut -c1-140
$S retarget.py work/rig_v2r.blend work/rig_v2r.blend "$L/Unarmed.glb:UnarmedGetHitF1:SrcHit" | cut -c1-100
K_Z=${K_Z:-0.1} $S flyer_clips.py work/rig_v2r.blend work/rig_v2.blend
FA=0.6 FA_RAMP=0.15,0.85 $S twist_bones.py work/rig_v2.blend work/rig_v2t.blend
$S weights_fix.py work/rig_v2t.blend work/rig_v3.blend
$S finger_weights.py work/rig_v3.blend work/rig_v4f.blend
$S reduce_rigged.py work/rig_v4f.blend work/rig_v4.blend
FINGER_K=${FINGER_K:-0.35} $S fingers_relax.py work/rig_v4.blend work/rig_v4o.blend
# G6: the taunt's left hand on the hip met the raised hover thigh; the falling right hand met the torso
$S arm_offset.py work/rig_v4o.blend work/rig_v4a.blend Fidget L 12 10 17 38 44
$S arm_offset.py work/rig_v4a.blend work/rig_v4a.blend Death R 16 46 52 60 66
$S build_wings.py work/rig_v4a.blend work/rig_v4w.blend
$S wing_flap_floor.py work/rig_v4w.blend work/rig_v5.blend
$S g6_contacts.py work/rig_v5.blend Standing Walking Running Attack Cast Hit Fidget Death
$S g5_hand_stretch.py work/rig_v5.blend Standing Walking Running Attack Cast Hit Fidget Death | cut -c1-90
$S g4_weights.py work/rig_v5.blend v5 Standing:0 Standing:54 Walking:30 Running:30 Attack:8 Attack:15 Attack:20 Attack:25 Attack:30 Cast:8 Cast:14 Cast:20 Cast:27 Cast:34 Hit:6 Hit:10 Fidget:15 Fidget:30 Death:30 Death:56 Death:80 | grep -E "^G4"
fi
