"""(PeasantDM2 copy of mm9_sven_claude/scripts/warp_face.py: own landmarks, hairline anchor row 230.)
Undo the Codex repaint's feature drift before project_face.py: per feature patch the offset of the repaint against
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
# PeasantDM2 landmarks in render_face.py's frame (centre z 1.045 m, ortho 0.26, 1254 px): eyes, inner/outer brows, nose
# tip and wings, mouth centre and corners, cheeks below the eyes
feats = [(485, 500), (715, 500), (440, 440), (760, 440), (555, 455), (650, 455), (600, 640), (540, 645), (660, 645),
         (600, 785), (520, 785), (680, 785), (470, 590), (730, 590)]
pts, offs = [], []
# PeasantDM2: ANCHORS="x,y,dx,dy;..." measured offsets (repaint - input) that the correlation cannot find (slit eyes against
# open eyes, a flat mouth against a smile: scripts/iris_centres.py and the mouth-line rows); NCC features within 45 px of an
# anchor are skipped
import os
ANCH = [tuple(float(v) for v in a.split(',')) for a in os.environ.get('ANCHORS', '').split(';') if a]
for ax_, ay_, dx_, dy_ in ANCH:
    pts.append((ax_, ay_)); offs.append((dx_, dy_))
feats = [f for f in feats if all((f[0] - a[0]) ** 2 + (f[1] - a[1]) ** 2 > 45 ** 2 for a in ANCH)]
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
    pts += [(x, 0), (x, R - 1), (x, 230)]; offs += [(0, 0)] * 3
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
