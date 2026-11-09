#!/usr/bin/env bash
# Hesper Kreegan (hkr) replayable chain. Usage: TOK=<lease token> scripts/rebuild.sh [rig|anim|all]
# rig:  the MM6 Demon (source/mm6_demon_source.glb) -> Body + B_* source-frame rig on the demon's joints and weights,
#       horns, finger weights by connectivity, torso weights, the curled fists and their grip tunnels.
# anim: 2Hand Shooting clips + Mixamo death, fists, carbine (v2) build/texture/fit/seat, clip timing, carbine drive, left hand on the
#       handguard, reach fix, pauldron bones, armour plates, armour-aware clearance (the upper arms too), feet, the
#       death's spine eased out of the cuirass, death floor, twist, tail, gates.
set -euo pipefail
cd "$(dirname "$0")/.."
P=$PWD; S=scripts/step.sh
REPO=$(cd ../../.. && pwd); G="$REPO/anim_library/humanoid_set/2Hand Shooting.glb"; MX=$REPO/anim_library/mixamo
STAGE=${1:-all}
HELD="Standing Walking Running Attack Hit Fidget"
CLIPS="$HELD Death"
SPEC=$P/scripts/armour_trooper.json
if [ "$STAGE" = all ] || [ "$STAGE" = rig ]; then
$S hkr_import.py
$S add_horns.py "$P/work/step1.blend" "$P/work/step1.blend"
$S build_rig_hkr.py
$S finger_weights_hkr.py "$P/work/rig_v1.blend" "$P/work/rig_v1f.blend"
$S torso_weights.py "$P/work/rig_v1f.blend" "$P/work/rig_v1f.blend"
CURL=${CURL:-40,65,45} CURL_L=35,60,40 AXIS_DEV_L=40 MIN_CLEAR_L=0.019 $S curl_hkr.py "$P/work/rig_v1f.blend"
cp work/grip_pose_L.json work/grip_pose_L_tun.json; cp work/grip_pose_R.json work/grip_pose_R_tun.json
fi
if [ "$STAGE" = all ] || [ "$STAGE" = anim ]; then
export GRIP_RAKE=${RIFLE_TILT:-0}
# the left tunnel runs back toward the stock (thumb side forward): a straight wrist with the forearm ~50 deg off the
# barrel; the source's sign needed a 105-120 deg wrist bend on the demon's hand
export BAR_SIGN=-1
$S retarget.py "$P/work/rig_v1f.blend" "$P/work/rig_v2s0.blend" "$G:2HandShootingIdle:Standing" "$G:2HandShootingWalk:Walking" \
    "$G:2HandShootingRunForward:Running" "$G:2HandShootingFireRifle1:Fire" "$G:2HandShootingGetHitF1:Hit" \
    "$G:2HandShootingIdleAlt:Aim" > /dev/null
