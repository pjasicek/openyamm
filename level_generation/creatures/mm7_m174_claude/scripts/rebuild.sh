#!/usr/bin/env bash
# Sun Cleric replayable chain (mm7 batch B; adapted from mm6_natm_claude and the accepted mm8_m460_claude robe).
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
run weights_robe.py "$P/work/rig_v1.blend" "$P/work/rig_v2w.blend"
fi
if [ "$STAGE" = all ] || [ "$STAGE" = anim ]; then
ARM_ABDUCT_DEG=${ARM_ABDUCT_DEG:-6} run retarget.py "$P/work/rig_v2w.blend" "$P/work/rig_v2s.blend" "$L/Relax.glb:RelaxIdle:Standing" "$L/Relax.glb:RelaxWalkForward:Walking" \
    "$L/Unarmed.glb:UnarmedCastRAttack1:Attack" "$L/Unarmed.glb:UnarmedGetHitF1:Hit" \
    "$L/Unarmed.glb:UnarmedCastDualAttack2:Cast"
# native m174 death leans back and falls onto the back: Mixamo Standing React Death Backward (travel halved in
# caster_timing; "Falling Back Death" kicked the legs up and flipped the robe chains into a funnel mid-fall)
run retarget_mixamo.py "$P/work/rig_v2s.blend" "$P/work/rig_v2s2.blend" "$MX/Standing React Death Backward.fbx:Death"
# Mixamo "Standing 2H Magic Attack 01" (the MM8 Cleric's cast) gathers both hands overhead: the sleeve armpits tore
# (arm p99 2.9, wrist 84 deg) and the native never raises the arms overhead; the set's two-handed forward push instead
run plant.py "$P/work/rig_v2s2.blend" "$P/work/rig_v2p0.blend" Attack Hit Cast
# the set's casts and punches turn the head and chest to the side: face the front (user review 2026-10-20)
run face_forward.py "$P/work/rig_v2p0.blend" "$P/work/rig_v2p.blend" Attack Cast
FIDGET=raise run author_fidget.py "$P/work/rig_v2p.blend" "$P/work/rig_v2f.blend"
run wrist_limit.py "$P/work/rig_v2f.blend" "$P/work/rig_v2f1.blend"
ATTACK_HAND=R run caster_timing.py "$P/work/rig_v2f1.blend" "$P/work/rig_v2t1.blend"
FA=0.6 FA_RAMP=0.15,0.85 run twist_bones.py "$P/work/rig_v2t1.blend" "$P/work/rig_v3.blend"
# supine death: the rest cone would stand up off the floor like a funnel; the lying target is flattened (DROP_FLAT)
DROP_FLAT=1 run robe_sim.py "$P/work/rig_v3.blend" "$P/work/rig_v3r.blend"
cp work/rig_v3r.blend work/rig_v4.blend        # no banners
run reduce_rigged.py "$P/work/rig_v4.blend" "$P/work/rig_v5.blend"
BODY_GARMENTS=${BODY_GARMENTS:-0,1,2,13} run gates.py "$P/work/rig_v5.blend" v5 > /dev/null
python3 scripts/gates_summary.py v5 | cut -c1-200
fi
