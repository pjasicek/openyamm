#!/usr/bin/env bash
# Dropped MM9 clips (run2-clips-groupC, 2026-10-31): build the MM9 clips the accepted export left out with this
# project's own clips_mm9.py (scripts/extra_clips_blend.py on work/shards_v2.blend, the blend build_export.py opens), graft them into
# a copy of the accepted export, floor them with the passes build_runtime.sh gives accepted clips of the same kind, then
# graft only the new clips onto the accepted export with claude_shared/graft_clips.py, so meshes, LODs, variants and
# accepted clips stay byte for byte. Ctl_* controls go through the same steps and are compared with the installed clips.
# Written by claude_shared/make_extra_clips.py from scripts/extra_clips.json.
# Floor as build_runtime.sh (swimmer rule since 2026-11-04): --swim 0.896, Death2 eased into a temporary Dead2.
# Death2 is MM9 diewater1 with build_export.py's Death treatment (convulsion to 0.45 s, then limp into the swim
# sprawl rolled 30 deg): diewater1 too is a sinking death that ends hanging head-up, standing on its tail on a floor.
# diewater2 is the accepted Death's source (the same treatment): not added again.
# Usage: TOK=<lease token> scripts/extra_clips.sh   (work/pre_clips_export.glb = the export before this step)
set -euo pipefail
cd "$(dirname "$0")/.."
here="$PWD"; repo="$(cd ../../.. && pwd)"; name=$(basename "$here" | sed 's/_claude$//')
G=../claude_shared/gltf_venv/bin/python; F=../claude_shared/floor/floor_fix.py; FS=scripts/floor_smooth.py
GR=../claude_shared/graft_clips.py
Q() { "$@" 2>&1 | grep -v "Unexpected value\|RuntimeWarning" ; }
E=${EXPORT:-work/pre_clips_export.glb}
(cd "$repo" && tools/run_creature_blender.sh --token "$TOK" level_generation/creatures/$(basename "$here")/scripts/extra_clips_blend.py \
  "$here/work/shards_v2.blend" "$here/work/extra_raw.glb" "$here/work/clips_extra.json" | tail -1)
Q $G $GR $E work/extra_raw.glb work/g0.glb --clip Fidget2 --clip Hit2 --clip Death2 --clip Jump --clip Ctl_Fidget --clip Ctl_Hit --clip Ctl_Walking --clip Dead2 | tail -1
Q $G $F work/g0.glb work/gc.glb --swim 0.896 Death2 Dead2 | tail -2
echo "control Ctl_Fidget vs Fidget"; Q $G ../claude_shared/compare_clips.py work/gc.glb Ctl_Fidget $E Fidget | tail -3
echo "control Ctl_Hit vs Hit"; Q $G ../claude_shared/compare_clips.py work/gc.glb Ctl_Hit $E Hit | tail -3
echo "control Ctl_Walking vs Walking"; Q $G ../claude_shared/compare_clips.py work/gc.glb Ctl_Walking $E Walking | tail -3
Q $G $F work/g0.glb work/gn.glb --swim 0.896 Death2 Dead2 | tail -2
Q $G $GR $E work/gn.glb export/$name.glb --clip Fidget2 --clip Hit2 --clip Death2 --clip Jump | tail -1
Q $G ../claude_shared/graft_byte_check.py $E export/$name.glb
