"""Keep inner cloth layers inside after the body fit (PeasantM5, 2026-11-02): the fit moved the shirt skirt in onto MM9's hips
faster than the trouser top and inner folds hidden behind it, which then poked through (clay `review/clay_fit_final.png`).
For every vertex that is hidden in the ORIGINAL master (its normal ray meets an own face within 3 cm; that face and the gap t0
are recorded), after the fit the vertex is kept at least c = min(t0, CLEAR) behind the recorded face's plane (fitted
positions): moved along the face normal only when it is closer or outside. 3 passes, then 3 smoothing passes of the
corrections over the corrected vertices. Positions only.
Args: -- <original blend> <fitted blend> <out blend> [CLEAR 0.004]"""
import bpy, bmesh, sys, json
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
ORIG, FIT, OUT = a[:3]; CLEAR = float(a[3]) if len(a) > 3 else 0.004
bpy.ops.wm.open_mainfile(filepath=ORIG)
me = bpy.data.objects['Body'].data
co0 = np.array([v.co[:] for v in me.vertices]); n0 = np.array([v.normal[:] for v in me.vertices])
polys = [list(p.vertices) for p in me.polygons]
own = BVHTree.FromPolygons([Vector(x) for x in co0], polys)
rec = {}
for i in range(len(co0)):
    n = Vector(n0[i])
    if n.length < 0.5: continue
    hit = own.ray_cast(Vector(co0[i]) + n * 0.001, n, 0.03)
    if hit[0] is not None and i not in polys[hit[2]]:
        rec[i] = (hit[2], hit[3] + 0.001)
bpy.ops.wm.open_mainfile(filepath=FIT)
o = bpy.data.objects['Body']; me = o.data
co = np.array([v.co[:] for v in me.vertices]); start = co.copy()
def plane(fi):
    P = co[polys[fi]]; c = P.mean(0)
    n = np.cross(P[1] - P[0], P[2] - P[0]); n /= np.linalg.norm(n) + 1e-12
    return c, n
fixed = set()
for _ in range(3):
    for i, (fi, t0) in rec.items():
        c, n = plane(fi)
        need = min(t0, CLEAR)
        s = float(np.dot(co[i] - c, n))       # face normal points outward: hidden vertex should have s <= -need
        if s > -need:
            co[i] -= (s + need) * n; fixed.add(i)
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
corr = co - start; fx = np.array(sorted(fixed), int)
for _ in range(3):
    nc = corr.copy()
    for i in fx:
        js = [e.other_vert(bm.verts[i]).index for e in bm.verts[i].link_edges]
        js = [j for j in js if j in fixed]
        if js: nc[i] = 0.5 * corr[i] + 0.5 * np.mean([corr[i]] + [corr[j] for j in js], 0)
        nc[i] = nc[i] if np.linalg.norm(nc[i]) >= np.linalg.norm(corr[i]) * 0.999 else corr[i]
    corr = nc
co = start + corr
for v in me.vertices: v.co = Vector(co[v.index])
me.update(); bpy.ops.wm.save_as_mainfile(filepath=OUT)
m = np.linalg.norm(corr, axis=1)
r = dict(hidden=len(rec), corrected=len(fixed), corr_max_mm=float(m.max() * 1000), corr_p90_mm=float(np.percentile(m[fx], 90) * 1000) if len(fx) else 0)
print('LAYER_KEEP', r)
