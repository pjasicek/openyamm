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
doc, b = gb.read(HERE / 'before' / 'mm9_zombie.glb')
M = {m['name']: m for m in doc['materials']}


def image_of(tex_index):
    return doc['textures'][tex_index]['source']


def base(name):
    return image_of(M[name]['pbrMetallicRoughness']['baseColorTexture']['index'])


SETS = {'Zombie_A': [base('Zombie_A'), image_of(M['Zombie_A']['extras']['openyamm_region_mask']['index'])],
        'ZombieHead_A': [base('ZombieHead_A'), image_of(M['ZombieHead_A']['extras']['openyamm_region_mask']['index'])],
        'ZombieTorso': [base('ZombieTorso'), base('ZombieTorso_B'), base('ZombieTorso_C')]}
out = {}
for prim, imgs in SETS.items():
    out[prim] = []
    for k, i in enumerate(imgs):
        v = doc['bufferViews'][doc['images'][i]['bufferView']]; o = v.get('byteOffset', 0)
        f = HERE / 'work' / f'tex_{prim}_{k}.png'; f.write_bytes(b[o:o + v['byteLength']]); out[prim].append(f.name)
        print('TEX', prim, k, doc['images'][i].get('name'))
(HERE / 'work' / 'tex_list.json').write_text(json.dumps(out, indent=1))
