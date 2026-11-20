from pathlib import Path
import json
import numpy as np
from PIL import Image
p=Path(__file__).resolve().parent
root=p.parents[2]
c=json.loads((p/'checks.json').read_text());records={}
for key in c['frames']:
    a=np.array(Image.open(p/(key+'.before_orb_grade.png')).convert('RGBA'))
    n=np.array(Image.open(root/'native'/(key+'.png')).convert('RGBA'))
    yy=np.indices(a.shape[:2])[0];ny=np.indices(n.shape[:2])[0]
    mask=(yy<66)&(a[:,:,2]>a[:,:,0].astype(int)+12)&(a[:,:,2]>a[:,:,1])&(a[:,:,3]>0)
    nm=(ny<33)&(n[:,:,2]>n[:,:,0].astype(int)+12)&(n[:,:,2]>n[:,:,1])&(n[:,:,3]>=192)
    solid=mask&(a[:,:,3]>=192)
    target=n[:,:,:3][nm].mean(axis=0)/255
    rgb=a[:,:,:3].astype(float)/255
    lo=np.full(3,.1);hi=np.full(3,5.)
    for _ in range(40):
        gamma=(lo+hi)/2
        mean=(rgb[solid]**gamma).mean(axis=0)
        lo=np.where(mean>target,gamma,lo);hi=np.where(mean<=target,gamma,hi)
    out=a.copy();out[:,:,:3][mask]=np.rint(255*rgb[mask]**gamma).astype(np.uint8)
    Image.fromarray(out).save(p/(key+'.png'))
    records[key]={'native_mean_rgb':(target*255).tolist(),'gamma':gamma.tolist(),'changed_pixels':int(mask.sum())}
(p/'orb_gamma.json').write_text(json.dumps({'method':'Bounded per-channel power curve on blue orb pixels only; no clipping, brass and alpha unchanged; original per-state target preserved. Replay from before_orb_grade backups.','frames':records},indent=2)+'\n')
