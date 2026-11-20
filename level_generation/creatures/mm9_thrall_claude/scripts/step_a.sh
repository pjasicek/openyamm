#!/bin/bash
# fit -> graft + views. Run from the project folder.
R=$PWD
F='^(PARTS|torso|floor)' scripts/run.sh fit_thrall.py $R/meshy/thrall_smart_v1/model_urls_glb.glb $R/source/true/thrall1_true.glb $R/scripts/fit_config.json $R/work/pose_v1.blend
F='^(RING|BRIDGE|COLLAR|NECK|FINAL)' scripts/run.sh graft_thrall.py $R/work/pose_v1.blend $R/work/head_parts.blend $R/work/graft_v1.blend
F=NOPE scripts/run.sh blend_views.py $R/work/graft_v1.blend x $R/work/gv; F=NOPE scripts/run.sh blend_parts.py $R/work/graft_v1.blend $R/work/gh 0.75 0,-0.2,0.72
python3 - <<'P'
from PIL import Image
s=Image.new('RGB',(5*400,2*400))
for k,v in enumerate(['q34','front','left','back','right']):
    s.paste(Image.open(f'work/ref/b1_{v}.png').convert('RGB').resize((400,400)),(k*400,0))
    s.paste(Image.open(f'work/gv_{v}.png').convert('RGB').resize((400,400)),(k*400,400))
s.save('work/_fit.png')
s=Image.new('RGB',(5*420,420))
for k,v in enumerate(['q34','front','left','back','under']):
    s.paste(Image.open(f'work/gh_{v}.png').convert('RGB').resize((420,420)),(k*420,0))
s.save('work/_gh.png')
P
