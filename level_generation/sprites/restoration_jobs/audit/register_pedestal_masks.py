from pathlib import Path
from PIL import Image
import numpy as np
from scipy import ndimage
import json,hashlib
p=Path('level_generation/sprites/restoration_jobs')
for job in ['g00353_v0_s0','g00361_v0_s0']:
 d=p/'results'/job/'attempt_03';raw=Image.open(d/'raw.png').convert('RGB');rgb=np.asarray(raw,dtype=float)/255
 m=np.asarray(Image.open(d/'mask.png').convert('L').resize(raw.size))>30
 # Generated masks contain shading. Only their outer silhouette is used; these props are opaque.
 near_matte=np.linalg.norm(rgb-np.array([1.,0.,1.]),axis=2)<.12
 seed=np.zeros(m.shape,dtype=bool);seed[0,:]=near_matte[0,:];seed[-1,:]=near_matte[-1,:];seed[:,0]=near_matte[:,0];seed[:,-1]=near_matte[:,-1]
 background=ndimage.binary_propagation(seed,mask=near_matte)
 m=~background;core=ndimage.distance_transform_edt(m)>4
 _,near=ndimage.distance_transform_edt(~core,return_indices=True);fg=rgb[near[0],near[1]]
 bg=np.array([1.,0.,1.]);v=fg-bg
 alpha=np.clip(np.sum((rgb-bg)*v,axis=2)/np.maximum(np.sum(v*v,axis=2),1e-8),0,1)
 alpha[core]=1
 alpha[~ndimage.binary_dilation(m,iterations=2)]=0
 Image.fromarray(np.uint8(np.round(alpha*255))).save(d/'mask_registered.png')
 (d/'mask_registration.json').write_text(json.dumps({'method':'Correct shifted companion silhouette using connected raw near-magenta exterior (distance<.12); retain all enclosed material regardless of color. Opaque interior beyond4px. Estimate boundary alpha by projection against nearest opaque RGB and pure magenta. No material desaturation.','raw_sha256':hashlib.sha256((d/'raw.png').read_bytes()).hexdigest(),'mask_sha256':hashlib.sha256((d/'mask.png').read_bytes()).hexdigest()},indent=2)+'\n')
