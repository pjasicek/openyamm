import sys,numpy as np
from pathlib import Path
from PIL import Image
from scipy.ndimage import binary_erosion,distance_transform_edt
ref,cur,out=map(Path,sys.argv[1:]);fields={}
for i in range(8):
 a=np.asarray(Image.open(ref/f'natm_b_{i}.png'))[:,:,3]>.5*255;b=np.asarray(Image.open(cur/f'natm_b_{i}.png'))[:,:,3]>.5*255
 border=a&~binary_erosion(a);dist,ids=distance_transform_edt(~border,return_indices=True);cb=b&~binary_erosion(b);cd=distance_transform_edt(~cb);fields[f'nearest_{i}']=ids;fields[f'candidate_{i}']=cd.astype(np.float32)
np.savez_compressed(out,**fields)
