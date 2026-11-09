#!/bin/bash
# strips of every clip for every tier + close-ups + sheets (project folder), one Chrome at a time
G=/home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared/gltf_venv/bin/python; x=export/mm9_trellborg.glb
for t in a b c; do mkdir -p review/shots/st$t
  scripts/vs.sh trell_$t review/shots/st$t $($G scripts/strips.py $x 5 Standing,Walking,Running,Fidget,Fidget2,Fidget3,Taunt,Aware,AttackMelee,AttackMelee2,AttackRanged,Hit,Hit2,Death,Death2,Dead,Backpedal,BackpedalRun st 2>/dev/null | tr '\n' ' ') | tail -1 | cut -c1-40
done
$G - <<'P' 2>/dev/null
from PIL import Image, ImageDraw
import glob, os
clips=['Standing','Walking','Running','Fidget','Fidget2','Fidget3','Taunt','Aware','AttackMelee','AttackMelee2','AttackRanged','Hit','Hit2','Death','Death2','Dead','Backpedal','BackpedalRun']
for t in 'abc':
    W=Image.new('RGB',(5*210,9*210),(30,30,34))
    for part,cs in ((1,clips[:9]),(2,clips[9:])):
        W=Image.new('RGB',(5*230,len(cs)*230),(30,30,34)); d=ImageDraw.Draw(W)
        for r,c in enumerate(cs):
            for k in range(5):
                f=f'review/shots/st{t}/st_{c}_{k:02d}.png'
                if os.path.exists(f): W.paste(Image.open(f).convert('RGB').resize((230,230)),(k*230,r*230))
            d.text((4,r*230+4),c,fill=(255,255,0))
        W.save(f'review/strips_{t}_{part}.png')
P
ls review/shots/*.png | wc -l
echo FINAL2_DONE
