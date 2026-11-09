from pathlib import Path
import json
import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt
p=Path(__file__).resolve().parent
k=next(iter(json.loads((p/'checks.json').read_text())['frames']))
a=np.array(Image.open(p/f'{k}.png').convert('RGBA'))
Image.fromarray(a).save(p/f'{k}.before_spill.png')
r,g,b=a[:,:,:3].astype(float).transpose(2,0,1)
bad=(a[:,:,3]>0)&(r>g*1.12+3)&(b>g*1.12+3)&(b>r*.65)
good=(a[:,:,3]>=192)&~bad
_,inds=distance_transform_edt(~good,return_indices=True)
a[bad,:3]=a[inds[0][bad],inds[1][bad],:3]
Image.fromarray(a).save(p/f'{k}.png')
(p/'spill_cleanup.json').write_text(json.dumps({'changed_rgb_pixels':int(bad.sum()),'alpha':'unchanged','method':'replace purple matte contamination with nearest opaque non-purple sprite RGB'},indent=2)+'\n')
