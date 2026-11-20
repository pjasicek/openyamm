#!/usr/bin/env bash
# Dropped MM9 clips (run2-clips-groupB, 2026-10-31): build the new clips with this project's own clip route (soft joint-offset
# line in clips_mm9.py), floor them in a copy of the installed export, then graft only the new clips onto the export with
# claude_shared/graft_clips.py, so meshes, LODs, variants and the accepted clips stay byte for byte. Run from the project
# folder on the accepted export (work/pre_clips_export.glb holds the export before this step). Then install with
# tools/install_model.py and bind the clips in actors.yml script_clips (bind_actors.py carries them).
set -euo pipefail
cd "$(dirname "$0")/.."
G=../claude_shared/gltf_venv/bin/python; F=../claude_shared/floor/floor_fix.py; GR=../claude_shared/graft_clips.py
Q() { "$@" 2>&1 | grep -v "Unexpected value\|RuntimeWarning" ; }
E=${EXPORT:-work/pre_clips_export.glb}
Q $G scripts/clips_mm9.py work/zombie_body_tex.glb work/zombie_extra_clips.glb scripts/roles_zombie_extra.json work/clips_extra.json
cp work/arm_bump.json work/arm_bump_accepted.json.bak
Q $G scripts/arm_bump.py work/zombie_extra_clips.glb work/zombie_extra_bump.glb Coffin2:L Coffin2:R Wakeup2:L Wakeup2:R
mv work/arm_bump.json work/arm_bump_extra.json; mv work/arm_bump_accepted.json.bak work/arm_bump.json
# Dead here is Death2's corpse, only for --ground-death; it is not grafted
Q $G $GR $E work/zombie_extra_bump.glb work/zombie_g0.glb --clip Death2 --clip Dead --clip Wakeup2 --clip Coffin2 --replace
Q $G $F work/zombie_g0.glb work/zombie_g1.glb --raise Wakeup2 --raise Coffin2 --ground-death Death2 Dead
Q $G $GR $E work/zombie_g1.glb export/mm9_zombie.glb --clip Death2 --clip Wakeup2 --clip Coffin2
