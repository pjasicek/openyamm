"""Rest-pose geometry error of a decimated mesh (work/mesh_r<NN>.npz) against the source (work/mesh_in.npz): distance
from each source vertex to the candidate surface, p99/max per region (work/groups.npy majority) and the worst spots.
Usage: blender -b -P rest_error.py -- <NN>"""
import os, sys, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
tag = sys.argv[sys.argv.index('--') + 1]
s = np.load(os.path.join(HERE, 'work', 'mesh_in.npz')); c = np.load(os.path.join(HERE, 'work', f'mesh_r{tag}.npz'))
g = np.load(os.path.join(HERE, 'work', 'groups.npy')); keep = np.load(os.path.join(HERE, 'work', 'keep_base.npy'))
tree = BVHTree.FromPolygons([Vector(p) for p in c['verts'].tolist()], c['faces'].tolist())
sv, sf = s['verts'], s['faces']
vg = np.full(len(sv), -1)
for k in range(3):
    vg[sf[:, k]] = np.where(keep, 99, g)
dist = np.array([(tree.find_nearest(Vector(p))[0] - Vector(p)).length for p in sv.tolist()]) * 1000
names = {0: 'rest', 1: 'face', 2: 'hair', 3: 'R hand', 4: 'L hand', 5: 'gown', 6: 'cape', 7: 'body skin', 8: 'hidden', 9: 'legs', 99: 'kept'}
for k in sorted(set(vg.tolist())):
    x = dist[vg == k]
    if len(x):
        print(f"REST {names.get(k, k):10s} n {len(x):5d} p99 {np.percentile(x, 99):6.2f} max {x.max():6.1f} at {np.round(sv[vg == k][x.argmax()], 3).tolist()}")
o = np.argsort(-dist)[:12]
print('WORST', [(round(float(dist[i]), 1), names.get(int(vg[i])), np.round(sv[i], 2).tolist()) for i in o])
