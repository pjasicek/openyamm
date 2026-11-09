"""Rest-pose surface error per beholder group (m166_groups.py labels) for ladder steps: source vertices -> candidate
surface and candidate vertices -> source surface (exact, BVH). Usage: blender -b -P err_groups.py -- r50 [r45 ...]"""
import sys
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
NAMES = {0: 'head', 1: 'tentacles', 2: 'stalks', 3: 'teeth', 4: 'tongue', -1: 'eyes kept'}
d = np.load('work/mesh_in.npz'); groups = np.load('work/groups.npy'); keep = np.load('work/keep_eyes.npy')
lab = np.where(keep, -1, groups); sv, sf = d['verts'], d['faces']
vlab = np.full(len(sv), -9); vlab[sf[:, 0]] = lab; vlab[sf[:, 1]] = lab; vlab[sf[:, 2]] = lab
bvh = lambda v, f: BVHTree.FromPolygons([Vector(x) for x in v.tolist()], f.tolist())
stree = bvh(sv, sf)
for tag in sys.argv[sys.argv.index('--') + 1:]:
    c = np.load(f'work/mesh_{tag}.npz'); cv, cf = c['verts'], c['faces']; ctree = bvh(cv, cf)
    d1 = np.array([ctree.find_nearest(Vector(p))[3] for p in sv.tolist()])
    r2 = [stree.find_nearest(Vector(p)) for p in cv.tolist()]
    d2 = np.array([r[3] for r in r2]); near = lab[np.array([r[2] for r in r2])]
    print('ERR', tag, len(cf), 'faces')
    for g, name in NAMES.items():
        a, b = d1[vlab == g], d2[near == g]
        print(f'ERR  {name:10s} src->cand p99 {np.percentile(a, 99)*1000:5.2f} max {a.max()*1000:5.2f}   '
              f'cand->src p99 {np.percentile(b, 99)*1000:5.2f} max {b.max()*1000:5.2f}   faces {int((c["group"] == g).sum())}')
