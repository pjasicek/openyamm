#!/usr/bin/env bash
# Viewer face shots (the user's own lighting): front close-up, 3/4, true profile, low 3/4, party view, for every tier,
# through the wrapper's viewer_shots.mjs with explicit cameras (glTF Y-up metres, +Z front; the server on 8912 must run,
# as tools/run_creature_review.py leaves it). Usage (repo root): scripts/face_shots.sh <prefix> [out dir, default review/shots]
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
    ${pre}_${t}_front:Standing:0:front:body:0.000,1.645,0.440:0.000,1.635,0.000 \
    ${pre}_${t}_q34:Standing:0:front:body:0.310,1.660,0.310:0.000,1.635,0.000 \
    ${pre}_${t}_profile:Standing:0:front:body:0.450,1.645,0.000:0.000,1.635,0.000 \
    ${pre}_${t}_low34:Standing:0:front:body:0.290,1.430,0.310:0.000,1.635,0.000 \
    ${pre}_${t}_party:Standing:0:front:body:0.000,2.150,2.400:0.000,1.450,0.000 2>&1 | tail -1 | cut -c1-120
done
