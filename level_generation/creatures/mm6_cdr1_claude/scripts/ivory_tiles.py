import json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
P=Path(__file__).resolve().parents[1];tiles={};N=2048
for label in ['body','head','wings']:
    cov=np.load(P/'work'/f'uvraster_ivory_{label}.npz')['piece']>=0
    if label=='head':
        t=json.loads((P/'work/teeth_tile.json').read_text());cov[t['y']:t['y']+t['height'],t['x']:t['x']+t['width']]=True
    occupied=ndimage.binary_dilation(cov,iterations=8);size=64
    candidates=[(x,y) for y in range(0,N-size,8) for x in range(0,N-size,8) if not occupied[y:y+size,x:x+size].any()]
    assert candidates, label
    x,y=candidates[0];tiles[label]={'x':x,'y':y,'size':size,'padding':8}
    yy,xx=np.mgrid[:size,:size];grain=1.5*np.sin(xx*.42)+.8*np.cos(xx*.91+yy*.11)+.8*np.sin(yy*.2)
    rgb=np.clip(np.array([225,215,188])+grain[:,:,None],0,255).astype(np.uint8)
    for suffix,mode,value in [('basecolor_2k','RGB',rgb),('normal_2k','RGB',[128,128,255]),('metal_rough_2k','RGB',[89,122,0]),('region_mask','RGBA',[0,0,0,0]),('material_classes','L',4)]:
        path=P/'textures'/f'cdr1_{label}_{suffix}.png';a=np.array(Image.open(path).convert(mode));a[y:y+size,x:x+size]=value;Image.fromarray(a).save(path)
(P/'work/ivory_tiles_v3.json').write_text(json.dumps(tiles,indent=2))
print(tiles)
