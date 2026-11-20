import sys, numpy as np
from PIL import Image
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from headpos import texel_positions
N = 2048
pos, cov = texel_positions(sys.argv[1], 'PeasantDM2Head', N)
img = np.asarray(Image.open('textures/pdm2_tp_head_basecolor.png').convert('RGB'), float)
P = np.nan_to_num(pos); y, x, z = P[..., 1], P[..., 0], P[..., 2]
zone = cov & (np.abs(x) < 0.16) & (y < 0.955) & (z < 0.115)
out = img.copy(); out[zone] = out[zone] * 0.5 + np.array([255, 0, 255]) * 0.5
Image.fromarray(np.uint8(out)).save('work/head_zone_overlay.png')
