#!/usr/bin/env bash
# Dropped MM9 clips (run2-clips-groupC, 2026-10-31): build the MM9 clips the accepted export left out with this
# project's own clips_mm9.py (scripts/extra_clips_blend.py on work/graft_v7.blend, the blend build_export.py opens), graft them into
# a copy of the accepted export, floor them with the passes build_runtime.sh gives accepted clips of the same kind, then
# graft only the new clips onto the accepted export with claude_shared/graft_clips.py, so meshes, LODs, variants and
# accepted clips stay byte for byte. Ctl_* controls go through the same steps and are compared with the installed clips.
# Written by claude_shared/make_extra_clips.py from scripts/extra_clips.json.
# Flier rule as build_runtime.sh: hover 0.4252 on every living clip, Death2 eases it out and is grounded on a temporary
# Dead2. MM9's stand and fidget1 are the crow on the ground (Perch, PerchFidget): ground-looped after the hover so its
# feet are on the floor. A new living clip still under the floor takes one --raise-uniform lift.
# Usage: TOK=<lease token> scripts/extra_clips.sh   (work/pre_clips_export.glb = the export before this step)
set -euo pipefail
cd "$(dirname "$0")/.."
here="$PWD"; repo="$(cd ../../.. && pwd)"; name=$(basename "$here" | sed 's/_claude$//')
G=../claude_shared/gltf_venv/bin/python; F=../claude_shared/floor/floor_fix.py; FS=scripts/floor_smooth.py
GR=../claude_shared/graft_clips.py
Q() { "$@" 2>&1 | grep -v "Unexpected value\|RuntimeWarning" ; }
E=${EXPORT:-work/pre_clips_export.glb}
(cd "$repo" && tools/run_creature_blender.sh --token "$TOK" level_generation/creatures/$(basename "$here")/scripts/extra_clips_blend.py \
  "$here/work/graft_v7.blend" "$here/work/extra_raw.glb" "$here/work/clips_extra.json" | tail -1)
Q $G $GR $E work/extra_raw.glb work/g0.glb --clip Perch --clip PerchFidget --clip Hit2 --clip Death2 --clip Ctl_Fidget --clip Ctl_Death --clip Dead2 --clip Ctl_Dead | tail -1
Q $G $F work/g0.glb work/gc.glb --hover 0.425200 Ctl_Death Ctl_Dead --ground-death Ctl_Death Ctl_Dead | tail -2
echo "control Ctl_Fidget vs Fidget"; Q $G ../claude_shared/compare_clips.py work/gc.glb Ctl_Fidget $E Fidget | tail -3
echo "control Ctl_Death vs Death"; Q $G ../claude_shared/compare_clips.py work/gc.glb Ctl_Death $E Death | tail -3
echo "control Ctl_Dead vs Dead"; Q $G ../claude_shared/compare_clips.py work/gc.glb Ctl_Dead $E Dead | tail -3
Q $G $F work/g0.glb work/gn_0.glb --hover 0.425200 Death2 Dead2 --ground-death Death2 Dead2 | tail -2
Q $G $F work/gn_0.glb work/gn.glb --ground-loop Perch --ground-loop PerchFidget --raise-uniform Hit2 | tail -2
Q $G $GR $E work/gn.glb export/$name.glb --clip Perch --clip PerchFidget --clip Hit2 --clip Death2 | tail -1
Q $G ../claude_shared/graft_byte_check.py $E export/$name.glb
