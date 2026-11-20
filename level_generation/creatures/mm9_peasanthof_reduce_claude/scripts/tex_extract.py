#!/usr/bin/env python3
"""Tier base colours of the installed GLB (M=1|2) for mpqem.py's texture guard: work/hof$M/tex_<prim material>_<A|B|M>.png.
HOF1: body PeasantHOF_A = the shared tone image with tier A's / tier B's region ramps applied by the engine rule
(claude_shared/tier_textures.apply, ramps and mask read from the GLB), M = the region mask (a collapse that moves a region border
is refused as well); head PeasantHOFHead A = tier A head image, B = tier B's (PeasantHOFHead_phof1_b), M = A again.
HOF2: one tier (phof2_c): body A = B = tier C, M = mask; head A = B = M = the head image."""
import io
import os
import sys
from pathlib import Path
import numpy as np
from PIL import Image
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts')); sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import bglbio as gb  # noqa: E402
import tier_textures as TT  # noqa: E402
M_ = os.environ['M']; OUT = HERE / 'work' / f'hof{M_}'
doc, b = gb.read(HERE / 'before' / f'mm9_peasanthof{M_}.glb')


def image(i):
    im = doc['images'][i]; v = doc['bufferViews'][im['bufferView']]; o = v.get('byteOffset', 0)
    return Image.open(io.BytesIO(b[o:o + v['byteLength']]))


def tex_of(m):
    return doc['textures'][m['pbrMetallicRoughness']['baseColorTexture']['index']]['source']


M = {m['name']: m for m in doc['materials']}
body = 'PeasantHOF_A' if M_ == '1' else 'PeasantHOF_C'
tone = np.asarray(image(tex_of(M[body])).convert('RGB'), np.float64) / 255
mimg = image(M[body]['extras']['openyamm_region_mask']['index']).convert('RGBA')
size = (tone.shape[1], tone.shape[0])
mask = np.stack([np.asarray(ch.resize(size, Image.BILINEAR), np.float64) / 255 for ch in mimg.split()], -1)
tiers = (('A', 'PeasantHOF_A'), ('B', 'PeasantHOF_B')) if M_ == '1' else (('A', body), ('B', body))
for tier, mat in tiers:
    out = TT.apply(tone, mask, M[mat]['extras']['openyamm_region_ramps'])
    Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)).save(OUT / f'tex_{body}_{tier}.png')
    print('TEX body', tier, mat)
Image.fromarray((mask[..., :3] * 255 + 0.5).astype(np.uint8)).save(OUT / f'tex_{body}_M.png')
heads = (('A', 'PeasantHOFHead'), ('B', 'PeasantHOFHead_phof1_b'), ('M', 'PeasantHOFHead')) if M_ == '1' else \
    (('A', 'PeasantHOFHead'), ('B', 'PeasantHOFHead'), ('M', 'PeasantHOFHead'))
for tier, mat in heads:
    image(tex_of(M[mat])).convert('RGB').save(OUT / f'tex_PeasantHOFHead_{tier}.png'); print('TEX head', tier, mat)
