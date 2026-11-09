#!/usr/bin/env python3
"""Texture-guard images for mpqem.py from the installed Lizard-Orc GLB (bytes as installed): work/tex_<base>_<A|B|C>.png for the
two body pages (Liz, LizB). The tiers share one paint under a region mask with ramps (R hide, G steel, B leather), so the guard is
A = the shared base colour (tier A shows it as painted), B = the region mask (from tier B's material), C = the metal/roughness map.
Imp copy (mm9_imp_reduce_claude/scripts/tex_extract.py), lizardorc-reduce-20261104."""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import bglbio as gb  # noqa: E402
doc, b = gb.read(HERE / 'before' / 'mm9_lizardorc.glb')


def image(tex_index):
    im = doc['images'][doc['textures'][tex_index]['source']]; v = doc['bufferViews'][im['bufferView']]
    o = v.get('byteOffset', 0); return b[o:o + v['byteLength']]


mats = {m['name']: m for m in doc['materials']}
for base in ('Liz', 'LizB'):
    out = {'A': image(mats[base + '_A']['pbrMetallicRoughness']['baseColorTexture']['index']),
           'B': image(mats[base + '_B']['extras']['openyamm_region_mask']['index']),
           'C': image(mats[base + '_A']['pbrMetallicRoughness']['metallicRoughnessTexture']['index'])}
    for t, data in out.items():
        (HERE / 'work' / f'tex_{base}_{t}.png').write_bytes(data); print('TEX', base, t, len(data))
