from pathlib import Path
import json
import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt,binary_dilation
p=Path(__file__).resolve().parent
records={}
for key in json.loads((p/'checks.json').read_text())['frames']:
 f=p/(key+'.png');b=p/(key+'.before_edge_cleanup.png')
 if not b.exists():b.write_bytes(f.read_bytes())
 a=np.array(Image.open(b).convert('RGBA'));rgb=a[:,:,:3].astype(float)
 excess=np.minimum(rgb[:,:,0],rgb[:,:,2])-rgb[:,:,1]
 edge=distance_transform_edt(a[:,:,3]>0)<=3
 brass=np.indices(excess.shape)[0]>=66
 strong=(excess>np.where(brass,35,100))&edge&(a[:,:,3]>0)
 band=binary_dilation(strong,iterations=1)&edge&(excess>np.where(brass,12,70))&(a[:,:,3]>0)
 clean=(a[:,:,3]>=240)&(excess<np.where(brass,12,65))
 _,idx=distance_transform_edt(~clean,return_indices=True)
 fg=rgb[tuple(idx)];d=np.array([255.,0.,255.])-fg
 mix=np.clip(np.sum((rgb-fg)*d,axis=2)/np.maximum(np.sum(d*d,axis=2),1),0,1)
 a[:,:,:3][band]=fg[band].astype('uint8')
 a[:,:,3][band]=np.rint(a[:,:,3][band]*(1-mix[band])).astype('uint8')
 a[:,:,3][band&(mix>.85)]=0;a[a[:,:,3]==0,:3]=0
 Image.fromarray(a).save(f);records[key]=int(band.sum())
(p/'edge_cleanup.json').write_text(json.dumps({'method':'Nearest opaque donor magenta unmix, restricted to outer three pixels and strong excess; purple interior preserved with elevated thresholds. Replay from before_edge_cleanup backups after process.','affected_pixels':records},indent=2)+'\n')
