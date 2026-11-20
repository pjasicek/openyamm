from pathlib import Path
import sys,numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt
P=Path(__file__).resolve().parents[1];dest=P/'work/round5'/f'baked{sys.argv[1]}'
for f in dest.glob('*_projection.npz'):
 data=np.load(f);valid=data['coverage']>0;_,idx=distance_transform_edt(~valid,return_indices=True)
 for mode in ['base','orm','mask','normal']:
  a=data[mode].copy();a[~valid]=a[tuple(idx[:,~valid])];Image.fromarray(np.rint(np.clip(a,0,1)*255).astype('uint8')).save(dest/(f.stem.replace('_projection','')+'_'+mode+'.png'))
