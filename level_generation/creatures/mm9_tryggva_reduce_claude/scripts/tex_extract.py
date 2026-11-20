#!/usr/bin/env python3
"""Base colours of the installed GLB for mpqem.py's texture guard: work/tex_<prim material>_{A,B,M}.png. One skin, no tiers and
no region mask on this model: A = B = the material's own base colour image, M black (PeasantM1 reduce project's tex_extract.py,
the head-set branch for every primitive)."""
import io
import sys
from pathlib import Path
import numpy as np
from PIL import Image
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import bglbio as gb, cfg  # noqa: E402
doc, b = gb.read(HERE / 'before' / cfg.GLB)


def image(i):
    im = doc['images'][i]; v = doc['bufferViews'][im['bufferView']]; o = v.get('byteOffset', 0)
    return Image.open(io.BytesIO(b[o:o + v['byteLength']]))


M = {m['name']: m for m in doc['materials']}
for prim in cfg.PR:
    m = M[prim]; assert 'openyamm_region_mask' not in m.get('extras', {}), prim
    im = image(doc['textures'][m['pbrMetallicRoughness']['baseColorTexture']['index']]['source']).convert('RGB')
    for tier in 'AB':
        im.save(HERE / 'work' / f'tex_{prim}_{tier}.png')
    Image.fromarray(np.zeros((im.size[1], im.size[0], 3), np.uint8)).save(HERE / 'work' / f'tex_{prim}_M.png')
    print('TEX', prim, im.size)
