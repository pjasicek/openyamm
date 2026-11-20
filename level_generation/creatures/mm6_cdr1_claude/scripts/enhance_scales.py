"""A restrained scale-groove contrast and normal-strength pass over the accepted hide."""
import json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
P=Path(__file__).resolve().parents[1];T=P/'textures';OLD=P/'work/before_scales_v4/textures';report={}
for label in ['body','head']:
    prefix=f'cdr1_{label}_'
    mask=np.array(Image.open(OLD/(prefix+'region_mask.png')).convert('RGBA'),float)/255
    classes=np.array(Image.open(OLD/(prefix+'material_classes.png')))
    weight=mask[:,:,0].copy();weight[np.isin(classes,[4,5,6,7])]=0
    rgb=np.array(Image.open(OLD/(prefix+'basecolor_2k.png')).convert('RGB'))
    color=rgb.astype(float)/255;lum=color@np.array([.2126,.7152,.0722])
    local=ndimage.gaussian_filter(lum,4)
    groove=np.maximum(np.log(np.maximum(local,.02))-np.log(np.maximum(lum,.02)),0)
    factor=np.exp(-np.minimum(groove*.55,.15)*weight)
    out=np.uint8(np.clip(color*factor[:,:,None],0,1)*255+.5)
    assert np.array_equal(rgb[weight==0],out[weight==0])
    Image.fromarray(out).save(T/(prefix+'basecolor_2k.png'))
    raw=np.array(Image.open(OLD/(prefix+'normal_2k.png')).convert('RGB'))
    normals=raw.astype(float)/127.5-1
    normals[:,:,:2]*=(1+.22*weight)[:,:,None]
    normals/=np.maximum(np.linalg.norm(normals,axis=2)[:,:,None],1e-6)
    result=np.uint8(np.clip(normals*.5+.5,0,1)*255+.5);result[weight==0]=raw[weight==0]
    assert np.array_equal(raw[classes==4],result[classes==4])
    Image.fromarray(result).save(T/(prefix+'normal_2k.png'))
    report[label]={'normal_xy_strength':1.22,'maximum_groove_darkening_percent':float((1-factor.min())*100),'average_hide_darkening_percent':float((1-factor[weight>.9]).mean()*100),'protected_ivory_unchanged':True,'affected_texels':int(np.any(rgb!=out,axis=2).sum())}
(P/'review/scales_v4/materials.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
