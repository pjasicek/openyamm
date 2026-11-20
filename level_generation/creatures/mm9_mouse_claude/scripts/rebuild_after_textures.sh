#!/usr/bin/env bash
# From composed textures to viewer: export, runtime GLB, viewer GLBs and manifest. Args: <lease token> <revision> [--install]
set -euo pipefail
T=$1; R=$2; I=${3:-}
cd "$(dirname "$0")/../../../.."; P=level_generation/creatures/mm9_mouse_claude
tools/run_creature_blender.sh --token $T $P/scripts/build_export.py $P/work/uv_v1b.blend $P/work/anim_v1.blend $P/export/mm9_mouse_lod0.glb $P/work/clips_v1.json >/dev/null
python3 tools/creature_workspace.py run --project $P --token $T -- $P/scripts/build_runtime.sh $I 2>&1 | grep -E "WINDING|LOD triangles|mm9_mouse.glb$|Installed|installed|Traceback|Error" || true
(cd $P && python3 scripts/viewer_tiers.py && python3 scripts/make_viewer_manifest.py $R "mouse_a=Mouse (A)=review/viewer/mouse_a.glb" "mouse_c=Evil mouse (C)=review/viewer/mouse_c.glb")
