#!/usr/bin/env python3
"""Guard images of the installed GLB for mpqem.py's texture guard: work/tex_<prim material>_<A|B|M>.png.
Kira (2026-11-05): one skin, no tiers, no region mask. A = B = the material's base colour; M = its ORM image resized to the
colour's size (a collapse that moves a metal/leather border or an AO crease is refused as well)."""
import io
import sys
from pathlib import Path
from PIL import Image
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import bglbio as gb  # noqa: E402
doc, b = gb.read(HERE / 'before' / 'mm9_kira.glb')


def image(i):
    im = doc['images'][i]; v = doc['bufferViews'][im['bufferView']]; o = v.get('byteOffset', 0)
    return Image.open(io.BytesIO(b[o:o + v['byteLength']]))


for m in doc['materials']:
    pbr = m['pbrMetallicRoughness']
    col = image(doc['textures'][pbr['baseColorTexture']['index']]['source']).convert('RGB')
    orm = image(doc['textures'][pbr['metallicRoughnessTexture']['index']]['source']).convert('RGB').resize(col.size, Image.BILINEAR)
    for t in 'AB':
        col.save(HERE / 'work' / f"tex_{m['name']}_{t}.png")
    orm.save(HERE / 'work' / f"tex_{m['name']}_M.png")
    print('TEX', m['name'], col.size)
