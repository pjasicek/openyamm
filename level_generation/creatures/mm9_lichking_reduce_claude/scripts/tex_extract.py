#!/usr/bin/env python3
"""Base colours of the installed Lich King GLB for mpqem.py's texture guard: work/tex_<prim material>_<tier>.png.
One tier (`lichking`), so A = B = the body tone with its region ramps applied by the engine rule (claude_shared/tier_textures.apply,
ramps and mask read from the GLB) and M = the region mask (a collapse that moves a region border is refused as well).
Head, staff and staff skull (kept whole): their colour images as A = B, M = the same image."""
import io
import sys
from pathlib import Path
import numpy as np
from PIL import Image
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts')); sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import bglbio as gb  # noqa: E402
import tier_textures as TT  # noqa: E402
doc, b = gb.read(HERE / 'before' / 'mm9_lichking.glb')


def image(i):
    im = doc['images'][i]; v = doc['bufferViews'][im['bufferView']]; o = v.get('byteOffset', 0)
    return Image.open(io.BytesIO(b[o:o + v['byteLength']]))


def tex_of(m):
    return doc['textures'][m['pbrMetallicRoughness']['baseColorTexture']['index']]['source']


M = {m['name']: m for m in doc['materials']}
for name in ('LichKing_LICHKING', 'LichKingStaffSkull_LICHKING'):
    tone = np.asarray(image(tex_of(M[name])).convert('RGB'), np.float64) / 255
    mimg = image(doc['textures'][M[name]['extras']['openyamm_region_mask']['index']]['source']).convert('RGBA')
    size = (tone.shape[1], tone.shape[0])
    mask = np.stack([np.asarray(ch.resize(size, Image.BILINEAR), np.float64) / 255 for ch in mimg.split()], -1)
    out = TT.apply(tone, mask, M[name]['extras']['openyamm_region_ramps'])
    im = Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8))
    im.save(HERE / 'work' / f'tex_{name}_A.png'); im.save(HERE / 'work' / f'tex_{name}_B.png')
    Image.fromarray((mask[..., :3] * 255 + 0.5).astype(np.uint8)).save(HERE / 'work' / f'tex_{name}_M.png'); print('TEX', name, size)
for name in ('LichKingHead', 'LichKingStaff'):
    im = image(tex_of(M[name])).convert('RGB')
    for t in 'ABM':
        im.save(HERE / 'work' / f'tex_{name}_{t}.png')
    print('TEX', name, im.size)
