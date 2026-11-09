#!/usr/bin/env bash
# Dropped MM9 clips (run2-clips-groupC, 2026-10-31). RAM.abc has only its setup pose: the ram plays SHEEP.abc's clips
# through the sheep's animated master (ram_export.py). So it takes the sheep's new clips as built by
# ../mm9_sheep_claude/scripts/extra_clips.sh (work/extra_raw.glb there: fidget2, Hattack2, wince2, die2 with the sheep's
# clips_mm9.py), grafted into a copy of the accepted ram export, floored as build_runtime.sh floors the accepted clips
# (ground-loop fidget, raise strike and hit, Death2 grounded on a temporary Dead2, then scripts/smooth_floor.py with
# work/smooth_extra.json), then only the new clips grafted onto the accepted export with claude_shared/graft_clips.py.
# Ctl_* controls (fidget1, Hattack1, die1) go through the same steps and are compared with the installed clips.
# Usage: scripts/extra_clips.sh (after the sheep's; work/pre_clips_export.glb = the export before this step)
set -euo pipefail
cd "$(dirname "$0")/.."
G=../claude_shared/gltf_venv/bin/python; F=../claude_shared/floor/floor_fix.py; GR=../claude_shared/graft_clips.py
Q() { "$@" 2>&1 | grep -v "Unexpected value\|RuntimeWarning" ; }
E=${EXPORT:-work/pre_clips_export.glb}; S=../mm9_sheep_claude/work/extra_raw.glb
Q $G $GR $E $S work/g0.glb $(for c in Fidget2 AttackMelee2 Hit2 Death2 Dead2 Ctl_Fidget Ctl_AttackMelee Ctl_Death Ctl_Dead; do echo --clip $c; done) | tail -1
Q $G $F work/g0.glb work/gc_0.glb --ground-loop Ctl_Fidget --raise Ctl_AttackMelee --ground-death Ctl_Death Ctl_Dead | tail -1
Q $G scripts/smooth_floor.py work/g0.glb work/gc_0.glb work/gc.glb work/smooth_extra.json | tail -1
for p in Ctl_Fidget:Fidget Ctl_AttackMelee:AttackMelee Ctl_Death:Death Ctl_Dead:Dead; do echo "control ${p%%:*} vs ${p##*:}"; Q $G ../claude_shared/compare_clips.py work/gc.glb ${p%%:*} $E ${p##*:} | tail -3; done
Q $G $F work/g0.glb work/gn_0.glb --ground-loop Fidget2 --raise AttackMelee2 --raise Hit2 --ground-death Death2 Dead2 | tail -1
Q $G scripts/smooth_floor.py work/g0.glb work/gn_0.glb work/gn.glb work/smooth_extra.json | tail -1
Q $G $GR $E work/gn.glb export/mm9_ram.glb --clip Fidget2 --clip AttackMelee2 --clip Hit2 --clip Death2 | tail -1
Q $G ../claude_shared/graft_byte_check.py $E export/mm9_ram.glb
