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
# Death and Dead are built only because skirt_keys.py and dead_hold.py need them; not grafted
Q $G scripts/clips_mm9.py work/guard_body_tex.glb work/x0.glb scripts/roles_guard_extra.json work/clips_extra.json
Q $G scripts/finger_keys.py work/x0.glb work/x1.glb work/hand_poses.json
Q $G scripts/helper_keys.py work/x1.glb work/x2.glb
Q $G scripts/skirt_keys.py work/x2.glb work/x3.glb work/skirt_keys_extra.json
eval "$G scripts/hand_rest.py work/x3.glb work/x4.glb $(cat scripts/hand_rest_guard_extra.txt)" 2>&1 | grep -v "Unexpected value\|RuntimeWarning"
Q $G scripts/dead_hold.py work/x4.glb work/x5.glb
Q $G scripts/helper_keys.py work/x5.glb work/x6.glb
Q $G $GR $E work/x6.glb work/g0.glb --clip CowerLoop
# seat the loop on the accepted CowerStart end / CowerEnd start (hand push, skirt, floor carry over), then fade a
# second hand push in and out over the loop: MM9's tremble brings the fist 3 cm into the helmet mid-loop
Q $G scripts/match_loop.py work/g0.glb work/g1.glb CowerLoop CowerStart CowerEnd
eval "$G scripts/hand_rest.py work/g1.glb work/g1h.glb $(cat scripts/hand_rest_guard_extra.txt)" 2>&1 | grep -v "Unexpected value\|RuntimeWarning"
Q $G scripts/helper_keys.py work/g1h.glb work/g1hh.glb
Q $G scripts/blend_window.py work/g1.glb work/g1hh.glb work/g1b.glb CowerLoop 2
Q $G scripts/helper_keys.py work/g1b.glb work/g1c.glb
Q $G $GR $E work/g1c.glb export/mm9_guard.glb --clip CowerLoop
