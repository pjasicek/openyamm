#!/bin/bash
# Viewer ear sheets (job 7, 2026-11-04): per tier, both ears side-on, both low 3/4 views from below the chin (the user's
# shot), front close-up and the party view, from the review viewer itself (its lighting). Usage (project folder):
# scripts/ear_shots.sh <out dir> [tier ...]   (tiers default: all seven of the manifest)
set -e
out=$1; shift
tiers=${@:-pdf1_a pdf1_b pdf2_b pdf3_a pdf3_b pdf4_a pdf4_b}
url=http://127.0.0.1:8912/level_generation/creatures/mm9_peasantdf_claude/review/viewer/
for t in $tiers; do
  sha=$(python3 -c "import json;print(next(m['sha256'] for m in json.load(open('review/viewer/manifest.json'))['models'] if m['id']=='$t'))")
  MODEL_SHA=$sha timeout 300 node scripts/viewer_shots.mjs $url $out/$t \
    earR:Standing:0:right:head:0.34,1.0,0.16:0.05,0.99,0.04 \
    earL:Standing:0:left:head:-0.34,1.0,0.16:-0.05,0.99,0.04 \
    lowR:Standing:0:quarter:head:0.21,0.90,0.27:0.04,1.0,0.02 \
    lowL:Standing:0:quarter:head:-0.21,0.90,0.27:-0.04,1.0,0.02 \
    front:Standing:0:front:head:0.0,1.0,0.62:0.0,0.99,0.0 \
    party:Standing:0:quarter:body:0.45,1.45,1.3:0.0,0.95,0.0
done
echo EARSHOTS $out
