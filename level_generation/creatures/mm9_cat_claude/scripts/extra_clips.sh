#!/usr/bin/env bash
# Dropped MM9 clips (run2-clips-groupC, 2026-10-31): build the MM9 clips the accepted export left out with this
# project's own clips_mm9.py (scripts/extra_clips_blend.py on work/uv_v1.blend, the blend build_export.py opens), graft them into
# a copy of the accepted export, floor them with the passes build_runtime.sh gives accepted clips of the same kind, then
# graft only the new clips onto the accepted export with claude_shared/graft_clips.py, so meshes, LODs, variants and
# accepted clips stay byte for byte. Ctl_* controls go through the same steps and are compared with the installed clips.
# Written by claude_shared/make_extra_clips.py from scripts/extra_clips.json.
# The cat's build_export.py steps run on the new clips too (rest offsets, hind_ik, fore_stance, knee helpers, the
# 3.12 cm rest shift). The MM9 cat's idle is a sit; down lies down (LieDown), up sits back up (GetUp), standdown is
# the lying idle (Lie) and fidgetdown1/2 its fidgets. Floor as build_runtime.sh: ground-loop, low-passed 0.05 s with smooth-hold 0.5 as the accepted Fidget.
# clips_mm9.py has no joint-offset cut (its 0.004 values are key data), so the soft line does not apply.
# Usage: TOK=<lease token> scripts/extra_clips.sh   (work/pre_clips_export.glb = the export before this step)
set -euo pipefail
cd "$(dirname "$0")/.."
here="$PWD"; repo="$(cd ../../.. && pwd)"; name=$(basename "$here" | sed 's/_claude$//')
G=../claude_shared/gltf_venv/bin/python; F=../claude_shared/floor/floor_fix.py; FS=scripts/floor_smooth.py
GR=../claude_shared/graft_clips.py
Q() { "$@" 2>&1 | grep -v "Unexpected value\|RuntimeWarning" ; }
E=${EXPORT:-work/pre_clips_export.glb}
(cd "$repo" && tools/run_creature_blender.sh --token "$TOK" level_generation/creatures/$(basename "$here")/scripts/extra_clips_blend.py \
  "$here/work/uv_v1.blend" "$here/work/extra_raw.glb" "$here/work/clips_extra.json" | tail -1)
Q $G $GR $E work/extra_raw.glb work/g0.glb --clip Fidget2 --clip LieDown --clip GetUp --clip Lie --clip LieFidget --clip LieFidget2 --clip Ctl_Fidget --clip Ctl_Standing | tail -1
Q $G $F work/g0.glb work/gc.glb --ground-loop Ctl_Standing --ground-loop Ctl_Fidget --smooth-hold 0.5 --smooth Ctl_Fidget 0.05 | tail -2
echo "control Ctl_Fidget vs Fidget"; Q $G ../claude_shared/compare_clips.py work/gc.glb Ctl_Fidget $E Fidget | tail -3
echo "control Ctl_Standing vs Standing"; Q $G ../claude_shared/compare_clips.py work/gc.glb Ctl_Standing $E Standing | tail -3
Q $G $F work/g0.glb work/gn.glb --ground-loop Fidget2 --ground-loop LieDown --ground-loop GetUp --ground-loop Lie --ground-loop LieFidget --ground-loop LieFidget2 --smooth-hold 0.5 --smooth Fidget2 0.05 --smooth LieDown 0.05 --smooth GetUp 0.05 --smooth LieFidget 0.05 --smooth LieFidget2 0.05 | tail -2
Q $G $GR $E work/gn.glb export/$name.glb --clip Fidget2 --clip LieDown --clip GetUp --clip Lie --clip LieFidget --clip LieFidget2 | tail -1
Q $G ../claude_shared/graft_byte_check.py $E export/$name.glb
