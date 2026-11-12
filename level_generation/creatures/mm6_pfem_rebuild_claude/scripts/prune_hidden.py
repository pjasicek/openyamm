"""Delete faces of the chosen parts that no view can reach (after mm6_gua_rebuild_claude/scripts/prune_hidden.py): rays from 0.4 mm above the
face centroid along 96 hemisphere directions; hidden when every ray meets another face within REACH. Here: the v3 skull skin under the hair shell.
Args: <in npz> <out npz> <part,part> [reach]"""
import bpy, sys, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, PARTS = a[:3]; REACH = float(a[3]) if len(a) > 3 else 0.5
D = dict(np.load(IN)); co, tri, comp = D['co'], D['tri'], D['comp']; names = [str(x) for x in D['names']]
sel = np.isin(comp[tri[:, 0]], [names.index(p) for p in PARTS.split(',')])
tree = BVHTree.FromPolygons([tuple(map(float, p)) for p in co], [tuple(map(int, t)) for t in tri])
k = np.arange(96) + 0.5; th = np.arccos(1 - k / 96); ph = math.pi * (1 + 5 ** 0.5) * k
Dd = np.c_[np.sin(th) * np.cos(ph), np.sin(th) * np.sin(ph), np.cos(th)]
hidden = np.zeros(len(tri), bool)
for fi in np.where(sel)[0]:
    p = co[tri[fi]]; n = np.cross(p[1] - p[0], p[2] - p[0]); ln = np.linalg.norm(n)
    if ln < 1e-12: continue
    n = Vector(n / ln); c = Vector(p.mean(0)) + n * 0.0004
    t = n.orthogonal().normalized(); b = n.cross(t); seen = False
    for d in Dd:
        hit = tree.ray_cast(c, t * d[0] + b * d[1] + n * d[2], REACH)
        if hit[0] is None or hit[2] == fi: seen = True; break
    if not seen: hidden[fi] = True
keep = ~hidden; t2 = tri[keep]; used, inv = np.unique(t2.ravel(), return_inverse=True)
D['co'] = co[used]; D['co_up'] = D['co_up'][used]; D['comp'] = comp[used]; D['tri'] = inv.reshape(-1, 3)
np.savez(OUT, **D)
print('PRUNE hidden', int(hidden.sum()), 'of', int(sel.sum()), 'tris now', len(t2))
