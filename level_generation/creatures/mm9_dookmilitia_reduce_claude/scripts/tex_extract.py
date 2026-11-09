#!/usr/bin/env python3
"""Texture-guard images for mpqem.py from the installed Half-Orc GLB (bytes as installed): work/tex_<base>_<A|B|C>.png = the
base colour of tier A, B and C for the limbs, torso and head materials (the Half-Orc's tiers are per-tier paints, no region
masks). After mm9_lizardorc_reduce_claude/scripts/tex_extract.py."""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import bglbio as gb  # noqa: E402
doc, b = gb.read(HERE / 'before' / 'mm9_dookmilitia.glb')


def image(tex_index):
    im = doc['images'][doc['textures'][tex_index]['source']]; v = doc['bufferViews'][im['bufferView']]
    o = v.get('byteOffset', 0); return b[o:o + v['byteLength']]


mats = {m['name']: m for m in doc['materials']}
for base in ('DookMilitia', 'DookTorso', 'DookHead'):
    for t in 'ABC':
        data = image(mats[f'{base}_{t}']['pbrMetallicRoughness']['baseColorTexture']['index'])
        (HERE / 'work' / f'tex_{base}_{t}.png').write_bytes(data); print('TEX', base, t, len(data))
