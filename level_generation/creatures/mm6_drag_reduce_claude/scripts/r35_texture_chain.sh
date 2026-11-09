#!/usr/bin/env bash
# After the two Meshy retexture downloads: UV parity, raster, AO, compose, export, runtime GLBs, viewer tiers.
set -euo pipefail
P="$(cd "$(dirname "$0")/.." && pwd)"; ROOT="$(cd "$P/../../.." && pwd)"; cd "$ROOT"
t(){ local s=$(date +%s); "$@" > "$P/work/log_$(basename "${@: -1}" .py).txt" 2>&1 || { echo "FAILED $*"; tail -20 "$P/work/log_$(basename "${@: -1}" .py).txt"; exit 1; }; echo "$(basename "${@: -1}") $(( $(date +%s) - s ))s"; }
t blender -b -P "$P/scripts/r35_verify_uv.py"
t blender -b -P "$P/scripts/r35_uv_raster.py"
t blender -b -P "$P/scripts/r35_bake_ao.py"
t python3 "$P/scripts/r35_compose.py"
t blender -b -P "$P/scripts/r35_export.py"
t python3 tools/prepare_actor_glb.py "$P/export/mm6_drag_selected.glb" "$P/export/mm6_drag_runtime_lod0.glb"
t blender -b -P "$P/scripts/r35_build_lods.py"
t python3 "$P/scripts/r35_finish_runtime.py"
mkdir -p "$P/review/viewer_r35"; t python3 "$P/scripts/r35_viewer_tiers.py"
