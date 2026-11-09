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
    target=float((native[:,:,:3]@weights)[native[:,:,3]>=192].mean())
    rgb=a[:66,:,:3].astype(float);mask=a[:66,:,3]>=192;lo,hi=.5,2.
    for _ in range(32):
        factor=(lo+hi)/2;mean=float((np.clip(rgb*factor,0,255)@weights)[mask].mean())
        if mean<target:lo=factor
        else:hi=factor
    a[:66,:,:3]=np.rint(np.clip(rgb*factor,0,255)).astype(np.uint8)
    Image.fromarray(a).save(dst);records[key]={'native_orb_mean_luma':target,'factor':factor}
(p/'orb_grade.json').write_text(json.dumps({'region_native_y':[0,33],'purpose':'Preserve measured native increasing orb brightness across five states; not normalize states to the same brightness. Alpha, geometry and brass support untouched.','frames':records},indent=2)+'\n')
