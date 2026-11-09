#!/usr/bin/env python3
"""Texture-guard images for mpqem.py from the installed GLB (bytes as installed): work/tex_<material>.png, the base colour
of each LOD0 material (one skin, no tiers: GreaterDemon and GreaterDemon_Wing share the body base colour)."""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import bglbio as gb  # noqa: E402
doc, b = gb.read(HERE / 'before' / 'mm9_greaterdemon.glb')


def image(tex_index):
    im = doc['images'][doc['textures'][tex_index]['source']]; v = doc['bufferViews'][im['bufferView']]
    o = v.get('byteOffset', 0); return b[o:o + v['byteLength']], im.get('name')


for m in doc['materials']:
    data, name = image(m['pbrMetallicRoughness']['baseColorTexture']['index'])
    (HERE / 'work' / f"tex_{m['name']}.png").write_bytes(data); print('TEX', m['name'], name, len(data))
