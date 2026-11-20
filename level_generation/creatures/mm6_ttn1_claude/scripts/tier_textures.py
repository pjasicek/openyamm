#!/usr/bin/env python3
"""Preview textures: each tier's ramps applied to a base colour with the shader's formula (fs_model.sc), written to
work/tier_<variant>_<name>.png. Args: ramps material index, base colour png, mask png, name."""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image
HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import region_variants as R
mi, base_p, mask_p, name = int(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4]
cfg = json.loads((HERE / 'textures' / 'ttn_ramps.json').read_text())['materials'][mi]
base = R.load_srgb(base_p); lin = R.srgb_to_linear(base); lum = lin @ R.LUMA
# per channel: PIL premultiplies RGBA by alpha when resizing, and the mask's alpha (region 4) is empty
mask = np.stack([np.asarray(c.resize(base.shape[1::-1], Image.BILINEAR), np.float64)
                 for c in Image.open(mask_p).convert('RGBA').split()], -1) / 255
for t in cfg['palettes']:
    out = lin.copy()
    for ch, r in enumerate(cfg['ramps'][t]):
        lo, hi = r['range']; c = np.array(r['colors'])
        x = np.clip((lum - lo) / (hi - lo), 0, 1) * 15; i = np.floor(x).astype(int).clip(0, 14); f = x - i
        col = c[i] * (1 - f[..., None]) + c[i + 1] * f[..., None]; w = mask[..., ch:ch + 1]
        out = out * (1 - w) + col * w
    s = np.where(out <= 0.0031308, out * 12.92, 1.055 * np.clip(out, 0, 1) ** (1 / 2.4) - 0.055)
    Image.fromarray((np.clip(s, 0, 1) * 255).astype(np.uint8)).save(HERE / 'work' / f'tier_{t}_{name}.png')
print('TIERS', list(cfg['palettes']))
