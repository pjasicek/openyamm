#!/usr/bin/env bash
# Dropped MM9 clips (run2-clips-groupC, 2026-10-31): build the MM9 clips the accepted export left out with this
# project's own clips_mm9.py (scripts/extra_clips_blend.py on work/uv_lobber_v4.blend, the blend build_export.py opens), graft them into
# a copy of the accepted export, floor them with the passes build_runtime.sh gives accepted clips of the same kind, then
# graft only the new clips onto the accepted export with claude_shared/graft_clips.py, so meshes, LODs, variants and
# accepted clips stay byte for byte. Ctl_* controls go through the same steps and are compared with the installed clips.
# Written by claude_shared/make_extra_clips.py from scripts/extra_clips.json.
# Floor as build_runtime.sh lobber: every living clip ground-looped (the root bulb on the floor).
# Left out: MM9 fall1 and falldown1, the drop from the ceiling. Our Lobber grows upright from the floor (README), so the
# fall would rise; its Death is DieAir1 then a wilt, as accepted.
# Usage: TOK=<lease token> scripts/extra_clips.sh   (work/pre_clips_export.glb = the export before this step)
set -euo pipefail
cd "$(dirname "$0")/.."
here="$PWD"; repo="$(cd ../../.. && pwd)"; name=mm9_lobber
G=../claude_shared/gltf_venv/bin/python; F=../claude_shared/floor/floor_fix.py; FS=scripts/floor_smooth.py
GR=../claude_shared/graft_clips.py
Q() { "$@" 2>&1 | grep -v "Unexpected value\|RuntimeWarning" ; }
E=${EXPORT:-work/pre_clips_export.glb}
(cd "$repo" && tools/run_creature_blender.sh --token "$TOK" level_generation/creatures/$(basename "$here")/scripts/extra_clips_blend.py \
  "$here/work/uv_lobber_v4.blend" "$here/work/extra_raw.glb" "$here/work/clips_extra.json" | tail -1)
Q $G $GR $E work/extra_raw.glb work/g0.glb --clip Fidget2 --clip Aware --clip Hit2 --clip Ctl_Fidget --clip Ctl_Hit | tail -1
Q $G $F work/g0.glb work/gc.glb --ground-loop Ctl_Fidget --ground-loop Ctl_Hit | tail -2
echo "control Ctl_Fidget vs Fidget"; Q $G ../claude_shared/compare_clips.py work/gc.glb Ctl_Fidget $E Fidget | tail -3
echo "control Ctl_Hit vs Hit"; Q $G ../claude_shared/compare_clips.py work/gc.glb Ctl_Hit $E Hit | tail -3
Q $G $F work/g0.glb work/gn.glb --ground-loop Fidget2 --ground-loop Aware --ground-loop Hit2 | tail -2
Q $G $GR $E work/gn.glb export/$name.glb --clip Fidget2 --clip Aware --clip Hit2 | tail -1
Q $G ../claude_shared/graft_byte_check.py $E export/$name.glb
