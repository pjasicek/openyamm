#!/usr/bin/env python3
"""Texture-guard images for mpqem.py from the installed GLB (bytes as installed): each LOD0 material's base colour in the three
tiers (the Clan Soldier's tiers are own images per tier, no ramps: ClanLimbs_A/B/C, ClanTorso_*, ClanHead_*).
-> work/tex_<base>_<tier>.png, work/tex_list.json {<base>_A: [files]}"""
import json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import bglbio as gb  # noqa: E402
doc, b = gb.read(HERE / 'before' / 'mm9_clansoldier.glb')
mats = {m['name']: m for m in doc['materials']}
def image(tex_index):
    im = doc['images'][doc['textures'][tex_index]['source']]; v = doc['bufferViews'][im['bufferView']]
    o = v.get('byteOffset', 0); return b[o:o + v['byteLength']], im.get('mimeType', 'image/png')
out = {}
for base in ('ClanLimbs', 'ClanTorso', 'ClanHead'):
    files = []
    for t in 'ABC':
        data, mime = image(mats[f'{base}_{t}']['pbrMetallicRoughness']['baseColorTexture']['index'])
        f = f'tex_{base}_{t}.' + ('png' if 'png' in mime else 'jpg'); (HERE / 'work' / f).write_bytes(data); files.append(f)
    out[f'{base}_A'] = files
json.dump(out, open(HERE / 'work' / 'tex_list.json', 'w'), indent=1); print('TEX', out)
