#!/usr/bin/env python3
"""Tier base colours of the installed GLB for mpqem.py's texture guard: work/tex_<prim material>_<tier>.png with tiers
Body (PeasantBoy_A / PeasantBoy_B): the shared tone image with each tier's region ramps applied by the
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
doc, b = gb.read(HERE / 'before' / 'mm9_peasantboy.glb')


def image(i):
    im = doc['images'][i]; v = doc['bufferViews'][im['bufferView']]; o = v.get('byteOffset', 0)
    return Image.open(io.BytesIO(b[o:o + v['byteLength']]))


def tex_of(m):
    return doc['textures'][m['pbrMetallicRoughness']['baseColorTexture']['index']]['source']


M = {m['name']: m for m in doc['materials']}
# Peasant boy (2026-11-05): tiers A = pboy_a, B = pboy_b (its own region mask pboy_region_mask_b: the open-vest panel), E = pboy_e;
# masks M (shared) and N (boy b's) as extra "tiers"; head: a, b, e head images
tone = np.asarray(image(tex_of(M['PeasantBoy_A'])).convert('RGB'), np.float64) / 255
size = (tone.shape[1], tone.shape[0])


def mask_of(mat):
    mimg = image(M[mat]['extras']['openyamm_region_mask']['index']).convert('RGBA')
    return np.stack([np.asarray(ch.resize(size, Image.BILINEAR), np.float64) / 255 for ch in mimg.split()], -1)


for tier, mat in (('A', 'PeasantBoy_A'), ('B', 'PeasantBoy_B'), ('E', 'PeasantBoy_E')):
    out = TT.apply(tone, mask_of(mat), M[mat]['extras']['openyamm_region_ramps'])
    Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)).save(HERE / 'work' / f'tex_PeasantBoy_A_{tier}.png')
    print('TEX body', tier, mat)
for t, mat in (('M', 'PeasantBoy_A'), ('N', 'PeasantBoy_B')):
    Image.fromarray((mask_of(mat)[..., :3] * 255 + 0.5).astype(np.uint8)).save(HERE / 'work' / f'tex_PeasantBoy_A_{t}.png')
for tier, mat in (('A', 'PeasantBoyHead'), ('B', 'PeasantBoyHead_pboy_b'), ('E', 'PeasantBoyHead_pboy_e')):
    image(tex_of(M[mat])).convert('RGB').save(HERE / 'work' / f'tex_PeasantBoyHead_{tier}.png'); print('TEX head', tier, mat)
