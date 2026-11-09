#!/usr/bin/env python3
"""Texture-guard images for mpqem.py from the installed GLB (bytes as installed): work/tex_<base>_<A|B|C>.png.
Ghoul: one shared base colour per set and every tier is ramps through the region mask (body R hide, G veins; head R hide,
G nose hollow), so A is the region mask, B the shared base colour and C the same base colour (all tiers read from it)."""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import bglbio as gb  # noqa: E402
doc, b = gb.read(HERE / 'before' / 'mm9_ghoul.glb')


def image(tex_index):
    im = doc['images'][doc['textures'][tex_index]['source']]; v = doc['bufferViews'][im['bufferView']]
    o = v.get('byteOffset', 0); return b[o:o + v['byteLength']]


mats = {m['name']: m for m in doc['materials']}
for base in ('Ghoul', 'GhoulHead'):
    out = {'A': image(mats[base + '_A']['extras']['openyamm_region_mask']['index']),
           'B': image(mats[base + '_B']['pbrMetallicRoughness']['baseColorTexture']['index']),
           'C': image(mats[base + '_B']['pbrMetallicRoughness']['baseColorTexture']['index'])}
    for t, data in out.items():
        (HERE / 'work' / f'tex_{base}_{t}.png').write_bytes(data); print('TEX', base, t, len(data))
