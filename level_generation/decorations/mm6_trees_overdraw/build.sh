#!/usr/bin/env bash
# MM6 leaf overdraw pass for one installed tree (species/<id>.json): card table -> crown shells -> card selection
# -> shell colour fit -> GLB -> gates + before/after sheet -> winding check. Installs nothing (README "Install").
# A species with "base" (the food tree tree06a) reuses the base's shells, card choice and shell colour, so every
# non-fruit part stays identical to the base (rebuild the base first).
# Usage: build.sh <id>          e.g. build.sh tree01
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
blender=/snap/bin/blender
id="$1"
cd "$here/scripts"
base=$(python3 -c "import common; print(common.load('$id').get('base') or '')")
python3 prep.py "$id"
if [[ -z "$base" ]]; then
  "$blender" --background --python shell.py -- "$id" 2>&1 | grep -E "^SHELL|Error|Traceback"
  python3 select_cards.py "$id"
  python3 tune.py "$id" | tail -1
else
  cp "../work/$base/shell.npz" "../work/$id/shell.npz"
  python3 -c "
import json, common
b = json.load(open(common.HERE + '/species/$base.json')); s = json.load(open(common.HERE + '/species/$id.json'))
s['shell'] = b['shell']; s['cards'] = b.get('cards', {})
json.dump(s, open(common.HERE + '/species/$id.json', 'w'), indent=1)"
  echo "BASE $id reuses $base (shell.npz, shell and card settings)"
fi
python3 compose.py "$id" | grep -E "BOUNDS|TRIS|WROTE"
python3 gate.py "$id" | grep -E "GATE|SHEET"
python3 ../../mm8_3d/animated/scripts/check_winding.py "../work/$id/mm6_deco_$id.glb" | tail -1
