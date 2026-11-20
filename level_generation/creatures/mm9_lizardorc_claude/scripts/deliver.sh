#!/bin/bash
# final gates, regression, strips, close-ups, compare, viewer check. Project folder.
. scripts/env.sh
scripts/viewer_update.sh r5 > /dev/null
scripts/gates.sh
$G scripts/plate_gate.py export/mm9_lizardorc.glb review/gates/plate.txt > /dev/null 2>&1
$G scripts/skirt_gate.py export/mm9_lizardorc.glb review/gates/skirt.json 2>/dev/null > review/gates/skirt.txt
$G ../claude_shared/texture_quality.py export/mm9_lizardorc.glb > review/gates/texq.txt 2>&1
(cd $REPO; python3 level_generation/creatures/../../tools/floor_audit.py --world mm9 --match 'MM9 Lizard*' > $P/review/gates/floor.txt 2>&1 || $G level_generation/creatures/claude_shared/floor/floor_audit.py --world mm9 --match 'MM9 Lizard*' > $P/review/gates/floor.txt 2>&1)
(cd $REPO; env -u PYTHONPATH ./build/game/openyamm --world mm9 --headless-run-regression-suite actors > $P/work/regression.log 2>&1)
for t in a b c; do scripts/strips.sh $t liz_$t > /dev/null 2>&1; done
TIER=liz_a scripts/vshots.sh $($G scripts/closeups.py) > work/close.log 2>&1
for t in a b c; do TIER=liz_$t scripts/vshots.sh t${t}_q:Standing:0.3:quarter:body:-1.6,1.3,3.2:0,.95,0 t${t}_f:Standing:0.3:front:body:0,1,3.6:0,.95,0 t${t}_b:Standing:0.3:back:body:0,1.2,-3.6:0,.95,0 t${t}_h:Standing:0.3:quarter:body:-.75,1.6,1.3:-.15,1.5,.3 > /dev/null 2>&1; done
$G - <<'P'
from PIL import Image, ImageDraw
import glob
S=420
def cr(p):
    im=Image.open(p).convert('RGB'); w,h=im.size; return im.crop(((w-h)//2,0,(w+h)//2,h)).resize((S,S))
o=Image.new('RGB',(S*4,S*3)); 
for r,t in enumerate('abc'):
    for c,k in enumerate('qfbh'): o.paste(cr(f'review/shots/t{t}_{k}.png'),(c*S,r*S))
o.save('review/sheet_tiers.png')
vs=['q34','front','back','left']; o=Image.new('RGB',(S*4,S*2))
for c,v in enumerate(vs): o.paste(Image.open(f'review/ref/mm9_{v}.png').convert('RGB').resize((S,S)),(c*S,0))
for c,k in enumerate('qfb'): o.paste(cr(f'review/shots/ta_{k}.png'),(c*S,S))
o.save('review/mm9_vs_ours.png')
fs=sorted(glob.glob('review/shots/*_Death.png')+glob.glob('review/shots/*_Dead.png')+glob.glob('review/shots/*_Hit2.png')+glob.glob('review/shots/*_AttackMelee.png')+glob.glob('review/shots/*_Death2.png'))
s=240; o=Image.new('RGB',(s*8,s*5))
keys=['kneeL','kneeR','groin','armL','armR','elbowL','neck','mouth']
for r,c_ in enumerate(('Death','Dead','Hit2','AttackMelee','Death2')):
    for c,k in enumerate(keys):
        im=Image.open(f'review/shots/{k}_{c_}.png').convert('RGB'); w,h=im.size; im=im.crop(((w-h)//2,0,(w+h)//2,h)).resize((s,s)); ImageDraw.Draw(im).text((3,3),f'{k} {c_}',fill=(255,255,0)); o.paste(im,(c*s,r*s))
o.save('review/sheet_closeups.png')
P
(cd $REPO; python3 tools/run_creature_review.py --project level_generation/creatures/mm9_lizardorc_claude check > $P/work/check.log 2>&1)
echo DELIVERDONE > work/deliver.done
