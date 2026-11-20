#!/bin/bash
# frame strips of every clip from viewer shots; project folder. Usage: scripts/strips.sh <tag> [tier] [view]  -> review/sheet_strips_<tag>.png
. scripts/env.sh
t=$1; tier=$2; view=${3:-quarter}
python3 - "$t" "$view" <<'PY' > work/_spec_$t.txt
import json,sys
m=json.load(open('review/viewer/manifest.json')); t,v=sys.argv[1:3]
s=[]
for c,i in m['clips'].items():
    d=i['duration']
    for k in range(6): s.append(f's{t}_{c}_{k}:{c}:{round(d*(k+.3)/6,3)}:{v}:body')
print(' '.join(s))
PY
TIER=$tier scripts/shots.sh $(cat work/_spec_$t.txt) > work/_strips_$t.log 2>&1
python3 - "$t" <<'PY'
import json,os,sys
from PIL import Image, ImageDraw
t=sys.argv[1]; m=json.load(open('review/viewer/manifest.json')); cl=list(m['clips']); S=190
sh=Image.new('RGB',(S*6,S*len(cl)),(40,40,40))
for r,c in enumerate(cl):
    for k in range(6):
        p=f'review/shots/s{t}_{c}_{k}.png'
        if not os.path.exists(p): continue
        im=Image.open(p).convert('RGB'); w,h=im.size; im=im.crop(((w-h)//2,0,(w+h)//2,h)).resize((S,S))
        if k==0: ImageDraw.Draw(im).text((3,3),c,fill=(255,255,0))
        sh.paste(im,(k*S,r*S))
sh.save(f'review/sheet_strips_{t}.png'); print('sheet',t)
PY
