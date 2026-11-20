"""Cloak cross-sections: per height, cloak vertex angles/radii vs leg/arm/torso extents (work/st1_vis.blend)."""
import bpy, os, sys, math
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'st1_vis.blend'))
O = {o.name: o for o in bpy.data.objects if o.type == 'MESH'}
def co(n): return np.array([tuple(o.matrix_world @ v.co) for o in [O[n]] for v in o.data.vertices])
C = co('P01'); body = {n: co(n) for n in ('P00', 'P02', 'P03', 'P04', 'P05', 'P06', 'P07')}
nrm = np.array([tuple(v.normal) for v in O['P01'].data.vertices])
for z in np.arange(0.10, 1.60, 0.08):
    s = C[np.abs(C[:, 2] - z) < 0.02]
    if not len(s): continue
    ang = np.degrees(np.arctan2(s[:, 0], s[:, 1]))  # 0 = back (+Y), +90 = his left (+X), 180 = front
    r = np.hypot(s[:, 0], s[:, 1])
    # front opening: angular gap around 180
    a = np.sort(np.mod(ang, 360)); gaps = np.diff(np.r_[a, a[0] + 360]); gi = gaps.argmax()
    line = f'z {z:.2f} n {len(s):4d} x[{s[:,0].min():+.3f},{s[:,0].max():+.3f}] y[{s[:,1].min():+.3f},{s[:,1].max():+.3f}] open {a[gi]:.0f}->{(a[gi]+gaps[gi])%360:.0f}'
    for n, b in body.items():
        bb = b[np.abs(b[:, 2] - z) < 0.02]
        if len(bb): line += f' | {n} x[{bb[:,0].min():+.3f},{bb[:,0].max():+.3f}] y[{bb[:,1].min():+.3f},{bb[:,1].max():+.3f}]'
    print(line)
# shell thickness: for cloak verts, ray inward along -normal to the other surface
from mathutils.bvhtree import BVHTree
from mathutils import Vector
me = O['P01'].data
tree = BVHTree.FromPolygons([v.co.copy() for v in me.vertices], [tuple(p.vertices) for p in me.polygons])
th = []
for v in me.vertices[::7]:
    h = tree.ray_cast(v.co - v.normal * 1e-4, -v.normal, 0.1)
    if h[0] is not None: th.append(h[3])
th = np.array(th); print('THICK n', len(th), 'pct', np.percentile(th, [5, 25, 50, 75, 95]).round(4))
