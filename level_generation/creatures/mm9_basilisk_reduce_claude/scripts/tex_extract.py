#!/usr/bin/env python3
"""Texture-guard images for mpqem.py from the installed Basilisk GLB (bytes as installed): work/tex_Basilisk_M.png (region
mask: red frill/mouth vs scales) and work/tex_Basilisk_B.png (the shared 2K base colour; tiers A and C ramp it by luminance)."""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import bglbio as gb  # noqa: E402
doc, b = gb.read(HERE / 'before' / 'mm9_basilisk.glb')


def image(tex_index):
    im = doc['images'][doc['textures'][tex_index]['source']]; v = doc['bufferViews'][im['bufferView']]
    o = v.get('byteOffset', 0); return b[o:o + v['byteLength']]


m = doc['materials'][0]; assert m['name'] == 'Basilisk_A'
assert doc['materials'][1]['pbrMetallicRoughness']['baseColorTexture']['index'] == m['pbrMetallicRoughness']['baseColorTexture']['index']
for t, data in {'M': image(m['extras']['openyamm_region_mask']['index']),
                'B': image(m['pbrMetallicRoughness']['baseColorTexture']['index'])}.items():
    (HERE / 'work' / f'tex_Basilisk_{t}.png').write_bytes(data); print('TEX', t, len(data))
