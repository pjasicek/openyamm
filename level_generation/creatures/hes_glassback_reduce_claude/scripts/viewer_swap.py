#!/usr/bin/env python3
"""Review-viewer GLB of the reduction (Glassback): the source project's viewer GLB of a tier (baked tier colours,
separate body and head primitives, the tier's crest nodes on their bones, sampled clips) with its body primitive
replaced by the reduced runtime LOD0's body-set faces (merged-atlas u < 0.5, mapped back to the body texture:
u * 2080 / 1024, tools/merge_head_material.py layout). The head set is kept exactly by the reduction, so the viewer's
head primitive stays; the script checks that the reduced head-set face count equals it.
Usage: viewer_swap.py <viewer.glb> <runtime.glb> <out.glb>"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb, accessor_bytes  # noqa: E402
NP = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8}
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}


def arr(doc, b, i):
    a = doc['accessors'][i]; x = np.frombuffer(accessor_bytes(doc, b, i), NP[a['componentType']]).reshape(-1, NC[a['type']])
    if a.get('normalized') and a['componentType'] != 5126:
        x = x / np.iinfo(NP[a['componentType']]).max
    return x.astype(np.float64 if a['componentType'] == 5126 or a.get('normalized') else np.int64)


view, run, outp = (Path(a) for a in sys.argv[1:4])
V, VB = read_glb(view); R, RB = read_glb(run)
NODE = 'Glassback'
vnode = next(n for n in V['nodes'] if n.get('name') == NODE); rnode = next(n for n in R['nodes'] if n.get('name') == NODE)
vj = [V['nodes'][i]['name'] for i in V['skins'][vnode['skin']]['joints']]
rj = [R['nodes'][i]['name'] for i in R['skins'][rnode['skin']]['joints']]
jmap = np.array([vj.index(n) if n in vj else 0 for n in rj])   # Socket_Beak carries no weights
rp = R['meshes'][rnode['mesh']]['primitives'][0]
A = {s: arr(R, RB, i) for s, i in rp['attributes'].items()}
F = arr(R, RB, rp['indices']).reshape(-1, 3)
body = A['TEXCOORD_0'][F][:, :, 0].mean(1) < 0.5
binary = bytearray(VB)


def put(data, comp, typ, count, target, mn=None, mx=None):
    binary.extend(b'\0' * (-len(binary) % 4)); off = len(binary); binary.extend(data)
    V['bufferViews'].append({'buffer': 0, 'byteOffset': off, 'byteLength': len(data), 'target': target})
    a = {'bufferView': len(V['bufferViews']) - 1, 'componentType': comp, 'type': typ, 'count': count}
    if mn is not None:
        a['min'], a['max'] = mn, mx
    V['accessors'].append(a); return len(V['accessors']) - 1


vmesh = V['meshes'][vnode['mesh']]
for p in vmesh['primitives']:
    name = V['materials'][p['material']]['name']
    if 'Head' in name:
        assert V['accessors'][p['indices']]['count'] // 3 == int((~body).sum()), 'head set changed'
        continue
    f = F[body]; used = np.unique(f); remap = -np.ones(len(A['POSITION']), np.int64); remap[used] = np.arange(len(used))
    P = A['POSITION'][used].astype(np.float32); uv = A['TEXCOORD_0'][used].copy(); uv[:, 0] *= 2080 / 1024
    J = jmap[A['JOINTS_0'][used]]
    p['attributes'] = {
        'POSITION': put(P.tobytes(), 5126, 'VEC3', len(P), 34962, P.min(0).tolist(), P.max(0).tolist()),
        'NORMAL': put(A['NORMAL'][used].astype(np.float32).tobytes(), 5126, 'VEC3', len(P), 34962),
        'TEXCOORD_0': put(uv.astype(np.float32).tobytes(), 5126, 'VEC2', len(P), 34962),
        'JOINTS_0': put(J.astype(np.uint16).tobytes(), 5123, 'VEC4', len(P), 34962),
        'WEIGHTS_0': put(A['WEIGHTS_0'][used].astype(np.float32).tobytes(), 5126, 'VEC4', len(P), 34962)}
    p['indices'] = put(remap[f].astype(np.uint32).reshape(-1).tobytes(), 5125, 'SCALAR', f.size, 34963)
    print('VIEWERSWAP', name, 'body', len(f), 'head', int((~body).sum()))
write_glb(outp, V, bytes(binary))
