#!/usr/bin/env bash
# Blaster Guy (m475) replayable chain, from the batch-B Warlock (mm7_m426_claude, settings in creature.json): the
# fused vest/cape shell is split below the waist and the cape below it rides 12 simulated chains across its own
# angular sector (cape_sector); the blaster pistol is a rigid attachment seated in the right fist.
# Usage: TOK=<lease token> scripts/rebuild.sh [rig|anim|all]   Aborts on the first failing step.
set -euo pipefail
cd "$(dirname "$0")/.."
P=$PWD; NAME=$(basename "$P")
REPO=$(cd ../../.. && pwd)
L=$REPO/anim_library/humanoid_set; MX=$REPO/anim_library/mixamo
run() { local out log; out=$(cd "$REPO" && tools/run_creature_blender.sh --token "$TOK" "level_generation/creatures/$NAME/scripts/$1" "${@:2}" 2>&1) || true
        log=$(echo "$out" | grep "Blender log" | awk '{print $3}')
        grep -E '^[A-Z][A-Z0-9_]+[ :]' "$log" | grep -v -E '^(Blender|FBX|Read|Info|INFO)' | cut -c1-240 || true
        if grep -q "Traceback\|script failed" "$log"; then grep -A12 Traceback "$log" | head -20; echo "STEP FAILED: $1"; exit 1; fi; }
STAGE=${1:-all}
if [ "$STAGE" = all ] || [ "$STAGE" = rig ]; then
[ -f work/source_rest.json ] || run source_rest.py "$L/Armed.glb"
run prepare_rig.py
run meshy_joints.py "$P/meshy/rig_v1/result_rigged_character_glb_url.glb" "$P/work/step1.blend"
run arm_rings.py "$P/work/step1.blend" | grep -v PROFILE || true
rm -f work/finger_joints.json          # rigid fists (Smart Topology fused the fingers)
HAND_FROM_FOREARM=1 run build_rig.py     # fists: PCA hand frames were 30-41 deg off the forearm
run weights_robe.py "$P/work/rig_v1.blend" "$P/work/rig_v2w1.blend"
run grip_from_fist.py "$P/work/rig_v2w1.blend" R                              # pistol grip tunnel in the right fist
run make_blaster.py
run seat_blaster.py "$P/work/rig_v2w1.blend" "$P/work/rig_v2w.blend"
A=25 DZ=0.005 run regrip_blaster.py "$P/work/rig_v2w.blend" "$P/work/rig_v2w.blend"   # grip along the fingers (user review 2026-10-20)
fi
if [ "$STAGE" = all ] || [ "$STAGE" = anim ]; then
# G1 (review/g1_candidates.png): upright Relax idle/walk (the gun hangs down at the side as in the native m475sa/w),
# the set's right-hand pistol attack (arm straight forward, recoil kick; native m475aa-ah), its pistol reload as the
# fidget (both hands at the gun in front, native m475fa-fd), unarmed get-hit, a left-hand cast for his heal/buff
# spells (the gun hand stays free), Mixamo backward death (the native falls back with the arms spread, m475da-dd)
ARM_ABDUCT_DEG=${ARM_ABDUCT_DEG:-8} run retarget.py "$P/work/rig_v2w.blend" "$P/work/rig_v2s0.blend" "$L/Relax.glb:RelaxIdle:Standing" "$L/Relax.glb:RelaxWalkForward:Walking" \
    "$L/1Hand.glb:PistolAttackR1:Attack" "$L/Unarmed.glb:UnarmedGetHitF1:Hit" "$L/Unarmed.glb:${CAST_CLIP:-UnarmedCastLAttack1}:Cast" \
    "$L/1Hand.glb:PistolReloadR1:Fidget"
run retarget_mixamo.py "$P/work/rig_v2s0.blend" "$P/work/rig_v2s.blend" "$MX/Standing React Death Backward.fbx:Death"
run plant.py "$P/work/rig_v2s.blend" "$P/work/rig_v2p0.blend" Attack Hit Cast Fidget
run face_forward.py "$P/work/rig_v2p0.blend" "$P/work/rig_v2p.blend" Attack Cast
SIDES=R run wrist_limit.py "$P/work/rig_v2p.blend" "$P/work/rig_v2f1.blend"
ATTACK_HAND=R run caster_timing.py "$P/work/rig_v2f1.blend" "$P/work/rig_v2t1.blend"
run aim_forward.py "$P/work/rig_v2t1.blend" "$P/work/rig_v2t2.blend" Attack   # the shot straight ahead (user review 2026-10-20)
run ground_clips.py "$P/work/rig_v2t2.blend" "$P/work/rig_v2t3.blend" Attack Hit   # no floating (user review 2026-10-20)
FA=0.6 FA_RAMP=0.15,0.85 run twist_bones.py "$P/work/rig_v2t3.blend" "$P/work/rig_v3.blend"
run flatten_feet.py "$P/work/rig_v3.blend" "$P/work/rig_v3f.blend" Standing Walking Attack Cast Hit Fidget
LEG_R=1.3 DROP_FLAT=1 run robe_sim.py "$P/work/rig_v3f.blend" "$P/work/rig_v3r.blend"
run robe_floor.py "$P/work/rig_v3r.blend" "$P/work/rig_v4.blend" Death
run reduce_rigged.py "$P/work/rig_v4.blend" "$P/work/rig_v5.blend"
BODY_GARMENTS=${BODY_GARMENTS:-0,1,2,15} run gates.py "$P/work/rig_v5.blend" v5 > /dev/null
python3 scripts/gates_summary.py v5 | cut -c1-200
fi
