#!/usr/bin/env python3
"""Tier base colours of the installed GLB for mpqem.py's texture guard: work/tex_<prim material>_<tier>.png.
PeasantM1d: both primitives (PM1d_C body, PM1dHead_C head + hands) share one tone image per set across the tiers and recolour it
with each tier's region ramps (claude_shared/tier_textures.apply, ramps and mask read from the GLB): A = pm1d_c (PM1d_C /
PM1dHead_C), B = pm1d_d (PM1d_D / PM1dHead_D); M = the region mask (a collapse moving a region border is refused as well)."""
import io
import sys
from pathlib import Path
import numpy as np
from PIL import Image
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts')); sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import bglbio as gb  # noqa: E402
import tier_textures as TT  # noqa: E402
doc, b = gb.read(HERE / 'before' / 'mm9_pm1d.glb')


def image(i):
    im = doc['images'][i]; v = doc['bufferViews'][im['bufferView']]; o = v.get('byteOffset', 0)
    return Image.open(io.BytesIO(b[o:o + v['byteLength']]))


def tex_of(m):
    return doc['textures'][m['pbrMetallicRoughness']['baseColorTexture']['index']]['source']


M = {m['name']: m for m in doc['materials']}
for prim, (ma, mb) in (('PM1d_C', ('PM1d_C', 'PM1d_D')), ('PM1dHead_C', ('PM1dHead_C', 'PM1dHead_D'))):
    tone = np.asarray(image(tex_of(M[ma])).convert('RGB'), np.float64) / 255
    mimg = image(doc['textures'][M[ma]['extras']['openyamm_region_mask']['index']]['source']).convert('RGBA')
    size = (tone.shape[1], tone.shape[0])
    mask = np.stack([np.asarray(ch.resize(size, Image.BILINEAR), np.float64) / 255 for ch in mimg.split()], -1)
    for tier, mat in (('A', ma), ('B', mb)):
        out = TT.apply(tone, mask, M[mat]['extras']['openyamm_region_ramps'])
        Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)).save(HERE / 'work' / f'tex_{prim}_{tier}.png')
        print('TEX', prim, tier, mat, size)
    Image.fromarray((mask[..., :3] * 255 + 0.5).astype(np.uint8)).save(HERE / 'work' / f'tex_{prim}_M.png')
