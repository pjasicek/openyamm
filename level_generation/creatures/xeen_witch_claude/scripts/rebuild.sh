#!/usr/bin/env bash
# Witch replayable chain (adapted from mm6_natm_claude/scripts/rebuild.sh). Run from anywhere with TOK=<lease token>;
# every Blender step goes through tools/run_creature_blender.sh (scripts/step.sh) and the chain stops at the first failure.
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; repo="$(cd -- "$here/../../.." && pwd)"
cd "$repo"
. "$here/scripts/libpath.sh"
P=level_generation/creatures/$(basename "$here"); W=$P/work
run() { "$here/scripts/step.sh" "$@" || exit 1; }
STAGE=${STAGE:-all}
if [ "$STAGE" = all ] || [ "$STAGE" = rig ]; then
run step1_clean.py $W/st_v1_parts.blend $W/step1.blend
run garments.py $W/step1.blend $W/step1.blend
run fit_witch_joints.py $W/step1.blend
[ -f "$here/work/finger_joints.json" ] && mv -f "$here/work/finger_joints.json" "$here/work/finger_joints.prev.json"
run build_rig.py
run fit_fingers.py $W/rig_v1.blend
run finger_joints.py $W/rig_v1.blend
run build_rig.py
run hand_frame_check.py $W/rig_v1.blend
fi
if [ "$STAGE" = all ] || [ "$STAGE" = anim ]; then
mapfile -t SETC < <(sed -e "s|\$L|$L|" "$here/scripts/set_clips.txt" | grep -v '^#' | grep .)
mapfile -t MXC < <(sed -e "s|\$MX|$MX|" "$here/scripts/mx_clips.txt" | grep -v '^#' | grep .)
run retarget.py $W/rig_v1.blend $W/rig_v2s.blend "$L/2Hand Staff.glb:StaffIdle:GripRef" "${SETC[@]}"
run retarget_mixamo.py $W/rig_v2s.blend $W/rig_v2r.blend "${MXC[@]}"
run run_fit.py $W/rig_v2r.blend $W/rig_v2f.blend
run foot_level.py $W/rig_v2f.blend $W/rig_v2l.blend Standing Walking:const Hit Cast Attack Fidget Death:until=24
SIDE=L run author_carry.py $W/rig_v2l.blend $W/rig_v2c.blend Standing:0.3 Walking:0.3 Running:0.15:Running Hit:0.4:Standing:pelvis:ref \
  Attack:0.25:Standing:chest:ref Cast:0.25:Standing:chest:ref Fidget:0.35:Standing:pelvis:ref Death:0.5:Death:chest:ref
[ "${UNTIL:-}" = carry ] && exit 0
run right_stance.py $W/rig_v2c.blend $W/rig_v2st0.blend Cast Standing
run arm_push.py $W/rig_v2st0.blend $W/rig_v2st.blend Attack:R:21:30:38:-0.03,-0.06,0.24 Attack:R:31:40:50:-0.10,-0.12,0.03
# G6 clearance (session 2): left elbow fold off the waist, corpse forearm out of the torso, staff fork off the boot;
# measured on the previous build's final body (work/measure_ref.blend, a copy of rig_v5.blend)
EASE=8 run elbow_clear.py $W/rig_v2st.blend $W/rig_v2sc.blend $W/measure_ref.blend Running:L:forearm:loop Cast:L:forearm Fidget:L:forearm Fidget:R:forearm Death:L:both
run wrist_ease.py $W/rig_v2sc.blend $W/rig_v2e.blend Cast:R Attack:R Attack:L Death:L Death:R Walking:L Fidget:L
run forearm_hinge.py $W/rig_v2e.blend $W/rig_v2.blend
FA=0.6 FA_RAMP=0.15,0.85 run twist_bones.py $W/rig_v2.blend $W/rig_v2t.blend
run weights_fix.py $W/rig_v2t.blend $W/rig_v3.blend
run finger_weights.py $W/rig_v3.blend $W/rig_v4f.blend
run reduce_rigged.py $W/rig_v4f.blend $W/rig_v4r.blend
run fingers_relax.py $W/rig_v4r.blend $W/rig_v4.blend
SIDE=L R_HANDLE=0.016 run grip_solve.py $W/rig_v4.blend GripRef 0
run apply_grip.py $W/rig_v4.blend $W/rig_v5g.blend
run clip_timing.py $W/rig_v5g.blend $W/rig_v5t.blend
# the death's blend-in from Standing (clip_timing) swings the staff fork into the left boot: clear it after the blend
EASE=6 run elbow_clear.py $W/rig_v5t.blend $W/rig_v5.blend $W/measure_ref.blend Death:L:staff
fi
