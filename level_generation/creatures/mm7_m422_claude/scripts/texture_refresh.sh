#!/usr/bin/env bash
# After a rig rebuild: carry the texture layout from the upload master (work/rig_v6_upload.blend, the mesh the Meshy
# retextures were made on) onto work/rig_v5.blend -> work/rig_v6.blend, re-rasterise, re-bake AO, compose, build the
# runtime GLBs and the viewer. Usage: TOK=<lease> scripts/texture_refresh.sh
set -euo pipefail
cd "$(dirname "$0")/.."; P=$PWD; NAME=$(basename "$P"); REPO=$(cd ../../.. && pwd)
B() { local out log; out=$(cd "$REPO" && tools/run_creature_blender.sh --token "$TOK" "level_generation/creatures/$NAME/scripts/$1" "${@:2}" 2>&1) || true
      log=$(echo "$out" | grep "Blender log" | awk '{print $3}'); grep -E '^(CARRYUV|RASTER|AO|UVOUT)' "$log" | cut -c1-160 || true
      if grep -q "Traceback" "$log"; then grep -A12 Traceback "$log" | head -20; exit 1; fi; }
UM=$(python3 -c "import json;print(json.load(open('creature.json')).get('texture_upload_master', 'work/rig_v6_upload.blend'))")
B carry_uv.py "$P/work/rig_v5.blend" "$P/$UM" "$P/work/rig_v6.blend"
B uv_outliers.py "$P/work/rig_v6.blend" 4
B uv_raster.py "$P/work/rig_v6.blend" UVMap 1024
B uv_raster.py "$P/work/rig_v6.blend" HeadUV 1024
B bake_ao_natm.py "$P/work/rig_v6.blend" 1024
python3 scripts/compose_m422.py | grep RAMP
bash scripts/build_runtime.sh 2>&1 | grep -E "LOD tri|variants|EXPORTED" | cut -c1-200
python3 scripts/viewer_tiers.py | tail -1; python3 scripts/update_viewer_manifest.py | tail -1
