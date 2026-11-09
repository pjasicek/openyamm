#!/usr/bin/env bash
# Dropped MM9 clips (run2-clips-groupC, 2026-10-31): build the MM9 clips the accepted export left out with this
# project's own clips_mm9.py (scripts/extra_clips_blend.py on the source blend build_export.py opens), graft them into a
# copy of the accepted export, floor them as the accepted clips were (flier hover 0.7187, Death2 eased out and grounded
# on a temporary Dead2, as build_runtime.sh does Death/Dead; a new living clip that still dips under the floor takes
# one constant --raise-uniform lift), then graft only the new clips onto the accepted export
# with claude_shared/graft_clips.py, so meshes, LODs, variants and accepted clips stay byte for byte. Ctl_* controls
# (fidgetair1, the DieAir1 death) are rebuilt the same way and compared with the installed clips (0.0000 deg, 0 cm).
# Usage: TOK=<lease token> scripts/extra_clips.sh   (work/pre_clips_export.glb = the export before this step)
# Then install with tools/install_model.py --world mm9 and bind the clips in actors.yml script_clips.
set -euo pipefail
cd "$(dirname "$0")/.."
here="$PWD"; repo="$(cd ../../.. && pwd)"
G=../claude_shared/gltf_venv/bin/python; F=../claude_shared/floor/floor_fix.py; GR=../claude_shared/graft_clips.py
Q() { "$@" 2>&1 | grep -v "Unexpected value\|RuntimeWarning" ; }
E=${EXPORT:-work/pre_clips_export.glb}
NEW=(Hang HangFidget Launch AttackRanged2 Hit2 Death2)
CTL=(Ctl_Fidget:Fidget Ctl_Death:Death Ctl_Dead:Dead)
(cd "$repo" && tools/run_creature_blender.sh --token "$TOK" level_generation/creatures/mm9_icky_claude/scripts/extra_clips_blend.py \
  "$here/work/uv_v3.blend" "$here/work/extra_raw.glb" "$here/work/clips_extra.json" | tail -1)
Q $G $GR $E work/extra_raw.glb work/g0.glb $(for c in "${NEW[@]}" Dead2 Ctl_Fidget Ctl_Death Ctl_Dead; do echo --clip $c; done) | tail -1
Q $G $F work/g0.glb work/gc.glb --hover 0.718700 Ctl_Death Ctl_Dead --ground-death Ctl_Death Ctl_Dead | tail -1
Q $G $F work/g0.glb work/g1h.glb --hover 0.718700 Death2 Dead2 --ground-death Death2 Dead2 | tail -1
# new living clips that dip under the floor after the hover (dfly Fidget2 -1.2 cm) take one constant lift (no-op otherwise)
Q $G $F work/g1h.glb work/g1.glb $(for c in "${NEW[@]}"; do [[ $c == Death2 ]] || echo --raise-uniform $c; done) | tail -2
for p in "${CTL[@]}"; do echo "control ${p%%:*} vs ${p##*:}"; Q $G ../claude_shared/compare_clips.py work/gc.glb ${p%%:*} $E ${p##*:} | tail -3; done
Q $G $GR $E work/g1.glb export/mm9_icky.glb $(for c in "${NEW[@]}"; do echo --clip $c; done) | tail -1
Q $G ../claude_shared/graft_byte_check.py $E export/mm9_icky.glb
