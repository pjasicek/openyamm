#!/usr/bin/env python3
"""Texture-aware reduction of the held severed forearm (work/mm7_m438_forearm_source_pre_reduce.glb, node 'Sword'; prop
space: +Y along the forearm toward the elbow wound, origin at the grip centre, the severed wrist at y = -0.04).
Weld exact duplicates (the source is smooth: one normal per position), then decimate only the severed hand beyond the
fist (y < Y_HAND, default -0.10: palm, back and the limp fingers) with MeshLab's texture-aware collapse, boundary kept;
the fist zone, the forearm, the ragged wound cap and both bone shafts are kept exactly. Source vertices keep their
normals, new vertices take area-weighted smooth normals of the reduced surface. Each ratio is written into a copy of
the source GLB (LOD0 primitive replaced; LOD1-3, materials, variants and images unchanged, buffer compacted) as
work/forearm_r<NN>.glb, with the two-way surface distance (mm, pymeshlab Hausdorff) printed.
Usage (venv with pymeshlab): prop_reduce.py <ratio,...> [Y_HAND]"""
import copy, os, sys
from pathlib import Path
import numpy as np
import pymeshlab as ml
HERE = Path(__file__).resolve().parents[1]; REPO = HERE.parents[2]
sys.path.insert(0, str(REPO / 'tools')); sys.path.insert(0, str(Path(__file__).resolve().parent))
import merge_head_material as M  # noqa: E402
from prop_ladder_io import write_obj, read_obj  # noqa: E402

ratios = [float(r) for r in sys.argv[1].split(',')]; YH = float(sys.argv[2]) if len(sys.argv) > 2 else -0.10
SRC = HERE / 'work/mm7_m438_forearm_source_pre_reduce.glb'
doc, binary = M.read_glb(SRC)
prim = doc['meshes'][0]['primitives'][0]; A = prim['attributes']
P = M.accessor_array(doc, binary, A['POSITION']); N = M.accessor_array(doc, binary, A['NORMAL'])
UV = M.accessor_array(doc, binary, A['TEXCOORD_0']); I = M.accessor_array(doc, binary, prim['indices']).reshape(-1, 3)
key, first, inv = np.unique(np.round(P, 7), axis=0, return_index=True, return_inverse=True); inv = inv.ravel()
V = P[first]; VN = N[first]; F = inv[I]; W = UV[I]                      # welded positions, wedge UVs per corner
cen = V[F].mean(1); hand = cen[:, 1] < YH
tmp = HERE / 'work/obj'; tmp.mkdir(exist_ok=True)
used = np.unique(F[hand]); remap = -np.ones(len(V), int); remap[used] = np.arange(len(used))
write_obj(str(tmp / 'hand.obj'), V[used], remap[F[hand]], W[hand].reshape(-1, 2))
write_obj(str(tmp / 'src.obj'), V, F, W.reshape(-1, 2))
H = float(np.ptp(V, axis=0).max())
np.savez(HERE / 'work/mesh_prop_src.npz', verts=V, faces=F, wuv=W.reshape(-1, 2))
print('PROP', len(F), 'faces; hand (y <', YH, ')', int(hand.sum()), 'decimated, kept', int((~hand).sum()), 'longest', round(H, 3))


def normals(v, f):
    n = np.zeros_like(v); fn = np.cross(v[f[:, 1]] - v[f[:, 0]], v[f[:, 2]] - v[f[:, 0]])
    for k in range(3):
        np.add.at(n, f[:, k], fn)
    return n / (np.linalg.norm(n, axis=1, keepdims=True) + 1e-12)


