#!/usr/bin/env bash
# fit + weights -> body export -> MM9 role clips. Usage: scripts/rebuild_rig.sh <mm9 body glb> <roles json> [tag]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$here"
V="${PYGLTF_PYTHON:?set PYGLTF_PYTHON to a python with pygltflib}"
tag="${3:-v1}"
B="/snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1 --python"
$B scripts/fit_rig.py -- meshy/body_smart_v1/model_urls_glb.glb "$1" work/fit_$tag.blend work/fit_$tag.json scripts/fit_config.json 2>&1 | grep -E "^FIT|Error|Traceback" | cut -c1-200
$B scripts/export_body.py -- work/fit_$tag.blend work/fit_${tag}_body.glb 2>&1 | grep -E "Error|Traceback" || true
"$V" scripts/clips_mm9.py work/fit_${tag}_body.glb work/fit_${tag}_anim.glb "$2" work/clips_$tag.json
