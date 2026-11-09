#!/usr/bin/env bash
# Dropped MM9 clips (run2-clips-groupD, 2026-10-31; the user lifted the approved-project hold for clip grafting only):
# the MM9 IMP.abc clips the accepted build left out, through this project's own clip steps (build_runtime.sh), then
# grafted onto the installed export with claude_shared/graft_clips.py so meshes, LODs, variants and the accepted clips
# stay byte for byte. Steps: clips_mm9.py (roles_imp_extra.json: soft joint-offset line, grip.json fist, Dead2 = die2's
# last pose held) -> trident_clear.py (as the accepted Fidget/Hit/Death; Fidget2
# through trident_clear_wide.py) -> graft into the accepted split body
# (work/split4.glb: trident split off, before the floor pass) -> floor_fix.py (floor_ops_extra*.txt, the accepted ops of
# the same kinds) -> mirror_glb.py -> graft the new clips onto work/pre_clips_export.glb (the installed export before
# this pass). MM9's Hattack1 carries Rattack1's keys (installed as AttackRanged), so attack_melee2 binds AttackRanged.
# Run from the project folder; then check_winding, tools/install_model.py --world mm9, bind_script_clips.py.
set -euo pipefail
cd "$(dirname "$0")/.."
G=../claude_shared/gltf_venv/bin/python; F=../claude_shared/floor/floor_fix.py; GR=../claude_shared/graft_clips.py
Q() { "$@" 2>&1 | grep -v "Unexpected value\|RuntimeWarning" ; }
NEW="--clip Fidget2 --clip Aware --clip Hit2 --clip Death2 --clip Dead2 --clip Backpedal --clip BackpedalRun"
Q $G scripts/clips_mm9.py work/imp_body_tex.glb work/extra_raw.glb scripts/roles_imp_extra.json work/clips_extra.json | tail -1
Q python3 scripts/trident_clear.py work/extra_raw.glb work/extra_clear1.glb Aware Hit2 Death2 Dead2
# Fidget2: the accepted constants left the trident head 3.0 cm in the head on one 48 fps frame; the wider copy leaves 0.5 cm
Q python3 scripts/trident_clear_wide.py work/extra_clear1.glb work/extra_clear.glb Fidget2
Q $G $GR work/split4.glb work/extra_clear.glb work/extra_g0.glb $NEW | tail -1
Q $G $F work/extra_g0.glb work/extra_f1.glb $(cat scripts/floor_ops_extra.txt) --ground-death Death2 Dead2
Q $G $F work/extra_f1.glb work/extra_f2.glb $(cat scripts/floor_ops_extra_hit.txt)
Q python3 scripts/mirror_glb.py work/extra_f2.glb work/extra_mirrored.glb
Q $G $GR ${EXPORT:-work/pre_clips_export.glb} work/extra_mirrored.glb work/mm9_imp_grafted.glb $NEW | tail -1
Q $G ../claude_shared/graft_byte_check.py ${EXPORT:-work/pre_clips_export.glb} work/mm9_imp_grafted.glb
# viewer/blade-gate copy with the trident: the same clips on the full GLB
Q $G $GR export/mm9_imp_full.glb work/extra_mirrored.glb work/full_extra.glb $NEW | tail -1
