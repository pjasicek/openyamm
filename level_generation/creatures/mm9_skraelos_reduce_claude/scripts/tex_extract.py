#!/usr/bin/env python3
"""Images of the installed GLB for mpqem.py's texture guard (Skraelos: one skin, no tiers, no region mask):
work/tex_<prim material>_<A,B,M,N>.png with A = B = the base colour, M = the ORM image, N = the emission mask (head) or the
base colour again (body), so a collapse that shows colours, roughness/AO or ember glow the source lacks there is refused."""
import io
import sys
from pathlib import Path
from PIL import Image
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import bglbio as gb  # noqa: E402
doc, b = gb.read(HERE / 'before' / 'mm9_skraelos.glb')


def image(t):
    im = doc['images'][doc['textures'][t]['source']]; v = doc['bufferViews'][im['bufferView']]; o = v.get('byteOffset', 0)
    return Image.open(io.BytesIO(b[o:o + v['byteLength']])).convert('RGB')


for m in doc['materials']:
    base = image(m['pbrMetallicRoughness']['baseColorTexture']['index'])
    orm = image(m['pbrMetallicRoughness']['metallicRoughnessTexture']['index']).resize(base.size, Image.BILINEAR)
    em = image(m['emissiveTexture']['index']).resize(base.size, Image.BILINEAR) if 'emissiveTexture' in m else base
    for t, im in (('A', base), ('B', base), ('M', orm), ('N', em)):
        im.save(HERE / 'work' / f"tex_{m['name']}_{t}.png")
    print('TEX', m['name'], base.size)
