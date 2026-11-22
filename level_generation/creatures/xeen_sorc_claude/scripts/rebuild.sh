#!/usr/bin/env bash
# Sorceress replayable chain (adapted from xeen_witch_claude / mm6_natm_claude). Run from anywhere with TOK=<lease token>;
# every Blender step goes through scripts/step.sh (lane Blender wrapper, logs in logs/) and the chain stops at the
# first failure. STAGE=rig | anim | all.
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; repo="$(cd -- "$here/../../.." && pwd)"
cd "$repo"
. "$here/scripts/libpath.sh"
W=$here/work
run() { "$here/scripts/step.sh" "$@" || exit 1; }
STAGE=${STAGE:-all}
if [ "$STAGE" = all ] || [ "$STAGE" = rig ]; then
run step1_clean.py $W/st_v1_parts.blend $W/step1.blend
run garments.py $W/step1.blend $W/step1.blend
run fit_sorc_joints.py $W/step1.blend
[ -f "$W/finger_joints.json" ] && mv -f "$W/finger_joints.json" "$W/finger_joints.prev.json"
run build_rig.py
run fit_fingers.py $W/rig_v1.blend
run finger_joints.py $W/rig_v1.blend
run build_rig.py
run hand_frame_check.py $W/rig_v1.blend
fi
if [ "$STAGE" = all ] || [ "$STAGE" = anim ]; then
mapfile -t SETC < <(sed -e "s|\$L|$L|" "$here/scripts/set_clips.txt" | grep -v '^#' | grep .)
mapfile -t MXC < <(sed -e "s|\$MX|$MX|" "$here/scripts/mx_clips.txt" | grep -v '^#' | grep .)
run retarget.py $W/rig_v1.blend $W/rig_v2s.blend "${SETC[@]}"
run retarget_mixamo.py $W/rig_v2s.blend $W/rig_v2r.blend "${MXC[@]}"
run run_fit.py $W/rig_v2r.blend $W/rig_v2f.blend
run foot_level.py $W/rig_v2f.blend $W/rig_v2l.blend Standing Walking:const Hit Cast Attack Fidget Death:until=24
cp -f $W/rig_v2l.blend $W/rig_v2st0.blend
${ARMPUSH:-true} && run arm_push.py $W/rig_v2st0.blend $W/rig_v2st.blend ${ARMPUSH_ARGS:-Attack:R:21:30:38:-0.03,-0.06,0.24 Attack:R:31:40:50:-0.10,-0.12,0.03}
[ "${UNTIL:-}" = push ] && exit 0
if [ -f $W/measure_ref.blend ] && [ -n "${CLEAR:-}" ]; then
EASE=8 run elbow_clear.py $W/rig_v2st.blend $W/rig_v2sc.blend $W/measure_ref.blend $CLEAR
else cp -f $W/rig_v2st.blend $W/rig_v2sc.blend; fi
run wrist_ease.py $W/rig_v2sc.blend $W/rig_v2e.blend Cast:R Cast:L Attack:R Attack:L Death:L Death:R Walking:L Walking:R Fidget:L Fidget:R
run forearm_hinge.py $W/rig_v2e.blend $W/rig_v2.blend
FA=0.6 FA_RAMP=0.15,0.85 run twist_bones.py $W/rig_v2.blend $W/rig_v2t.blend
run panel_bones.py $W/rig_v2t.blend $W/rig_v2p.blend
run weights_fix.py $W/rig_v2p.blend $W/rig_v3.blend
run finger_weights.py $W/rig_v3.blend $W/rig_v4f.blend
run reduce_rigged.py $W/rig_v4f.blend $W/rig_v4r.blend
run fingers_relax.py $W/rig_v4r.blend $W/rig_v4.blend
run clip_timing.py $W/rig_v4.blend $W/rig_v5.blend
fi
