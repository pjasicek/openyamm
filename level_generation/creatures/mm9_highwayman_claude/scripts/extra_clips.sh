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
# Death and Dead are built only because skirt_keys.py needs them; not grafted
Q $G scripts/clips_mm9.py work/hw_body.glb work/x0.glb scripts/roles_hw_extra.json work/clips_extra.json
Q $G scripts/finger_keys.py work/x0.glb work/x1.glb work/hand_poses.json
# the accepted Cower's arm_out L -14 deg (0.5-1.7 s) split over the phases: rises into the crouch, held, eases out
Q $G scripts/arm_out.py work/x1.glb work/x1b.glb CowerStart:L:0.2:1.0:-14 CowerLoop:L:-1000:1000.9:-14 CowerEnd:L:-0.4:0.4:-14
Q $G scripts/half_keys.py work/x1b.glb work/x2.glb
Q $G scripts/skirt_keys.py work/x2.glb work/x3.glb work/skirt_report_extra.json
Q $G scripts/dagger_hide.py work/x3.glb work/x4.glb
Q $G $GR $E work/x4.glb work/g0.glb --clip CowerStart --clip CowerLoop --clip CowerEnd
Q $G $F work/g0.glb work/g1.glb --raise CowerStart --raise CowerLoop --raise CowerEnd --smooth-hold 0.2 --smooth CowerStart 0.08 --smooth-loop CowerLoop 0.08 --smooth CowerEnd 0.08
Q $G $GR $E work/g1.glb export/mm9_highwayman.glb --clip CowerStart --clip CowerLoop --clip CowerEnd
