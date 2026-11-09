"""Tier base colours with the engine region rule baked in (system Python; for Blender previews and review only):
t = (linear luminance - lo) / (hi - lo), colour = mix(base, ramp(t), mask channel), per set and tier.
Usage: tier_bake.py [prefix=textures/v3/m182v3] -> work/v3/tiers/{set}_{a,b,c}.png"""
import json, sys
import numpy as np
from pathlib import Path
from PIL import Image
P = Path(__file__).resolve().parents[2]; pre = Path(sys.argv[1]) if len(sys.argv) > 1 else P / 'textures/v3/m182v3'
O = P / 'work/v3/tiers'; O.mkdir(parents=True, exist_ok=True)
lin = lambda c: np.where(c <= .04045, c / 12.92, ((c + .055) / 1.055) ** 2.4)
srgb = lambda c: np.where(c <= .0031308, c * 12.92, 1.055 * np.clip(c, 0, None) ** (1 / 2.4) - .055)
W = np.array([.2126, .7152, .0722])
ramps = json.loads(Path(str(pre) + '_ramps.json').read_text())
def ramp(colors, t):
    c = np.array(colors); x = np.clip(t, 0, 1) * (len(c) - 1); i = np.minimum(x.astype(int), len(c) - 2); f = (x - i)[..., None]
    return c[i] * (1 - f) + c[i + 1] * f
for label, mat in [('body', 'DragonBody'), ('head', 'DragonHead'), ('wings', 'DragonWings')]:
    base = lin(np.asarray(Image.open(f'{pre}_{label}_basecolor_2k.png').convert('RGB'), float) / 255)
    mask = np.asarray(Image.open(f'{pre}_{label}_region_mask.png').convert('RGBA'), float) / 255
    lum = base @ W
    for tier in 'abc':
        out = base.copy()
        for c, reg in enumerate(ramps[f'{mat}_{tier.upper()}']):
            lo, hi = reg['range']; out = out * (1 - mask[..., c:c + 1]) + ramp(reg['colors'], (lum - lo) / (hi - lo)) * mask[..., c:c + 1]
        Image.fromarray(np.uint8(np.clip(srgb(out), 0, 1) * 255 + .5)).save(O / f'{label}_{tier}.png')
print('TIERS baked')
