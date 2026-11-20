#!/usr/bin/env python3
"""Guard images of the installed GLB for mpqem.py's texture guard: work/tex_<primitive>_<k>.png (bytes as installed) and
work/tex_list.json. The zombie's body and head tiers share one base colour and differ by region-mask ramps, so their guard
images are the base colour and the region mask (a collapse that moves a mask boundary changes the tier colour); the torso has
its own base colour per tier (ZombieTorso, _B, _C)."""
import json
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import bglbio as gb  # noqa: E402
doc, b = gb.read(HERE / 'before' / 'mm9_honkf.glb')
M = {m['name']: m for m in doc['materials']}


def image_of(tex_index):
    return doc['textures'][tex_index]['source']


def base(name):
    return image_of(M[name]['pbrMetallicRoughness']['baseColorTexture']['index'])


SETS = {'HonkF_A': [base('HonkF_A'), image_of(M['HonkF_A']['extras']['openyamm_region_mask']['index'])],
        'HonkFHead': [base('HonkFHead'), base('HonkFHead_honkf_b')]}
out = {}
for prim, imgs in SETS.items():
    out[prim] = []
    for k, i in enumerate(imgs):
        v = doc['bufferViews'][doc['images'][i]['bufferView']]; o = v.get('byteOffset', 0)
        f = HERE / 'work' / f'tex_{prim}_{k}.png'; f.write_bytes(b[o:o + v['byteLength']]); out[prim].append(f.name)
        print('TEX', prim, k, doc['images'][i].get('name'))
(HERE / 'work' / 'tex_list.json').write_text(json.dumps(out, indent=1))
