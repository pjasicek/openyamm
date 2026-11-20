#!/usr/bin/env bash
# Ashrunners (har) replayable chain. Usage: TOK=<lease token> scripts/rebuild.sh [rig|anim|rifle|pistol|merge|gates|all]
# rig:    joints (Meshy auto-rig + arm rings + leg rings, knees on the hip-ankle line), source-frame rig with the fists
#         continuing the forearm, weights (cloak/tunic chains, thigh panels, rigid belt gear and pack, uniform plates),
#         reduction (work/rig_tex.blend: the texture topology), chest strips, grip tunnels, rifle frame, the three guns.
# rifle:  tiers B and C (rifle / carbine, both hands): the guard's 2Hand Shooting chain -> work/R_v4.blend
# pistol: tier A (one-handed pistol): the Blaster Guy's chain (m475) + a Mixamo run -> work/P_v4.blend
# merge:  the pistol clips renamed P_* into the rifle blend -> work/rig_v5.blend; gates.
set -euo pipefail
cd "$(dirname "$0")/.."
P=$PWD; S=scripts/step.sh
REPO=$(cd ../../.. && pwd); L=$REPO/anim_library/humanoid_set; G="$L/2Hand Shooting.glb"; MX=$REPO/anim_library/mixamo
STAGE=${1:-all}
want() { [ "$STAGE" = all ] || [ "$STAGE" = "$1" ] || { [ "$STAGE" = anim ] && [ "$1" != rig ] && [ "$1" != gates ]; }; }
if want rig; then
[ -f work/source_rest.json ] || $S source_rest.py "$G"
$S prepare_rig.py
$S meshy_joints.py "$P/meshy/rig_v1/result_rigged_character_glb_url.glb" "$P/work/step1.blend"
$S arm_rings.py "$P/work/step1.blend" | grep -v PROFILE || true
$S leg_rings.py "$P/work/step1.blend"
python3 scripts/knees_straight.py
rm -f work/finger_joints.json                       # rigid fists (Smart Topology fused the fingers)
HAND_FROM_FOREARM=1 $S build_rig.py
$S weights_robe.py "$P/work/rig_v1.blend" "$P/work/rig_v2w1.blend"
$S reduce_rigged.py "$P/work/rig_v2w1.blend" "$P/work/rig_tex.blend"
$S mark_strips.py "$P/work/rig_tex.blend" "$P/work/rig_tex.blend"
for s in R L; do $S grip_from_fist.py "$P/work/rig_tex.blend" $s; cp work/grip_pose.json work/grip_pose_$s.json; cp work/grip_pose.json work/grip_pose_${s}_tun.json; done
cp work/grip_pose_R.json work/grip_pose.json
$S rifle_fit.py "$P/work/rig_tex.blend"
python3 scripts/rifle_texture.py && python3 scripts/weather_rifle.py
$S make_rifle.py
for g in pistol carbine; do python3 -W ignore scripts/prop_profile.py $g; $S make_slab_prop.py $g; done
$S make_gear.py "$P/work/rig_tex.blend" && python3 scripts/gear_maps.py
$S seat_props.py "$P/work/rig_tex.blend" "$P/work/rig_v2w.blend"
fi
CLIPS="Standing Walking Running Attack Hit Death Fidget"
HELD="Standing Walking Running Attack Hit Fidget"
if want rifle; then
# G1: the guard's (hes_guard_claude/review/g1_candidates.jpg): low-ready idle, walk, run, shouldered FireRifle1, get-hit,
# the aiming idle as the fidget; Mixamo "Death From The Front" (face down: the cloak stays on top of the body)
$S retarget.py "$P/work/rig_v2w.blend" "$P/work/R_s0.blend" "$G:2HandShootingIdle:Standing" "$G:2HandShootingWalk:Walking" \
    "$G:2HandShootingRunForward:Running" "$G:2HandShootingFireRifle1:Fire" "$G:2HandShootingGetHitF1:Hit" \
    "$G:2HandShootingIdleAlt:Aim" > /dev/null
$S retarget_mixamo.py "$P/work/R_s0.blend" "$P/work/R_s0m.blend" "$MX/Death From The Front.fbx:Death"
$S clip_timing_hgd.py "$P/work/R_s0m.blend" "$P/work/R_t1.blend"
$S rifle_drive.py "$P/work/R_t1.blend" "$P/work/R_t1d.blend" $CLIPS
Y_LO=0.28 Y_HI=0.37 ROLL_SEARCH=1 NEAR=0.25 FAR=0.35 $S support_hand.py "$P/work/R_t1d.blend" "$P/work/R_t2.blend" $HELD
$S support_hand.py "$P/work/R_t2.blend" "$P/work/R_t2.blend" Death
$S rifle_clear.py "$P/work/R_t2.blend" "$P/work/R_t2c.blend" $HELD
Y_LO=0.28 Y_HI=0.37 ROLL_SEARCH=1 NEAR=0.25 FAR=0.35 $S support_hand.py "$P/work/R_t2c.blend" "$P/work/R_t2s.blend" $HELD
# wrists <= 60 deg (polish 2026-10-22): the elbow plane of both arms, the support fist's roll about / slide along the
# handguard, chosen over each clip; the hands' grip on the gun and the gun itself do not move
PHI_STEP=10 $S wrist_elbow.py "$P/work/R_t2s.blend" "$P/work/R_t2w.blend" LR $HELD Death
$S ground_clips.py "$P/work/R_t2w.blend" "$P/work/R_t3.blend" Attack Hit Fidget
$S flatten_feet.py "$P/work/R_t3.blend" "$P/work/R_t4.blend" Standing Attack Hit Fidget
NOGUN=1 $S death_floor.py "$P/work/R_t4.blend" "$P/work/R_t4f.blend" Death | grep -v need
$S drop_gun.py "$P/work/R_t4f.blend" "$P/work/R_t5.blend" Death Rifle=Rifle Carbine=Carbine   # the gun falls beside him
FA=0.6 FA_RAMP=0.15,0.85 $S twist_bones.py "$P/work/R_t5.blend" "$P/work/R_v3.blend" | grep -v BAKED
LEG_R=${LEG_R:-1.6} DROP_FLAT=0.6 $S robe_sim.py "$P/work/R_v3.blend" "$P/work/R_v3r.blend" $CLIPS | grep CLOAK
$S robe_floor.py "$P/work/R_v3r.blend" "$P/work/R_v4.blend" Death
fi
PCLIPS="Standing Walking Running Attack Hit Death Fidget"
if want pistol; then
# G1: the Blaster Guy's (mm7_m475_claude/review/g1_candidates.png): upright Relax idle/walk (the pistol hangs at the
# side), the set's right-hand pistol attack, unarmed get-hit, the pistol reload as the fidget; Mixamo Standard Run
# (the playbook's run source); the same face-down death as the rifle tiers
ARM_ABDUCT_DEG=${ARM_ABDUCT_DEG:-8} $S retarget.py "$P/work/rig_v2w.blend" "$P/work/P_s0.blend" "$L/Relax.glb:RelaxIdle:Standing" \
    "$L/Relax.glb:RelaxWalkForward:Walking" "$L/1Hand.glb:PistolAttackR1:Attack" "$L/Unarmed.glb:UnarmedGetHitF1:Hit" \
    "$L/1Hand.glb:PistolReloadR1:Fidget" > /dev/null
