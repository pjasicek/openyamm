#!/usr/bin/env python3
"""Last step: what the engine's blended pass needs. It writes no depth and keeps a blended primitive's triangle order, on every LOD (decimation shuffles them), so order is authored here, after the mirror:
- Robe lining: the robe's triangles again, inside-out with flipped normals (a single-sided tube would show nothing of its far wall). Lining first, outer faces after: seen from outside the far wall's inner
  side is behind the near wall's outer side, seen from below or inside only the lining faces the camera.
- Body: collar bowl, lining, robe, jacket. Arms: hand first (the wrist stub sits inside the sleeve), then sleeve and cuff. Head: dark pockets, interior faces (radial test), then the shell by distance from its centre.
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
isrobe = np.array([n.startswith('Y') for n in names])
ishand = np.array([n.startswith('Finger') or n.startswith('Zhand') or n.startswith('Zfing') for n in names])


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
for mesh in doc['meshes']:
    if 'Shadow' in mesh.get('name', ''):
        continue
    for p in mesh['primitives']:
        name = doc['materials'][p['material']]['name']
        at = p['attributes']
        T = raw(p['indices']).reshape(-1, 3).astype(np.int64)
        P = raw(at['POSITION']).astype(np.float64)
        J = raw(at['JOINTS_0']).astype(np.int64); W = raw(at['WEIGHTS_0']).astype(np.float64)
        if W.max() > 1.5:
            W = W / 255
        dom = J[np.arange(len(J)), W.argmax(1)]
        if name.startswith('GhostHead'):
            c = 0.5 * (P.min(0) + P.max(0))
            UV = raw(at['TEXCOORD_0']).astype(np.float64)
            du = UV[T].max(1) - UV[T].min(1)
            cap = du.max(1) < 1e-6                 # the throat's dark pocket: first of all
            dist = np.linalg.norm(P[T].mean(1) - c, axis=1)
            # the scrap on each jaw: pieces of the mouth's inside reach out by the cheek, and sorted by distance alone they drew over the near cheek. A face with more head further out along its radial line is interior, whatever its distance; so is a face turned inward
            A_, B_, C_ = P[T[:, 0]], P[T[:, 1]], P[T[:, 2]]
            E1, E2 = B_ - A_, C_ - A_
            n = np.cross(E1, E2)
            cen_f = P[T].mean(1)
            # grazing faces too: the jaw's underside sits in a concave fold, further out than the cheek that hides it
            inner = (n * (cen_f - c)).sum(1) / np.maximum(np.linalg.norm(n, axis=1) * dist, 1e-12) < 0.45
            for i in np.nonzero(~inner)[0]:
                d = cen_f[i] - c; d = d / max(np.linalg.norm(d), 1e-12)
                o = cen_f[i] + d * 1e-4
                h = np.cross(d, E2); det = (E1 * h).sum(1)
                s_ = o - A_
                with np.errstate(divide='ignore', invalid='ignore'):
                    f_ = 1 / det
                    u_ = f_ * (s_ * h).sum(1); q_ = np.cross(s_, E1); v_ = f_ * (q_ * d).sum(1); t_ = f_ * (E2 * q_).sum(1)
                inner[i] = bool(((np.abs(det) > 1e-14) & (u_ >= 0) & (v_ >= 0) & (u_ + v_ <= 1) & (t_ > 2e-4)).any())
            order = np.lexsort((dist, ~inner, ~cap))
            T = T[order]
        elif name.startswith('GhostArm'):
            hand = ishand[dom[T]].mean(1) > 0.5
            T = np.concatenate([T[hand], T[~hand]])
        else:
            # chain-weighted faces, and the rows up to the belt that ride XCENTER (each chain root sits at its own row: without them the lining's top edge is a staircase, seen through the front)
            vr = isrobe[dom]
            vr = vr | ((np.array(names)[dom] == 'XCENTER') & (P[:, 1] < P[vr, 1].max() + 0.075))
            robe = vr[T].mean(1) > 0.6
            rv = np.unique(T[robe])
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
            lining = remap[T[robe]][:, ::-1]
            UVb = raw(p['attributes']['TEXCOORD_0']).astype(np.float64)
            rest = T[~robe]
            bowl = (UVb[rest].max(1) - UVb[rest].min(1)).max(1) < 1e-6      # the collar's dark bowl: under everything, or it interleaves with the ruff in triangle order
            T = np.concatenate([rest[bowl], lining, T[robe], rest[~bowl]])
            report.append((mesh['name'], name, 'lining', len(lining), 'of', len(T)))
        a0 = dict(doc['accessors'][p['indices']])
        idx = T.reshape(-1, 1).astype(np.uint32 if T.max() > 65535 else {5121: np.uint8, 5123: np.uint16, 5125: np.uint32}[max(a0['componentType'], 5123)])
        a0['componentType'] = {np.dtype(np.uint16): 5123, np.dtype(np.uint32): 5125}[idx.dtype] if idx.dtype != np.uint8 else 5121
        p['indices'] = put(idx, a0, 'SCALAR')
for r in report:
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
