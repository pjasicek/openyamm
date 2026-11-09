#!/usr/bin/env python3
"""Head material tiers: the hood (cloak faces of the head set) is cloth like the body cloak; the face, hair and neck
keep their colour; the hood alone takes the neck-seam gain (argument, default 0.687). Rasterizes the head UV layout (work/head_uv_layout.json from dump_head_uv.py) and uses the body's
cloth ramps (merge_head_material.py merges the head into the body material and requires the same ramps). Writes
textures/thf_head_region_mask.png and appends a 'ThiefHead' material to textures/thf_ramps.json."""
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
    if part == 'Cloak':
        d.polygon([(u * N, (1 - v) * N) for u, v in pts], fill=255, outline=255)
hood = ndimage.binary_dilation(np.asarray(img) > 0, iterations=2)
w = np.clip(ndimage.gaussian_filter(hood.astype(np.float64), 1.0), 0, 1)
# the seam to the body runs through the hood (head_seam_gain measured 0.687 there): the gain darkens the hood only,
# so its cloth luminance meets the body cloak's (the cloth ramp maps luminance to colour); the face keeps gain 1
# (compose_head_set.py runs with --seam-gain 1.0)
seam = json.loads((T / 'thf_head_seam.json').read_text()) if (T / 'thf_head_seam.json').exists() else {}
HOOD_GAIN = float(sys.argv[1]) if len(sys.argv) > 1 else 0.687
img = np.asarray(Image.open(T / 'thf_head_basecolor_graded.png').convert('RGB'), np.float64) / 255
lin = R.srgb_to_linear(img) * (1 - w[..., None] * (1 - HOOD_GAIN))
enc = np.where(lin <= 0.0031308, lin * 12.92, 1.055 * np.maximum(lin, 0) ** (1 / 2.4) - 0.055)
Image.fromarray((np.clip(enc, 0, 1) * 255 + 0.5).astype(np.uint8)).save(T / 'thf_head_basecolor_graded.png', optimize=True)
R.write_mask([w], T / 'thf_head_region_mask.png', size=N)
cfg = json.loads((T / 'thf_ramps.json').read_text())
body = cfg['materials'][0]
cfg['materials'] = [body, {'base': 'ThiefHead_A', 'prefix': 'ThiefHead', 'mask': 'thf_head_region_mask.png',
                           'regions': body['regions'], 'palettes': body['palettes'], 'ramps': body['ramps']}]
(T / 'thf_ramps.json').write_text(json.dumps(cfg, indent=1) + '\n')
print('HEAD hood texels', int((w > 0.5).sum()))
