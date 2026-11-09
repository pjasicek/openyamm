"""Complete atlas padding for coarse faces spanning small concave UV gaps; maps stay shared."""
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
P=Path(__file__).resolve().parents[1]
namespace={'__file__':str(P/'scripts/round2_textures.py')}
exec((P/'scripts/round2_textures.py').read_text().split('native=load')[0],namespace)
m=np.load(P/'work/round2/mesh0.npz');pos,part,_=namespace['raster'](m,0,4096)
covered=part>=0;del pos,part
_,nearest=ndimage.distance_transform_edt(~covered,return_indices=True)
for kind in ['basecolor','normal','metal_rough','region_mask']:
 path=P/f'work/round2/textures/mfp_{kind}.png';a=np.array(Image.open(path));a[~covered]=a[tuple(nearest[:,~covered])];Image.fromarray(a).save(path)
print('Completed shared body atlas padding')
