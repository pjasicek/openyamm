#!/usr/bin/env bash
# m312 peasant dwarf woman replayable chain (mm7 batch J; the Mage chain of mm7_m274_claude without staff, cape, attack
# and cast: floor-length dress on 12 x 4 robe chains, legs kept for the shoes under the hem).
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
cp "$P/work/rig_v2w0.blend" "$P/work/rig_v2w.blend"
fi
if [ "$STAGE" = all ] || [ "$STAGE" = anim ]; then
# G1 2026-10-20: native m312 stands with the arms hanging, walks with a short arm swing, recoils with the arms flung out
# (na-ne), falls onto the back (da-dd, xa); its fidget barely moves (a nod)
ARM_ABDUCT_DEG=${ARM_ABDUCT_DEG:-6} run retarget.py "$P/work/rig_v2w.blend" "$P/work/rig_v2s.blend" "$L/Relax.glb:RelaxIdle:Standing" "$L/Relax.glb:${WALK_CLIP:-RelaxWalkForward}:Walking" \
    "$L/Unarmed.glb:UnarmedGetHitF2:Hit" "$L/Relax.glb:RelaxYes:Fidget" \
    "$L/Unarmed.glb:UnarmedDeath1:Death"
# death: the set's Unarmed Death1 (crouches, falls onto the back, legs forward under the dress, as native m312da-xa);
# the Relax lie-down landed face down; Mixamo React Death Backward strode wide and kicked
# the legs up: the shoes left the hem by 40 cm (damping its legs pushed the body 66 cm through the floor while it sat)
cp "$P/work/rig_v2s.blend" "$P/work/rig_v2s2.blend"
# the hit planted (legs hold Standing: a stride shows the shoes outside the hem); GetHitF2 recoils back with the arms out
# like native na-nc (F1 doubles over forward)
run plant.py "$P/work/rig_v2s2.blend" "$P/work/rig_v2p.blend" Hit
# the corpse raised a knee through the dress: the death keeps DEATH_LEGS of its source leg motion (leg_damp.py)
run leg_damp.py "$P/work/rig_v2p.blend" "$P/work/rig_v2p.blend" Death:${DEATH_LEGS:-0.4}
SIDES=LR run wrist_limit.py "$P/work/rig_v2p.blend" "$P/work/rig_v2f1.blend"
run caster_timing.py "$P/work/rig_v2f1.blend" "$P/work/rig_v2t1.blend"
FA=0.6 FA_RAMP=0.15,0.85 run twist_bones.py "$P/work/rig_v2t1.blend" "$P/work/rig_v3.blend"
run flatten_feet.py "$P/work/rig_v3.blend" "$P/work/rig_v3f.blend" Standing Walking:const Hit Fidget   # shoes on the floor; the walk: one constant correction per foot (ankle twitch, review 2026-10-20)
# walk bob (batch A, mm7_m222_claude): the walk's pelvis/head zigzag; both steps alike, legs re-solved to the same ankle paths
run walk_bob.py "$P/work/rig_v3f.blend" "$P/work/rig_v3f.blend"
LEG_R=1.3 DROP_FLAT=1 run robe_sim.py "$P/work/rig_v3f.blend" "$P/work/rig_v4.blend"   # lying: the robe lies flat over the legs
run reduce_rigged.py "$P/work/rig_v4.blend" "$P/work/rig_v5.blend"
BODY_GARMENTS=${BODY_GARMENTS:-0,1,2,13} run gates.py "$P/work/rig_v5.blend" v5 > /dev/null
python3 scripts/gates_summary.py v5 | cut -c1-200
fi
