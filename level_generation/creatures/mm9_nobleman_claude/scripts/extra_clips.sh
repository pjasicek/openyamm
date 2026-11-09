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
Q $G scripts/clips_mm9.py work/nb_body.glb work/x0.glb scripts/roles_nb_extra.json work/clips_extra.json
Q $G scripts/arm_const.py work/x0.glb work/x1.glb $(cat scripts/arm_const.txt)
Q $G scripts/half_keys.py work/x1.glb work/x2.glb
Q $G scripts/skirt_keys.py work/x2.glb work/x3.glb work/skirt_report_extra.json
Q $G $GR $E work/x3.glb work/g0.glb --clip CowerStart --clip CowerLoop --clip CowerEnd
Q $G $F work/g0.glb work/g1.glb --raise CowerStart --raise CowerLoop --raise CowerEnd --smooth-hold 0.2 --smooth CowerStart 0.08 --smooth-loop CowerLoop 0.08 --smooth CowerEnd 0.08
Q $G $GR $E work/g1.glb export/mm9_nobleman.glb --clip CowerStart --clip CowerLoop --clip CowerEnd
