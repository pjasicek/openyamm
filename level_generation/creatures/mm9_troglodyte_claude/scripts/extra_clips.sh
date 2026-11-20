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
Q $G scripts/clips_mm9.py work/body.glb work/extra_raw.glb scripts/roles_trog_extra.json work/clips_extra.json
Q $G scripts/half_keys.py work/extra_raw.glb work/extra_half.glb
Q $G scripts/half_keys.py work/extra_half.glb work/extra_final.glb
Q $G $GR $E work/extra_final.glb work/g0.glb --clip Backpedal --clip BackpedalRun
Q $G $F work/g0.glb work/g1.glb --ground-loop Backpedal --raise BackpedalRun --smooth-hold 0 --smooth-loop Backpedal 0.06 --smooth-loop BackpedalRun 0.05
Q $G $GR $E work/g1.glb export/mm9_troglodyte.glb --clip Backpedal --clip BackpedalRun
