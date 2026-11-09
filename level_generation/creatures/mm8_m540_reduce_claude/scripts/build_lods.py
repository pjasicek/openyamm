"""work/r77_lod0.glb -> export/mm8_m540.glb with LOD1-3 and shadow LODs, as mm8_m540_claude/scripts/build_lods.py:
build_actor_lods ratios 0.5 / 0.25 / 0.125 with 8 influences for the body, and the head texture set (u > 0.5) reduced
by bounded spatial cells (4 / 8 / 16 mm, reduce_head_lods.py) because its fine surfaces collapse under edge
decimation. The installed model has one merged material, so the head faces go to a temporary second material for
the LOD build and every level is merged back into one primitive afterwards.
Usage: blender -b -P build_lods.py  (REA_LOD0 / REA_OUT override the paths)"""
import copy
import json
import os
import struct
import sys
from pathlib import Path
import numpy as np
P = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(P.parents[2] / 'tools'))
import build_actor_lods as glb  # noqa: E402

SRC = P / os.environ.get('REA_LOD0', 'work/r77_lod0.glb'); OUT = P / os.environ.get('REA_OUT', 'export/mm8_m540.glb')
SPLIT = P / 'work/lod0_split.glb'; LODS = P / 'work/lods_split.glb'; NODE = 'OgreMage'
FMT = {5121: 'u1', 5123: '<u2', 5125: '<u4', 5126: '<f4'}
NCOMP = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}


def arr(d, b, i):
    a = d['accessors'][i]
    return np.frombuffer(glb.accessor_bytes(d, b, i), dtype=FMT[a['componentType']]).reshape(a['count'], -1).copy()


def add(d, b, template, values):
    a = {k: v for k, v in template.items() if k not in ('bufferView', 'byteOffset', 'min', 'max')}
    a['count'] = len(values)
    if 'min' in template:
        a['min'] = values.min(0).tolist(); a['max'] = values.max(0).tolist()
    return glb.append_accessor(d, b, a, np.ascontiguousarray(values.astype(FMT[a['componentType']])).tobytes())


def sub_primitive(d, b, prim, tris):
    """New primitive with only the given triangles (unused vertices dropped)."""
    used, inv = np.unique(tris, return_inverse=True)
    attrs = {s: add(d, b, d['accessors'][i], arr(d, b, i)[used]) for s, i in prim['attributes'].items()}
    idx = glb.append_accessor(d, b, {'componentType': 5125, 'type': 'SCALAR', 'count': inv.size},
                              inv.astype('<u4').tobytes())
    return {'attributes': attrs, 'indices': idx, 'material': prim['material']}


# 1. split LOD0 into body (material 0) and head (temporary material 'OgreMageHead')
d, b = glb.read_glb(SRC); b = bytearray(b)
mesh = d['meshes'][next(n['mesh'] for n in d['nodes'] if n.get('name') == NODE)]
assert len(mesh['primitives']) == 1 and 'openyamm_lods' not in mesh.get('extras', {})
prim = mesh['primitives'][0]; variants = prim.get('extensions')
tri = arr(d, b, prim['indices']).reshape(-1, 3); uv = arr(d, b, prim['attributes']['TEXCOORD_0'])
head = uv[tri, 0].mean(1) > .5
d['materials'].append(dict(copy.deepcopy(d['materials'][prim['material']]), name='OgreMageHead'))
body_p = sub_primitive(d, b, prim, tri[~head]); head_p = sub_primitive(d, b, prim, tri[head])
head_p['material'] = len(d['materials']) - 1
mesh['primitives'] = [body_p, head_p]
glb.write_glb(SPLIT, d, bytes(b))
print('SPLIT body', int((~head).sum()), 'head', int(head.sum()))

# 2. ordinary LODs (the head slot is replaced below)
glb.generate(SPLIT, LODS, NODE, ratios=(.5, .25, .125), max_influences=8,
             material_ratios={'OgreMageHead': (.9, .8, .7)})

