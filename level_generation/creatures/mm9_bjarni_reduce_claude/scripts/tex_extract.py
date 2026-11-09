#!/usr/bin/env python3
"""Base colours of the installed Bjarni GLB for mpqem.py's texture guard: work/tex_<prim material>_{A,B,M}.png.
Markel has one skin (no tiers, no region mask): A and B are both the material's own base colour image, M black.
(From the PeasantM5 reduction's tex_extract.py, which recoloured two tiers.)"""
import io
import sys
from pathlib import Path
import numpy as np
from PIL import Image
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import bglbio as gb  # noqa: E402
doc, b = gb.read(HERE / 'before' / 'mm9_bjarni.glb')


def image(i):
    im = doc['images'][i]; v = doc['bufferViews'][im['bufferView']]; o = v.get('byteOffset', 0)
    return Image.open(io.BytesIO(b[o:o + v['byteLength']]))


for m in doc['materials']:
    im = image(doc['textures'][m['pbrMetallicRoughness']['baseColorTexture']['index']]['source']).convert('RGB')
    for t in 'AB':
        im.save(HERE / 'work' / f"tex_{m['name']}_{t}.png")
    Image.fromarray(np.zeros((im.size[1], im.size[0], 3), np.uint8)).save(HERE / 'work' / f"tex_{m['name']}_M.png")
    print('TEX', m['name'], im.size)
