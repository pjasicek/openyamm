#!/usr/bin/env bash
# Texture pass maps -> runtime -> viewer (2026-10-30). Run from the repo root under the lease: scripts/texpass_finish.sh <token> [--install]
set -euo pipefail
P=level_generation/creatures/mm9_nagate_claude; S=level_generation/creatures/claude_shared
python3 $P/scripts/compose_nagate.py > /dev/null
python3 $S/grade_basecolor.py --ao $P/textures/nagate_ao_2k.png --fine 1.0 --local 0.3 --ao-strength 0.5 --contrast 1.06 \
  --saturation 1.15 $P/textures/nagate_basecolor.png
python3 $P/scripts/nagate_grain.py
python3 $P/scripts/compose_nagate.py > /dev/null
python3 $S/ramp_match.py $P/work/before_texpass/textures $P/textures nagate $P/work/uv3d_nagate.npz $P/work/uv3d_nagate_v2.npz 0,1,3
tools/run_creature_blender.sh --token "$1" $P/scripts/build_export.py $P/work/uv_v2.blend nagate $P/work/anim_v2.blend $P/export/mm9_nagate_lod0.glb $P/work/clips_v2.json
python3 tools/creature_workspace.py run --project $P --token "$1" -- $P/scripts/build_runtime.sh nagate ${2:-}
python3 $P/scripts/viewer_tiers.py nagate
python3 $P/scripts/make_viewer_manifest.py r2_nagate_texpass_20261030 "nagate_a=Nagate Hatchling (Nagate A)=$P/review/viewer/nagate_a.glb" \
  "nagate_b=Nagate (Nagate B)=$P/review/viewer/nagate_b.glb" "nagate_c=Nagate Elder (Nagate C)=$P/review/viewer/nagate_c.glb" | tail -1
