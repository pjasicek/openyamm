#!/usr/bin/env bash
# Builder 2: compose + gate + winding for one tree with the shell.value already in species/<id>.json (no tune.py),
# after build.sh has made work/<id>/shell.npz and the card choice. Usage: b2_finish.sh <id>
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
id="$1"
cd "$here/scripts"
python3 b2_compose.py "$id" | grep -E "B2_COMPOSE|BOUNDS|TRIS|WROTE"
python3 gate.py "$id" | grep -E "GATE|SHEET"
python3 ../../mm8_3d/animated/scripts/check_winding.py "../work/$id/mm6_deco_$id.glb" | tail -n 1
