#!/usr/bin/env python3
"""Texture guard images for mpqem.py (evil sorcerer fix pass): each LOD0 primitive's base colour in the three tiers, taken
from the review viewer GLBs of the installed model (review/viewer/es_<t>_before.glb, viewer_tiers.py: ramps baked with the
engine rule, tier A's own Low image, per-tier head images), resized to 1024 px.
-> work/tex_<material>_<tier>.png, work/tex_list.json {LOD0 material name: [files]}"""
import io, json, sys
from pathlib import Path
from PIL import Image
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import bglbio as G  # noqa: E402
S = 1024; out = {}
base_doc, _ = G.read(HERE / 'before' / 'mm9_evilsorcerer.glb')
bnode = next(n for n in base_doc['nodes'] if n.get('name') == 'Sorcerer' and 'mesh' in n)
names = [base_doc['materials'][p['material']]['name'] for p in base_doc['meshes'][bnode['mesh']]['primitives']]
for t in 'abc':
    doc, b = G.read(HERE / 'review' / 'viewer' / f'es_{t}_before.glb')
    node = next(n for n in doc['nodes'] if n.get('name') == 'Sorcerer' and 'mesh' in n)
    for name, p in zip(names, doc['meshes'][node['mesh']]['primitives']):
        tex = doc['materials'][p['material']]['pbrMetallicRoughness']['baseColorTexture']['index']
        im = doc['images'][doc['textures'][tex]['source']]; v = doc['bufferViews'][im['bufferView']]; o = v.get('byteOffset', 0)
        img = Image.open(io.BytesIO(bytes(b[o:o + v['byteLength']]))).convert('RGB').resize((S, S), Image.LANCZOS)
        f = f'tex_{name}_{t}.png'; img.save(HERE / 'work' / f); out.setdefault(name, []).append(f)
json.dump(out, open(HERE / 'work' / 'tex_list.json', 'w'), indent=1); print('TEX', out)
