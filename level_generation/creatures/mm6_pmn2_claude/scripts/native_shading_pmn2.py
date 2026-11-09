#!/usr/bin/env python3
"""Native shading transfer on the mage's recoloured cloth (claude_shared/native_shading.py,
../NATIVE_SHADING_TRANSFER.md; user request 2026-10-08). Runs after prepare_textures.py, edits
textures/pmn2_a_basecolor.png in place (prepare_textures.py rewrites it on every build).

Only the cloth that the native palettes 801/802/803 recolour (mantle, trousers, pouches: the robe mask) is shaded:
skin, leather and boots share heights with each other, so one height profile cannot tell them apart, and the head has
its own texture set. The native cloth brightness by height (config native_shading.json, reference palette 801) is
blended 65 % into Meshy's cloth, keeping its folds as detail; tier_ramps.py then colours the cloth from the same
native pixels in each palette. Pre-transfer textures and scripts: textures_pre_native/."""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / 'mm6_gob_claude' / 'scripts'))
sys.path.insert(0, str(ROOT.parent / 'claude_shared'))
import compose_textures_v2 as C
import native_shading as NS

AMOUNT = 0.65
T = ROOT / 'textures'
base = np.asarray(Image.open(T / 'pmn2_a_basecolor.png').convert('RGB'), np.float64) / 255
data = np.load(ROOT / 'work' / 'uv3d_body.npz')
part_map, xyz = C.rasterise(data)
if part_map.shape != base.shape[:2]:
    raise SystemExit(f'atlas {base.shape[:2]} != raster {part_map.shape}')
mask = Image.open(T / 'pmn2_metal_rough_1k.png').convert('RGB').getchannel('R').resize(base.shape[1::-1], Image.BILINEAR)
robe = (np.asarray(mask, np.float64) / 255 > 0.5) & (part_map == 0)
z = xyz[..., 2][part_map == 0]
height = NS.texel_coordinate(xyz, 'height', z_range=(float(z.min()), float(z.max())))
profile = json.loads((ROOT / 'work' / 'native_shading' / 'profile.json').read_text())
NS.shade(base, height, robe, profile, luminance=profile['regions']['robe']['luminance'], amount=AMOUNT)
Image.fromarray((np.clip(base, 0, 1) * 255 + 0.5).astype(np.uint8)).save(T / 'pmn2_a_basecolor.png', optimize=True)
print('SHADED robe texels', int(robe.sum()))
