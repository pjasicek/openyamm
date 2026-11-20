"""Decode original indexed sprites with their real native tier palettes, not BMP preview colours."""
from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib,numpy as np
P=Path(__file__).resolve().parents[1];R=P.parents[2]
s=json.loads((P.parent/'mm8_m632/sources.json').read_text())
N=P/'references_native';N.mkdir(exist_ok=True)
palettes={}
for pal,info in s['palette_sources'].items():
    f=R/info['path'];raw=f.read_bytes();assert hashlib.sha256(raw).hexdigest()==info['sha256']
    palettes[pal]=np.frombuffer(raw[:768],np.uint8).reshape(256,3)
def decode(info,pal='633'):
    f=R/info['path'];assert hashlib.sha256(f.read_bytes()).hexdigest()==info['sha256'],f
    idx=np.array(Image.open(f));rgb=palettes[pal][idx]
    return Image.fromarray(np.concatenate([rgb,np.where(idx==0,0,255).astype(np.uint8)[...,None]],axis=2))
for stem,info in s['sources'].items():decode(info).save(N/f'{stem}.png')
(N/'inventory.json').write_text(json.dumps(s,indent=2)+'\n')
def sheet(names,file,columns=5,scale=2):
    tile=256*scale;out=Image.new('RGB',(columns*tile,((len(names)+columns-1)//columns)*(tile+26)),(65,67,70));draw=ImageDraw.Draw(out)
    for i,stem in enumerate(names):
        im=Image.open(N/f'{stem}.png').resize((tile,tile),Image.Resampling.NEAREST);x=i%columns*tile;y=i//columns*(tile+26)
        out.paste(im,(x,y),im);draw.text((x+6,y+tile+5),stem,fill='white')
    out.save(N/file)
sheet([f'm632sa{i}' for i in range(5)],'standing.png')
sheet([f'm632a{f}{v}' for v in [0,2] for f in 'abcdefgh'],'attack.png',8,2)
sheet([f'm632{a}{f}0' for a,frames in [('w','abcdefgh'),('f','abcde'),('n','abcde'),('d','abcd'),('x','a')] for f in frames],'motion.png',8,1)
preview=Image.new('RGB',(3*512,560),(65,67,70));draw=ImageDraw.Draw(preview)
for i,pal in enumerate(palettes):
    img=decode(s['sources']['m632sa0'],pal);img.save(N/f'standing_{pal}.png');img=img.resize((512,512),Image.Resampling.NEAREST)
    preview.paste(img,(i*512,0),img);draw.text((i*512+10,530),f'Native palette {pal}',fill='white')
preview.save(N/'tiers.png')
print('NATIVE',len(s['sources']),'verified bitmaps,',len(palettes),'verified palettes')
