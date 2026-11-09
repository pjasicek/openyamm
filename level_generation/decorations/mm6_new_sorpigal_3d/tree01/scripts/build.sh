#!/usr/bin/env bash
# Rebuild mm6_deco_tree01.glb from the downloaded sources: inputs -> atlas -> tree -> impostor -> export -> link,
# validate (and --install) -> review renders and sheets.
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
blender=/snap/bin/blender
cd "$here"
python3 scripts/prepare_inputs.py
python3 scripts/make_leaf_atlas.py
"$blender" --background --python scripts/build_tree.py 2>&1 | grep -E "BARK|CARDS|^LOD|Error|Traceback"
"$blender" --background --python scripts/bake_impostor.py 2>&1 | grep -E "IMPOSTOR|Error|Traceback"
python3 scripts/finish_impostor.py
"$blender" --background --python scripts/export_tree.py 2>&1 | grep -E "EXPORTED|Error|Traceback"
python3 scripts/post_process.py "$@" | tee work/validation.txt
"$blender" --background --python scripts/render_review.py -- work/fin work/tree_export.blend eye,three_quarter 2>&1 \
  | grep -E "Error|Traceback" || true
counts=$(python3 -c "import re;print(','.join(re.search(r'LOD triangles \[([0-9, ]+)\]',open('work/validation.txt').read()).group(1).replace(' ','').split(',')))")
python3 scripts/make_sheets.py "$counts"
python3 scripts/lod_tone.py fin
