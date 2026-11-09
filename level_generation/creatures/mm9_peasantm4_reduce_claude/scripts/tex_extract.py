#!/usr/bin/env python3
"""Base colours of the installed PeasantM4 GLB for mpqem.py's texture guard: work/tex_<prim material>_{A,B,M}.png. PeasantM4 has one
tier and no region masks (no KHR_materials_variants): A = B = the material's own colour image, M = the same image (the guard's third
channel set then repeats the colour test; harmless)."""
import io
import sys
from pathlib import Path
from PIL import Image
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import bglbio as gb  # noqa: E402
doc, b = gb.read(HERE / 'before' / 'mm9_peasantm4.glb')


def image(i):
    im = doc['images'][i]; v = doc['bufferViews'][im['bufferView']]; o = v.get('byteOffset', 0)
    return Image.open(io.BytesIO(b[o:o + v['byteLength']]))


for m in doc['materials']:
    img = image(doc['textures'][m['pbrMetallicRoughness']['baseColorTexture']['index']]['source']).convert('RGB')
    for t in 'ABM':
        img.save(HERE / 'work' / f"tex_{m['name']}_{t}.png")
    print('TEX', m['name'], img.size)
