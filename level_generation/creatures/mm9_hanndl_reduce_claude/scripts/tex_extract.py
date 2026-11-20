#!/usr/bin/env python3
"""Base colours of the installed GLB for mpqem.py's texture guard (Hanndl: one tier, no region ramps or mask):
work/tex_<prim material>_A.png = the material's own base colour image (body Hanndl, head set HanndlHead)."""
import io
import sys
from pathlib import Path
from PIL import Image
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import bglbio as gb  # noqa: E402
doc, b = gb.read(HERE / 'before' / 'mm9_hanndl.glb')
for m in doc['materials']:
    i = doc['textures'][m['pbrMetallicRoughness']['baseColorTexture']['index']]['source']
    v = doc['bufferViews'][doc['images'][i]['bufferView']]; o = v.get('byteOffset', 0)
    im = Image.open(io.BytesIO(b[o:o + v['byteLength']])).convert('RGB')
    im.save(HERE / 'work' / f"tex_{m['name']}_A.png"); print('TEX', m['name'], doc['images'][i].get('name'), im.size)
