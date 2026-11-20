#!/bin/bash
# Job 7 neck/jaw close-ups from the review viewer: front-low (under the chin), low 3/4 both sides (the user's shot).
# Usage (project folder): scripts/neck_shots.sh <out dir> <viewer dir under review/> <tier ...>
set -e
out=$1; vdir=$2; shift 2
url=http://127.0.0.1:8912/level_generation/creatures/mm9_peasantdf_claude/review/$vdir/
for t in "$@"; do
  sha=$(python3 -c "import json;print(next(m['sha256'] for m in json.load(open('review/$vdir/manifest.json'))['models'] if m['id']=='$t'))")
  MODEL_SHA=$sha timeout 300 node scripts/viewer_shots.mjs $url $out/$t \
    neckF:Standing:0:front:head:0.0,0.86,0.30:0.0,0.93,0.02 \
    neckR:Standing:0:quarter:head:0.17,0.86,0.22:0.02,0.93,0.02 \
    neckL:Standing:0:quarter:head:-0.17,0.86,0.22:-0.02,0.93,0.02
done
echo NECKSHOTS $out
