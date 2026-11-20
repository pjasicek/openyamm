#!/usr/bin/env python3
"""The clay's mirror seam came through as a dark line down the back view's shell: a feathered strip of shell from 80 px beside it replaces the centre. Project folder."""
import numpy as np
from PIL import Image
p = 'references_head/a_02_back_clean.png'
a = np.array(Image.open(p).convert('RGBA'), np.float32); H, W = a.shape[:2]
y0, y1 = int(H * 0.22), int(H * 0.70)
xx = np.arange(W); m = np.clip((26 - np.abs(xx - W / 2)) / 10, 0, 1)
ey = np.clip((np.arange(H) - y0) / 20, 0, 1) * np.clip((y1 - np.arange(H)) / 20, 0, 1)
M = (m[None] * ey[:, None])[..., None]
src = np.roll(a[..., :3], 84, axis=1)
a[..., :3] = a[..., :3] * (1 - M) + src * M
Image.fromarray(a.astype('u1')).save(p)
