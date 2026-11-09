#!/usr/bin/env python3
"""Inventory of the four installed GLBs: mesh nodes, primitives, counts, and which arrays are byte-identical across them."""
import sys, hashlib
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, accessor_bytes
H = lambda b: hashlib.sha1(b).hexdigest()[:10]
docs = {}
for n in '1234':
    doc, b = read_glb(Path(f'before/mm9_peasantdf{n}.glb')); docs[n] = (doc, b)
doc, b = docs['1']
print('nodes with mesh:', [(i, nd.get('name'), nd.get('mesh'), nd.get('skin')) for i, nd in enumerate(doc['nodes']) if 'mesh' in nd])
print('materials:', [m['name'] for m in doc['materials']])
print('extensions:', doc.get('extensionsUsed'))
for n, (doc, b) in docs.items():
    print('==', n, 'meshes', len(doc['meshes']), 'anims', len(doc.get('animations', [])), 'images', len(doc.get('images', [])))
    for mi, m in enumerate(doc['meshes']):
        for pi, p in enumerate(m['primitives']):
            a = p['attributes']; nt = doc['accessors'][p['indices']]['count'] // 3; nv = doc['accessors'][a['POSITION']]['count']
            hs = {k: H(accessor_bytes(doc, b, v)) for k, v in a.items()}
            print(f"  mesh{mi} {m.get('name')} prim{pi} mat={doc['materials'][p['material']]['name']} tris={nt} verts={nv} idx={H(accessor_bytes(doc,b,p['indices']))} P={hs['POSITION']} UV={hs.get('TEXCOORD_0')} J={hs.get('JOINTS_0')} W={hs.get('WEIGHTS_0')} N={hs.get('NORMAL')} ext={list(p.get('extensions',{}).keys())} extras={list(m.get('extras',{}).keys())}")
