#!/usr/bin/env bash
# m242 (ghost) replayable chain. Every Blender step through b.sh (memory-capped, own log). TOKEN = workspace lease.
#   STAGE=rig : step1_clean (pieces, cloth flag, joints from the bone pieces) -> build_rig (source frames, rigid piece
#               weights, no Meshy auto-rig) -> robe_rig (24 robe chain bones, cloth weights)
#   STAGE=anim: retarget_mixamo (upper bodies) -> ghost_motion (hover, swoop, attack window, robe waves, death)
#               -> ghost_gates
set -euo pipefail
cd "$(dirname "$0")/.."
: "${TOKEN:?set TOKEN}"; export CAP=${CAP:-8G}
W=$PWD/work; MX=/home/pjasicek/github/OpenYAMM/anim_library/mixamo; B=scripts/b.sh
STAGE=${STAGE:-all}
if [ "$STAGE" = all ] || [ "$STAGE" = rig ]; then
PAT="CLEAN|JOINTS" $B step1_clean.py $W/st_v1_parts.blend $W/step1.blend
PAT="RIG|WEIGHTS" $B build_rig.py
PAT=ROBE $B robe_rig.py $W/rig_v1.blend $W/rig_v1r.blend
fi
if [ "$STAGE" = all ] || [ "$STAGE" = anim ]; then
PAT=RETARGET $B retarget_mixamo.py $W/rig_v1r.blend $W/rig_v2r.blend "$MX/Zombie Idle.fbx:Standing" "$MX/Zombie Walk.fbx:Walking:plant" \
  "$MX/Zombie Attack.fbx:Attack:plant" "$MX/Zombie Reaction Hit.fbx:Hit:plant" "$MX/Zombie Scream.fbx:Fidget:plant" "$MX/Zombie Idle.fbx:Death"
PAT="CLIP|IMPACT" $B ghost_motion.py $W/rig_v2r.blend $W/rig_v3.blend
PAT=GATE $B ghost_gates.py $W/rig_v3.blend
fi
