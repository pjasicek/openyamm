#!/usr/bin/env python3
"""Grey smudge in the moustache (mm9_bjarni, 2026-11-02): Meshy's 4K head paint left a flat grey blob in the beard chart under
the left nostril (texels about x 1358-1388, y 1884-1926 of the 2K head set), and the three hole-fill triangles there sample it,
so a dark-grey patch showed on the moustache in close-ups. The blob takes the beard strands 38 texels below it in the same chart
(soft elliptical mask, feathered). Runs on textures/mk_tp_head_basecolor.png in place, after hand_clean.py and
head_patch_fix.py. Usage (project folder): moustache_fix.py"""
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

T = Path('textures/mk_tp_head_basecolor.png')
img = np.asarray(Image.open(T).convert('RGB')).astype(np.float64)
CX, CY, RX, RY, DY = 1373, 1905, 17, 25, 38
yy, xx = np.mgrid[0:img.shape[0], 0:img.shape[1]]
d = ((xx - CX) / RX) ** 2 + ((yy - CY) / RY) ** 2
w = np.clip((1.3 - d) / 0.5, 0, 1)
w = ndi.gaussian_filter(w, 1.5)
src = np.roll(img, -DY, axis=0)
out = img * (1 - w[..., None]) + src * w[..., None]
Image.fromarray(np.uint8(np.clip(np.round(out), 0, 255))).save(T)
print('MOUSTACHE_FIX texels', int((w > 0.01).sum()), 'centre', img[CY, CX].round(0).tolist(), '->', out[CY, CX].round(0).tolist())
