from pathlib import Path
import json
import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt, binary_dilation
p=Path(__file__).resolve().parent
f=p/'a_12855437ec349b6d1ebb.png'
b=p/'a_12855437ec349b6d1ebb.before_secondary_matte.png'
if not b.exists(): b.write_bytes(f.read_bytes())
a=np.array(Image.open(b).convert('RGBA')); rgb=a[:,:,:3].astype(float)
excess=np.minimum(rgb[:,:,0],rgb[:,:,2])-rgb[:,:,1]
strong=(excess>80)&(a[:,:,3]>0)
band=binary_dilation(strong,iterations=1)&(excess>65)&(a[:,:,3]>0)
clean=(a[:,:,3]>=192)&(excess<=45)
_,idx=distance_transform_edt(~clean,return_indices=True)
fg=rgb[tuple(idx)]; direction=np.array([255.,0.,255.])-fg
mix=np.clip(np.sum((rgb-fg)*direction,axis=2)/np.maximum(np.sum(direction*direction,axis=2),1),0,1)
a[:,:,:3][band]=np.clip(fg[band],0,255).astype('uint8')
a[:,:,3][band]=np.rint(a[:,:,3][band]*(1-mix[band])).astype('uint8')
a[:,:,3][band & (mix>.85)]=0
a[a[:,:,3]==0,:3]=0
Image.fromarray(a).save(f)
(p/'secondary_matte_cleanup.json').write_text(json.dumps({'method':'Local nearest opaque green/brown donor with magenta mixture alpha removal, limited to highly saturated secondary magenta contamination only; muted native rose leaves excluded; primary cyan export retained.','affected_pixels':int(band.sum()),'backup':b.name},indent=2)+'\n')
