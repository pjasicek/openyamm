#!/usr/bin/env python3
"""The back of the head read as a smooth pale column from a distance (the coordinator, r4): MM9's hair block is mid blue with strong dark
streaks. The head set's own paint (one source) behind the ears gets more contrast round a lower mid tone and a little more blue:
c' = m + (c - m) * K about m = 0.52, then times 0.94; blended in by y 0.00 -> 0.05 (the face and ears stay). In place on
textures/yan_head_final.png (the input kept as textures/yan_head_final_prehair.png)."""
import shutil
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
K = 1.35
src = Path('textures/yan_head_final_prehair.png')
if not src.exists(): shutil.copyfile('textures/yan_head_final.png', src)
H = np.asarray(Image.open(src).convert('RGB'), np.float32) / 255
Z = np.load('work/head_pos.npz'); pos, cov, prt = Z['pos'], Z['cov'], Z['prt']
y = pos[..., 1]
w = np.clip(y / 0.05, 0, 1) * cov * (prt < 13)
w = ndimage.gaussian_filter(w.astype(np.float32), 2)[..., None]
m = 0.52
out = (m + (H - m) * K) * 0.94
grey = out.mean(2, keepdims=True); out = grey + (out - grey) * 1.12
res = H * (1 - w) + np.clip(out, 0, 1) * w
Image.fromarray((np.clip(res, 0, 1) * 255 + .5).astype('u1')).save('textures/yan_head_final.png')
print('HAIRPAINT texels', int((w[..., 0] > 0.5).sum()))
