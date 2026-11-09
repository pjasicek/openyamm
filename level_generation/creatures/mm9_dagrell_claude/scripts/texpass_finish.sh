#!/usr/bin/env bash
# Texture pass maps -> runtime -> viewer (2026-10-30). Run from the repo root under the lease: scripts/texpass_finish.sh <token> [--install]
set -euo pipefail
P=level_generation/creatures/mm9_dagrell_claude; S=level_generation/creatures/claude_shared
python3 $P/scripts/compose_dagrell.py > /dev/null
python3 $S/grade_basecolor.py --ao $P/textures/dagrell_ao_2k.png --fine 1.0 --local 0.3 --ao-strength 0.5 --contrast 1.06 \
  --saturation 1.15 $P/textures/dagrell_basecolor.png
python3 $P/scripts/dagrell_grain.py
python3 $P/scripts/compose_dagrell.py > /dev/null
python3 $S/ramp_match.py $P/work/before_texpass/textures $P/textures dagrell $P/work/uv3d_dagrell_v6uv.npz $P/work/uv3d_dagrell_v8.npz 0,1
tools/run_creature_blender.sh --token "$1" $P/scripts/build_export.py $P/work/uv_v8.blend dagrell $P/work/anim_v8.blend $P/export/mm9_dagrell_lod0.glb $P/work/clips_v8.json
python3 tools/creature_workspace.py run --project $P --token "$1" -- $P/scripts/build_runtime.sh dagrell ${2:-}
python3 $P/scripts/viewer_tiers.py dagrell
python3 $P/scripts/make_viewer_manifest.py r6_dagrell_texpass_20261030 "dagrell_a=Dagrell (Dagrell A)=$P/review/viewer/dagrell_a.glb" \
  "dagrell_b=Venomous Dagrell (Dagrell B)=$P/review/viewer/dagrell_b.glb" "dagrell_c=Spectre Dagrell (Dagrell C)=$P/review/viewer/dagrell_c.glb" | tail -1
