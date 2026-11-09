import sys, numpy as np
from PIL import Image
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from headpos import texel_positions
N = 1024
pos, cov = texel_positions(sys.argv[1], 'PeasantDM2Head', N)
img = np.asarray(Image.open('textures/pdm2_tp_head_basecolor.png').convert('RGB').resize((N, N)), float)
P = np.nan_to_num(pos); y, x, z = P[..., 1], P[..., 0], P[..., 2]
lum = img @ [0.299, 0.587, 0.114]
dark = cov & (lum < 70) & (np.abs(x) < 0.2)
print('dark head texels', dark.sum(), 'y pct', np.percentile(y[dark], [2, 10, 50, 90, 98]).round(3), 'z pct', np.percentile(z[dark], [2, 50, 98]).round(3))
for y0 in np.arange(0.84, 1.10, 0.02):
    m = cov & (y >= y0) & (y < y0 + 0.02) & (np.abs(x) < 0.2)
    if m.sum():
        print('y %.2f n %5d dark %.2f lum %5.1f zmin %.3f zmax %.3f' % (y0, m.sum(), (m & dark).sum() / m.sum(), np.median(lum[m]), z[m].min(), z[m].max()))
