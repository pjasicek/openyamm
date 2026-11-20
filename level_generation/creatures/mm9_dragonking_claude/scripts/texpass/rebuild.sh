#!/usr/bin/env bash
# Export + runtime + viewer on the texture-pass blend. Usage: TOKEN=<lease> scripts/texpass/rebuild.sh <viewer revision> [--install]
set -euo pipefail
cd "$(dirname "$0")/../../../../.."
P=level_generation/creatures/mm9_dragonking_claude; T=${TOKEN:?}
L=$(tools/run_creature_blender.sh --token $T $P/scripts/build_export.py $PWD/$P/work/texpass/uv_final.blend $PWD/$P/work/anim_v3.blend $PWD/$P/export/mm9_dragonking_lod0.glb $PWD/$P/work/clips_v3.json 2>&1 | sed -n 's/Blender log: //p')
grep -E "SHADING|Traceback" $L | cut -c1-160 || true
python3 tools/creature_workspace.py run --project $P --token $T -- $P/scripts/build_runtime.sh ${2:-}
python3 $P/scripts/make_viewer_manifest.py "$1" "dragonking=Dragon King (GREENDRAGONLT)=$P/export/mm9_dragonking.glb"
