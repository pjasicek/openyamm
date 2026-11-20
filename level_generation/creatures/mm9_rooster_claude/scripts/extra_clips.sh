#!/usr/bin/env bash
# Dropped MM9 clips (run2-clips-groupC, 2026-10-31): build the MM9 clips the accepted export left out with this
# project's own clips_mm9.py (scripts/extra_clips_blend.py on work/uv_v1c.blend, the blend build_export.py opens), graft them into
# a copy of the accepted export, floor them with the passes build_runtime.sh gives accepted clips of the same kind, then
# graft only the new clips onto the accepted export with claude_shared/graft_clips.py, so meshes, LODs, variants and
# accepted clips stay byte for byte. Ctl_* controls go through the same steps and are compared with the installed clips.
# Written by claude_shared/make_extra_clips.py from scripts/extra_clips.json.
# Floor as build_runtime.sh: ground-loop for the fidget, raise for the hit (low-passed 0.06 s), Death2 grounded on a
# temporary Dead2 (low-passed 0.08 s).
# Usage: TOK=<lease token> scripts/extra_clips.sh   (work/pre_clips_export.glb = the export before this step)
set -euo pipefail
cd "$(dirname "$0")/.."
here="$PWD"; repo="$(cd ../../.. && pwd)"; name=$(basename "$here" | sed 's/_claude$//')
G=../claude_shared/gltf_venv/bin/python; F=../claude_shared/floor/floor_fix.py; FS=scripts/floor_smooth.py
GR=../claude_shared/graft_clips.py
Q() { "$@" 2>&1 | grep -v "Unexpected value\|RuntimeWarning" ; }
E=${EXPORT:-work/pre_clips_export.glb}
(cd "$repo" && tools/run_creature_blender.sh --token "$TOK" level_generation/creatures/$(basename "$here")/scripts/extra_clips_blend.py \
  "$here/work/uv_v1c.blend" "$here/work/extra_raw.glb" "$here/work/clips_extra.json" | tail -1)
Q $G $GR $E work/extra_raw.glb work/g0.glb --clip Fidget2 --clip Hit2 --clip Death2 --clip Ctl_Fidget --clip Ctl_Hit --clip Ctl_Death --clip Dead2 --clip Ctl_Dead | tail -1
Q $G $F work/g0.glb work/gc.glb --ground-loop Ctl_Fidget --raise Ctl_Hit --ground-death Ctl_Death Ctl_Dead --smooth Ctl_Hit 0.06 --smooth Ctl_Death 0.08 | tail -2
echo "control Ctl_Fidget vs Fidget"; Q $G ../claude_shared/compare_clips.py work/gc.glb Ctl_Fidget $E Fidget | tail -3
echo "control Ctl_Hit vs Hit"; Q $G ../claude_shared/compare_clips.py work/gc.glb Ctl_Hit $E Hit | tail -3
echo "control Ctl_Death vs Death"; Q $G ../claude_shared/compare_clips.py work/gc.glb Ctl_Death $E Death | tail -3
echo "control Ctl_Dead vs Dead"; Q $G ../claude_shared/compare_clips.py work/gc.glb Ctl_Dead $E Dead | tail -3
Q $G $F work/g0.glb work/gn.glb --ground-loop Fidget2 --raise Hit2 --ground-death Death2 Dead2 --smooth Hit2 0.06 --smooth Death2 0.08 | tail -2
Q $G $GR $E work/gn.glb export/$name.glb --clip Fidget2 --clip Hit2 --clip Death2 | tail -1
Q $G ../claude_shared/graft_byte_check.py $E export/$name.glb
