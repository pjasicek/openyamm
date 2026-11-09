#!/bin/bash
# MM9 reference renders for the Codex HD masters: five body views, five head views, the skin x4.
# Usage (repo root): scripts/ref_sheets.sh <project> <id> <dtx> <head z>
set -e
P=$1; ID=$2; DTX=$3; HZ=$4
R=$P/references_hd; mkdir -p $R/mm9
B="/snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1 --python $P/scripts/ref_renders.py --"
$B $P/source/mm9/$ID.glb $R/mm9 body 640 1.95 > $R/mm9/render.log 2>&1
VIEWS=q34,front,left,back,right CENTER=0,0,$HZ $B $P/source/mm9/$ID.glb $R/mm9 head 512 0.42 > $R/mm9/render_head.log 2>&1
python3 - "$R" "$DTX" <<'PY'
import sys
from PIL import Image
R,dtx=sys.argv[1],sys.argv[2]
def row(names,size,out):
    S=Image.new('RGB',(size*len(names),size))
    for i,n in enumerate(names): S.paste(Image.open(f'{R}/mm9/{n}.png').convert('RGB').resize((size,size)),(size*i,0))
    S.save(out)
row(['body_q34','body_front','body_left','body_back','body_right'],640,f'{R}/mm9_views.png')
row(['head_front','head_left','head_q34','head_right','head_back'],512,f'{R}/mm9_head_views.png')
PY
PYTHONPATH=/usr/lib/python3/dist-packages level_generation/creatures/claude_shared/gltf_venv/bin/python - "$P/source/mm9" "$R" <<'PY'
import sys,glob
from PIL import Image
src,R=sys.argv[1],sys.argv[2]
f=sorted(glob.glob(src+'/skins/*.png')+glob.glob(src+'/import/**/*.png',recursive=True))
print(f)
im=Image.open(f[0]).convert('RGB'); im.resize((im.width*4,im.height*4),Image.LANCZOS).save(R+'/mm9_skin_x4.png')
PY
