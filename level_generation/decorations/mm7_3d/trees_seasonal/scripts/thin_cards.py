#!/usr/bin/env python3
"""Thin a tree's LOD0 leaf cards (quality pass 2026-10-16): the darkest cards by COLOR_0 (the baked sky occlusion,
so the most hidden ones inside the crown, behind other cards) are dropped from the LOD0 `Leaves` primitive, up to
`fraction` of the cards. Cards touching the LOD0 top or bottom (within 2 cm) are kept, so the family's LOD0 height
does not move. Only the index accessor changes (the vertices stay; deco_swap_glb.py compacts the file later).
A seasonal twin (autumn, the fruit tree) drops exactly the same cards: pass the summer's drop list with --like; the
card positions must match. Writes work/reduce/<id>_thin.glb and work/reduce/<id>_thin.json.
Usage: thin_cards.py <id> <fraction> | thin_cards.py <id> --like <summer id>"""
import json, os, sys
from pathlib import Path
import numpy as np
import common
sys.path.insert(0, os.path.join(common.REPO, 'tools'))
from build_actor_lods import read_glb, write_glb, accessor_bytes, append_accessor  # noqa: E402

sid = sys.argv[1]
spec = common.load(sid)
OUT = os.path.join(common.TREES, 'work', 'reduce'); os.makedirs(OUT, exist_ok=True)
src = Path(spec['work']) / spec['output']
doc, binary = read_glb(src); binary = bytearray(binary)
node = next(n for n in doc['nodes'] if 'mesh' in n)
mesh = doc['meshes'][node['mesh']]


def arr(index):
    a = doc['accessors'][index]
    dt = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8}[a['componentType']]
    width = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a['type']]
    v = np.frombuffer(accessor_bytes(doc, binary, index), dt).reshape(a['count'], width).astype(np.float64)
    if a['componentType'] != 5126 and a['type'] != 'SCALAR':
        v /= {5121: 255.0, 5123: 65535.0}[a['componentType']]
    return v


prim = next(p for p in mesh['primitives'] if doc['materials'][p['material']]['name'] == 'Leaves')
pos = arr(prim['attributes']['POSITION']); col = arr(prim['attributes']['COLOR_0'])[:, :3]
tri = arr(prim['indices']).astype(np.int64).reshape(-1, 3)
allpos = np.concatenate([arr(p['attributes']['POSITION']) for p in mesh['primitives']])
top, bottom = allpos[:, 1].max(), allpos[:, 1].min()
# cards: connected triangle groups (cut cards are small fans that share their vertices)
parent = list(range(len(pos)))


def find(a):
    while parent[a] != a:
        parent[a] = parent[parent[a]]; a = parent[a]
    return a


for a, b, c in tri:
    for x, y in ((a, b), (a, c)):
        rx, ry = find(int(x)), find(int(y))
        if rx != ry:
            parent[ry] = rx
card_of_tri = np.array([find(int(t[0])) for t in tri])
cards = sorted(set(card_of_tri.tolist()))
verts_of = {}
for t, c in zip(tri, card_of_tri):
    verts_of.setdefault(int(c), set()).update(int(v) for v in t)
if '--like' in sys.argv:
    ref = json.load(open(os.path.join(OUT, f"{sys.argv[sys.argv.index('--like') + 1]}_thin.json")))
    drop = set(ref['dropped'])
    centres = {c: pos[list(verts_of[c])].mean(0) for c in cards}
    for c, centre in zip(ref['dropped'], ref['dropped_centres']):
        assert c in centres and np.allclose(centres[c], centre, atol=1e-5), ('card mismatch', c)
    fraction = ref['fraction']
else:
    fraction = float(sys.argv[2])
    lum = {c: float(col[list(verts_of[c])].mean()) for c in cards}
    protected = {c for c in cards if pos[list(verts_of[c]), 1].max() > top - 0.02
                 or pos[list(verts_of[c]), 1].min() < bottom + 0.02}
    order = sorted((c for c in cards if c not in protected), key=lambda c: lum[c])
    drop = set(order[:int(round(fraction * len(cards)))])
keep_tri = tri[~np.isin(card_of_tri, list(drop))]
old_acc = doc['accessors'][prim['indices']]
data = keep_tri.astype(np.uint32 if old_acc['componentType'] == 5125 else np.uint16).tobytes()
acc = {'componentType': old_acc['componentType'], 'count': int(keep_tri.size), 'type': 'SCALAR'}
prim['indices'] = append_accessor(doc, binary, acc, data)
out = Path(OUT) / f'{sid}_thin.glb'
write_glb(out, doc, bytes(binary))
json.dump({'fraction': fraction, 'cards': len(cards), 'dropped': sorted(drop),
           'dropped_centres': [pos[list(verts_of[c])].mean(0).tolist() for c in sorted(drop)],
           'leaf_triangles': [int(len(tri)), int(len(keep_tri))]}, open(os.path.join(OUT, f'{sid}_thin.json'), 'w'))
print('THIN', sid, 'cards', len(cards), 'dropped', len(drop), 'leaf triangles', len(tri), '->', len(keep_tri))
