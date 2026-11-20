#!/usr/bin/env python3
"""Tier base colours of the installed GLB for mpqem.py's texture guard: work/tex_<prim material>_<tier>.png with tiers
PeasantM7 (from PeasantM7d): A = pm7_a, B = pm7_b. Body (PeasantM7_A / PeasantM7_B): the shared tone image with each tier's region ramps applied by the
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
doc, b = gb.read(HERE / 'before' / 'mm9_peasantm7.glb')


def image(i):
    im = doc['images'][i]; v = doc['bufferViews'][im['bufferView']]; o = v.get('byteOffset', 0)
    return Image.open(io.BytesIO(b[o:o + v['byteLength']]))


def tex_of(m):
    return doc['textures'][m['pbrMetallicRoughness']['baseColorTexture']['index']]['source']


M = {m['name']: m for m in doc['materials']}
tone = np.asarray(image(tex_of(M['PeasantM7_A'])).convert('RGB'), np.float64) / 255
mimg = image(M['PeasantM7_A']['extras']['openyamm_region_mask']['index']).convert('RGBA')
size = (tone.shape[1], tone.shape[0])
mask = np.stack([np.asarray(ch.resize(size, Image.BILINEAR), np.float64) / 255 for ch in mimg.split()], -1)
for tier, mat in (('A', 'PeasantM7_A'), ('B', 'PeasantM7_B')):
    out = TT.apply(tone, mask, M[mat]['extras']['openyamm_region_ramps'])
    Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)).save(HERE / 'work' / f'tex_PeasantM7_A_{tier}.png')
    print('TEX body', tier, mat)
mrgb = mask[..., :3].copy(); mrgb[..., 2] = np.maximum(mrgb[..., 2], mask[..., 3])   # A is empty on PeasantM7 (kept from PeasantM7d)
Image.fromarray((mrgb * 255 + 0.5).astype(np.uint8)).save(HERE / 'work' / 'tex_PeasantM7_A_M.png')
# PeasantM7: the head set has ramps too (R = hair), one shared colour image; tiers by the same engine rule, mask as tier M
htone = np.asarray(image(tex_of(M['PeasantM7Head_A'])).convert('RGB'), np.float64) / 255
himg = image(M['PeasantM7Head_A']['extras']['openyamm_region_mask']['index']).convert('RGBA')
hsize = (htone.shape[1], htone.shape[0])
hmask = np.stack([np.asarray(ch.resize(hsize, Image.BILINEAR), np.float64) / 255 for ch in himg.split()], -1)
for tier, mat in (('A', 'PeasantM7Head_A'), ('B', 'PeasantM7Head_B')):
    out = TT.apply(htone, hmask, M[mat]['extras']['openyamm_region_ramps'])
    Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)).save(HERE / 'work' / f'tex_PeasantM7Head_A_{tier}.png')
    print('TEX head', tier, mat)
Image.fromarray((hmask[..., :3] * 255 + 0.5).astype(np.uint8)).save(HERE / 'work' / 'tex_PeasantM7Head_A_M.png')
