#!/usr/bin/env bash
# Rebuild the leftover MM6 dungeon rocks (scripts/rocks.json): build_rock.py -> review renders -> sheet -> finish
# (link LODs, validate) [--install copies new GLBs to assets_dev/worlds/mm6/models; --replace-own lets a rebuild
# overwrite GLBs this batch installed]. Usage: build_rocks.sh [--install [--replace-own]] [rock...]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
blender=/snap/bin/blender
cd "$here"
flags=(); while [[ "${1:-}" == --* ]]; do flags+=("$1"); shift; done
mkdir -p work/rocks/logs
for pair in rock01:rock01_p336 rock02:rock02_p336 rock03:rock03_p336 rock10:rock10_p336 rock11:rock11_p336 \
            rock06:rock06_p336 6rock02:rok2_p142; do
  rock=${pair%%:*}; sprite=${pair##*:}
  if (( $# )) && [[ " $* " != *" $rock "* ]]; then continue; fi
  "$blender" --background --python scripts/build_rock.py -- "$rock" > "work/rocks/logs/$rock.log" 2>&1
  grep -E "^LEVEL|Traceback|Error" "work/rocks/logs/$rock.log" || true
  "$blender" --background --python scripts/review.py -- "$rock" "work/rocks/${rock}_export.glb" 0 > /dev/null 2>&1
  python3 scripts/sheet.py "$rock" "$sprite.png"
  python3 scripts/finish.py "$rock" "${flags[@]}"
done