for r in ratios:
    ms = ml.MeshSet(); ms.load_new_mesh(str(tmp / 'hand.obj'))
    ms.meshing_decimation_quadric_edge_collapse_with_texture(targetfacenum=int(hand.sum() * r), qualitythr=.3, extratcoordw=1.0,
        preserveboundary=True, boundaryweight=10.0, optimalplacement=True, preservenormal=True)
    ms.save_current_mesh(str(tmp / 'out.obj'), save_textures=False)
    hv, hf, hw = read_obj(str(tmp / 'out.obj'))
    # weld back onto the source positions (boundary vertices are preserved exactly)
    from scipy.spatial import cKDTree
    dist, near = cKDTree(V).query(hv)
    vid = np.where(dist < 1e-7, near, len(V) + np.arange(len(hv)))
    allv = np.concatenate([V, hv]); nf = np.concatenate([F[~hand], vid[hf]]); nw = np.concatenate([W[~hand], hw.reshape(-1, 3, 2)])
    keepv = np.unique(nf); m2 = -np.ones(len(allv), int); m2[keepv] = np.arange(len(keepv))
    nv, nf = allv[keepv], m2[nf]
    nn = normals(nv, nf); src = keepv < len(V); nn[src] = VN[keepv[src]]
    # glTF vertices: unique (position, uv) per corner
    corner = np.concatenate([nf.reshape(-1, 1), np.round(nw.reshape(-1, 2), 7)], axis=1)
    ukey, cfirst, cinv = np.unique(corner, axis=0, return_index=True, return_inverse=True); cinv = cinv.ravel()
    vi = nf.reshape(-1)[cfirst]
    gp, gn, gu = nv[vi].astype(np.float32), nn[vi].astype(np.float32), nw.reshape(-1, 2)[cfirst].astype(np.float32)
    gi = cinv.astype(np.uint16 if len(gp) < 65536 else np.uint32)
    write_obj(str(tmp / 'red.obj'), nv, nf, nw.reshape(-1, 2))
    np.savez(HERE / f'work/mesh_prop_r{int(round(r * 100))}.npz', verts=nv, faces=nf, wuv=nw.reshape(-1, 2))
    ms = ml.MeshSet(); ms.load_new_mesh(str(tmp / 'src.obj')); ms.load_new_mesh(str(tmp / 'red.obj'))
    a = ms.get_hausdorff_distance(sampledmesh=1, targetmesh=0, samplevert=True, sampleface=True, samplenum=30000)
    b = ms.get_hausdorff_distance(sampledmesh=0, targetmesh=1, samplevert=True, sampleface=True, samplenum=30000)
    d2, b2 = copy.deepcopy(doc), bytearray(binary)
    p2 = d2['meshes'][0]['primitives'][0]
    p2['attributes'] = {'POSITION': M.append_accessor(d2, b2, gp, doc['accessors'][A['POSITION']], 34962),
                        'NORMAL': M.append_accessor(d2, b2, gn, doc['accessors'][A['NORMAL']], 34962),
                        'TEXCOORD_0': M.append_accessor(d2, b2, gu, doc['accessors'][A['TEXCOORD_0']], 34962)}
    p2['indices'] = M.append_accessor(d2, b2, gi, dict(doc['accessors'][prim['indices']],
                                      componentType=5123 if gi.dtype == np.uint16 else 5125), 34963)
    # compact: drop the old LOD0 accessors/views
    used_acc = sorted({i for m in d2['meshes'] for p in m['primitives'] for i in list(p['attributes'].values()) + [p['indices']]})
    views = sorted({d2['accessors'][i]['bufferView'] for i in used_acc} | {im['bufferView'] for im in d2.get('images', []) if 'bufferView' in im})
    vmap, packed, nviews = {}, bytearray(), []
    for k, o in enumerate(views):
        v = copy.deepcopy(d2['bufferViews'][o]); s = v.get('byteOffset', 0)
        packed.extend(b'\0' * (-len(packed) % 4)); v['byteOffset'] = len(packed)
        packed.extend(b2[s:s + v['byteLength']]); nviews.append(v); vmap[o] = k
    amap = {o: k for k, o in enumerate(used_acc)}
    d2['accessors'] = [dict(d2['accessors'][o], bufferView=vmap[d2['accessors'][o]['bufferView']]) for o in used_acc]
    d2['bufferViews'] = nviews
    for im in d2.get('images', []):
        if 'bufferView' in im:
            im['bufferView'] = vmap[im['bufferView']]
    for m in d2['meshes']:
        for p in m['primitives']:
            p['attributes'] = {k: amap[v] for k, v in p['attributes'].items()}; p['indices'] = amap[p['indices']]
    out = HERE / f'work/forearm_r{int(round(r * 100))}.glb'
    M.write_glb(out, d2, packed)
    print(f'PROPRED r{int(round(r * 100))} {len(F)} -> {len(nf)} tris, {len(gp)} verts; two-way max {max(a["max"], b["max"]) * 1000:.2f} mm '
          f'mean {max(a["mean"], b["mean"]) * 1000:.3f} mm; bounds dev {np.abs(np.concatenate([gp.min(0) - P.min(0), gp.max(0) - P.max(0)])).max() * 1000:.2f} mm -> {out.name}')
