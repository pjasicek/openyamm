#!/usr/bin/env bash
# Texture pass acceptance shots from the review viewer, identical cameras for before and after, both tiers:
# scripts/texpass_shots.sh <prefix> <lease token>. Writes review/shots/<prefix>_<a|c>_<shot>.png.
# Named cameras go through tools/run_creature_review.py (focus presets scaled to the Basilisk in review.js); the top
# of the back has no named view, so that one uses the wrapper's viewer_shots.mjs with an explicit camera.
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; repo="$(cd -- "$here/../../.." && pwd)"; cd "$repo"
pre=$1; token=$2
P=level_generation/creatures/mm9_basilisk_claude
for t in a c; do
  python3 tools/run_creature_review.py --project $P --token "$token" --tier basilisk_$t shots \
    ${pre}_${t}_body_q:Standing:0:quarter:body ${pre}_${t}_body_left:Standing:0:left:body \
    ${pre}_${t}_head_q:Standing:0:quarter:head ${pre}_${t}_head_front:Standing:0:front:head \
    ${pre}_${t}_head_left:Standing:0:left:head ${pre}_${t}_mouth:AttackMelee:0.6:front:head \
    ${pre}_${t}_frill_left:Standing:0:left:shoulders ${pre}_${t}_frill_right:Standing:0:right:shoulders \
    ${pre}_${t}_flank:Standing:0:left:skirt ${pre}_${t}_leg_front:Standing:0:left:arms \
    ${pre}_${t}_leg_hind:Standing:0:left:feet
  url=$(python3 - "$here" basilisk_$t <<'P'
import json, sys
from pathlib import Path
from urllib.parse import quote
here = Path(sys.argv[1]); m = json.loads((here / 'review/viewer/manifest.json').read_text())
sha = next(x['sha256'] for x in m['models'] if x['id'] == sys.argv[2])
print(f"http://127.0.0.1:8912/level_generation/creatures/{here.name}/review/viewer/#" + quote(json.dumps({'clip': 'Standing', 'model_sha256': sha})))
P
)
  node level_generation/creatures/mm8_m424_claude/scripts/viewer_shots.mjs "$url" "$here/review/shots" \
    ${pre}_${t}_back_top:Standing:0:front:body:0.75,2.25,-0.55:0,0.55,-0.3 \
    ${pre}_${t}_tail:Standing:0:front:body:1.1,1.2,-1.75:0,0.3,-1.1
done
