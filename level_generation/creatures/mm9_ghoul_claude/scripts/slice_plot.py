"""Cross-section plot of the Meshy npz at z levels. Args: npz out z1 z2 ... """
import sys
import numpy as np
from PIL import Image, ImageDraw
d = np.load(sys.argv[1]); V, F = d['V'], d['F']
zs = [float(x) for x in sys.argv[3:]]
S = 1400; W = 500
im = Image.new('RGB', (W * len(zs), W), (20, 20, 20)); dr = ImageDraw.Draw(im)
for k, z in enumerate(zs):
    a = V[F]; s = a[..., 2] - z
    m = (s.min(1) < 0) & (s.max(1) > 0)
    for t in a[m]:
        pts = []
        for i in range(3):
            p, q = t[i], t[(i + 1) % 3]
            if (p[2] - z) * (q[2] - z) < 0:
                f = (z - p[2]) / (q[2] - p[2]); r = p + f * (q - p); pts.append(r)
        if len(pts) == 2:
            xy = [(W * k + W / 2 + p[0] * S, W / 2 - (p[1]) * S) for p in pts]
            dr.line(xy, fill=(255, 220, 120), width=1)
    dr.text((W * k + 5, 5), f'z={z}', fill=(255, 255, 255))
    dr.line([(W * k, 0), (W * k, W)], fill=(80, 80, 80))
im.save(sys.argv[2])
