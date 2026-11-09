import sys, numpy as np
from PIL import Image
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from headpos import texel_positions
N = 2048
pos, cov = texel_positions(sys.argv[1], 'PeasantDM2Head', N)
img = np.asarray(Image.open('textures/pdm2_tp_head_basecolor.png').convert('RGB'), float)
P = np.nan_to_num(pos); y, x, z = P[..., 1], P[..., 0], P[..., 2]
lum = img @ [0.299, 0.587, 0.114]
zone = cov & (np.abs(x) < 0.16) & (y < 0.96) & (z < 0.07)
ys, xs = np.nonzero(zone)
y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
dbg = img.copy(); dbg[~cov] = [0, 0, 255]; dark = zone & (lum < 110); dbg[dark] = [0, 255, 0]
Image.fromarray(np.uint8(np.concatenate([img[y0:y1, x0:x1], dbg[y0:y1, x0:x1]], 1))).save('review/neck_probe3.png')
print('BOX', y0, y1, x0, x1, 'dark', dark.sum())
