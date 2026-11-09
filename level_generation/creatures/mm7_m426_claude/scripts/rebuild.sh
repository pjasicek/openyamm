#!/usr/bin/env bash
# Warlock replayable chain (mm7 batch B; adapted from mm6_natm_claude and the accepted mm8_m460_claude robe).
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
run strip_legs.py
run arm_rings.py "$P/work/step1.blend" | grep -v PROFILE || true
if python3 -c "import json,sys;sys.exit(0 if json.load(open('creature.json')).get('joints_fix', True) else 1)"; then run joints_fix.py "$P/work/step1.blend"; fi
rm -f work/finger_joints.json          # rigid claws: no finger fit (fused Smart Topology fingers)
run build_rig.py
run weights_robe.py "$P/work/rig_v1.blend" "$P/work/rig_v2w0.blend"
cp work/rig_v2w0.blend work/rig_v2w1.blend           # no separate cape shell (fused into the gown)
run grip_from_fist.py "$P/work/rig_v2w1.blend" L                              # staff seat in the left fist
run make_wand.py
run seat_staff.py "$P/work/rig_v2w1.blend" "$P/work/rig_v2w.blend"
fi
if [ "$STAGE" = all ] || [ "$STAGE" = anim ]; then
ARM_ABDUCT_DEG=${ARM_ABDUCT_DEG:-6} run retarget.py "$P/work/rig_v2w.blend" "$P/work/rig_v2s.blend" "$L/Relax.glb:RelaxIdle:Standing" "$L/Relax.glb:RelaxWalkForward:Walking" \
    "$L/Unarmed.glb:UnarmedCastLAttack3:Cast" "$L/Unarmed.glb:UnarmedGetHitF1:Hit" "$L/Relax.glb:RelaxLaydownLayDown:Death"
# (the native falls backwards; Mixamo Standing React Death Backward and the set's Unarmed Death 1 splay the legs out of
# the gown. Relax Lay Down, with the hidden leg shafts dropped at export (creature.json drop_legs_above), keeps them in)
cp work/rig_v2s.blend work/rig_v2s2.blend
run plant.py "$P/work/rig_v2s2.blend" "$P/work/rig_v2p0.blend" Hit Cast
# the set's casts and punches turn the head and chest to the side: face the front (user review 2026-10-20)
run face_forward.py "$P/work/rig_v2p0.blend" "$P/work/rig_v2p.blend" Cast
# wand carry (left hand); the one Cast (attack and spell; user review 2026-10-20: the wand is the casting thing, no
# separate right-palm clip) follows the source left arm fully: the wand is raised and flung forward (native aa-ag)
run author_carry.py "$P/work/rig_v2p.blend" "$P/work/rig_v2c.blend" Standing:0.3 Walking:0.3 Hit:0.4 Cast:1.0
run wand_cast.py "$P/work/rig_v2c.blend" "$P/work/rig_v2cw.blend"          # the wand raised and thrust at the target
run staff_fidget.py "$P/work/rig_v2cw.blend" "$P/work/rig_v2f.blend"
SIDES=LR run wrist_limit.py "$P/work/rig_v2f.blend" "$P/work/rig_v2f1.blend"
ATTACK_HAND=L run caster_timing.py "$P/work/rig_v2f1.blend" "$P/work/rig_v2t1.blend"
SMOOTH_BONES=B_Spine,B_Spine1,B_Spine2,B_Neck,B_Head run smooth_bones.py "$P/work/rig_v2t1.blend" "$P/work/rig_v2t2.blend" Cast   # trunk/head jolts of the set (user review)
FA=0.6 FA_RAMP=0.15,0.85 run twist_bones.py "$P/work/rig_v2t2.blend" "$P/work/rig_v3.blend"
run flatten_feet.py "$P/work/rig_v3.blend" "$P/work/rig_v3f.blend" Standing Walking Cast Hit Fidget   # bare feet flat (user review)
LEG_R=1.3 DROP_FLAT=1 run robe_sim.py "$P/work/rig_v3f.blend" "$P/work/rig_v3r.blend"   # lying: the robe lies flat over the legs
run robe_floor.py "$P/work/rig_v3r.blend" "$P/work/rig_v4.blend" Death   # the flared cape hem above the floor when lying
run reduce_rigged.py "$P/work/rig_v4.blend" "$P/work/rig_v5.blend"
BODY_GARMENTS=${BODY_GARMENTS:-0,1,2,13} run gates.py "$P/work/rig_v5.blend" v5 > /dev/null
python3 scripts/gates_summary.py v5 | cut -c1-200
fi
