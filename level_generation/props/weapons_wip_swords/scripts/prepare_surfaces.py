"""Convert the painted template to relightable colour, roughness and OpenGL normal maps."""
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

PROJECT=Path(__file__).resolve().parents[1]
PALETTE={
 'steel':('b9c1c7',0,1,.31),'silver':('ced1d4',0,1,.27),'iron':('959b9d',0,1,.46),
 'blue':('8cb3ce',0,1,.26),'purple':('b19fbf',0,1,.27),'pink':('c6a5b8',0,1,.30),
 'darksteel':('6c747b',0,1,.38),'greensteel':('999f86',0,1,.42),
 'gold':('d6ae51',1,1,.30),'bronze':('a57d53',4,1,.44),
 'brown':('805038',2,0,.65),'black':('343133',2,0,.68),'red':('923e2c',2,0,.58),
 'ivory':('d6c9a7',5,0,.42),'fire':('e6a13e',3,1,.32),
 'rust':('92704e',0,0,.70),'bone':('d5c9ae',5,0,.50),
 'rune':('888d96',6,1,.38),'feather':('d6ae51',7,1,.32),
 'ruby':('b83d48',5,0,.16),'emerald':('319c62',5,0,.16),
 'cyan':('58b4cb',5,0,.16),'pinkgem':('bc5fb5',5,0,.16),
 'warmsteel':('bbb49b',0,1,.29),'gold_blade':('c9b46e',0,1,.29),
}


def main():
    source=PROJECT/'references/surface_painted.png';im=Image.open(source).convert('RGB')
    w,h=im.size
    for name,(colour,tile,metal,rough) in PALETTE.items():
        x,y=tile%4*w//4,tile//4*h//2
        cell=im.crop((x+8,y+8,x+w//4-8,y+h//2-8)).resize((512,512),Image.Resampling.LANCZOS)
        rgb=np.asarray(cell,dtype=float)/255
        lum=rgb.mean(axis=2)
        colour=np.array([int(colour[i:i+2],16) for i in (0,2,4)],dtype=float)
        if name=='fire':
            albedo=np.clip(rgb*255*.45+colour[None,None,:]*.55,30,243)
        else:
            # Remove the painted highlights: the relief belongs in normal/roughness, not albedo.
            contrast=.12 if tile in (0,1,4,7) else .28
            albedo=np.clip(colour[None,None,:]*(1+contrast*(lum-lum.mean()))[:,:,None],30,243)
        if name=='rust':
            mottling=np.asarray(cell.filter(ImageFilter.GaussianBlur(2)),dtype=float).mean(axis=2)/255
            exposed=mottling>np.quantile(mottling,.62)
            albedo=np.where(exposed[:,:,None],np.array([151,153,147]),np.array([124,81,48]))
            albedo=np.clip(albedo*(.88+.24*mottling[:,:,None]),30,243)
        Image.fromarray(albedo.astype('uint8')).save(PROJECT/'textures'/f'{name}_base.png')
        mr=np.empty((512,512,3),dtype=np.uint8);mr[:,:,0]=255
        mr[:,:,1]=np.clip((rough+.10*(lum-lum.mean()))*255,0,255)
        mr[:,:,2]=255*metal
        if name=='rust':
            mr[:,:,2]=exposed*255
            mr[:,:,1]=np.where(exposed,125,194)
        Image.fromarray(mr).save(PROJECT/'textures'/f'{name}_mr.png')
        field=np.asarray(cell.convert('L').filter(ImageFilter.GaussianBlur(.65)),dtype=float)/255
        dy,dx=np.gradient(field)
        scale=2.0 if tile in (1,4,5,6,7) else .65
        normal=np.stack((-dx*scale,dy*scale,np.ones_like(dx)),axis=-1)
        normal/=np.linalg.norm(normal,axis=-1)[:,:,None]
        if name in ('ruby','emerald','cyan','pinkgem'):
            normal[:]=(0,0,1)
        Image.fromarray(np.uint8(np.clip((normal*.5+.5)*255,0,255))).save(PROJECT/'textures'/f'{name}_normal.png')
        assert albedo.min()>=30 and albedo.max()<=243
    # Puck's large red ladder is a design feature, painted into one inset panel.
    panel=Image.new('RGB',(512,512),(203,163,64));draw=ImageDraw.Draw(panel)
    mask=Image.new('RGB',(512,512),(255,86,255));md=ImageDraw.Draw(mask)
    for y in range(0,512,42):
        draw.rectangle((90,y+5,422,y+33),fill=(164,35,48))
        md.rectangle((90,y+5,422,y+33),fill=(255,70,0))
    panel.save(PROJECT/'textures/ladder_base.png');mask.save(PROJECT/'textures/ladder_mr.png')
    Image.new('RGB',(512,512),(128,128,255)).save(PROJECT/'textures/ladder_normal.png')
    receipt={'tool':'image_gen.imagegen','images':1,'prompt':'references/surface_prompt.txt',
             'guide':'references/surface_uv_template.png','output':'references/surface_painted.png',
             'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'size':list(im.size)}
    receipts=[receipt]
    for name in ('iron_feather','bone','dragon'):
        f=PROJECT/f'references/{name}_hilt_hd.png'
        if f.exists():receipts.append({'tool':'image_gen.imagegen','output':str(f.relative_to(PROJECT)),
                         'prompt':f'references/{name}_hilt_prompt.txt','sha256':hashlib.sha256(f.read_bytes()).hexdigest(),
                         'size':list(Image.open(f).size)})
    (PROJECT/'references/generation_receipts.json').write_text(json.dumps(receipts,indent=2)+'\n')
    print('Prepared',len(PALETTE),'material colours, binary metal masks and +Y tangent normals')


if __name__=='__main__':main()
