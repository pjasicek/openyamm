#!/usr/bin/env python3
"""Texture-guard images for mpqem.py from the installed GLB (Sigmund has no tiers): work/tex_<material>_<A|B|M>.png with
A = B = M = the material's base colour (no region mask or tier ramps on this model)."""
import io
import sys
from pathlib import Path
from PIL import Image
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import bglbio as gb  # noqa: E402
doc, b = gb.read(HERE / 'before' / 'mm9_sigmund.glb')


def image(i):
    im = doc['images'][i]; v = doc['bufferViews'][im['bufferView']]; o = v.get('byteOffset', 0)
    return Image.open(io.BytesIO(b[o:o + v['byteLength']]))


for m in doc['materials']:
    col = image(doc['textures'][m['pbrMetallicRoughness']['baseColorTexture']['index']]['source']).convert('RGB')
    nrm = image(doc['textures'][m['normalTexture']['index']]['source']).convert('RGB')
    for t in "AB":
        col.save(HERE / 'work' / f"tex_{m['name']}_{t}.png")
    col.save(HERE / "work" / f"tex_{m['name']}_M.png")
    print('TEX', m['name'], col.size, nrm.size)
