#!/usr/bin/env bash
# Build MM8 rocks (scripts/rocks.json): build_rock.py -> review renders -> sheet -> finish (link LODs, validate)
# [--install: tools/install_model.py --engine]. Usage: build.sh [--install] rock...  (no names: every rock in rocks.json)
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
blender=/snap/bin/blender
cd "$here"
flags=(); while [[ "${1:-}" == --* ]]; do flags+=("$1"); shift; done
rocks=("$@"); if (( ${#rocks[@]} == 0 )); then mapfile -t rocks < <(python3 -c "import json; print('\n'.join(json.load(open('scripts/rocks.json'))))"); fi
mkdir -p work/logs
for rock in "${rocks[@]}"; do
  yaw=$(python3 -c "import json; print(json.load(open('scripts/rocks.json'))['$rock'].get('review_yaw', 0))")
  "$blender" --background --python-exit-code 1 --python scripts/build_rock.py -- "$rock" > "work/logs/$rock.log" 2>&1 || { tail -5 "work/logs/$rock.log"; continue; }
  grep -E "^BUILD (gain|fit|moss|tar|high)|^LEVEL|Traceback|Error" "work/logs/$rock.log" || true
  "$blender" --background --python scripts/review.py -- "$rock" "work/$rock/${rock}_export.glb" "$yaw" > "work/logs/${rock}_review.log" 2>&1
  tris=$(grep -E "^LEVEL" "work/logs/$rock.log" | awk '{print $5}' | tr '\n' ' ')
  python3 scripts/sheet.py "$rock" $tris
  python3 scripts/finish.py "$rock" "${flags[@]}"
done
