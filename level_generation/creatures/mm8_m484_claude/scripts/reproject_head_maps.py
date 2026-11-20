"""Resample the original head maps through the unchanged per-face UV correspondence."""
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
P=Path(__file__).resolve().parents[1];m=np.load(P/'work/head_uv_lookup.npz');uv,cov=m['uv'],m['coverage'];out=P/'work/head_uv_repacked';out.mkdir(exist_ok=True)
_,ix=ndimage.distance_transform_edt(~cov,return_indices=True)
for label in ['base_color','normal','roughness','metallic']:
 a=np.asarray(Image.open(P/f'meshy/head_retexture_v1/texture_urls_0_{label}.png').convert('RGB'),float)
 coords=np.array([(1-uv[...,1])*a.shape[0]-.5,uv[...,0]*a.shape[1]-.5])
 result=np.stack([ndimage.map_coordinates(a[...,i],coords,order=1,mode='nearest') for i in range(3)],-1);result=result[tuple(ix)]
 Image.fromarray(np.uint8(np.clip(result+.5,0,255))).save(out/f'texture_urls_0_{label}.png')
print('REPROJECTED head maps')
