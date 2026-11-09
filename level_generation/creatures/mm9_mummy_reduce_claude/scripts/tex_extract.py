#!/usr/bin/env python3
"""Guard images of the installed GLB for mpqem.py's texture guard: work/tex_<primitive>_<k>.png (bytes as installed) and
work/tex_list.json. Mummy (copied from the Zombie's): every tier has its own body and head base colour (Mummy, Mummy_B, Mummy_C;
MummyHead, MummyHead_B, MummyHead_C), so the guard images are the three tier base colours per primitive."""
import json
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import bglbio as gb  # noqa: E402
doc, b = gb.read(HERE / 'before' / 'mm9_mummy.glb')
M = {m['name']: m for m in doc['materials']}


def image_of(tex_index):
    return doc['textures'][tex_index]['source']


def base(name):
    return image_of(M[name]['pbrMetallicRoughness']['baseColorTexture']['index'])


SETS = {'Mummy': [base('Mummy'), base('Mummy_B'), base('Mummy_C')],
        'MummyHead': [base('MummyHead'), base('MummyHead_B'), base('MummyHead_C')]}
out = {}
for prim, imgs in SETS.items():
    out[prim] = []
    for k, i in enumerate(imgs):
        v = doc['bufferViews'][doc['images'][i]['bufferView']]; o = v.get('byteOffset', 0)
        f = HERE / 'work' / f'tex_{prim}_{k}.png'; f.write_bytes(b[o:o + v['byteLength']]); out[prim].append(f.name)
        print('TEX', prim, k, doc['images'][i].get('name'))
(HERE / 'work' / 'tex_list.json').write_text(json.dumps(out, indent=1))
