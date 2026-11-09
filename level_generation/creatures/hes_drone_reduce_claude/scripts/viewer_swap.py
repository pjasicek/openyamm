#!/usr/bin/env python3
"""Review-viewer GLB of the reduction (drone): the source project's viewer GLB of a tier (baked tier colours, that
tier's gear joined into the mesh, the thrust cone, sampled clips) with its body faces replaced by the reduced
runtime LOD0 (same atlas UVs, so the baked tier texture applies unchanged). Gear faces (vertices dominated by a Gear*
joint) are kept from the viewer GLB, or replaced by a reduced attachment GLB (--gear <glb>:<joint>, static mesh in
the joint's space, rigid on that joint). Material by name (Casing_A / Glow_A).
Usage: viewer_swap.py <viewer.glb> <runtime.glb> <out.glb> [--gear a.glb:GearEmitter ...]"""
import copy, sys
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


def prim_arrays(doc, b, p, jmap=None):
    out = {s: arr(doc, b, i) for s, i in p['attributes'].items() if s in ('POSITION', 'NORMAL', 'TEXCOORD_0', 'JOINTS_0', 'WEIGHTS_0')}
    if jmap is not None:
        out['JOINTS_0'] = jmap[out['JOINTS_0']]
    return out, arr(doc, b, p['indices']).reshape(-1, 3)


view, run, outp = (Path(a) for a in sys.argv[1:4])
gears = [g.split(':') for g in sys.argv[sys.argv.index('--gear') + 1:]] if '--gear' in sys.argv else []
V, VB = read_glb(view); R, RB = read_glb(run)
vnode = next(n for n in V['nodes'] if n.get('name') == 'HDR'); rnode = next(n for n in R['nodes'] if n.get('name') == 'HDR')
vj = [V['nodes'][i]['name'] for i in V['skins'][vnode['skin']]['joints']]
rj = [R['nodes'][i]['name'] for i in R['skins'][rnode['skin']]['joints']]
jmap = np.array([vj.index(n) for n in rj])
gear_j = {k for k, n in enumerate(vj) if n.startswith('Gear')}
replace_j = {vj.index(j) for _, j in gears}
ibm = arr(V, VB, V['skins'][vnode['skin']]['inverseBindMatrices']).reshape(-1, 4, 4).transpose(0, 2, 1)  # column-major
rprims = {R['materials'][p['material']]['name']: p for p in R['meshes'][rnode['mesh']]['primitives']}
binary = bytearray(VB); vmesh = V['meshes'][vnode['mesh']]


def put(data, comp, typ, count, target=None, mn=None, mx=None):
    binary.extend(b'\0' * (-len(binary) % 4)); off = len(binary); binary.extend(data)
    bv = {'buffer': 0, 'byteOffset': off, 'byteLength': len(data)}
    if target:
        bv['target'] = target
    V['bufferViews'].append(bv)
    a = {'bufferView': len(V['bufferViews']) - 1, 'componentType': comp, 'type': typ, 'count': count}
    if mn is not None:
        a['min'], a['max'] = mn, mx
    V['accessors'].append(a); return len(V['accessors']) - 1


for p in vmesh['primitives']:
    name = V['materials'][p['material']]['name']
    va, vf = prim_arrays(V, VB, p)
    dom = va['JOINTS_0'][np.arange(len(va['JOINTS_0'])), va['WEIGHTS_0'].argmax(1)]
    gv = np.isin(dom, list(gear_j - replace_j))
    keepf = gv[vf].all(1)
    parts = [(va, vf[keepf])]
    ra, rf = prim_arrays(R, RB, rprims[name], jmap); parts.append((ra, rf))
    for gpath, joint in gears:
        G, GB = read_glb(Path(gpath)); k = vj.index(joint)
        for gp in G['meshes'][next(n for n in G['nodes'] if 'mesh' in n)['mesh']]['primitives']:
            if G['materials'][gp['material']]['name'] != name:
                continue
            ga, gf = prim_arrays(G, GB, gp)
            M = np.linalg.inv(ibm[k]); P = np.c_[ga['POSITION'], np.ones(len(ga['POSITION']))] @ M.T
            Nn = ga['NORMAL'] @ M[:3, :3].T; Nn /= np.linalg.norm(Nn, axis=1, keepdims=True)
            n = len(P); J = np.zeros((n, 4), np.int64); J[:, 0] = k; W = np.zeros((n, 4)); W[:, 0] = 1
            parts.append(({'POSITION': P[:, :3], 'NORMAL': Nn, 'TEXCOORD_0': ga['TEXCOORD_0'], 'JOINTS_0': J, 'WEIGHTS_0': W}, gf))
    attrs, faces, off = {s: [] for s in ('POSITION', 'NORMAL', 'TEXCOORD_0', 'JOINTS_0', 'WEIGHTS_0')}, [], 0
    for a, f in parts:
        used = np.unique(f); remap = -np.ones(len(a['POSITION']), np.int64); remap[used] = np.arange(len(used)) + off
        for s in attrs:
            attrs[s].append(a[s][used])
        faces.append(remap[f]); off += len(used)
    A = {s: np.concatenate(x) for s, x in attrs.items()}; F = np.concatenate(faces)
    P = A['POSITION'].astype(np.float32)
    p['attributes'] = {
        'POSITION': put(P.tobytes(), 5126, 'VEC3', len(P), 34962, P.min(0).tolist(), P.max(0).tolist()),
        'NORMAL': put(A['NORMAL'].astype(np.float32).tobytes(), 5126, 'VEC3', len(P), 34962),
        'TEXCOORD_0': put(A['TEXCOORD_0'].astype(np.float32).tobytes(), 5126, 'VEC2', len(P), 34962),
        'JOINTS_0': put(A['JOINTS_0'].astype(np.uint16).tobytes(), 5123, 'VEC4', len(P), 34962),
        'WEIGHTS_0': put(A['WEIGHTS_0'].astype(np.float32).tobytes(), 5126, 'VEC4', len(P), 34962)}
    p['indices'] = put(F.astype(np.uint32).reshape(-1).tobytes(), 5125, 'SCALAR', F.size, 34963)
    print('VIEWERSWAP', name, 'gear kept', int(keepf.sum()), 'body', len(rf), 'total', len(F))
write_glb(outp, V, bytes(binary))
