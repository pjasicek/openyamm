#!/bin/sh
# Replayable animation chain (run from the project directory): Meshy rig (+ jaw bone) -> Mixamo Mutant retargets ->
# native-timed clips work/rig_v2.blend -> audit -> rig_v3 with the head split (same head UVs as the head retexture).
set -e
B="/snap/bin/blender --background"
$B --python scripts/build_rig_wfigt1.py | grep -E "RIGID|JAW|FLOOR|Error|Traceback"
$B work/rig_v1.blend --python scripts/retarget_fbx.py -- mixamo/mutant_walking.fbx:MxWalk mixamo/mutant_run.fbx:MxRun \
  mixamo/mutant_swiping.fbx:MxSwipe mixamo/mutant_roaring.fbx:MxRoar mixamo/mutant_dying.fbx:MxDeath \
  mixamo/mutant_breathing_idle.fbx:MxIdle mixamo/mutant_flexing_muscles.fbx:MxFlex \
  mixamo/zombie_reaction_hit.fbx:MxHit | grep -E "RETARGET|Error|Traceback"
$B --python scripts/build_clips_wfigt1.py | grep -E "CLIP|FLOOR|Error|Traceback"
$B --python scripts/pose_audit.py -- rig_v2.blend | grep -E "AUDIT|Error"
cp work/rig_v2.blend work/rig_v3.blend
$B work/rig_v3.blend --python ../claude_shared/head_texture_split.py -- --mesh Werewolf --rig Werewolf_Rig \
  --out texturing/wfigt1_head_upload.glb --groups Head Jaw --parts 0 6 7 8 --whole-parts 6 7 | grep HEAD_SPLIT
