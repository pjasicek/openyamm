#!/usr/bin/env bash
# Viewer neck/collar shots (user note 2026-11-02 "some artifacts here?"): front close-up of the neck, 3/4, side, from above,
# and Talk / Fidget head turns, both tiers. Usage (repo root): scripts/neck_shots.sh <prefix> [out dir]
set -euo pipefail
here=level_generation/creatures/mm9_peasantm3_claude
pre=$1; out=${2:-$PWD/$here/review/shots}
for t in pm3_a pm3_b; do
  url=$(python3 - "$here" $t <<'P'
import json, sys
from pathlib import Path
from urllib.parse import quote
here = Path(sys.argv[1]); m = json.loads((here / 'review/viewer/manifest.json').read_text())
sha = next(x['sha256'] for x in m['models'] if x['id'] == sys.argv[2])
print(f"http://127.0.0.1:8912/{here.as_posix()}/review/viewer/#" + quote(json.dumps({'clip': 'Standing', 'model_sha256': sha})))
P
)
  node level_generation/creatures/mm8_m424_claude/scripts/viewer_shots.mjs "$url" "$out" \
    ${pre}_${t}_nfront:Standing:0:front:body:0.000,1.480,0.380:0.000,1.470,0.000 \
    ${pre}_${t}_nq34:Standing:0:front:body:0.270,1.500,0.270:0.000,1.470,0.000 \
    ${pre}_${t}_nside:Standing:0:front:body:0.380,1.480,0.000:0.000,1.470,0.000 \
    ${pre}_${t}_nabove:Standing:0:front:body:0.000,1.800,0.250:0.000,1.470,0.000 \
    ${pre}_${t}_ntalk:Talk:2.2:front:body:0.150,1.500,0.380:0.000,1.470,0.000 \
    ${pre}_${t}_nfidget:Fidget:1.8:front:body:-0.150,1.500,0.380:0.000,1.470,0.000 2>&1 | tail -1 | cut -c1-120
done
