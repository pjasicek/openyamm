"""Undo the Codex repaint's feature drift before project_face.py: per feature patch the offset of the repaint against
the input (normalised cross-correlation of the high-pass luminance), a smooth displacement field through those offsets
(Gaussian RBF, sigma 90 px; zero anchors on the hairline and the frame edges), the repaint resampled so its features sit
on the input's. Args: <in png> <repaint png> <out png>"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
a = np.asarray(Image.open(sys.argv[1]).convert('L')).astype(np.float64)
B = np.asarray(Image.open(sys.argv[2]).convert('RGB')).astype(np.float64)
b = B.mean(2)
hp = lambda x: x - ndi.gaussian_filter(x, 6)
A, Bh = hp(a), hp(b)
R = a.shape[0]
feats = [(455, 575), (722, 575), (600, 770), (600, 900), (520, 905), (680, 905), (430, 495), (745, 495), (600, 1050),
         (380, 700), (820, 700), (600, 640)]
pts, offs = [], []
for x, y in feats:
    h = 36; t = A[y - h:y + h, x - h:x + h]; t = (t - t.mean()) / (t.std() + 1e-9)
    best = (-9, 0, 0)
    for dy in range(-30, 31):
        for dx in range(-30, 31):
            s = Bh[y - h + dy:y + h + dy, x - h + dx:x + h + dx]; s = (s - s.mean()) / (s.std() + 1e-9)
            c = (t * s).mean()
            if c > best[0]:
                best = (c, dx, dy)
    print('FEAT', x, y, 'dx', best[1], 'dy', best[2], 'ncc %.2f' % best[0])
    if best[0] > 0.45:
        pts.append((x, y)); offs.append((best[1], best[2]))
for x in range(0, R, 125):
    pts += [(x, 0), (x, R - 1), (x, 300)]; offs += [(0, 0)] * 3
for y in range(0, R, 125):
    pts += [(0, y), (R - 1, y)]; offs += [(0, 0)] * 2
pts = np.array(pts, float); offs = np.array(offs, float)
S = 90.0
K = np.exp(-((pts[:, None, :] - pts[None, :, :]) ** 2).sum(-1) / (2 * S * S)) + 1e-3 * np.eye(len(pts))
wts = np.linalg.solve(K, offs)
gy, gx = np.mgrid[0:R, 0:R].astype(np.float64)
field = np.zeros((R, R, 2))
for p, w in zip(pts, wts):
    k = np.exp(-((gx - p[0]) ** 2 + (gy - p[1]) ** 2) / (2 * S * S))
    field += k[..., None] * w
out = np.stack([ndi.map_coordinates(B[..., c], [gy + field[..., 1], gx + field[..., 0]], order=1, mode='nearest')
                for c in range(3)], -1)
Image.fromarray(np.uint8(np.clip(out, 0, 255))).save(sys.argv[3])
print('WARP max shift px', np.abs(field).max().round(1))
