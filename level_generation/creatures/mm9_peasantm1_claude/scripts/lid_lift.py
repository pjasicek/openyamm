#!/usr/bin/env python3
"""Lift the upper-lid shadow of a front face repaint (face fix r15): Codex painted a brown socket shadow between the
brows and the upper lashes, and warp_eyes.py stretched tier A's lashes over it; from the viewer's raised head camera
that band read as a second dark brow over half-closed eyes. Between rows Y0 and Y1 (soft 10 px ramp above, 18 px below) and columns X0-X1
(soft 30 px), the broad colour (Gaussian 10 px) moves STRENGTH toward the forehead's median colour (rows FY0-FY1),
fine detail (lashes, creases) kept at 70 %. Usage: lid_lift.py <in png> <out png> Y0 Y1 [X0 X1 FY0 FY1 STRENGTH]"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage
src, dst = sys.argv[1:3]
Y0, Y1 = float(sys.argv[3]), float(sys.argv[4])
X0, X1, FY0, FY1, S = (float(v) for v in (sys.argv[5:10] if len(sys.argv) > 9 else (300, 954, 330, 390, 0.6)))
im = np.asarray(Image.open(src).convert('RGB'), float)
H, W = im.shape[:2]
ys, xs = np.mgrid[0:H, 0:W]


def ramp(v, a, b):
    return np.clip((v - a) / (b - a), 0, 1)


w = ramp(ys, Y0 - 10, Y0) * (1 - ramp(ys, Y1, Y1 + 18)) * ramp(xs, X0, X0 + 30) * (1 - ramp(xs, X1 - 30, X1)) * S
ref = np.median(im[int(FY0):int(FY1), int(X0) + 120:int(X1) - 120].reshape(-1, 3), 0)
low = ndimage.gaussian_filter(im, (10, 10, 0))
detail = im - low
out = im * (1 - w[..., None]) + (low + (ref - low) * 1.0 + detail * 0.7) * w[..., None]
Image.fromarray(np.uint8(np.clip(out, 0, 255))).save(dst)
print('LIDLIFT', dst, 'forehead ref', ref.round())
