#!/bin/bash
# Usage: scripts/clay.sh <glb> <out png> <items> [views]: clay frames sheet. env SIZE ORTHO
R=$PWD; glb=$1; out=$2; items=$3; views=${4:-front,side,q34}
F=NOPE scripts/run.sh clay_frames.py $R/$glb $R/work/_cf $items $views
python3 - "$out" <<'P'
import sys
from PIL import Image, ImageDraw
rows=[l.split('\t') for l in open('work/_cf.list').read().split('\n') if l]
s=Image.open(rows[0][1]).size[0]
W=Image.new('RGB',(s*(len(rows[0])-1),s*len(rows)))
for y,r in enumerate(rows):
    for x,p in enumerate(r[1:]):
        im=Image.open(p).convert('RGB'); ImageDraw.Draw(im).text((4,4),r[0],fill=(255,255,0)); W.paste(im,(x*s,y*s))
W.save(sys.argv[1])
P
