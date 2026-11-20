#!/bin/bash
# Zoom shots (repo root): scripts/zoom_shots.sh <project> <token> <tier> <prefix> "<x,y,z,size>" [views (default front quarter back)]
# focus 'feet' -> the given focus; views back -> low 3/4 from below. Restores review.js.
P=$1; T=$2; TIER=$3; N=$4; F=$5; V=${6:-front quarter back}
J=$P/review/viewer/review.js; cp $P/work/review_js_keep.js $J
sed -i "s/back:\[0,0,-1\]/back:[-0.45,-0.55,1]/; s/feet:\[0,0.3,0,1.3\]/feet:[$F]/" $J
A=(); for v in $V; do A+=("${N}_z$v:Standing:0:$v:feet"); done
python3 tools/run_creature_review.py --project $P --token $T --tier $TIER shots "${A[@]}" 2>&1 | tail -1
cp $P/work/review_js_keep.js $J
