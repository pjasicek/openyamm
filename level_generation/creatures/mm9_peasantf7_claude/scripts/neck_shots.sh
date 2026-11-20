#!/bin/bash
# Neck-graft review shots in the viewer's own lighting (repo root): scripts/neck_shots.sh <project> <token> <tier> <outname-prefix> [clip:time]
# As face_shots.sh, plus neck close-ups: focus 'arms' -> neck front close-up, 'skirt' -> neck/chest wider; views back -> low 3/4 from
# below, rear -> party view (~22 deg above); focus feet -> big front face close-up. Restores review.js.
P=$1; T=$2; TIER=$3; N=$4; CT=${5:-Standing:0}; C=${CT%%:*}; S=${CT##*:}
J=$P/review/viewer/review.js; cp $P/work/review_js_keep.js $J
sed -i "s/back:\[0,0,-1\]/back:[-0.45,-0.55,1]/; s/rear:\[-0.7,0,-1\]/rear:[0,0.42,1]/; s/feet:\[0,0.3,0,1.3\]/feet:[0,1.61,0.02,0.30]/; s/arms:\[0,1.15,0,2.3\]/arms:[0,1.49,0.02,0.24]/; s/skirt:\[0,0.8,0,1.7\]/skirt:[0,1.50,0.02,0.40]/" $J
python3 tools/run_creature_review.py --project $P --token $T --tier $TIER shots \
  ${N}_close:$C:$S:front:feet ${N}_neck:$C:$S:front:arms ${N}_neckq:$C:$S:quarter:arms ${N}_neckw:$C:$S:front:skirt \
  ${N}_q34:$C:$S:quarter:head ${N}_prof:$C:$S:left:head ${N}_low:$C:$S:back:skirt ${N}_party:$C:$S:rear:shoulders 2>&1 | tail -2
cp $P/work/review_js_keep.js $J
