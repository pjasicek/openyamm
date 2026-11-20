from pathlib import Path
import json
import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt
p=Path(__file__).resolve().parent
k=next(iter(json.loads((p/'checks.json').read_text())['frames']))
a=np.array(Image.open(p/f'{k}.png').convert('RGBA'))
Image.fromarray(a).save(p/f'{k}.before_cyan_edge.png')
r,g,b=a[:,:,:3].astype(float).transpose(2,0,1)
edge=distance_transform_edt(a[:,:,3]>=192)<=2
bad=(a[:,:,3]>0)&edge&(g>r*1.5+4)&(b>r*1.5+4)&(g>b*.75)
good=(a[:,:,3]>=192)&~bad
_,inds=distance_transform_edt(~good,return_indices=True)
a[bad,:3]=a[inds[0][bad],inds[1][bad],:3]
Image.fromarray(a).save(p/f'{k}.png')
(p/'cyan_edge_cleanup.json').write_text(json.dumps({'changed_rgb_pixels':int(bad.sum()),'alpha':'unchanged','method':'Replace saturated cyan boundary residue within two pixels of alpha boundary with nearest opaque non-residue RGB; preserve interior blue snow.'},indent=2)+'\n')
