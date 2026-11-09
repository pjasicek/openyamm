#!/usr/bin/env bash
# Viewer shots with explicit cameras (the wrapper takes named views only): scripts/close_shots.sh <tier id> <prefix>
# Writes review/shots/<prefix>_*.png: below (soles), ear root, head three-quarter, rump, tail root.
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; repo="$(cd -- "$here/../../.." && pwd)"; cd "$repo"
tier=$1; pre=$2
url=$(python3 - "$here" "$tier" <<'P'
import json, sys
from pathlib import Path
from urllib.parse import quote
here = Path(sys.argv[1]); m = json.loads((here / 'review/viewer/manifest.json').read_text())
sha = next(x['sha256'] for x in m['models'] if x['id'] == sys.argv[2])
print(f"http://127.0.0.1:8912/level_generation/creatures/{here.name}/review/viewer/#" + quote(json.dumps({'clip': 'Standing', 'model_sha256': sha})))
P
)
node level_generation/creatures/mm8_m424_claude/scripts/viewer_shots.mjs "$url" "$here/review/shots" \
  ${pre}_below:Standing:0:front:body:-0.03,-0.33,0.0:0,0.01,0.0 \
  ${pre}_below_run:Running:0.03:front:body:-0.03,-0.2,0.02:0,0.01,0.02 \
  ${pre}_ear:Standing:0:front:head:-0.11,0.07,0.04:-0.01,0.035,0.075 \
  ${pre}_earback:Standing:0:front:head:-0.07,0.075,-0.02:-0.01,0.04,0.07 \
  ${pre}_face:Standing:0:front:head:-0.06,0.05,0.17:0,0.028,0.095 \
  ${pre}_rump:Standing:0:front:body:-0.05,0.05,-0.13:0,0.015,-0.01
