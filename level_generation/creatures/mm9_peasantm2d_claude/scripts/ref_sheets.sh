#!/bin/bash
# MM9 reference renders for the Codex HD masters (from mm9_peasantm8d_claude): five body views, five head views, the skin x4.
# Usage (repo root): scripts/ref_sheets.sh <project> <id> <head z> <suffix>   (writes references_hd/mm9_views<suffix>.png etc.)
set -e
P=$1; ID=$2; HZ=$3; SFX=$4
R=$P/references_hd; mkdir -p $R/mm9
B="/snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1 --python $P/scripts/ref_renders.py --"
$B $P/source/mm9/$ID.glb $R/mm9 body$SFX 640 1.95 > $R/mm9/render$SFX.log 2>&1
VIEWS=q34,front,left,back,right CENTER=0,0,$HZ $B $P/source/mm9/$ID.glb $R/mm9 head$SFX 512 0.42 > $R/mm9/render_head$SFX.log 2>&1
python3 - "$R" "$P/source/mm9/skins/$ID.png" "$SFX" <<'PY'
import sys
from PIL import Image
R,skin,s=sys.argv[1:4]
def row(names,size,out):
    S=Image.new('RGB',(size*len(names),size))
    for i,n in enumerate(names): S.paste(Image.open(f'{R}/mm9/{n}.png').convert('RGB').resize((size,size)),(size*i,0))
    S.save(out)
row([f'body{s}_q34',f'body{s}_front',f'body{s}_left',f'body{s}_back',f'body{s}_right'],640,f'{R}/mm9_views{s}.png')
row([f'head{s}_front',f'head{s}_left',f'head{s}_q34',f'head{s}_right',f'head{s}_back'],512,f'{R}/mm9_head_views{s}.png')
im=Image.open(skin).convert('RGB'); im.resize((im.width*4,im.height*4),Image.LANCZOS).save(f'{R}/mm9_skin_x4{s}.png')
PY
