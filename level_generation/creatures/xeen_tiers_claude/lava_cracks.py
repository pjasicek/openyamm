#!/usr/bin/env python3
"""Emission masks for the Lava Golem tier (D-10): the crevices of the body region glow. Per LOD atlas of a region-ramp
GLB: texels in the given mask channel whose luminance is below their local mean (Gaussian, radius R) by more than a
threshold, scaled to 0..1, written as a grey PNG for claude_shared/emission.py.

    lava_cracks.py <glb> <channel> <out_prefix> [--radius 6] [--lo 0.06] [--hi 0.25]
Writes <out_prefix>_tex<mask texture>.png for each (base, mask) pair, in material order (LOD0, LOD2, LOD3)."""
import argparse
import io
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from xeen_tiers import read  # noqa: E402
from add_region import image_bytes  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument('glb'); ap.add_argument('channel', type=int); ap.add_argument('prefix')
ap.add_argument('--radius', type=float, default=6); ap.add_argument('--lo', type=float, default=0.06)
ap.add_argument('--hi', type=float, default=0.25)
a = ap.parse_args()
doc, binary = read(a.glb)
done = set()
for mat in doc['materials']:
    ex = mat.get('extras', {})
    if 'openyamm_region_mask' not in ex:
        continue
    key = (mat['pbrMetallicRoughness']['baseColorTexture']['index'], ex['openyamm_region_mask']['index'])
    if key in done:
        continue
    done.add(key)
    base = Image.open(io.BytesIO(image_bytes(doc, binary, doc['textures'][key[0]]['source']))).convert('L')
    mask = Image.open(io.BytesIO(image_bytes(doc, binary, doc['textures'][key[1]]['source']))).convert('RGBA')
    mask = np.asarray(mask.resize(base.size, Image.BILINEAR), np.float64)[..., a.channel] / 255
    lum = np.asarray(base, np.float64) / 255
    local = np.asarray(base.filter(ImageFilter.GaussianBlur(a.radius)), np.float64) / 255
    crack = np.clip(((local - lum) / np.maximum(local, 0.05) - a.lo) / (a.hi - a.lo), 0, 1) * mask
    out = f'{a.prefix}_tex{key[1]}.png'
    Image.fromarray((crack * 255 + 0.5).astype(np.uint8), 'L').save(out)
    print('WROTE', out, f'{(crack > 0.5).mean() * 100:.1f} % glowing of the atlas', mat['name'])
