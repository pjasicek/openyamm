#!/usr/bin/env python3
"""Last step: what the engine's blended pass needs. It writes no depth and keeps a blended primitive's triangle order, on every LOD (decimation shuffles them), so order is authored here, after the mirror:
- Lining on Skirt, Cape and the Wings: their triangles again, inside-out with flipped normals. Lining first, outer faces after: seen from outside the far wall's inner side is behind the near wall's outer side; seen from below or inside only the lining faces the camera. The cloak is a sheet, so each side sees one of the two.
- Arms: hand and claws first (the wrist sits inside the cuff), then sleeve. The head is opaque and needs no order.
Primitives themselves are sorted by the engine, back to front by their rest-pose centres. Usage: finish_blend.py in.glb out.glb"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb
SIZES = {5121: 1, 5123: 2, 5125: 4, 5126: 4}
g = Glb(sys.argv[1])
doc = g.json
names = [doc['nodes'][j]['name'] for j in doc['skins'][0]['joints']]
ishand = np.array([n.startswith('Zfing') or n.startswith('Zhand') for n in names])


def raw(i):
    a = doc['accessors'][i]; v = doc['bufferViews'][a['bufferView']]
    dt = {5121: np.uint8, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}[a['componentType']]
    k = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a['type']]
    st = v.get('byteStride') or SIZES[a['componentType']] * k
    off = v.get('byteOffset', 0) + a.get('byteOffset', 0)
    return np.ndarray((a['count'], k), dt, g.bin, off, (st, SIZES[a['componentType']])).copy()


def put(arr, a0, kind):
    arr = np.ascontiguousarray(arr)
    g.bin += b'\0' * (-len(g.bin) % 4)
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(g.bin), 'byteLength': arr.nbytes})
    g.bin += arr.tobytes()
    a = {'bufferView': len(doc['bufferViews']) - 1, 'componentType': a0['componentType'], 'count': len(arr), 'type': kind}
    if a0.get('normalized'):
        a['normalized'] = True
    if kind == 'VEC3':
        a['min'] = arr.min(0).astype(float).tolist(); a['max'] = arr.max(0).astype(float).tolist()
    doc['accessors'].append(a)
    doc['buffers'][0]['byteLength'] = len(g.bin)
    return len(doc['accessors']) - 1


report = []


def components(T, n):
    par = np.arange(n)

    def find(x):
        while par[x] != x:
            par[x] = par[par[x]]; x = par[x]
        return x
    for t in T:
        a, b, c = find(t[0]), find(t[1]), find(t[2])
        par[b] = a; par[find(c)] = a
    return np.array([find(i) for i in range(n)])


for mesh in doc['meshes']:
    if 'Shadow' in mesh.get('name', ''):
        continue
    for p in mesh['primitives']:
        name = doc['materials'][p['material']]['name']
        base = name.rsplit('_', 1)[0]
        at = p['attributes']
        T = raw(p['indices']).reshape(-1, 3).astype(np.int64)
        P = raw(at['POSITION']).astype(np.float64)
        J = raw(at['JOINTS_0']).astype(np.int64); W = raw(at['WEIGHTS_0']).astype(np.float64)
        if W.max() > 1.5:
            W = W / 255
        dom = J[np.arange(len(J)), W.argmax(1)]
        if base == 'BansheeHead':
            continue                                                   # opaque: depth does it
        if base in ('BansheeArmL', 'BansheeArmR'):
            hand = ishand[dom[T]].mean(1) > 0.5
            T = np.concatenate([T[hand], T[~hand]])
        elif base in ('BansheeSkirt', 'BansheeCape', 'BansheeWingL', 'BansheeWingR'):
            rv = np.unique(T)
            remap = -np.ones(len(P), np.int64); remap[rv] = len(P) + np.arange(len(rv))
            attrs = {}
            for sem, i in at.items():
                a0 = doc['accessors'][i]
                arr = raw(i)
                extra = arr[rv].copy()
                if sem == 'NORMAL':
                    extra = -extra
                attrs[sem] = put(np.concatenate([arr, extra]), a0, a0['type'])
            p['attributes'] = attrs
            lining = remap[T][:, ::-1]
            T = np.concatenate([lining, T])
            report.append((mesh['name'], base, 'lining', len(lining)))
        a0 = dict(doc['accessors'][p['indices']])
        idx = T.reshape(-1, 1).astype(np.uint32 if T.max() > 65535 else {5121: np.uint8, 5123: np.uint16, 5125: np.uint32}[max(a0['componentType'], 5123)])
        a0['componentType'] = {np.dtype(np.uint16): 5123, np.dtype(np.uint32): 5125}[idx.dtype] if idx.dtype != np.uint8 else 5121
        p['indices'] = put(idx, a0, 'SCALAR')
for r in report[:8]:
    print('FINISH', *r)
# the engine refuses dedicated shadow LODs on blended geometry (and a blended creature casts no shadow): they go
keep = [i for i, m in enumerate(doc['meshes']) if 'Shadow' not in m.get('name', '')]
mp = {o: n for n, o in enumerate(keep)}
for node in doc['nodes']:
    if 'mesh' in node:
        node['mesh'] = mp[node['mesh']]
doc['meshes'] = [doc['meshes'][i] for i in keep]
for m in doc['meshes']:
    ex = m.get('extras', {})
    ex.pop('openyamm_shadow_lods', None)
    if 'openyamm_lods' in ex:
        ex['openyamm_lods'] = [mp[i] for i in ex['openyamm_lods']]
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared'))
import region_variants as RV
d2, b2 = RV._compact(doc, bytes(g.bin))
RV.write_glb(sys.argv[2], d2, b2)
