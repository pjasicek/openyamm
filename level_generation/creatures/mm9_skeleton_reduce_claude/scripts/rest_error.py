#!/usr/bin/env python3
"""Rest-pose two-way distance per decimation group (candidate vertices to the source group's surface and source
vertices to the candidate group's surface, exact point-triangle distance through pymeshlab's Hausdorff filter).
Usage: rest_error.py <tag> [top N]"""
import json, sys
import numpy as np
import pymeshlab as ml
tag = sys.argv[1]; top = int(sys.argv[2]) if len(sys.argv) > 2 else 15
s = np.load('work/mesh_in.npz'); c = np.load(f'work/mesh_r{tag}.npz')
G = np.load('work/groups.npy'); plan = json.load(open('work/group_plan.json'))
rows = []


def mesh(v, f):
    u, inv = np.unique(f, return_inverse=True)
    return ml.Mesh(v[u], inv.reshape(-1, 3).astype(np.int32))



for g, (r, cat, n) in plan.items():
    g = int(g); sf = s['faces'][G == g]; cf = c['faces'][c['group'] == g]
    if len(cf) == 0:
        continue
    ms = ml.MeshSet()
    ms.add_mesh(mesh(s['verts'], sf)); ms.add_mesh(mesh(c['verts'], cf))
    a = ms.get_hausdorff_distance(sampledmesh=1, targetmesh=0, samplevert=True, sampleface=True, samplenum=2000)
    b = ms.get_hausdorff_distance(sampledmesh=0, targetmesh=1, samplevert=True, sampleface=True, samplenum=2000)
    rows.append((max(a['max'], b['max']) * 1000, a['mean'] * 1000, b['mean'] * 1000, g, cat, n, len(cf)))
rows.sort(reverse=True)
print('group cat faces->out  max mm  mean cand->src  mean src->cand')
for m, a, b, g, cat, n, k in rows[:top]:
    print(f'g{g:3d} {cat:6s} {n:4d}->{k:4d}  {m:6.2f}  {a:5.2f}  {b:5.2f}')
print('ALL max p50 %.2f p90 %.2f' % tuple(np.percentile([r[0] for r in rows], [50, 90])))
