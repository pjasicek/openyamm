#!/bin/bash
# Review sheets from viewer shots. Project folder.
. scripts/env.sh
for t in a b c; do
  S=""; M=""
  for s in "Standing:0.5:stand:0.5" "Walking:0.3:walk:0.3" "AttackMelee:0.35:hattack1:0.35" "Taunt:0.7:taunt:0.7" "Hit:0.3:wince1:0.3" "Death:0.9:die1:0.9" "Dead:0.5:die1:1.39"; do
    IFS=: read c1 t1 c2 t2 <<< "$s"
    S="$S o${t}_$c1:$c1:$t1:quarter:body"; M="$M m${t}_$c1:$c2:$t2:quarter:body"
  done
  S="$S o${t}_left:Standing:0.5:left:body o${t}_back:Standing:0.5:back:body o${t}_head:Standing:0.5:quarter:head o${t}_mouth:Taunt:0.7:quarter:head"
  M="$M m${t}_left:stand:0.5:left:body m${t}_back:stand:0.5:back:body m${t}_head:stand:0.5:quarter:head m${t}_mouth:taunt:0.7:quarter:head"
  TIER=trog_$t scripts/vshots.sh $S 2>&1 | tail -1
  VIEW=viewer_mm9 TIER=trog_$t scripts/vshots.sh $M 2>&1 | tail -1
done
python3 - <<'PY'
from PIL import Image, ImageDraw
K=['Standing','Walking','AttackMelee','Taunt','Hit','Death','Dead','left','back','head','mouth']
C=240
for t in 'abc':
    s=Image.new('RGB',(C*len(K),C*2),(40,40,40))
    for r,p in enumerate('mo'):
        for k,c in enumerate(K):
            im=Image.open(f'review/shots/{p}{t}_{c}.png').convert('RGB'); w,h=im.size; m=min(w,h); im=im.crop(((w-m)//2,(h-m)//2,(w+m)//2,(h+m)//2)).resize((C,C),Image.LANCZOS)
            ImageDraw.Draw(im).text((4,4),('MM9 ' if p=='m' else 'ours ')+t.upper()+' '+c,fill=(255,255,0)); s.paste(im,(k*C,r*C))
    s.save(f'review/mm9_vs_ours_{t}.png')
s=Image.new('RGB',(C*2*4,C*2*3),(40,40,40))
for r,t in enumerate('abc'):
    for k,c in enumerate(['Standing','left','back','head']):
        im=Image.open(f'review/shots/o{t}_{c}.png').convert('RGB'); w,h=im.size; m=min(w,h); im=im.crop(((w-m)//2,(h-m)//2,(w+m)//2,(h+m)//2)).resize((C*2,C*2),Image.LANCZOS); s.paste(im,(k*C*2,r*C*2))
s.save('review/sheet_tiers.png')
PY
echo SHEETSDONE
