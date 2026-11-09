"""Native diagonal structure with bounded generated microdetail and separate contact shade."""
import sys, json, shutil
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]))
from common import *
from scipy.ndimage import gaussian_filter, distance_transform_edt
from PIL import ImageDraw
# Assemble both native diagonal orientations, with no rotation or per-instance edits.
canvas=Image.new('RGB',(1536,1056),'#202933'); draw=ImageDraw.Draw(canvas)
for col,(label,folder) in enumerate([('Native',P/'references'),('Rejected v7',HERE.parent/'v7/runtime'),('Native reconstruction',HERE/'runtime')]):
    draw.text((col*512+8,4),label,fill='white')
    for row,orient in enumerate(['ne','nw']):
        patch=Image.new('RGB',(768,768))
        dirt=Image.open(M/'runtime/dirt.png') if col else Image.open(P/'references/dirttyl.png').resize((256,256))
        for y in range(3):
            for x in range(3):
                name=None
                if orient=='ne':
                    if x==y: name='drsrne2'
                    elif x==y+1: name='drsrne1'
                else:
                    if x==2-y: name='drsrnw2'
                    elif x==1-y: name='drsrnw1'
                tile=Image.open(folder/(name+'.png')).resize((256,256)) if name else dirt
                patch.paste(tile,(x*256,y*256))
        canvas.paste(patch.resize((512,512)),(col*512,24+row*516))
canvas.save(HERE/'assembled_paths.png')
