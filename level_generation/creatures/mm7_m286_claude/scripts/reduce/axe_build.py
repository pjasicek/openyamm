#!/usr/bin/env python3
"""Reduced axe GLB from the source axe (work/mm7_m286_axe_source_pre_reduce.glb, node Sword, materials, variants and
images kept): LOD0 from a decimate_tex.py step (work/axe_dec/mesh_r<NN>.npz), optional new LOD1 from another step,
then the source LODs listed in AXE_KEEP_LODS (default 2,3: the source LOD2/LOD3, already coarser). Normals by angle
(AXE_ANGLE, default 0 degrees: the source is entirely flat-shaded, every corner normal equals its face normal, so the
kept grip keeps its exact normals and the reduced faces get the same faceted look; 30 smoothed the slightly tapered
blade plates and the band transitions, up to 17 degrees off the source on unchanged faces); vertices split per (position, UV, normal). Unreferenced
buffer data is compacted. Prints per LOD triangles and, for faces equal to source faces, the largest normal change.
Steps from AXE_DIR (default work/axe_dec) or as <dir>:<NN>. Usage: axe_build.py <out.glb> <lod0 step> [<lod1 step>]"""
import copy, math, os, struct, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[5] / 'tools')); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_actor_lods import read_glb, write_glb  # noqa: E402
import axe_glb  # noqa: E402
SRC = 'work/mm7_m286_axe_source_pre_reduce.glb'
ANG = math.cos(math.radians(float(os.environ.get('AXE_ANGLE', '0'))))


def by_angle(v, f, wuv):
    fn = np.cross(v[f[:, 1]] - v[f[:, 0]], v[f[:, 2]] - v[f[:, 0]]); area = np.linalg.norm(fn, axis=1)
    un = fn / np.maximum(area, 1e-12)[:, None]
    vf = [[] for _ in range(len(v))]
    for i, t in enumerate(f):
        for a in t:
            vf[a].append(i)
    P, N, U, idx, key = [], [], [], [], {}
    for i, t in enumerate(f):
        tri = []
        for k, a in enumerate(t):
            nb = [j for j in vf[a] if un[j] @ un[i] >= ANG - 1e-9]
            n = fn[nb].sum(0); n /= max(np.linalg.norm(n), 1e-12)
            uv = wuv[3 * i + k]
            kk = (int(a), round(float(uv[0]), 6), round(float(uv[1]), 6), *np.round(n, 4).tolist())
            if kk not in key:
                key[kk] = len(P); P.append(v[a]); N.append(n); U.append(uv)
            tri.append(key[kk])
        idx.append(tri)
    return np.array(P, np.float32), np.array(N, np.float32), np.array(U, np.float32), np.array(idx, np.uint32)


out = Path(sys.argv[1]); steps = sys.argv[2:]
doc, binary = read_glb(Path(SRC)); binary = bytearray(binary)
sdoc, sb, sbase = axe_glb.read(SRC)
P0, N0, UV0, F0 = axe_glb.prim(sdoc, sb, sbase, 0)
src_corner = {}
for t in F0:
    k = tuple(sorted(map(tuple, np.round(P0[t], 5))))
    src_corner[k] = {tuple(np.round(P0[a], 5)): N0[a] for a in t}


def add(arr, comp, typ, target=None):
    binary.extend(b'\0' * (-len(binary) % 4)); data = arr.tobytes()
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(data), **({'target': target} if target else {})})
    binary.extend(data)
    a = {'bufferView': len(doc['bufferViews']) - 1, 'componentType': comp, 'count': len(arr), 'type': typ}
    if typ == 'VEC3' and comp == 5126 and target == 34962 and arr is not None:
        a['min'] = arr.min(0).tolist(); a['max'] = arr.max(0).tolist()
    doc['accessors'].append(a); return len(doc['accessors']) - 1


meshes = []
for lod, nn in enumerate(steps):
    folder, nn = nn.split(':') if ':' in nn else (os.environ.get('AXE_DIR', 'work/axe_dec'), nn)
    d = np.load(f'{folder}/mesh_r{nn}.npz')
    P, N, U, I = by_angle(d['verts'], d['faces'], d['wuv'])
    m = copy.deepcopy(doc['meshes'][lod]); p = m['primitives'][0]
    p['attributes'] = {'POSITION': add(P, 5126, 'VEC3', 34962), 'NORMAL': add(N, 5126, 'VEC3', 34962),
                       'TEXCOORD_0': add(U, 5126, 'VEC2', 34962)}
    doc['accessors'][p['attributes']['POSITION']].update(min=P.min(0).tolist(), max=P.max(0).tolist())
    p['indices'] = add(I.ravel(), 5125, 'SCALAR', 34963)
    dev = []
    for t in I:
        k = tuple(sorted(map(tuple, np.round(P[t].astype(float), 5))))
        if k in src_corner:
            dev += [math.degrees(math.acos(np.clip(N[a] @ src_corner[k][tuple(np.round(P[a].astype(float), 5))], -1, 1))) for a in t]
    print(f'AXEBUILD LOD{lod} r{nn} tris {len(I)} verts {len(P)} source faces {len(dev) // 3} normal change max {max(dev or [0]):.1f} deg '
          f'p95 {np.percentile(dev, 95) if dev else 0:.1f}')
    meshes.append(m)
for i in [int(x) for x in os.environ.get('AXE_KEEP_LODS', '2,3').split(',') if x]:
    meshes.append(copy.deepcopy(doc['meshes'][i])); print('AXEBUILD kept source LOD', i, doc['accessors'][doc['meshes'][i]['primitives'][0]['indices']]['count'] // 3, 'tris')
meshes[0]['extras'] = dict(doc['meshes'][0].get('extras', {}), openyamm_lods=list(range(1, len(meshes))))
for m in meshes[1:]:
    m.pop('extras', None)
names = ['Sword'] + [f'Sword_LOD{k}' for k in range(1, len(meshes))]
for m, nm in zip(meshes, names):
    m['name'] = nm
doc['meshes'] = meshes
used = sorted({a for m in meshes for p in m['primitives'] for a in [*p['attributes'].values(), p['indices']]})
amap = {o: n for n, o in enumerate(used)}
views = sorted({doc['accessors'][a]['bufferView'] for a in used} | {im['bufferView'] for im in doc.get('images', []) if 'bufferView' in im})
vmap, nb, nv = {}, bytearray(), []
for n, o in enumerate(views):
    v = copy.deepcopy(doc['bufferViews'][o]); s = v.get('byteOffset', 0)
    nb.extend(b'\0' * (-len(nb) % 4)); v['byteOffset'] = len(nb); nb.extend(binary[s:s + v['byteLength']]); nv.append(v); vmap[o] = n
doc['accessors'] = [dict(doc['accessors'][o], bufferView=vmap[doc['accessors'][o]['bufferView']]) for o in used]
doc['bufferViews'] = nv
for im in doc.get('images', []):
    if 'bufferView' in im:
        im['bufferView'] = vmap[im['bufferView']]
for m in meshes:
    for p in m['primitives']:
        p['attributes'] = {k: amap[v] for k, v in p['attributes'].items()}; p['indices'] = amap[p['indices']]
write_glb(out, doc, bytes(nb))
print('AXEBUILD wrote', out, [doc['accessors'][m['primitives'][0]['indices']]['count'] // 3 for m in meshes], f'{len(nb) / 1e6:.2f} MB')
