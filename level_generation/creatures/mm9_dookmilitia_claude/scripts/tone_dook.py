#!/usr/bin/env python3
"""MM9's mail and studs are dark: the Codex/Meshy paints have the right means (tunic 37-64 against MM9's 39-52) but white ring and stud highlights (p95 220-250, MM9 about 90). A soft knee on luminance per tier, hue kept; gold and bronze (saturated) keep more of their light. Overwrites *_raw_graded.png. Project folder."""
import numpy as np
from PIL import Image
W = np.array([.2126, .7152, .0722], np.float32)
def knee(p, k, s, sat_keep=0.6):
    a = np.asarray(Image.open(p).convert('RGB'), np.float32); L = a @ W
    mx, mn = a.max(2), a.min(2); sat = (mx - mn) / np.maximum(mx, 1)
    s2 = s + (1 - s) * sat_keep * np.clip((sat - 0.25) / 0.25, 0, 1)
    L2 = np.where(L > k, k + (L - k) * s2, L)
    b = a * (L2 / np.maximum(L, 1))[..., None]
    Image.fromarray(np.clip(b + .5, 0, 255).astype('u1')).save(p)
    print('TONE', p, 'p95', int(np.percentile(L, 95)), '->', int(np.percentile(L2, 95)))
for t in 'abc': knee(f'textures/dook_torso_{t}_raw_graded.png', 78, 0.32)
for t in 'ac': knee(f'textures/dook_limbs_{t}_raw_graded.png', 90, 0.45)
