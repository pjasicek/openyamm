#!/usr/bin/env bash
# Builder 2: shell + card selection + under-crown carve + compose + gate + winding, with the shell factor already in
# species/<id>.json (no tune.py). After build.sh <id> has run once (prep, tune), or to redo a tree after a settings
# change. Usage: b2_rebuild.sh <id>
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
id="$1"
cd "$here/scripts"
/snap/bin/blender --background --python shell.py -- "$id" 2>&1 | grep -E "^SHELL|Error|Traceback"
python3 select_cards.py "$id"
rm -f "../work/$id/shell_preunder.npz"
python3 b2_undercarve.py "$id" | grep UNDERCARVE
"$here/scripts/b2_finish.sh" "$id"
