#!/bin/bash
# all tiers, both hands, four clips, side and back of the wrist; one sheet per tier and review/sheet_wrist_fix.png. Project folder.
G=/home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared/gltf_venv/bin/python
S=$($G scripts/hand_specs.py export/mm9_trellborg.glb 2>/dev/null | tr '\n' ' ')
for t in ${TIERS:-a b c}; do mkdir -p review/shots/wrist$t; scripts/vs.sh trell_$t review/shots/wrist$t $S | tail -1 | cut -c1-10; done
$G - <<'P' 2>/dev/null
from PIL import Image
c_=('Standing','Running','Walking','AttackMelee'); v_=('Rs','Rb','Ls','Lb'); C=480
A=Image.new('RGB',(3*4*C,4*C))
for i,t in enumerate('abc'):
    W=Image.new('RGB',(4*C,4*C))
    for r,c in enumerate(c_):
        for k,v in enumerate(v_):
            W.paste(Image.open(f'review/shots/wrist{t}/{c}{v}.png').convert('RGB').resize((C,C)),(k*C,r*C))
    W.save(f'review/wrist_{t}.png'); A.paste(W,(i*4*C,0))
A.save('review/sheet_wrist_fix.png')
P
echo WSHEET_DONE
