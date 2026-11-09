#!/bin/bash
# halo-free copies of the selected masters (project folder): references_hd/*_clean.png and a grey-background contact sheet
cd references_hd
for v in 00_three_quarter 01_front 02_back 03_left 04_right; do python3 ../scripts/clean_alpha.py $v.png ${v}_clean.png ${THR:-240} | tail -1; done
python3 - <<'PY'
from PIL import Image
import numpy as np
ims=[]
for v in ('00_three_quarter','01_front','02_back','03_left','04_right'):
    a=np.array(Image.open(v+'_clean.png').convert('RGBA')).astype(float); al=a[...,3:]/255
    ims.append(Image.fromarray((a[...,:3]*al+128*(1-al)).astype('u1')).resize((512,768)))
s=Image.new('RGB',(512*5,768))
for i,im in enumerate(ims): s.paste(im,(i*512,0))
s.save('clean_views_sheet.png')
PY
