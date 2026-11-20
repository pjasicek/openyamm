#!/bin/sh
# Replayable animation chain (run from the project directory): Meshy rig + library clips -> work/rig_v1.blend ->
# native-timed clips work/rig_v2.blend -> audit -> rig_v3 with the head split (same head UVs as the head retexture).
set -e
B="/snap/bin/blender --background"
M=meshy
$B --python scripts/build_rig_ttn.py -- $M/anim_cast_v1/result_animation_glb_url.glb:CastSrc \
  $M/anim_hit_v1/result_animation_glb_url.glb:HitSrc $M/anim_death_v2/result_animation_glb_url.glb:DeathSrc \
  $M/anim_idle_v1/result_animation_glb_url.glb:IdleSrc $M/anim_fidget_v1/result_animation_glb_url.glb:FidgetSrc \
  $M/anim_hook_v1/result_animation_glb_url.glb:HookSrc $M/anim_uppercut_v1/result_animation_glb_url.glb:UppercutSrc \
  | grep -E "RIGID|FLOOR|SHOULDERS|Error|Traceback"
$B work/rig_v1.blend --python scripts/retarget_fbx.py -- mixamo/standing_1h_magic_attack_01.fbx:Mx1HSrc \
  mixamo/two_hand_spell_casting.fbx:Mx2HSrc | grep -E "RETARGET|Error|Traceback"
$B --python scripts/build_clips_ttn.py | grep -E "CLIP|FLOOR|Error|Traceback"
$B --python scripts/pose_audit.py -- rig_v2.blend | grep -E "AUDIT|Error"
cp work/rig_v2.blend work/rig_v3.blend
$B work/rig_v3.blend --python ../claude_shared/head_texture_split.py -- --mesh Titan --rig Titan_Rig \
  --out texturing/ttn_head_upload.glb --groups Head --parts 0 9 10 11 12 --whole-parts 9 10 11 12 | grep HEAD_SPLIT
