#!/usr/bin/env python3
"""Base colours of the installed GLB for mpqem.py's texture guard: work/tex_<material>_{A,B,M}.png. PeasantDM4 has one skin and
no region mask (no tiers), so A = B = M = the material's own base colour image (mpqem.py reads three; the guard is the same)."""
import io
import sys
from pathlib import Path
from PIL import Image
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import bglbio as gb  # noqa: E402
doc, b = gb.read(HERE / 'before' / 'mm9_peasantdm4.glb')
for m in doc['materials']:
    i = doc['textures'][m['pbrMetallicRoughness']['baseColorTexture']['index']]['source']
    v = doc['bufferViews'][doc['images'][i]['bufferView']]; o = v.get('byteOffset', 0)
    im = Image.open(io.BytesIO(b[o:o + v['byteLength']])).convert('RGB')
    for t in 'ABM':
        im.save(HERE / 'work' / f'tex_{m["name"]}_{t}.png')
    print('TEX', m['name'], im.size, doc['images'][i].get('name'))
