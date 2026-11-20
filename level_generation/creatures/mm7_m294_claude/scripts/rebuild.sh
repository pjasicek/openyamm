#!/usr/bin/env bash
# Necromancer replayable chain (mm7 batch F; copied from mm7_m426_claude: natm source-frame rig + mm8_m460 robe chains).
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
run weights_robe.py "$P/work/rig_v1.blend" "$P/work/rig_v2w.blend"      # no held prop
fi
if [ "$STAGE" = all ] || [ "$STAGE" = anim ]; then
ARM_ABDUCT_DEG=${ARM_ABDUCT_DEG:-6} run retarget.py "$P/work/rig_v2w.blend" "$P/work/rig_v2s.blend" "$L/Relax.glb:RelaxIdle:Standing" "$L/Relax.glb:RelaxWalkForward:Walking" \
    "$L/Unarmed.glb:UnarmedGetHitF1:Hit" "$L/Unarmed.glb:UnarmedCastDualSummon2:Cast" \
    "$L/Unarmed.glb:UnarmedDeath1:Death" "$L/Relax.glb:RelaxTalk3:Fidget"
# G1 (review/g1_casts_front.png, g1c_sheet.png): Cast = Dual Summon 2 (arms spread wide, native aa2-aa3). User review
# 2026-10-20: no separate Attack (Dual Summon 1, arms overhead, was built first); the binding plays Cast for attacks.
# Death: the native falls backwards (m294d*): Unarmed Death 1. The legs are their own piece (boots), not inside a gown.
cp work/rig_v2s.blend work/rig_v2s2.blend
run plant.py "$P/work/rig_v2s2.blend" "$P/work/rig_v2p0.blend" Hit Cast
run face_forward.py "$P/work/rig_v2p0.blend" "$P/work/rig_v2p.blend" Cast
run wrist_limit.py "$P/work/rig_v2p.blend" "$P/work/rig_v2f1.blend"
run caster_timing.py "$P/work/rig_v2f1.blend" "$P/work/rig_v2t1.blend"
FA=0.6 FA_RAMP=0.15,0.85 run twist_bones.py "$P/work/rig_v2t1.blend" "$P/work/rig_v3.blend"
run flatten_feet.py "$P/work/rig_v3.blend" "$P/work/rig_v3f.blend" Standing Walking Cast Hit Fidget   # heeled boots at their rest pitch
run floor_pass.py "$P/work/rig_v3f.blend" "$P/work/rig_v3g.blend" Standing Walking Cast Hit Fidget   # soles on the floor (sole_probe)
LEG_R=1.3 DROP_FLAT=1 run robe_sim.py "$P/work/rig_v3g.blend" "$P/work/rig_v3r.blend"   # lying: the robe lies flat over the legs
run robe_floor.py "$P/work/rig_v3r.blend" "$P/work/rig_v4.blend" Death   # the flared cape hem above the floor when lying
run reduce_rigged.py "$P/work/rig_v4.blend" "$P/work/rig_v5.blend"
BODY_GARMENTS=${BODY_GARMENTS:-0,1,2,13,17} run gates.py "$P/work/rig_v5.blend" v5 > /dev/null
python3 scripts/gates_summary.py v5 | cut -c1-200
fi
