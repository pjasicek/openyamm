#!/usr/bin/env python3
"""Neutral normal on the lash-line sliver under the right eye (PeasantM5, viewer r2): face 3801 of the head (an 11 mm2 triangle
of the lower lid) maps onto a UV sliver inside the painted iris (spot_fix_pm5.py refills its colour); its normal-map texels hold
the iris relief, which shaded it as a dark triangle in the viewer. Those texels (the same UV triangle, 2 px dilation, at the
normal map's size) are set to the flat tangent normal. Usage (project folder): normal_sliver.py <normal png> [...]"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
TRI = np.array([(916, 427), (929, 433), (925, 424)], float) / 2048.0
for path in sys.argv[1:]:
    im = np.asarray(Image.open(path).convert('RGB')).copy(); N = im.shape[0]
    a, b, c = TRI * N
    yy, xx = np.mgrid[0:N, 0:N] + 0.5
    m = np.array([[b[0] - a[0], c[0] - a[0]], [b[1] - a[1], c[1] - a[1]]])
    l = np.linalg.solve(m, np.stack([xx.ravel() - a[0], yy.ravel() - a[1]])).T
    inside = ((l >= -0.05).all(1) & (l.sum(1) <= 1.05)).reshape(N, N)
    inside = ndi.binary_dilation(inside, iterations=2)
    im[inside] = (128, 128, 255)
    Image.fromarray(im).save(path); print('NORMAL_SLIVER', path, int(inside.sum()))
