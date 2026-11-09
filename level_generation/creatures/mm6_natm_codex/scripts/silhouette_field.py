import sys,numpy as np
from pathlib import Path
from PIL import Image
from scipy.ndimage import binary_erosion,distance_transform_edt
ref,cur,out=map(Path,sys.argv[1:]);fields={}
for i in range(8):
 a=np.asarray(Image.open(ref/f'natm_b_{i}.png'))[:,:,3]>.5*255;b=np.asarray(Image.open(cur/f'natm_b_{i}.png'))[:,:,3]>.5*255
 border=a&~binary_erosion(a);dist,ids=distance_transform_edt(~border,return_indices=True);cb=b&~binary_erosion(b);cd=distance_transform_edt(~cb);signed=distance_transform_edt(a)-distance_transform_edt(~a);gy,gx=np.gradient(signed);ny,nx=ids;norm=np.maximum(np.hypot(gy[ny,nx],gx[ny,nx]),1e-6);edge=np.stack([ny+.5-.5*gy[ny,nx]/norm,nx+.5-.5*gx[ny,nx]/norm]);fields[f'nearest_{i}']=edge.astype(np.float32);fields[f'candidate_{i}']=cd.astype(np.float32)
np.savez_compressed(out,**fields)
