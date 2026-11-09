"""UV coverage of the welded source at the base colour size: work/uv_cover.png (white = used) and the colour of the
unused texels. Usage: uv_coverage.py"""
import numpy as np
from PIL import Image, ImageDraw
d = np.load('work/mesh_in.npz'); uv = d['wuv'].reshape(-1, 3, 2)
img = np.asarray(Image.open('work/basecolor.png').convert('RGB')); H, W = img.shape[:2]
cov = Image.new('L', (W, H), 0); dr = ImageDraw.Draw(cov)
for t in uv:
    dr.polygon([(u * W, (1 - v) * H) for u, v in t], fill=255)
cov.save('work/uv_cover.png'); c = np.asarray(cov) > 0
out = img[~c].astype(float)
print('coverage', round(c.mean(), 3), 'unused texel colour mean', out.mean(0).round(1), 'share near-black', round((out.max(1) < 30).mean(), 3))
# gutter ring: texels within 6 px outside coverage
from scipy import ndimage
ring = ndimage.binary_dilation(c, iterations=6) & ~c
r = img[ring].astype(float); print('6px ring mean', r.mean(0).round(1), 'near-black share', round((r.max(1) < 40).mean(), 3))
