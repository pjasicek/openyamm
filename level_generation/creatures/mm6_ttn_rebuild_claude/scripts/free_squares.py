"""Largest empty squares in the LOD0 atlas (glTF image space), with a margin, ignoring the old hand faces."""
import sys, numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
d = np.load(sys.argv[1]); W, H = 2080, 1024; margin = 6
names = list(d['names']); uv = d['uv']; idx = d['idx'].reshape(-1, 3); j = d['j']; w = d['w']
hand = sum(((j == names.index(b)) * w).sum(1) for b in ('LeftHand', 'RightHand'))
occ = Image.new('L', (W, H), 0); do = ImageDraw.Draw(occ)
for t in idx:
    if hand[t].mean() > 0.5: continue
    do.polygon([(uv[k][0] * W, uv[k][1] * H) for k in t], fill=255)
o = np.array(occ) > 0
o[:, 1024:1056] = True
o = ndimage.binary_dilation(o, iterations=margin)
o[:, :1] = o[:, -1:] = True; o[:1] = o[-1:] = True
free = ~o
dist = ndimage.distance_transform_cdt(free, metric='chessboard')
found = []
for _ in range(6):
    k = np.unravel_index(np.argmax(dist), dist.shape); r = int(dist[k])
    if r < 20: break
    y, x = k; found.append((x - r + 1, y - r + 1, 2 * r - 1))
    free[max(0, y - r - margin):y + r + margin, max(0, x - r - margin):x + r + margin] = False
    dist = ndimage.distance_transform_cdt(free, metric='chessboard')
print('squares (x, y, side px):', found)
