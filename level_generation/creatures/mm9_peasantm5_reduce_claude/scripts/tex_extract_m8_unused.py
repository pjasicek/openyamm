#!/usr/bin/env python3
"""Base colours of the installed GLB for mpqem.py's texture guard: work/tex_<prim material>_<A,B,M>.png.
PeasantM5 has one tier and no region mask: A = B = M = each primitive's own base colour image (PeasantM5 body,
PeasantM5Head head + hands)."""
import io
import sys
from pathlib import Path
from PIL import Image
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import bglbio as gb  # noqa: E402
doc, b = gb.read(HERE / 'before' / 'mm9_peasantm5.glb')


def image(i):
    im = doc['images'][i]; v = doc['bufferViews'][im['bufferView']]; o = v.get('byteOffset', 0)
    return Image.open(io.BytesIO(b[o:o + v['byteLength']]))


for m in doc['materials']:
    src = doc['textures'][m['pbrMetallicRoughness']['baseColorTexture']['index']]['source']
    img = image(src).convert('RGB')
    for t in 'ABM':
        img.save(HERE / 'work' / f"tex_{m['name']}_{t}.png")
    print('TEX', m['name'], img.size)
