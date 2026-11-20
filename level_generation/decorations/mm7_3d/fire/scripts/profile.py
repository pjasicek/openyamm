"""Print a sprite's silhouette per row (x2 restored frame): z in world units above the frame bottom, left/right
edges relative to the frame centre and the mean sRGB colour. Usage: profile.py <texture> <world units per x2 px>
[step rows]"""
import sys
import numpy as np
from PIL import Image
from pathlib import Path

X2 = Path(__file__).resolve().parents[5] / 'assets_legacy/decorations_x2_20261016'
tex, upp = sys.argv[1], float(sys.argv[2])
step = int(sys.argv[3]) if len(sys.argv) > 3 else 4
im = np.asarray(Image.open(next(X2.glob(f'{tex}_p*.png'))).convert('RGBA')).astype(float)
h, w = im.shape[:2]
a = im[..., 3] > 128
cx = w / 2
for y in range(0, h, step):
    xs = np.nonzero(a[y])[0]
    if len(xs) == 0:
        continue
    c = im[y, xs, :3].mean(0)
    print(f'z {((h - y) * upp):6.1f}  x {((xs[0] - cx) * upp):6.1f} .. {((xs[-1] + 1 - cx) * upp):6.1f}  '
          f'w {((xs[-1] + 1 - xs[0]) * upp):6.1f}  rgb {c.astype(int)}')
