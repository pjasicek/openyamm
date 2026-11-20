#!/usr/bin/env bash
# Dropped MM9 clips (run2-clips-groupC, 2026-10-31): build the MM9 clips the accepted export left out with this
# project's own clips_mm9.py (scripts/extra_clips_blend.py on work/uv_v2.blend, the blend build_export.py opens), graft
# them into a copy of the accepted export, floor them as build_runtime.sh floors the accepted clips (scripts/floor_smooth.py:
# Death2 grounded on a temporary Dead2, as Death). The installed Fidget and Hit are NOT what build_runtime.sh's --raise
# gives today (the raw clips float 0.9-1.9 cm, the installed ones touch the floor); floor_fix.py --ground-loop reproduces
# Fidget within 0.04 cm and Hit within 0.56 cm, so every new living clip takes --ground-loop, low-passed 0.08 s), then graft only the new clips onto the accepted
# export with claude_shared/graft_clips.py, so meshes, LODs, variants and accepted clips stay byte for byte. Ctl_*
# controls (Fidget1, Walk, Die1) go through the same steps and are compared with the installed clips.
# Usage: TOK=<lease token> scripts/extra_clips.sh   (work/pre_clips_export.glb = the export before this step)
set -euo pipefail
cd "$(dirname "$0")/.."
here="$PWD"; repo="$(cd ../../.. && pwd)"; name=$(basename "$here" | sed 's/_claude$//')
G=../claude_shared/gltf_venv/bin/python; FS=scripts/floor_smooth.py; F=../claude_shared/floor/floor_fix.py; GR=../claude_shared/graft_clips.py
Q() { "$@" 2>&1 | grep -v "Unexpected value\|RuntimeWarning" ; }
E=${EXPORT:-work/pre_clips_export.glb}
NEW=(Fidget2 Fidget3 Tipover Standup Tipover2 Standup2 Hit2 Death2)
GROUND=(Fidget2 Fidget3 Tipover Standup Tipover2 Standup2 Hit2)
CTL=(Ctl_Fidget:Fidget Ctl_Walking:Walking Ctl_Death:Death Ctl_Dead:Dead Ctl_Hit:Hit)
(cd "$repo" && tools/run_creature_blender.sh --token "$TOK" level_generation/creatures/$(basename "$here")/scripts/extra_clips_blend.py \
  "$here/work/uv_v2.blend" "$here/work/extra_raw.glb" "$here/work/clips_extra.json" | tail -1)
Q $G $GR $E work/extra_raw.glb work/g0.glb $(for c in "${NEW[@]}" Dead2 Ctl_Fidget Ctl_Walking Ctl_Death Ctl_Dead Ctl_Hit; do echo --clip $c; done) | tail -1
Q $G $F work/g0.glb work/g0c.glb --ground-loop Ctl_Fidget | tail -1
Q $G $FS work/g0c.glb work/gc.glb --loop Ctl_Walking --raise Ctl_Hit --ground-death Ctl_Death Ctl_Dead | tail -1
Q $G $F work/g0.glb work/g0g.glb $(for c in "${GROUND[@]}"; do echo --ground-loop $c --smooth $c 0.08; done) | tail -1
Q $G $FS work/g0g.glb work/g1.glb --ground-death Death2 Dead2 | tail -1
for p in "${CTL[@]}"; do echo "control ${p%%:*} vs ${p##*:}"; Q $G ../claude_shared/compare_clips.py work/gc.glb ${p%%:*} $E ${p##*:} | tail -3; done
Q $G $GR $E work/g1.glb export/$name.glb $(for c in "${NEW[@]}"; do echo --clip $c; done) | tail -1
Q $G ../claude_shared/graft_byte_check.py $E export/$name.glb
