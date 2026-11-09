#!/usr/bin/env python3
"""Tier base colours of the installed GLB for mpqem.py's texture guard: work/tex_<prim material>_<tier>.png with tiers
A = wy_young (Morgan), B = wy_mature (Verdandi). Body (Wyrde_YOUNG / Wyrde_MATURE): the shared tone image with each tier's region
ramps applied by the engine rule (claude_shared/tier_textures.apply, ramps and mask read from the GLB itself); the region mask is
written as a third "tier" M (R mantle, G gown, B damask) and a fourth N (A, Verdandi's cord, as grey), so a collapse that moves a
region border is refused as well. Head: each tier's own colour image (M, N = the default material's image)."""
import io
import sys
from pathlib import Path
import numpy as np
from PIL import Image
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts')); sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import bglbio as gb  # noqa: E402
import tier_textures as TT  # noqa: E402
doc, b = gb.read(HERE / 'before' / 'mm9_wyrde.glb')


def image(i):
    im = doc['images'][i]; v = doc['bufferViews'][im['bufferView']]; o = v.get('byteOffset', 0)
    return Image.open(io.BytesIO(b[o:o + v['byteLength']]))


def tex_of(m):
    return doc['textures'][m['pbrMetallicRoughness']['baseColorTexture']['index']]['source']


M = {m['name']: m for m in doc['materials']}
print({k: tex_of(v) for k, v in M.items()})
tone = np.asarray(image(tex_of(M['Wyrde_YOUNG'])).convert('RGB'), np.float64) / 255
mimg = image(M['Wyrde_YOUNG']['extras']['openyamm_region_mask']['index']).convert('RGBA')
size = (tone.shape[1], tone.shape[0])
mask = np.stack([np.asarray(ch.resize(size, Image.BILINEAR), np.float64) / 255 for ch in mimg.split()], -1)
for tier, mat in (('A', 'Wyrde_YOUNG'), ('B', 'Wyrde_MATURE')):
    out = TT.apply(tone, mask, M[mat]['extras']['openyamm_region_ramps'])
    Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)).save(HERE / 'work' / f'tex_Wyrde_YOUNG_{tier}.png')
    print('TEX body', tier, mat)
Image.fromarray((mask[..., :3] * 255 + 0.5).astype(np.uint8)).save(HERE / 'work' / 'tex_Wyrde_YOUNG_M.png')
Image.fromarray((np.repeat(mask[..., 3:4], 3, -1) * 255 + 0.5).astype(np.uint8)).save(HERE / 'work' / 'tex_Wyrde_YOUNG_N.png')
for tier, mat in (('A', 'WyrdeHead_wy_young'), ('B', 'WyrdeHead_wy_mature'), ('M', 'WyrdeHead'), ('N', 'WyrdeHead')):
    image(tex_of(M[mat])).convert('RGB').save(HERE / 'work' / f'tex_WyrdeHead_{tier}.png'); print('TEX head', tier, mat)
