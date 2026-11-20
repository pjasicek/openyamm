#!/usr/bin/env python3
"""Move the repainted eyes onto the mesh's eyes (face fix): Codex opened tier A's eyes 35 px (5.6 mm at ortho 0.2) above
the input's, i.e. onto the upper lid of the mesh. A vertical displacement d(y) (smoothstep 0 at the brows, DY at the
input's eye line, 0 at the cheeks) moves them back: out(y) = repaint(y - d(y)); brows, nose and cheeks are unchanged.
Measured on full-size crops (references_face/): A input eye line y 550, repaint 515; B 545 / 550 (left as it is).
Usage: warp_eyes.py <repaint png> <out png> <eye line y in the input> <dy> [top y] [bottom y]"""
import sys
import numpy as np
from PIL import Image
src, dst, EY, DY = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4])
TOP = float(sys.argv[5]) if len(sys.argv) > 5 else EY - 70
BOT = float(sys.argv[6]) if len(sys.argv) > 6 else EY + 90
im = np.asarray(Image.open(src).convert('RGB'), float)
H, W = im.shape[:2]
y = np.arange(H, dtype=float)


def ss(t):
    t = np.clip(t, 0, 1); return t * t * (3 - 2 * t)


d = np.where(y < EY, ss((y - TOP) / (EY - TOP)), ss((BOT - y) / (BOT - EY))) * DY
sy = np.clip(y - d, 0, H - 1.001)
y0 = sy.astype(int); f = (sy - y0)[:, None, None]
out = im[y0] * (1 - f) + im[y0 + 1] * f
Image.fromarray(np.uint8(np.clip(out, 0, 255))).save(dst)
print('WARP', dst, 'max shift', DY)
