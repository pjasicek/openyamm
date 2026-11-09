#!/bin/bash
# rebuild runtime + viewer (project folder)
PYGLTF_PYTHON=$PWD/../claude_shared/gltf_venv/bin/python TOKEN="${TOKEN:?set TOKEN to the lease token}" bash scripts/build_runtime.sh "$@" 2>&1 | grep -v "Unexpected value" | grep -E "FAILED|Traceback|Error|WINDING|LOD triangles|CLIPS|installed|Installed" | cut -c1-220
../claude_shared/gltf_venv/bin/python scripts/viewer_tiers.py 2>&1 | grep -E "Error|Traceback" 
python3 scripts/make_viewer_manifest.py ${REV:-r1_imp_20261030} "imp_a=Imply A (MM9 yellow)=review/viewer/imp_a.glb" "imp_b=Imp B (brown, shin wraps)=review/viewer/imp_b.glb" "imp_c=Imp Elder C (red, tongue)=review/viewer/imp_c.glb" | cut -c1-100
