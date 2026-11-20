"""Embed manifest for an offline viewer; no server or fetch permissions needed."""
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from process import resize_base
ROOT=Path(__file__).resolve().parent
manifest=json.loads((ROOT/'manifest.json').read_text())
template=(ROOT/'viewer.html').read_text()
assert template.count('/* MANIFEST */')==1
(ROOT/'review.html').write_text(template.replace('/* MANIFEST */',json.dumps(manifest,separators=(',',':'))))
registration=json.loads((ROOT/'registration.json').read_text())
for kind in ['all_base_dark','all_masks_light']:
    background=(42,45,43) if 'dark' in kind else (224,224,220)
    rows=(len(registration)+11)//12
    contact=Image.new('RGB',(12*144,rows*176),background);draw=ImageDraw.Draw(contact)
    for index,(name,record) in enumerate(registration.items()):
        im=Image.open(ROOT/f'aligned_2x/{name}.png');ox,oy=record['canvas_origin_px']
        if 'masks' in kind:
            a=np.array(im);w=np.array(Image.open(ROOT/f'masks_2x/{name}.png'))/255
            a[:,:,:3]=np.round(a[:,:,:3]*(1-.7*w[:,:,None])+np.array([255,100,0])*.7*w[:,:,None]).astype(np.uint8)
            im=Image.fromarray(a)
        size=(round(im.width/4),round(im.height/4))
        im=(im.convert('RGBa').resize(size,Image.Resampling.LANCZOS).convert('RGBA')
            if 'masks' in kind else resize_base(im,size))
        x=index%12*144;y=index//12*176
        contact.paste(im,(x+8+round(ox/4),y+28+round(oy/4)),im)
        draw.text((x+4,y+5),name,fill='white' if 'dark' in kind else 'black')
    contact.save(ROOT/f'review/{kind}.png')
print(ROOT/'review.html')
