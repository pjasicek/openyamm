"""Compose the same all-palette/all-mask evidence for every available session candidate."""
import argparse
import json
from pathlib import Path
import sys
import numpy as np
from PIL import Image, ImageDraw

REPO=Path.cwd()
SESSION=REPO/'level_generation/creatures/mm7_mm8_packed_outline/session_mm7_03'
sys.path.insert(0,str(REPO/'level_generation/creatures/mm7_m514'))
sys.path.insert(0,str(REPO/'level_generation/creatures/mm6_remaining/redo_2x'))
from process import apply_variant,composite
from review_detail_and_alpha import review


def contacts(family):
    out=SESSION/family/'redo_2x'
    names=list(json.loads((out/'registration.json').read_text()))
    variants=json.loads((out/'variants.json').read_text())['variants']
    pages=[]
    for start in range(0,len(names),16):
        selected=names[start:start+16]
        page=Image.new('RGB',(1728,896),'#303030');draw=ImageDraw.Draw(page)
        for i,name in enumerate(selected):
            image=Image.open(out/f'aligned_2x/{name}.png').convert('RGBA')
            mask=Image.open(out/f'masks_2x/{name}.png')
            bounds=image.getchannel('A').getbbox()
            pixels=np.array(image);weights=np.array(mask).astype(float)/255*.7
            if weights.ndim==2:
                pixels[:,:,:3]=np.round(pixels[:,:,:3]*(1-weights[:,:,None])+weights[:,:,None]*[0,200,255]).astype(np.uint8)
            else:
                colors=np.array([[0,200,255],[255,180,0],[220,50,220]])
                pixels[:,:,:3]=np.round(pixels[:,:,:3]*(1-weights.sum(axis=2)[:,:,None])+np.einsum('hwk,kc->hwc',weights,colors)).astype(np.uint8)
            tiles=[apply_variant(image,mask,v) for v in variants]+[Image.fromarray(pixels)]
            x,y=i%4*432,i//4*224
            draw.text((x+2,y+2),name+' / '+','.join(str(v['palette_id']) for v in variants)+' / mask',fill='white')
            for col,tile in enumerate(tiles):
                tile=tile.crop(bounds);tile.thumbnail((104,196),Image.Resampling.LANCZOS)
                page.paste(tile,(x+col*108+(108-tile.width)//2,y+24+(196-tile.height)//2),tile)
        path=out/f'review/all_palette_mask_{start//16:02d}.png';page.save(path);pages.append(str(path.relative_to(out)))
    (out/'review/all_palette_mask.json').write_text(json.dumps(dict(status='visual_review_pending',frames=names,
        palettes=[v['palette_id'] for v in variants],pages=pages,all_masks=True),indent=2)+'\n')
    if (out/'hair_regions.json').exists():
        zones=json.loads((out/'hair_regions.json').read_text())
        for start in range(0,len(names),30):
            page=Image.new('RGB',(1080,900),'#303030');draw=ImageDraw.Draw(page)
            for i,name in enumerate(names[start:start+30]):
                im=Image.open(out/f'aligned_2x/{name}.png').convert('RGBA')
                pixels=np.array(im);weights=np.array(Image.open(out/f'masks_2x/{name}.png')).astype(float)/255
                colors=np.array([[0,220,255],[255,170,0],[220,50,220]])
                pixels[:,:,:3]=np.round(pixels[:,:,:3]*(1-.6*weights.sum(axis=2)[:,:,None])+.6*np.einsum('hwk,kc->hwc',weights,colors)).astype(np.uint8)
                x0,y0,x1,y1=zones[name]
                tile=Image.fromarray(pixels).crop((max(0,x0-30),max(0,y0-30),min(im.width,x1+30),min(im.height,y1+30)))
                tile.thumbnail((175,160));x=i%6*180;y=i//6*180
                page.paste(tile,(x,y+20),tile);draw.text((x,y),name,fill='white')
            page.save(out/f'review/hair_mask_review_{start//30}.png')
    review(str((SESSION/family).relative_to(REPO)))
    print(family,len(names),len(pages),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('families',nargs='+');args=parser.parse_args()
    for family in args.families:contacts(family)
