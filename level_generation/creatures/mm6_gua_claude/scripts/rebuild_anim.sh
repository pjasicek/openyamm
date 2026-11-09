#!/bin/sh
# Replayable animation chain for the guard (run from the project directory):
# rig (Meshy weights, rigid fists/head, feet, wrists) -> halberd seat -> carry -> attack -> hit -> death -> audit.
set -e
B="/snap/bin/blender --background --python"
$B scripts/build_rig_gua.py -- meshy/anim_death_v1/result_animation_glb_url.glb:DyingSrc | grep -E "RIGID|FLOOR|FEET"
$B scripts/seat_halberd.py | grep -E "TUNNEL|WIDEN"
$B scripts/carry_halberd.py | grep -E "STANDING|CARRY"
$B scripts/attack_halberd.py | grep -E "ROLL|flips"
$B scripts/hit_halberd.py | grep -E "flips"
$B scripts/death_halberd.py | grep -E "flips"
# forearm twist bones: weights split along the forearm, every clip's hand twist baked into them
/snap/bin/blender --background work/rig_v6.blend --python scripts/twist_gua.py -- setup | grep TWIST
/snap/bin/blender --background work/rig_v6.blend --python scripts/twist_gua.py -- bake | grep TWIST
$B scripts/pose_audit.py -- rig_v6.blend | grep AUDIT
# head texture set: copy the animated master and split the head (parts Head, Coif, Helmet, Nasal) onto its own UVs
cp work/rig_v6.blend work/rig_v7.blend
/snap/bin/blender --background work/rig_v7.blend --python ../claude_shared/head_texture_split.py -- --mesh Guard \
  --rig Guard_Rig --out texturing/gua_head_upload.glb --groups Head --parts 4 5 6 7 --whole-parts 4 5 6 7 | grep HEAD_SPLIT
