from pathlib import Path
from PIL import Image
import json,numpy as np
p=Path(__file__).resolve().parent
root=p.parents[2]
c=json.loads((p/'checks.json').read_text());records={};weights=np.array([.2126,.7152,.0722])
for key in c['frames']:
    dst=p/(key+'.png');backup=p/(key+'.before_orb_grade.png')
    if not backup.exists():backup.write_bytes(dst.read_bytes())
    a=np.array(Image.open(backup).convert('RGBA'));native=np.array(Image.open(root/'native'/(key+'.png')).convert('RGBA'))[:33]
    target=native[:,:,:3][native[:,:,3]>=192].mean(axis=0)
    rgb=a[:66,:,:3].astype(float);mask=a[:66,:,3]>=192;lo,hi=np.full(3,.5),np.full(3,3.)
    for _ in range(32):
        factor=(lo+hi)/2;mean=np.clip(rgb*factor,0,255)[mask].mean(axis=0)
        lo=np.where(mean<target,factor,lo);hi=np.where(mean>=target,factor,hi)
    a[:66,:,:3]=np.rint(np.clip(rgb*factor,0,255)).astype(np.uint8)
    Image.fromarray(a).save(dst);records[key]={'native_orb_mean_rgb':target.tolist(),'factor':factor.tolist()}
(p/'orb_grade.json').write_text(json.dumps({'region_native_y':[0,33],'purpose':'Preserve measured native orb mean color and brightness across five states; not normalize states to the same brightness. Alpha, geometry and brass support untouched.','frames':records},indent=2)+'\n')
