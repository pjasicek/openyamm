#!/usr/bin/env python3
"""Region labels for rim_lining.py only (PeasantDM4 has one skin and no runtime region mask): textures/
pdm4_lining_regions.png, 1K RGBA in the body UV layout. R tunic and shirt (everything not below), G trousers (dull brown,
saturation < 0.8, 0.20-0.48 m), B boots (saturated leather below 0.33 m), A unused. Heights from the static export
(floor 0). rim_lining.py picks each lining's dark texel among the faces of its region and limits the boot band to B/G.
Usage (project folder): lining_regions.py [export glb work/pdm4_body_tex.glb]"""
import sys
sys.path.insert(0, 'scripts')
import numpy as np
from PIL import Image
from scipy import ndimage
from headpos import texel_positions
glb = sys.argv[1] if len(sys.argv) > 1 else 'work/pdm4_body_tex.glb'
N = 1024
pos, cov = texel_positions(glb, 'PeasantDM4', N)
img = np.asarray(Image.open('textures/pdm4_tp_basecolor_graded.png').convert('RGB').resize((N, N), Image.BILINEAR), float)
mx = img.max(2); mn = img.min(2); sat = (mx - mn) / np.maximum(mx, 1)
sat = ndimage.uniform_filter(sat, 5)
y = np.nan_to_num(pos[..., 1], nan=9)
B = cov & (y < 0.33) & (sat > 0.8)
G = cov & (y > 0.20) & (y < 0.48) & (sat <= 0.8) & ~B
R = cov & ~B & ~G
m = np.zeros((N, N, 4), np.uint8)
m[..., 0] = R * 255; m[..., 1] = G * 255; m[..., 2] = B * 255
# pad into the gutters (nearest covered texel)
_, (iy, ix) = ndimage.distance_transform_edt(~cov, return_indices=True)
m = m[iy, ix]
Image.fromarray(m, 'RGBA').save('textures/pdm4_lining_regions.png')
print('LINING_REGIONS texels R', int(R.sum()), 'G', int(G.sum()), 'B', int(B.sum()))
