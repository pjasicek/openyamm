#!/bin/sh
# Flat close-up of the pile LOD0 (pile_closeup.py) next to the x2 sprite: review/shape/pile_close_cmp_<tag>.png
cd "$(dirname "$0")"
/snap/bin/blender --background ../work/skullpile.blend --python pile_closeup.py -- ../review/shape/pile_close.png 2 ${2:-0} 2>&1 | grep -E "Error|Trace"
python3 -c "
from PIL import Image
a=Image.open('/home/pjasicek/github/OpenYAMM/assets_dev/engine/decorations_x2/sklplrev_p547.png').convert('RGBA'); b=Image.open('../review/shape/pile_close.png').convert('RGBA'); b=b.crop(b.getbbox()).resize(a.size)
s=Image.new('RGBA',(a.size[0]*2+10,a.size[1]),(60,60,70,255)); s.alpha_composite(a,(0,0)); s.alpha_composite(b,(a.size[0]+10,0)); s.convert('RGB').resize((s.size[0]*2,s.size[1]*2)).save('../review/shape/pile_close_cmp_$1.png')"
