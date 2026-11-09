#!/usr/bin/env python3
"""Tier base colours of the installed GLB for mpqem.py's texture guard: work/tex_<prim material>_<tier>.png with tiers
PeasantDM1: A = pdm1_a, B = pdm1_b. Body ramped; head = each tier's own image (no mask) (DM3 copy: one image per primitive): the shared tone image with each tier's region ramps applied by the
engine rule (claude_shared/tier_textures.apply, ramps and mask read from the GLB itself); the region mask is written as a
third "tier" M (a collapse that moves a region border is refused as well). Head: each tier's own colour image."""
import io
import sys
from pathlib import Path
import numpy as np
from PIL import Image
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts')); sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import bglbio as gb  # noqa: E402
import tier_textures as TT  # noqa: E402
doc, b = gb.read(HERE / 'before' / 'mm9_peasantdm1.glb')


def image(i):
    im = doc['images'][i]; v = doc['bufferViews'][im['bufferView']]; o = v.get('byteOffset', 0)
    return Image.open(io.BytesIO(b[o:o + v['byteLength']]))


def tex_of(m):
    return doc['textures'][m['pbrMetallicRoughness']['baseColorTexture']['index']]['source']


M = {m['name']: m for m in doc['materials']}
for prim, mats in (('PeasantDM1_A', ('PeasantDM1_A', 'PeasantDM1_B')), ('PeasantDM1Head', ('PeasantDM1Head', 'PeasantDM1Head_pdm1_b'))):
    tone = np.asarray(image(tex_of(M[mats[0]])).convert('RGB'), np.float64) / 255
    if 'openyamm_region_mask' not in M[mats[0]].get('extras', {}):
        # PeasantDM1: the head has no region mask; each tier is its own head colour image (tier B: another man), M = black
        for tier, mat in zip('AB', mats):
            image(tex_of(M[mat])).convert('RGB').save(HERE / 'work' / f'tex_{prim}_{tier}.png'); print('TEX', prim, tier, mat)
        Image.fromarray(np.zeros_like((tone * 255).astype(np.uint8))).save(HERE / 'work' / f'tex_{prim}_M.png')
        continue
    mimg = image(M[mats[0]]['extras']['openyamm_region_mask']['index']).convert('RGBA')
    size = (tone.shape[1], tone.shape[0])
    mask = np.stack([np.asarray(ch.resize(size, Image.BILINEAR), np.float64) / 255 for ch in mimg.split()], -1)
    for tier, mat in zip('AB', mats):
        out = TT.apply(tone, mask, M[mat]['extras']['openyamm_region_ramps'])
        Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)).save(HERE / 'work' / f'tex_{prim}_{tier}.png')
        print('TEX', prim, tier, mat)
    Image.fromarray((mask[..., :3] * 255 + 0.5).astype(np.uint8)).save(HERE / 'work' / f'tex_{prim}_M.png')
