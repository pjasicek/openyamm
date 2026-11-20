import sys, numpy as np
from PIL import Image
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from headpos import texel_positions
N = 2048
pos, cov = texel_positions(sys.argv[1], 'PeasantDM2Head', N)
img = np.asarray(Image.open('textures/pdm2_tp_head_basecolor_preneck.png').convert('RGB'), float)
P = np.nan_to_num(pos); y, x, z = P[..., 1], P[..., 0], P[..., 2]
lum = img @ [0.299, 0.587, 0.114]; mx, mn = img.max(-1), img.min(-1); sat = (mx - mn) / np.maximum(mx, 1)
zone = cov & (np.abs(x) < 0.16) & (y < 0.955)
for name, m in (('dark', zone & (lum < 85)), ('light', zone & (lum >= 140)), ('mid', zone & (lum >= 85) & (lum < 140))):
    print(name, m.sum(), 'sat pct', np.percentile(sat[m], [10, 50, 90]).round(2), 'z pct', np.percentile(z[m], [10, 50, 90]).round(3))
