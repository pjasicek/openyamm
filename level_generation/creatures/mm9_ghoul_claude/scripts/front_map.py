"""Front-projected image of the body atlas around the belt, for alignment. Args: <png> <out>"""
import sys
import numpy as np
from PIL import Image
sys.path.insert(0, 'scripts'); import project_lib as PL; F = np.load('work/faces.npz'); sel = (F['head'] == 0) & (F['part'] != 3); pos, nor, cov, bar, fid = PL.raster(F['uvb'][sel], F['co'][sel], 2048)
base = np.asarray(Image.open(sys.argv[1]).convert('RGB'))
m = cov & (pos[..., 1] < 0.0) & (np.abs(pos[..., 0]) < 0.3) & (pos[..., 2] > -0.05) & (pos[..., 2] < 0.45)
s = 1000
W, H = int(0.6 * s), int(0.5 * s)
im = np.zeros((H, W, 3), 'u1')
x = ((pos[..., 0] + 0.3) * s).astype(int); y = ((0.45 - pos[..., 2]) * s).astype(int)
z_ = pos[..., 1]
buf = np.full((H, W), 9.0)
for yy, xx, zz, c in zip(y[m], x[m], z_[m], base[m]):
    if 0 <= yy < H and 0 <= xx < W and zz < buf[yy, xx]:
        buf[yy, xx] = zz; im[yy, xx] = c
from PIL import ImageDraw
I = Image.fromarray(im).resize((W * 2, H * 2), Image.NEAREST); D = ImageDraw.Draw(I)
for z in np.arange(0.0, 0.45, 0.05):
    yy = (0.45 - z) * s * 2; D.line([(0, yy), (40, yy)], fill=(0, 255, 0)); D.text((44, yy - 5), f'{z:.2f}', fill=(0, 255, 0))
I.save(sys.argv[2])
