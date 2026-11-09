#!/usr/bin/env bash
# mouth_tail.sh <token> <sx> <sz> <revision>: mouth deform on uv_v2 -> uv_v3, re-derived maps, export, runtime, viewer.
set -uo pipefail
T="$1"; SX="$2"; SZ="$3"; REV="$4"
cd "$(dirname "$0")/../../../.."
P=level_generation/creatures/mm9_fish_claude; B="tools/run_creature_blender.sh --token $T"
log() { sed 's/Blender log: //'; }
L=$($B $P/scripts/mouth_deform.py $P/work/uv_v2.blend $P/work/uv_v3.blend $SX $SZ | log); grep -E "DEFORM|Traceback" "$L"
L=$($B $P/scripts/mouth_measure.py $P/work/uv_v3.blend | log); grep -E "MOUTH|Traceback" "$L" | cut -c1-330
HEAD_GROUPS=XCENTER JAW_GROUPS=Xjaw $B $P/scripts/dump_uv3d.py $P/work/uv_v3.blend $P/work/uv3d_body.npz Body >/dev/null
$B $P/scripts/bake_ao.py $P/work/uv_v3.blend Body $PWD/$P/textures/fish_ao_2k.png 0.02 2048 >/dev/null
python3 $P/scripts/texel_map.py
(cd $P && python3 scripts/compose_fish.py | tail -1 && python3 ../claude_shared/grade_basecolor.py --ao textures/fish_ao_2k.png \
  --fine 1.0 --local 0.3 --ao-strength 0.5 --contrast 1.06 --saturation 1.15 textures/fish_basecolor.png | tail -1 \
  && scripts/rebuild_tail.sh "$T" uv_v3.blend "$REV")
