#!/bin/bash
# Nose/mouth zoom shots (repo root): scripts/nose_shots.sh <project> <token> <tier> <prefix> [clip:time]; focus 'feet' -> nose/mouth zoom,
# views back -> low 3/4 from below. Restores review.js.
P=$1; T=$2; TIER=$3; N=$4; CT=${5:-Standing:0}; C=${CT%%:*}; S=${CT##*:}
J=$P/review/viewer/review.js; cp $P/work/review_js_keep.js $J
sed -i "s/back:\[0,0,-1\]/back:[-0.45,-0.55,1]/; s/feet:\[0,0.3,0,1.3\]/feet:[0,1.565,0.03,0.13]/" $J
python3 tools/run_creature_review.py --project $P --token $T --tier $TIER shots ${N}_nose:$C:$S:front:feet ${N}_noseq:$C:$S:quarter:feet ${N}_noselow:$C:$S:back:feet 2>&1 | tail -1
cp $P/work/review_js_keep.js $J
