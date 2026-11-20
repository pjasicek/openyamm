#!/usr/bin/env python3
"""Prepare a Codex face repaint for projection (face fix 2026-11-02): (1) the mouth moved down onto the input's lip line (Codex left the
lip seam ~25 px high): a smooth vertical displacement round the mouth, found from the darkest row of the centre columns in both images;
(2) the repaint's overall skin colour matched to the input by per-channel gains measured on the forehead and chin (the rosy cheeks stay
relatively rosier), so the projection window's edge does not show. Args: <in png> <out png> <aligned png>"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage
A, B, OUT = sys.argv[1:4]
a = np.asarray(Image.open(A).convert('RGB'), float); b = np.asarray(Image.open(B).convert('RGB'), float); H, W = a.shape[:2]
la, lb = a.mean(-1), b.mean(-1)
ra = 760 + int(np.argmin(la[760:940, 600:654].mean(1))); rb = 760 + int(np.argmin(lb[760:940, 600:654].mean(1)))
dy = ra - rb; print('lip line in', ra, 'out', rb, 'shift', dy)
yy, xx = np.mgrid[0:H, 0:W].astype(float)
# displacement: full inside an ellipse round the mouth, smooth falloff to zero by the nose and the chin's end
cx, cy = 627.0, float(rb)
r = np.sqrt(((xx - cx) / 190.0) ** 2 + ((yy - cy) / 95.0) ** 2)
k = np.clip(1.5 - r, 0, 1); k = k * k * (3 - 2 * k)
src_y = yy - dy * k
bw = np.stack([ndimage.map_coordinates(b[..., c], [src_y, xx], order=1, mode='nearest') for c in range(3)], -1)
reg = np.zeros((H, W), bool); reg[295:335, 560:700] = True; reg[960:1010, 580:680] = True
g = a[reg].mean(0) / np.maximum(bw[reg].mean(0), 1e-3); print('gains', np.round(g, 3))
bw = np.clip(bw * g, 0, 255)
Image.fromarray(np.uint8(bw + 0.5)).save(OUT); print('ALIGNED', OUT)
