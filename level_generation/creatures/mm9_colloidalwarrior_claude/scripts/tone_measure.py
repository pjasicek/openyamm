#!/usr/bin/env python3
"""Mean HSV of the creature's pixels in viewer shots (background removed by its distance from the corner colour), MM9 vs ours.
Args: pairs mm9_shot:our_shot ..."""
import sys, colorsys
import numpy as np
from PIL import Image
def stats(p):
    a = np.asarray(Image.open(f'review/shots/{p}.png').convert('RGB'), np.float32) / 255
    h, w, _ = a.shape; a = a[: int(h * 0.88)]                  # drop the badge strip
    bg = np.median(np.concatenate([a[:20, :20].reshape(-1, 3), a[:20, -20:].reshape(-1, 3)]), 0)
    m = np.linalg.norm(a - bg, axis=2) > 0.12
    px = a[m]; mx = px.max(1); mn = px.min(1)
    v = mx; s = (mx - mn) / np.maximum(mx, 1e-4)
    rgb = px.mean(0)
    return dict(n=int(m.sum()), V=float(np.median(v)), S=float(np.median(s)), V25=float(np.percentile(v, 25)), V75=float(np.percentile(v, 75)), rgb=np.round(rgb * 255).astype(int).tolist())
for pair in sys.argv[1:]:
    a, b = pair.split(':'); A, Bs = stats(a), stats(b)
    print(f'{a:12s} V {A["V"]:.3f} ({A["V25"]:.2f}-{A["V75"]:.2f}) S {A["S"]:.3f} rgb {A["rgb"]} | {b:12s} V {Bs["V"]:.3f} ({Bs["V25"]:.2f}-{Bs["V75"]:.2f}) S {Bs["S"]:.3f} rgb {Bs["rgb"]} | value x{A["V"]/Bs["V"]:.2f} sat x{A["S"]/Bs["S"]:.2f}')
