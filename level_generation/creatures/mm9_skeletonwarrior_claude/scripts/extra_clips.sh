#!/usr/bin/env bash
# Dropped MM9 clips (run2-clips-groupD, 2026-10-31; the user lifted the approved-project hold for clip grafting only): the
# SKELETONWARRIOR.abc clips the accepted build left out, through this project's clip steps (rebuild.sh, build_runtime.sh),
# grafted onto the installed export with claude_shared/graft_clips.py so meshes, LODs, variants and accepted clips stay
# byte for byte. MM9 fidget2 carries ResurrectSpell's keys: bound, not grafted.
#  1. clips_mm9.py (roles_skelwar_extra.json: thin keys, root lift, soft joint-offset line, Dead2 = die2's last pose held),
#     on the body and on the approved before-skirt body (work/before_skirt/final_clips.glb: the plate-fit reference);
#  2. finger_keys.py, release 0.600 s (RAttack1OLD's RangeAttack): the throw hand goes to the clip named AttackRanged,
#     so RAttack1OLD is built under that name and renamed AttackRangedOld (rename_clip.py);
#  3. skirt_keys_extra.py (copy of skirt_keys.py: Backpedal loops, Death2/Dead2 like Death/Dead);
#  4. graft into export/mm9_skelwar_skins.glb (before the floor) -> floor_fix.py (floor_ops_extra.txt, ops of the accepted
#     clips of the same kinds) -> skirt_floor_extra.py (copy of skirt_floor.py: Death2/Dead2 keep the before-skirt body's
#     floored root, plates turned clear) -> floor_fix.py --ground-death again (that root left the corpse 2.9 cm up);
#  5. graft the new clips onto work/pre_clips_export.glb (the installed export before this pass).
set -euo pipefail
cd "$(dirname "$0")/.."
G=../claude_shared/gltf_venv/bin/python; F=../claude_shared/floor/floor_fix.py; GR=../claude_shared/graft_clips.py
Q() { "$@" 2>&1 | grep -v "Unexpected value\|RuntimeWarning" ; }
NEW="--clip Search --clip AttackMeleeOld --clip AttackRangedOld --clip Hit2 --clip Death2 --clip Dead2 --clip Backpedal --clip BackpedalRun"
Q $G scripts/clips_mm9.py work/skelwar_body_tex.glb work/extra_clips.glb scripts/roles_skelwar_extra.json work/clips_extra.json | tail -1
Q $G scripts/clips_mm9.py work/before_skirt/final_clips.glb work/extra_old_raw.glb scripts/roles_skelwar_extra.json work/clips_extra_old.json | tail -1
Q $G scripts/finger_keys.py work/extra_clips.glb work/extra_fingers0.glb work/hand_poses.json 0.600
Q $G scripts/rename_clip.py work/extra_fingers0.glb work/extra_fingers.glb AttackRanged=AttackRangedOld
Q $G scripts/rename_clip.py work/extra_old_raw.glb work/extra_old.glb AttackRanged=AttackRangedOld
Q $G scripts/skirt_keys_extra.py work/extra_fingers.glb work/extra_old.glb work/extra_final.glb work/skirt_keys_extra.json | grep -E "^(CLIP|SKIRT)" | cut -c1-180
Q $G $GR export/mm9_skelwar_skins.glb work/extra_final.glb work/extra_g0.glb $NEW | tail -1
Q $G $F work/extra_g0.glb work/extra_f1.glb $(cat scripts/floor_ops_extra.txt) --ground-death Death2 Dead2
Q $G $GR work/before_skirt/mm9_skelwar.glb work/extra_old.glb work/extra_old_g0.glb --clip Death2 --clip Dead2 | tail -1
Q $G $F work/extra_old_g0.glb work/extra_old_floor.glb --ground-death Death2 Dead2
Q $G scripts/skirt_floor_extra.py work/extra_f1.glb work/extra_old_floor.glb work/extra_f2.glb
Q $G $F work/extra_f2.glb work/extra_f3.glb --ground-death Death2 Dead2
Q $G $GR ${EXPORT:-work/pre_clips_export.glb} work/extra_f3.glb work/mm9_skelwar_grafted.glb $NEW | tail -1
Q $G ../claude_shared/graft_byte_check.py ${EXPORT:-work/pre_clips_export.glb} work/mm9_skelwar_grafted.glb
