#!/usr/bin/env python3
"""Tier base colours of the installed mm9_phom1.glb for mpqem.py's texture guard: work/tex_<prim material>_<tier>.png.
Tiers: A = phom1_a (PHOM1_A / PHOM1Head_A: shared paint + region ramps), B = phom1_b (PHOM1_B / PHOM1Head_B: same paint, other
ramps), C = phom2_a (PHOM1_PHOM2_A / PHOM1Head_PHOM2_A: own colour images, no ramps). Ramps applied by the engine rule
(claude_shared/tier_textures.apply, ramps and mask read from the GLB). M = the region mask as RGB (R, G, B channels plus the
alpha region at half weight in all three, so every region border, the alpha one included, changes the colour)."""
import io
import sys
from pathlib import Path
import numpy as np
from PIL import Image
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts')); sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import bglbio as gb  # noqa: E402
import tier_textures as TT  # noqa: E402
doc, b = gb.read(HERE / 'before' / 'mm9_phom1.glb')


def image(i):
    im = doc['images'][i]; v = doc['bufferViews'][im['bufferView']]; o = v.get('byteOffset', 0)
    return Image.open(io.BytesIO(b[o:o + v['byteLength']]))


def tex_of(m):
    return doc['textures'][m['pbrMetallicRoughness']['baseColorTexture']['index']]['source']


M = {m['name']: m for m in doc['materials']}
for prim, tiers in (('PHOM1_A', ('PHOM1_A', 'PHOM1_B', 'PHOM1_PHOM2_A')),
                    ('PHOM1Head_A', ('PHOM1Head_A', 'PHOM1Head_B', 'PHOM1Head_PHOM2_A'))):
    tone_img = image(tex_of(M[prim])).convert('RGB'); size = tone_img.size
    tone = np.asarray(tone_img, np.float64) / 255
    mimg = image(M[prim]['extras']['openyamm_region_mask']['index']).convert('RGBA')
    mask = np.stack([np.asarray(ch.resize(size, Image.BILINEAR), np.float64) / 255 for ch in mimg.split()], -1)
    for tier, mat in zip('ABC', tiers):
        if 'openyamm_region_ramps' in M[mat].get('extras', {}):
            assert tex_of(M[mat]) == tex_of(M[prim])
            out = TT.apply(tone, mask, M[mat]['extras']['openyamm_region_ramps'])
            im = Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8))
        else:
            im = image(tex_of(M[mat])).convert('RGB')
            if im.size != size:
                im = im.resize(size, Image.LANCZOS)
        im.save(HERE / 'work' / f'tex_{prim}_{tier}.png'); print('TEX', prim, tier, mat, im.size)
    mrgb = np.clip(mask[..., :3] + 0.5 * mask[..., 3:4], 0, 1)
    Image.fromarray((mrgb * 255 + 0.5).astype(np.uint8)).save(HERE / 'work' / f'tex_{prim}_M.png'); print('TEX', prim, 'M')