# 3. head LODs by bounded spatial cells (mm8_m540_claude/scripts/reduce_head_lods.py; the neck below y 1.40 is not
# clustered so the head stays joined to the body)
d, b = glb.read_glb(LODS); b = bytearray(b)
hm = next(i for i, m in enumerate(d['materials']) if m['name'] == 'OgreMageHead')
base = d['meshes'][next(n['mesh'] for n in d['nodes'] if n.get('name') == NODE)]
hp = next(p for p in base['primitives'] if p['material'] == hm)
pos = arr(d, b, hp['attributes']['POSITION']); htri = arr(d, b, hp['indices']).reshape(-1, 3); report = []
for level, (mi, cell) in enumerate(zip(base['extras']['openyamm_lods'], (.004, .008, .016)), 1):
    xyz = pos.copy(); groups = {}
    for i, v in enumerate(pos):
        groups.setdefault(tuple(np.floor(v / cell).astype(int)) if v[1] > 1.40 else ('neck', i), []).append(i)
    cluster = np.empty(len(pos), int)
    for g, ids in enumerate(groups.values()):
        xyz[ids] = pos[ids].mean(0); cluster[ids] = g
    ids = cluster[htri]; keep = (ids[:, 0] != ids[:, 1]) & (ids[:, 0] != ids[:, 2]) & (ids[:, 1] != ids[:, 2])
    sel = htri[keep]
    _, uniq = np.unique(np.sort(cluster[sel], axis=1), axis=0, return_index=True); sel = sel[np.sort(uniq)]
    used, inv = np.unique(sel, return_inverse=True)
    attrs = {}
    for s, i in hp['attributes'].items():
        attrs[s] = add(d, b, d['accessors'][i], (xyz if s == 'POSITION' else arr(d, b, i))[used])
    idx = glb.append_accessor(d, b, {'componentType': 5125, 'type': 'SCALAR', 'count': inv.size}, inv.astype('<u4').tobytes())
    m = d['meshes'][mi]; slot = next(k for k, p in enumerate(m['primitives']) if p['material'] == hm)
    m['primitives'][slot] = {'attributes': attrs, 'indices': idx, 'material': hm}
    delta = float(np.linalg.norm(xyz - pos, axis=1).max()); assert delta < cell * 1.74
    report.append({'level': level, 'cell_m': cell, 'head_triangles': int(len(sel)), 'max_vertex_displacement_m': delta})


# 4. merge head back into the body primitive of every colour level (one material, the installed variants)
def merge(m):
    ps = m['primitives']; sems = set().union(*(p['attributes'] for p in ps))
    attrs, off, idx = {}, 0, []
    for s in sorted(sems):
        parts = []
        for p in ps:
            n = d['accessors'][p['attributes']['POSITION']]['count']
            if s in p['attributes']:
                parts.append(arr(d, b, p['attributes'][s]).astype(np.float64))
            else:  # glTF omits the second influence set when it is all zero
                parts.append(np.zeros((n, NCOMP[d['accessors'][next(q['attributes'][s] for q in ps if s in q['attributes'])]['type']])))
        tmpl = max((d['accessors'][p['attributes'][s]] for p in ps if s in p['attributes']), key=lambda a: a['componentType'])
        attrs[s] = add(d, b, tmpl, np.concatenate(parts))
    for p in ps:
        idx.append(arr(d, b, p['indices']).ravel() + off); off += d['accessors'][p['attributes']['POSITION']]['count']
    idx = np.concatenate(idx)
    out = {'attributes': attrs, 'material': 0,
           'indices': glb.append_accessor(d, b, {'componentType': 5125, 'type': 'SCALAR', 'count': idx.size}, idx.astype('<u4').tobytes())}
    if variants:
        out['extensions'] = copy.deepcopy(variants)
    m['primitives'] = [out]


levels = [d['nodes'][next(i for i, n in enumerate(d['nodes']) if n.get('name') == NODE)]['mesh']] + base['extras']['openyamm_lods']
for mi in levels:
    merge(d['meshes'][mi])
for mi, si in zip(levels, base['extras']['openyamm_shadow_lods']):
    d['meshes'][si] = glb.merge_shadow(d, b, d['meshes'][mi])
assert d['materials'][-1]['name'] == 'OgreMageHead'; d['materials'].pop()
for m in d['meshes']:
    for p in m['primitives']:
        assert p['material'] < len(d['materials']) and d['accessors'][p['indices']]['count'] % 3 == 0
counts = [d['accessors'][d['meshes'][mi]['primitives'][0]['indices']]['count'] // 3 for mi in levels]
assert all(x > y for x, y in zip(counts, counts[1:])), counts
glb.write_glb(OUT, d, bytes(b))
(OUT.parent / 'lods.json').write_text(json.dumps({'triangles': counts, 'head_reduction': report, 'source': str(SRC)}, indent=2) + '\n')
print('LODS', counts, report)