$S retarget_mixamo.py "$P/work/P_s0.blend" "$P/work/P_s.blend" "$MX/Death From The Front.fbx:Death" "$MX/Standard Run.fbx:Running"
$S hybrid_run.py "$P/work/P_s.blend" "$P/work/P_s.blend" "$P/work/R_s0.blend" Running Running Running   # legs of the 2Hand run (cloak)
$S plant.py "$P/work/P_s.blend" "$P/work/P_p0.blend" Attack Hit Fidget
$S face_forward.py "$P/work/P_p0.blend" "$P/work/P_p.blend" Attack
SIDES=R $S wrist_limit.py "$P/work/P_p.blend" "$P/work/P_f1.blend"
TIMING_JSON=clip_timing_P.json ATTACK_HAND=R $S caster_timing.py "$P/work/P_f1.blend" "$P/work/P_t1.blend"
AIM_BONE=Pistol $S aim_forward.py "$P/work/P_t1.blend" "$P/work/P_t2.blend" Attack
$S ground_clips.py "$P/work/P_t2.blend" "$P/work/P_t3.blend" Attack Hit Fidget
$S drop_gun.py "$P/work/P_t3.blend" "$P/work/P_t3d.blend" Death Pistol=Pistol   # caster_timing.py floors the body; the pistol falls
ARM_ABDUCT_DEG=${ABDUCT_P:-6} $S abduct_arms.py "$P/work/P_t3d.blend" "$P/work/P_t3d.blend" Standing Running Hit Fidget   # hands clear of the cloak edges (g6_hand_proximity.py)
ARM_ABDUCT_DEG=${ABDUCT_PW:-10} $S abduct_arms.py "$P/work/P_t3d.blend" "$P/work/P_t3d.blend" Walking
ARM_ABDUCT_DEG_L=8 ARM_ABDUCT_DEG_R=0 $S abduct_arms.py "$P/work/P_t3d.blend" "$P/work/P_t3d.blend" Attack   # the free left hand
# one-handed (2026-10-22 review): the free left arm hangs as in Standing (local, follows the trunk) with a share of
# the source's reaction; the set's attack, hit and reload clips bent it forward to the gun
SHARE_Attack=0.15 SHARE_Hit=0.3 SHARE_Fidget=0.1 $S left_arm_rest.py "$P/work/P_t3d.blend" "$P/work/P_t3d.blend" Attack Hit Fidget
ARM_ABDUCT_DEG_L=4 ARM_ABDUCT_DEG_R=0 $S abduct_arms.py "$P/work/P_t3d.blend" "$P/work/P_t3d.blend" Attack Hit Fidget   # 10 deg: the hand off the cloak edge
FA=0.6 FA_RAMP=0.15,0.85 $S twist_bones.py "$P/work/P_t3d.blend" "$P/work/P_v3.blend" | grep -v BAKED
$S flatten_feet.py "$P/work/P_v3.blend" "$P/work/P_v3f.blend" Standing Walking Attack Hit Fidget
LEG_R=${LEG_R:-1.6} DROP_FLAT=0.6 $S robe_sim.py "$P/work/P_v3f.blend" "$P/work/P_v3r.blend" $PCLIPS | grep CLOAK
$S robe_floor.py "$P/work/P_v3r.blend" "$P/work/P_v4.blend" Death
fi
if want merge; then
$S merge_clips.py "$P/work/R_v4.blend" "$P/work/P_v4.blend" "$P/work/rig_v5.blend" P_ $PCLIPS
fi
if want gates; then
ALL="$CLIPS P_Standing P_Walking P_Running P_Attack P_Hit P_Death P_Fidget"
$S rifle_up_check.py "$P/work/rig_v5.blend" $HELD Death
BODY_GARMENTS=0,1,15 $S gates.py "$P/work/rig_v5.blend" v5 $ALL > /dev/null
python3 scripts/gates_summary.py v5 | cut -c1-260
$S g6_hand_proximity.py "$P/work/rig_v5.blend" v5 $ALL
COAT_GARMENTS=2,13 $S g6_leg_leak.py "$P/work/rig_v5.blend" v5 $ALL
fi
