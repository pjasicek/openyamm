#!/usr/bin/env python3
"""Texture-guard images for mpqem.py from the installed Imp GLB (bytes as installed): work/tex_<base>_<A|B|C>.png.
The three tiers share one base colour under a region mask with ramps (R skin, G claw tips / eyes), so the guard is
A = the region mask, B = the shared base colour, C = the metal/roughness map (the steel studs and belt metal on the leather,
which the colour guard alone would see only as pale blobs). Bigfoot copy, imp-reduce-20261104."""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import bglbio as gb  # noqa: E402
doc, b = gb.read(HERE / 'before' / 'mm9_imp.glb')


def image(tex_index):
    im = doc['images'][doc['textures'][tex_index]['source']]; v = doc['bufferViews'][im['bufferView']]
    o = v.get('byteOffset', 0); return b[o:o + v['byteLength']]


mats = {m['name']: m for m in doc['materials']}
for base in ('Imp', 'ImpHead'):
    out = {'A': image(mats[base + '_A']['extras']['openyamm_region_mask']['index']),
           'B': image(mats[base + '_A']['pbrMetallicRoughness']['baseColorTexture']['index']),
           'C': image(mats[base + '_A']['pbrMetallicRoughness']['metallicRoughnessTexture']['index'])}
    for t, data in out.items():
        (HERE / 'work' / f'tex_{base}_{t}.png').write_bytes(data); print('TEX', base, t, len(data))
