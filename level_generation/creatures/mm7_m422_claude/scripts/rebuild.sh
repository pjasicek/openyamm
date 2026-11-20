#!/usr/bin/env bash
# Vampire replayable chain (mm7 batch F; the batch-B robed-caster chain of mm7_m274_claude: coat skirt chains + cape sheet).
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
run clean_parts.py                     # sticks off the mouth, stray triangle; coat shell -> coat/skirt/cape/collar pieces
run prepare_rig.py
run meshy_joints.py "$P/meshy/rig_v1/result_rigged_character_glb_url.glb" "$P/work/step1.blend"
run strip_legs.py
run arm_rings.py "$P/work/step1.blend" | grep -v PROFILE || true
if python3 -c "import json,sys;sys.exit(0 if json.load(open('creature.json')).get('joints_fix', True) else 1)"; then run joints_fix.py "$P/work/step1.blend"; fi
run legs_fix.py "$P/work/step1.blend"          # knees/ankles onto the leg mesh centre line (Meshy's knees sat on the coat front)
rm -f work/finger_joints.json          # rigid open hands: no finger fit
run build_rig.py
run weights_robe.py "$P/work/rig_v1.blend" "$P/work/rig_v2w0.blend"
run shrink_legs.py "$P/work/rig_v2w0.blend" "$P/work/rig_v2w0s.blend"            # hidden trousers thinned (skirt poke)
run sheet_rig.py "$P/work/rig_v2w0s.blend" "$P/work/rig_v2w.blend"              # the cape: simulated chains on the chest
fi
if [ "$STAGE" = all ] || [ "$STAGE" = anim ]; then
# native m422 death: falls onto the back with the legs kicking up: Mixamo "Dying Backwards" (staggers, sits, falls
# back; the legs stay together under the closed coat). Tried: Mixamo "Standing React Death Backward" (strode wide, the
# knee came through the coat front), Mixamo "Dying" (lay face down), the set's Unarmed Death1 (the coat stayed behind the
# bent knees). DEATH_CLIP=hs:<set>:<clip> retargets a set death instead.
DEATH_CLIP=${DEATH_CLIP:-mx:Dying Backwards}
if [ "${DEATH_CLIP%%:*}" = hs ]; then
  D=${DEATH_CLIP#hs:}; DS="$L/${D%%:*}.glb:${D#*:}:Death"
else DS=""; fi
ARM_ABDUCT_DEG=${ARM_ABDUCT_DEG:-6} run retarget.py "$P/work/rig_v2w.blend" "$P/work/rig_v2s.blend" "$L/Relax.glb:RelaxIdle:Standing" "$L/Relax.glb:RelaxWalkForward:Walking" \
    "$L/Unarmed.glb:UnarmedGetHitF1:Hit" $DS
# Attack (user review 1, G1 sheet review/g1_attack_candidates.png): Mixamo "Standing Melee Attack Downward", planted:
# the right claw rises behind and over the head and rakes down and forward across the body (native aa-ad raise,
# ae-af lunge); a cross punch read as a boxer's guard, the zombie grab bent double for 4.6 s, the backhand swung wide
MXA=("$MX/${ATTACK_CLIP:-Standing Melee Attack Downward}.fbx:Attack:plant")
if [ -z "$DS" ]; then MXA+=("$MX/${DEATH_CLIP#mx:}.fbx:Death"); fi
run retarget_mixamo.py "$P/work/rig_v2s.blend" "$P/work/rig_v2s2.blend" "${MXA[@]}"
run plant.py "$P/work/rig_v2s2.blend" "$P/work/rig_v2p0.blend" Hit
run face_forward.py "$P/work/rig_v2p0.blend" "$P/work/rig_v2p.blend" Attack
FIDGET=cape run author_fidget.py "$P/work/rig_v2p.blend" "$P/work/rig_v2f.blend"
run wrist_limit.py "$P/work/rig_v2f.blend" "$P/work/rig_v2f1.blend"
# the attack's wind-up lifted the claw straight overhead and tore the coat armpit (user review 1): soft elevation cap
KNEE=${KNEE:-80} GAIN=${GAIN:-0.4} run arm_cap.py "$P/work/rig_v2f1.blend" "$P/work/rig_v2f2.blend" Attack Fidget
ATTACK_END=${ATTACK_END:-1.47} ATTACK_LEAD=${ATTACK_LEAD:-0.1} ATTACK_HAND=R run caster_timing.py "$P/work/rig_v2f2.blend" "$P/work/rig_v2t1.blend"
FA=0.6 FA_RAMP=0.15,0.85 run twist_bones.py "$P/work/rig_v2t1.blend" "$P/work/rig_v3.blend"
GROUND=Hit,Walking run flatten_feet.py "$P/work/rig_v3.blend" "$P/work/rig_v3f.blend" Standing Walking Attack Hit Fidget
# user review 2026-10-20 "use legs during his attack": authored lower body on the timed attack (copied from m178)
run attack_legs.py "$P/work/rig_v3f.blend" "$P/work/rig_v3a.blend"
BEND_MAX=${BEND_MAX:-15} BEND_SMOOTH=${BEND_SMOOTH:-3} NB_FINAL=1 MID_COLLIDE=1 PUSH_CAP=${PUSH_CAP:-0.012} LEG_R=${LEG_R:-1.6} DROP_FLAT=1 run robe_sim.py "$P/work/rig_v3a.blend" "$P/work/rig_v3r.blend"
TILT_CLIPS=Death,Attack TILT0=10 TILT1=40 NB_FINAL=1 DROP_FLAT=1 CHAINS_KEY=sheet_chains ROOT=B_Spine2 PREFIX=Sheet_ run robe_sim.py "$P/work/rig_v3r.blend" "$P/work/rig_v4.blend"
run reduce_rigged.py "$P/work/rig_v4.blend" "$P/work/rig_v5.blend"
BODY_GARMENTS=${BODY_GARMENTS:-0,1,2} run gates.py "$P/work/rig_v5.blend" v5 > /dev/null
python3 scripts/gates_summary.py v5 | cut -c1-200
fi
