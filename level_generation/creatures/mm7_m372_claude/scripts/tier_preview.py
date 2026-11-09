#!/usr/bin/env python3
"""Preview of the shader's region recolour (fs_model: t = clamp((lum - lo) / (hi - lo)), ramp at t x 15, mixed by the
mask) for every tier, on the body and head base colours. Writes work/tierprev_<variant>_{body,head}.png. Args: none"""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import region_variants as R
T = HERE / 'textures'
cfg = json.loads((T / 'm372_ramps.json').read_text())


def l2s(x):
    return np.where(x <= 0.0031308, x * 12.92, 1.055 * np.power(np.maximum(x, 0), 1 / 2.4) - 0.055)


for mat, tag, tex in ((cfg['materials'][0], 'body', 'm372_basecolor_1k.png'), (cfg['materials'][1], 'head', 'm372_head_basecolor_1k.png')):
    base = R.load_srgb(T / tex); M = np.asarray(Image.open(T / mat['mask']).convert('RGBA'), np.float64) / 255
    lum = R.luminance(base)
    for var in cfg['variants']:
        out = base.copy()
        for ch, rp in enumerate(mat['ramps'][var]):                        # m372: every region (R tunic, G hair, B beard)
            lo, hi = rp['range']; cols = np.array(rp['colors']); mask = M[..., ch]
            t = np.clip((lum - lo) / (hi - lo), 0, 1) * 15; i0 = np.floor(t).astype(int).clip(0, 14); f = (t - i0)[..., None]
            ramp = l2s(cols[i0] * (1 - f) + cols[i0 + 1] * f)
            out = out * (1 - mask[..., None]) + ramp * mask[..., None]
        Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)).save(HERE / 'work' / f'tierprev_{var}_{tag}.png')
print('TIERPREV done')
