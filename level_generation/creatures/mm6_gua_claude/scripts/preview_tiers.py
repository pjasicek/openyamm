#!/usr/bin/env python3
"""CPU preview of the shader's region ramps (fs_model.sc math) on the 1K body base colour for every tier:
review/tier_preview.png (A | B | C atlases side by side) plus per-region luminance histograms in the console."""
import json
import sys
from pathlib import Path
import numpy as np
from PIL import Image
HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import region_variants as R
T = HERE / 'textures'
prefix = sys.argv[1] if len(sys.argv) > 1 else 'gua'
cfg = json.loads((T / f'{prefix}_ramps.json').read_text())['materials'][0]
base = R.load_srgb(T / f'{prefix}_a_basecolor_1k.png')
mask = np.asarray(Image.open(T / cfg['mask']).convert('RGBA'), np.float64) / 255
lin = R.srgb_to_linear(base)
lum = lin @ R.LUMA
enc = lambda v: np.where(v <= 0.0031308, v * 12.92, 1.055 * np.maximum(v, 0) ** (1 / 2.4) - 0.055)
outs = []
for variant in cfg['ramps']:
    col = lin.copy()
    for ch, ramp in enumerate(cfg['ramps'][variant]):
        lo, hi = ramp['range']
        t = np.clip((lum - lo) / (hi - lo), 0, 1) * 15
        i0 = np.minimum(np.floor(t).astype(int), 14)
        f = (t - i0)[..., None]
        stops = np.asarray(ramp['colors'])
        rc = stops[i0] * (1 - f) + stops[i0 + 1] * f
        col = col * (1 - mask[..., ch:ch + 1]) + rc * mask[..., ch:ch + 1]
    outs.append((np.clip(enc(col), 0, 1) * 255).astype(np.uint8))
Image.fromarray(np.concatenate(outs, 1)).resize((1536, 512), Image.LANCZOS).save(HERE / 'review' / 'tier_preview.png')
for ch, name in enumerate(cfg['regions']):
    m = mask[..., ch] > 0.9
    print(name, 'lum pcts 2/25/50/75/98', np.round(np.percentile(lum[m], [2, 25, 50, 75, 98]), 4))
