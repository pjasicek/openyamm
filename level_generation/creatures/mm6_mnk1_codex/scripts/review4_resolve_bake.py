import numpy as np
from pathlib import Path
from scipy.ndimage import distance_transform_edt
from PIL import Image
p=Path(__file__).resolve().parents[1];out=p/'review/round4';data=np.load(out/'surface_bake.npz');valid=data['valid'];dist,indices=distance_transform_edt(~valid,return_indices=True);pad=(~valid)&(dist<=24)
for name in ['basecolor_2k','region_mask','orm_1k','normal_1k']:
 a=data[name].copy();a[pad]=a[indices[0][pad],indices[1][pad]]
 if name=='normal_1k':a[(~valid)&(~pad)]=[128,128,255,255]
 Image.fromarray(np.flipud(a)).save(out/f'rebaked/mnk1_{name}.png')
assert int(valid.sum())>1000000
