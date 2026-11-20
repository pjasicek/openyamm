#!/usr/bin/env bash
# Dropped MM9 clips (run2-clips-groupD, 2026-10-31; the user lifted the approved-project hold for clip grafting only):
# die2, Backpedal, BackpedalRun, through this project's clip steps (build_runtime.sh), grafted onto the installed export
# with claude_shared/graft_clips.py so meshes, LODs, variants and accepted clips stay byte for byte. Steps: clips_mm9.py
# (roles_lich_extra.json, soft joint-offset line, Dead2 = die2's last pose held; no hand_rest: these hands stay off the thigh)
# -> graft into export/mm9_lich_glow.glb (before cloth_flat) -> cloth_flat_extra.py (copy of cloth_flat.py on Death2/Dead2)
# -> floor_fix.py (floor_ops_extra.txt) -> mirror_glb.py -> graft onto work/pre_clips_export.glb (the installed export before).
set -euo pipefail
cd "$(dirname "$0")/.."
G=../claude_shared/gltf_venv/bin/python; F=../claude_shared/floor/floor_fix.py; GR=../claude_shared/graft_clips.py
Q() { "$@" 2>&1 | grep -v "Unexpected value\|RuntimeWarning" ; }
NEW="--clip Death2 --clip Dead2 --clip Backpedal --clip BackpedalRun"
Q $G scripts/clips_mm9.py work/lich_body_tex.glb work/extra_raw.glb scripts/roles_lich_extra.json work/clips_extra.json | tail -1
Q $G $GR export/mm9_lich_glow.glb work/extra_raw.glb work/extra_g0.glb $NEW | tail -1
Q $G -W ignore scripts/cloth_flat_extra.py work/extra_g0.glb work/extra_flat.glb | tail -9
Q $G -W ignore $F work/extra_flat.glb work/extra_floor.glb $(cat scripts/floor_ops_extra.txt) --ground-death Death2 Dead2 | tail -4
Q $G -W ignore scripts/mirror_glb.py work/extra_floor.glb work/extra_mirrored.glb
Q $G $GR ${EXPORT:-work/pre_clips_export.glb} work/extra_mirrored.glb work/mm9_lich_grafted.glb $NEW | tail -1
Q $G ../claude_shared/graft_byte_check.py ${EXPORT:-work/pre_clips_export.glb} work/mm9_lich_grafted.glb