$S retarget_mixamo.py "$P/work/rig_v2s0.blend" "$P/work/rig_v2s0m.blend" "$MX/Dying Backwards.fbx:Death"
$S apply_grip_hkr.py "$P/work/rig_v2s0m.blend" "$P/work/rig_v2g.blend" > /dev/null
RIFLE_YAW=${RIFLE_YAW:-30} RIFLE_TILT=${RIFLE_TILT:-0} HG_Y=0.28 HG_Z=0.08 $S rifle_fit.py "$P/work/rig_v2g.blend"
HG_R=0.018 $S make_carbine.py
python3 scripts/carbine_texture.py              # v2 carbine: the texture follows work/carbine_layout.json
$S seat_rifle.py "$P/work/rig_v2g.blend" "$P/work/rig_v2s1.blend"
$S clip_timing_hgd.py "$P/work/rig_v2s1.blend" "$P/work/rig_v2t1.blend"
NEAR=0.12 FAR=0.22 $S rifle_drive.py "$P/work/rig_v2t1.blend" "$P/work/rig_v2t1d.blend" $CLIPS
export Y_LO=0.20 Y_HI=0.34
ROLL_RANGE=180 ELBOW_RANGE=60 NEAR=0.25 FAR=0.35 $S support_hand.py "$P/work/rig_v2t1d.blend" "$P/work/rig_v2t2.blend" $HELD
ROLL_RANGE=180 ELBOW_RANGE=60 $S support_hand.py "$P/work/rig_v2t2.blend" "$P/work/rig_v2t2.blend" Death
REACH=0.93 $S reach_fix.py "$P/work/rig_v2t2.blend" "$P/work/rig_v2t2r.blend" $HELD
ROLL_RANGE=180 ELBOW_RANGE=60 NEAR=0.25 FAR=0.35 $S support_hand.py "$P/work/rig_v2t2r.blend" "$P/work/rig_v2t2r.blend" $HELD
fi
if [ "$STAGE" = all ] || [ "$STAGE" = anim ] || [ "$STAGE" = tail ]; then
export Y_LO=0.20 Y_HI=0.34 BAR_SIGN=-1
$S leg_limit.py "$P/work/rig_v2t2r.blend" "$P/work/rig_v2t2l.blend" Running   # the armoured run's knee drive: 88 -> 68 deg
$S helper_bones.py "$P/work/rig_v2t2l.blend" "$P/work/rig_v2t2p.blend" > /dev/null
$S bulk_body.py "$P/work/rig_v2t2p.blend" "$P/work/rig_v2t2p.blend"   # the Trooper caste's bulk (thin_co kept for the base)
python3 scripts/armour_spec_v4.py                # v4 armour (bulky shell, two tassets, rigid small parts): writes $SPEC
$S make_armour.py "$P/work/rig_v2t2p.blend" "$SPEC" "$P/work/rig_v2a.blend" | tail -1
python3 scripts/armour_texture.py
$S skin_shell.py "$P/work/rig_v2a.blend" "$SPEC" "$P/work/rig_v2a.blend" | grep SHELLHIDE   # shell weights from the skin
LEFT=1 MARGIN=0.02 PASSES=5 $S armour_clear.py "$P/work/rig_v2a.blend" "$P/work/rig_v2ac.blend" $HELD
REACH=0.93 $S reach_fix.py "$P/work/rig_v2ac.blend" "$P/work/rig_v2ac.blend" $HELD
ROLL_RANGE=180 ELBOW_RANGE=60 NEAR=0.25 FAR=0.35 $S support_hand.py "$P/work/rig_v2ac.blend" "$P/work/rig_v2ac.blend" $HELD
LEFT=1 MARGIN=0.02 PASSES=3 $S armour_clear.py "$P/work/rig_v2ac.blend" "$P/work/rig_v2ac.blend" $HELD   # the reach fix moved the gun again
ROLL_RANGE=180 ELBOW_RANGE=60 NEAR=0.25 FAR=0.35 $S support_hand.py "$P/work/rig_v2ac.blend" "$P/work/rig_v2ac.blend" $HELD
$S helper_bones.py "$P/work/rig_v2ac.blend" "$P/work/rig_v2ac.blend" > /dev/null
$S ground_clips.py "$P/work/rig_v2ac.blend" "$P/work/rig_v2t3.blend" Attack Hit Fidget
$S flatten_feet.py "$P/work/rig_v2t3.blend" "$P/work/rig_v2t4.blend" Standing Attack Hit Fidget
$S death_unfold.py "$P/work/rig_v2t4.blend" "$P/work/rig_v2t4.blend" Death   # the crouch folded the belly into the cuirass
$S death_floor.py "$P/work/rig_v2t4.blend" "$P/work/rig_v2t5.blend" Death | grep -v need
FA=0.6 FA_RAMP=0.15,0.85 $S twist_bones.py "$P/work/rig_v2t5.blend" "$P/work/rig_v3.blend" | grep -v BAKED
$S skin_shell.py "$P/work/rig_v3.blend" "$SPEC" "$P/work/rig_v3.blend" | grep SHELLHIDE   # again: the twist bones now carry the arm plates
CYCLIC=1 MAXP=50 $S foot_floor.py "$P/work/rig_v3.blend" "$P/work/rig_v3.blend" Walking Running
CYCLIC=1 MAXP=50 $S foot_floor.py "$P/work/rig_v3.blend" "$P/work/rig_v3.blend" Walking Running
FLOOR=0.07 $S tail_anim.py "$P/work/rig_v3.blend" "$P/work/rig_v3t.blend" $CLIPS
$S armour_gate.py "$P/work/rig_v3t.blend" a3 "$SPEC" $CLIPS > /dev/null
$S shell_stretch.py "$P/work/rig_v3t.blend" "$SPEC" a3 $CLIPS | tail -1
$S shell_leak.py "$P/work/rig_v3t.blend" "$SPEC" a3 $CLIPS
python3 scripts/gate_table.py a3
fi
