#!/usr/bin/env bash
# m342 female peasant replayable chain (batch K; the batch-B Monk robe chain m290 + m352 fingers and clip timing).
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
# m342 (female peasant, batch K): the batch-B robe chain (Monk m290) for the floor-length skirt and petticoat, plus
# the m352 finger fit on the separate hand shells (P04 left, P05 right) and its unarmed clip timing
if [ "$STAGE" = all ] || [ "$STAGE" = rig ]; then
[ -f work/source_rest.json ] || run source_rest.py "$L/Armed.glb"
run prepare_rig.py
run meshy_joints.py "$P/meshy/rig_v1/result_rigged_character_glb_url.glb" "$P/work/step1.blend"
run strip_legs.py                                      # legs under the skirt removed above the shoes
run arm_rings.py "$P/work/step1.blend" | grep -v PROFILE || true
if python3 -c "import json,sys;sys.exit(0 if json.load(open('creature.json')).get('joints_fix', True) else 1)"; then run joints_fix.py "$P/work/step1.blend"; fi
rm -f work/finger_joints.json
run build_rig.py
run fit_fingers.py "$P/work/rig_v1.blend"
run finger_joints.py "$P/work/rig_v1.blend"
run build_rig.py
run hand_frame_check.py "$P/work/rig_v1.blend"
run weights_robe.py "$P/work/rig_v1.blend" "$P/work/rig_v2w0.blend"
SMOOTH_PASSES=${SMOOTH_PASSES:-6} run finger_weights.py "$P/work/rig_v2w0.blend" "$P/work/rig_v2w.blend"
fi
if [ "$STAGE" = all ] || [ "$STAGE" = anim ]; then
# user review 2026-10-20 ("in the air", "walks very funny"): batch J's dress route (mm7_m312_claude): legs and shoes on
# the leg bones under the skirt (garment 15), the set's short Relax Walk Forward, feet flattened, walk bob evened, the
# set's Unarmed Death 1 with the legs damped to DEATH_LEGS so they stay under the skirt
ARM_ABDUCT_DEG=${ARM_ABDUCT_DEG:-6} run retarget.py "$P/work/rig_v2w.blend" "$P/work/rig_v2s.blend" "$L/Relax.glb:${WALK_CLIP:-RelaxWalkForward}:Walking" "$L/Unarmed.glb:UnarmedDeath1:Death"
mapfile -t MXC < <(sed -e "s|\$MX|$MX|" "${MX_LIST:-scripts/mx_clips.txt}" | grep -v '^#' | grep .)
run retarget_mixamo.py "$P/work/rig_v2s.blend" "$P/work/rig_v2r.blend" "${MXC[@]}"
run leg_damp.py "$P/work/rig_v2r.blend" "$P/work/rig_v2r.blend" Death:${DEATH_LEGS:-0.4}
run wrist_limit.py "$P/work/rig_v2r.blend" "$P/work/rig_v2f1.blend"
run clip_timing.py "$P/work/rig_v2f1.blend" "$P/work/rig_v2t1.blend"
FA=0.6 FA_RAMP=0.15,0.85 run twist_bones.py "$P/work/rig_v2t1.blend" "$P/work/rig_v3.blend"
run flatten_feet.py "$P/work/rig_v3.blend" "$P/work/rig_v3f.blend" Standing Walking:const Hit Fidget   # shoes on the floor; walk: one constant correction per foot
run walk_bob.py "$P/work/rig_v3f.blend" "$P/work/rig_v3f.blend"   # batch A/J walk fix: even pelvis bob, legs re-solved
UNARMED=1 LEFT_CURL=${CURL:-0.6} RIGHT_CURL=${CURL:-0.6} run apply_grip.py "$P/work/rig_v3f.blend" "$P/work/rig_v3g.blend"
LEG_R=1.3 DROP_FLAT=1 run robe_sim.py "$P/work/rig_v3g.blend" "$P/work/rig_v3r.blend"
cp work/rig_v3r.blend work/rig_v4.blend
run reduce_rigged.py "$P/work/rig_v4.blend" "$P/work/rig_v5.blend"
BODY_GARMENTS=${BODY_GARMENTS:-0,1,2} run gates.py "$P/work/rig_v5.blend" v5 > /dev/null
python3 scripts/gates_summary.py v5 | cut -c1-200
fi
