from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import binary_erosion,binary_dilation,distance_transform_edt
import json,hashlib
p=Path('/home/pjasicek/github/OpenYAMM/level_generation/sprites/restoration_jobs/results/g17470_v0_s0/attempt_01')
c=np.asarray(Image.open(p/'raw.png').convert('RGB'),dtype=float)/255
m=np.asarray(Image.open(p/'mask.png').convert('L'),dtype=float)/255
core=binary_erosion(m>.2,iterations=4)
_,idx=distance_transform_edt(~core,return_indices=True)
f=c[idx[0],idx[1]]
bg=np.array([1.,0.,1.]);v=f-bg
alpha=np.clip(np.sum((c-bg)*v,axis=2)/np.maximum(np.sum(v*v,axis=2),1e-6),0,1)
alpha[core]=1
alpha[~binary_dilation(m>.2,iterations=2)]=0
alpha[alpha<.025]=0
Image.fromarray(np.rint(alpha*255).astype('uint8')).save(p/'projected_mask.png')
(p/'projected_mask.json').write_text(json.dumps({'method':'Opaque angel body, feathers and horn: mask threshold0.2 eroded4 establishes solid interior, nearest opaque-core RGB projected against magenta; preserve core alpha1, constrain to mask support dilated2, reject alpha below0.025. No RGB redraw or per-frame transforms.','raw_sha256':hashlib.sha256((p/'raw.png').read_bytes()).hexdigest(),'mask_sha256':hashlib.sha256((p/'mask.png').read_bytes()).hexdigest()},indent=2)+'\n')
