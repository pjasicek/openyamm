#!/usr/bin/env bash
# Landfall Guard (hgd) replayable chain. Usage: TOK=<lease token> scripts/rebuild.sh [rig|anim|all]
# rig: joints (Meshy auto-rig + arm rings + leg rings), source-frame rig with the hands framed on their grip tunnels,
#      weights (skirt chains, rigid fittings, uniform plates), grip tunnels, rifle frame + rifle + seat.
# anim: 2Hand Shooting clips + Mixamo death, clip timing (raise into the shot, aiming fidget), rifle clearance, the
#      left fist on the handguard, feet, death floor, twist bones, skirt simulation, reduction, gates.
set -euo pipefail
cd "$(dirname "$0")/.."
P=$PWD; S=scripts/step.sh
REPO=$(cd ../../.. && pwd); G="$REPO/anim_library/humanoid_set/2Hand Shooting.glb"; MX=$REPO/anim_library/mixamo
STAGE=${1:-all}
if [ "$STAGE" = all ] || [ "$STAGE" = rig ]; then
[ -f work/source_rest.json ] || $S source_rest.py "$G"
$S prepare_rig.py
$S meshy_joints.py "$P/meshy/rig_v1/result_rigged_character_glb_url.glb" "$P/work/step1.blend"
$S arm_rings.py "$P/work/step1.blend" | grep -v PROFILE || true
$S leg_rings.py "$P/work/step1.blend"
rm -f work/finger_joints.json                       # rigid fists (Smart Topology fused the fingers)
# the hands continue the forearm (a fist's PCA frame is 30-41 deg off); the grip tunnels measured in that frame
HAND_FROM_FOREARM=1 $S build_rig.py
$S weights_robe.py "$P/work/rig_v1.blend" "$P/work/rig_v2w1.blend"
$S grip_from_fist.py "$P/work/rig_v2w1.blend" R && cp work/grip_pose.json work/grip_pose_R.json && cp work/grip_pose.json work/grip_pose_R_tun.json
$S grip_from_fist.py "$P/work/rig_v2w1.blend" L && cp work/grip_pose.json work/grip_pose_L.json && cp work/grip_pose.json work/grip_pose_L_tun.json
fi
if [ "$STAGE" = all ] || [ "$STAGE" = anim ]; then
# G1 (review/g1_candidates.jpg, g1_deaths.jpg): the set's low-ready idle, walk, run, the shouldered FireRifle1, the
# get-hit, the aiming idle (fidget source); Mixamo "Death From The Front" (doubles over, kneels, folds face down)
$S retarget.py "$P/work/rig_v2w1.blend" "$P/work/rig_v2s0.blend" "$G:2HandShootingIdle:Standing" "$G:2HandShootingWalk:Walking" \
    "$G:2HandShootingRunForward:Running" "$G:2HandShootingFireRifle1:Fire" "$G:2HandShootingGetHitF1:Hit" \
    "$G:2HandShootingIdleAlt:Aim" > /dev/null
$S retarget_mixamo.py "$P/work/rig_v2s0.blend" "$P/work/rig_v2s0m.blend" "$MX/Death From The Front.fbx:Death"
$S rifle_fit.py "$P/work/rig_v2s0m.blend"              # the rifle held as a pistol grip in the right fist
python3 scripts/rifle_texture.py
$S make_rifle.py
$S seat_rifle.py "$P/work/rig_v2s0m.blend" "$P/work/rig_v2s1.blend"
$S clip_timing_hgd.py "$P/work/rig_v2s1.blend" "$P/work/rig_v2t1.blend"
CLIPS="Standing Walking Running Attack Hit Death Fidget"
HELD="Standing Walking Running Attack Hit Fidget"   # the left hand never leaves the gun in these
$S rifle_drive.py "$P/work/rig_v2t1.blend" "$P/work/rig_v2t1d.blend" $CLIPS   # the rifle level in roll, the right hand from it
NEAR=0.25 FAR=0.35 $S support_hand.py "$P/work/rig_v2t1d.blend" "$P/work/rig_v2t2.blend" $HELD
$S support_hand.py "$P/work/rig_v2t2.blend" "$P/work/rig_v2t2.blend" Death    # the fall lets go (source distance)
$S rifle_clear.py "$P/work/rig_v2t2.blend" "$P/work/rig_v2t2c.blend" $HELD
NEAR=0.25 FAR=0.35 $S support_hand.py "$P/work/rig_v2t2c.blend" "$P/work/rig_v2t2s.blend" $HELD
$S ground_clips.py "$P/work/rig_v2t2s.blend" "$P/work/rig_v2t3.blend" Attack Hit Fidget
$S flatten_feet.py "$P/work/rig_v2t3.blend" "$P/work/rig_v2t4.blend" Standing Attack Hit Fidget
$S death_floor.py "$P/work/rig_v2t4.blend" "$P/work/rig_v2t5.blend" Death | grep -v need
FA=0.6 FA_RAMP=0.15,0.85 $S twist_bones.py "$P/work/rig_v2t5.blend" "$P/work/rig_v3.blend" | grep -v BAKED
LEG_R=1.3 DROP_FLAT=1 $S robe_sim.py "$P/work/rig_v3.blend" "$P/work/rig_v3r.blend" $CLIPS | grep CLOAK
$S robe_floor.py "$P/work/rig_v3r.blend" "$P/work/rig_v4.blend" Death
$S reduce_rigged.py "$P/work/rig_v4.blend" "$P/work/rig_v5.blend"
$S rifle_up_check.py "$P/work/rig_v5.blend" $CLIPS
BODY_GARMENTS=0,1,15 $S gates.py "$P/work/rig_v5.blend" v5 $CLIPS > /dev/null
python3 scripts/gates_summary.py v5 | cut -c1-260
fi
