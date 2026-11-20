#!/bin/bash
# frame strips: six frames of every clip per tier from viewer shots. Project folder
. scripts/env.sh
for t in a b c; do
python3 - "$t" <<'PY' > work/_spec_$t.txt
import json,sys
m=json.load(open('review/viewer/manifest.json')); t=sys.argv[1]
s=[]
for c,i in m['clips'].items():
    d=i['duration']
    for k in range(6): s.append(f's{t}_{c}_{k}:{c}:{round(d*k/5.0001,3)}:quarter:body')
print(' '.join(s))
PY
TIER=trog_$t scripts/vshots.sh $(cat work/_spec_$t.txt) 2>&1 | tail -1
done
python3 scripts/strip_sheets.py
echo STRIPSDONE
