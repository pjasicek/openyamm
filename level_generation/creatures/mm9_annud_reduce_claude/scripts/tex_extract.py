#!/usr/bin/env python3
"""Tier base colours of the installed GLB for mpqem.py's texture guard (Annud, PeasantF3's tex_extract.py pattern):
work/tex_<prim material>_<tier>.png with A = the default look (the material's own colour image), B = pm6_a (the same image with
Annud_PM6_A's / AnnudHead_PM6_A's region ramps applied by the engine rule, claude_shared/tier_textures.apply, mask and ramps read
from the GLB), M = the region mask (a collapse that moves the tunic-region border is refused as well)."""
import io
import sys
from pathlib import Path
import numpy as np
from PIL import Image
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts')); sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import bglbio as gb  # noqa: E402
import tier_textures as TT  # noqa: E402
doc, b = gb.read(HERE / 'before' / 'mm9_annud.glb')


def image(i):
    im = doc['images'][i]; v = doc['bufferViews'][im['bufferView']]; o = v.get('byteOffset', 0)
    return Image.open(io.BytesIO(b[o:o + v['byteLength']]))


def tex(i):
    return doc['textures'][i]['source']


M = {m['name']: m for m in doc['materials']}
for base, tier in (('Annud', 'Annud_PM6_A'), ('AnnudHead', 'AnnudHead_PM6_A')):
    img = image(tex(M[base]['pbrMetallicRoughness']['baseColorTexture']['index'])).convert('RGB')
    img.save(HERE / 'work' / f'tex_{base}_A.png')
    tone = np.asarray(img, np.float64) / 255; size = (tone.shape[1], tone.shape[0])
    mimg = image(tex(M[tier]['extras']['openyamm_region_mask']['index'])).convert('RGBA')
    mask = np.stack([np.asarray(ch.resize(size, Image.BILINEAR), np.float64) / 255 for ch in mimg.split()], -1)
    out = TT.apply(tone, mask, M[tier]['extras']['openyamm_region_ramps'])
    Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)).save(HERE / 'work' / f'tex_{base}_B.png')
    Image.fromarray((mask[..., :3] * 255 + 0.5).astype(np.uint8)).save(HERE / 'work' / f'tex_{base}_M.png')
    print('TEX', base, img.size, 'mask', mimg.size, 'region share', round(float((mask[..., 0] > 0.5).mean()), 3))
