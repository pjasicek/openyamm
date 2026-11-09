#!/usr/bin/env bash
# Viewer face pre-screen shots (the user's lighting): front close-up, 3/4, both true profiles, low 3/4 from below, under
# the jaw, both ears, party view, for every tier, through mm8_m424's viewer_shots.mjs with explicit cameras (glTF Y-up
# metres, +Z front; head centre ~1.03 m). Server on 8912. At most one run at a time.
# Usage (repo root): scripts/face_shots.sh <prefix> [clip] [seconds] [out dir]
set -euo pipefail
here=level_generation/creatures/mm9_peasantdm3_claude
pre=$1; clip=${2:-Standing}; sec=${3:-0}; out=${4:-$PWD/$here/review/shots}
H=${HEADY:-1.03}
for t in pdm3_a pdm3_b; do
  url=$(python3 - "$here" $t "$clip" <<'P'
import json, sys
from pathlib import Path
from urllib.parse import quote
here = Path(sys.argv[1]); m = json.loads((here / 'review/viewer/manifest.json').read_text())
sha = next(x['sha256'] for x in m['models'] if x['id'] == sys.argv[2])
print(f"http://127.0.0.1:8912/{here.as_posix()}/review/viewer/#" + quote(json.dumps({'clip': sys.argv[3], 'model_sha256': sha})))
P
)
  y() { python3 -c "print(f'{$H + $1:.3f}')"; }
  MODEL_SHA=$(python3 -c "import json;print(next(x['sha256'] for x in json.load(open('$here/review/viewer/manifest.json'))['models'] if x['id']=='$t'))") \
  node level_generation/creatures/mm9_peasantdm3_claude/scripts/viewer_shots.mjs "$url" "$out" \
    ${pre}_${t}_front:$clip:$sec:front:body:0.000,$(y 0.0),0.420:0.000,$(y -0.01),0.000 \
    ${pre}_${t}_q34:$clip:$sec:front:body:0.300,$(y 0.015),0.300:0.000,$(y -0.01),0.000 \
    ${pre}_${t}_profR:$clip:$sec:front:body:0.430,$(y 0.0),0.000:0.000,$(y -0.01),0.000 \
    ${pre}_${t}_profL:$clip:$sec:front:body:-0.430,$(y 0.0),0.000:0.000,$(y -0.01),0.000 \
    ${pre}_${t}_low34:$clip:$sec:front:body:0.280,$(y -0.20),0.300:0.000,$(y -0.02),0.000 \
    ${pre}_${t}_under:$clip:$sec:front:body:0.000,$(y -0.30),0.260:0.000,$(y -0.05),0.000 \
    ${pre}_${t}_earR:$clip:$sec:front:body:0.300,$(y 0.02),-0.060:0.080,$(y 0.0),0.000 \
    ${pre}_${t}_earL:$clip:$sec:front:body:-0.300,$(y 0.02),-0.060:-0.080,$(y 0.0),0.000 \
    ${pre}_${t}_party:$clip:$sec:front:body:0.000,1.900,2.300:0.000,0.950,0.000 \
    ${pre}_${t}_party34:$clip:$sec:front:body:1.500,1.900,1.700:0.000,0.950,0.000 2>&1 | tail -1 | cut -c1-160
done
