#!/usr/bin/env python3
"""Meshy's mail, scales and fur come back far paler than MM9's at viewing distance: bright pixels of fine patterns win the mip average. A soft knee on luminance, hue kept, in place on the graded images. Args: <knee> <slope> images..."""
import sys
import numpy as np
from PIL import Image
k, s = float(sys.argv[1]), float(sys.argv[2]); GREY = 0.3
W = np.array([0.2126, 0.7152, 0.0722], np.float32)
for f in sys.argv[3:]:
    a = np.asarray(Image.open(f).convert('RGB'), np.float32) / 255
    L = a @ W
    Ln = np.where(L > k, k + (1 - s) * 0.0 + (L - k) * s, L)
    sat = a.max(2) - a.min(2)
    grey = np.clip((0.14 - sat) / 0.09, 0, 1) * np.clip((L - 0.2) / 0.2, 0, 1)
    Ln = Ln * (1 - GREY * grey)                                  # mail rings and pale scales: the white rings read as dots
    a = a * (Ln / np.maximum(L, 1e-3))[..., None]
    Image.fromarray((np.clip(a, 0, 1) * 255 + .5).astype('u1')).save(f)
    print('TONE', f, round(float(L.mean()), 3), round(float(Ln.mean()), 3))
