#!/bin/bash
# MM9 renders for the Codex masters: five views of the whole figure without sword and shield, waist, head. Repo root.
cd /home/pjasicek/github/OpenYAMM; P=level_generation/creatures/mm9_clansoldier_claude; R=$P/references_hd; mkdir -p $R/renders
B="/snap/bin/blender --background --factory-startup --python-exit-code 1 --python $P/scripts/ref_renders.py --"
for t in 1 2 3; do l=$(echo abc | cut -c$t)
  HIDE_WEAPONS=1 $B $PWD/$P/source/true/clan${t}_true.glb $PWD/$R/renders full_$l 1024 2.3 2>&1 | grep -E "BOUNDS|Error"
  HIDE_WEAPONS=1 CENTER=0,0,-0.15 $B $PWD/$P/source/true/clan${t}_true.glb $PWD/$R/renders waist_$l 800 0.9 2>&1 | grep -E "Error"
  HIDE_WEAPONS=1 CENTER=0,0,0.78 $B $PWD/$P/source/true/clan${t}_true.glb $PWD/$R/renders head_$l 800 0.62 2>&1 | grep -E "Error"
done
python3 - <<'P'
from PIL import Image
import os
R='level_generation/creatures/mm9_clansoldier_claude/references_hd'
for t,c,s in [('a','1','beldonian1'),('b','2','beldonian2'),('c','3','beldonian3')]:
    for kind,out,S in [('full','views',640),('waist','waist_views',500),('head','head_views',500)]:
        W=Image.new('RGB',(S*5,S),(107,107,107))
        for i,v in enumerate(['q34','front','left','back','right']):
            W.paste(Image.open(f'{R}/renders/{kind}_{t}_{v}.png').convert('RGB').resize((S,S),Image.LANCZOS),(i*S,0))
        W.save(f'{R}/mm9_{out}_{t}.png')
    im=Image.open(f'level_generation/creatures/mm9_clansoldier_claude/source/c{c}/skins/{s}.png').convert('RGB')
    im.resize((1024,1024),Image.LANCZOS).save(f'{R}/mm9_skin_x4_{t}.png')
P
