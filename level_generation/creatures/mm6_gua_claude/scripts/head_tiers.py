#!/usr/bin/env python3
"""Head material tiers: the coif is mail and recolours with the shirt. Rasterizes the coif faces of the head UV
layout (work/head_uv_layout.json from dump_head_uv.py) into the mail channel (B) of textures/gua_head_region_mask.png
and appends a 'GuardHead' material to textures/gua_ramps.json that reuses the body's three ramps per tier (R and G
are empty on the head)."""
import json
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import region_variants as R
T = HERE / 'textures'
N = 1024
layout = json.loads((HERE / 'work' / 'head_uv_layout.json').read_text())
img = Image.new('L', (N, N), 0)
d = ImageDraw.Draw(img)
for part, pts in layout['faces']:
    if part == 'Coif':
        d.polygon([(u * N, (1 - v) * N) for u, v in pts], fill=255, outline=255)
coif = ndimage.binary_dilation(np.asarray(img) > 0, iterations=2)
head = R.load_srgb(T / 'gua_head_basecolor_graded.png', N)
hsv = np.asarray(Image.fromarray((head * 255).astype(np.uint8)).convert('HSV'), np.float64) / 255
skin_eyes = (hsv[..., 0] * 360 > 5) & (hsv[..., 0] * 360 < 30) & (hsv[..., 1] < 0.45) & (hsv[..., 2] > 0.55)
w = ndimage.gaussian_filter((coif & ~skin_eyes).astype(np.float64), 1.0)
# the coif is mail: match its luminance distribution to the profile-shaded shirt mail (prepare_textures.py), so the
# head's mail is as dark as the body's (user review 2159), keeping the coif's own ring detail
body = R.load_srgb(T / 'gua_a_basecolor.png', 2048)
bmask = np.asarray(Image.open(T / 'gua_region_mask.png').getchannel('B').resize((2048, 2048), Image.BILINEAR)) > 230
lin = R.srgb_to_linear(head)
hl = lin @ R.LUMA
core = w > 0.9
gain = np.median(R.srgb_to_linear(body[bmask]) @ R.LUMA) / max(np.median(hl[core]), 1e-4)
lin = lin * (1 + (gain - 1) * w[..., None])
head = np.where(lin <= 0.0031308, lin * 12.92, 1.055 * np.clip(lin, 0, 1) ** (1 / 2.4) - 0.055)
Image.fromarray((np.clip(head, 0, 1) * 255 + 0.5).astype(np.uint8)).save(T / 'gua_head_basecolor_graded.png')
print('HEAD coif luminance gain', round(float(gain), 3))
zero = np.zeros_like(w)
R.write_mask([zero, zero, w], T / 'gua_head_region_mask.png', size=N)
cfg = json.loads((T / 'gua_ramps.json').read_text())
body = cfg['materials'][0]
cfg['materials'] = [body, {'base': 'GuardHead_A', 'prefix': 'GuardHead', 'mask': 'gua_head_region_mask.png',
                           'regions': body['regions'], 'palettes': body['palettes'], 'ramps': body['ramps']}]
(T / 'gua_ramps.json').write_text(json.dumps(cfg, indent=1) + '\n')
print('HEAD mask coif texels', int((w > 0.5).sum()))
