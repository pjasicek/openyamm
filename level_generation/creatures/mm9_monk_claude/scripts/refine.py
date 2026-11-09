"""Edge rings where the rig bends: elbows (four rings across the sleeve) and the lower robe (rows). Args: <in npz> <out npz>"""
import bpy, bmesh, sys
import numpy as np
from mathutils import Vector
IN, OUT = sys.argv[sys.argv.index('--') + 1:]
D = dict(np.load(IN)); co, tri, comp = D['co'], D['tri'], D['comp']; names = [str(x) for x in D['names']]
sh, wr, ax = D['sh'], D['wr'], D['ax']
L = np.linalg.norm(wr - sh); el = sh + ax * 0.26
k = names.index('robe'); bpy.ops.wm.read_factory_settings(use_empty=True)
v = np.where(comp == k)[0]; rem = -np.ones(len(co), int); rem[v] = np.arange(len(v)); t = rem[tri[comp[tri[:, 0]] == k]]
bm = bmesh.new(); vs = [bm.verts.new(p) for p in co[v].tolist()]
for f in t.tolist():
    try: bm.faces.new([vs[i] for i in f])
    except ValueError: pass
bm.normal_update()
def cut(pt, n, cond=None):
    fs = [f for f in bm.faces if cond is None or cond(f.calc_center_median())]
    g = list({x for f in fs for x in f.verts}) + list({e for f in fs for e in f.edges}) + fs
    bmesh.ops.bisect_plane(bm, geom=g, plane_co=pt, plane_no=n, dist=1e-4)
for z in np.arange(-0.84, 0.16, 0.11): cut((0, 0, float(z)), (0, 0, 1), lambda c: c.z < 0.19 and abs(c.x) < 0.34)
for s in (1, -1):
    a = ax * [s, 1, 1]; e = el * [s, 1, 1]
    for d in (-0.075, -0.03, 0.03, 0.075): cut(Vector(e + a * d), Vector(a), lambda c: c.x * s > 0.22)
bm.normal_update()
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
vv = np.array([x.co[:] for x in bm.verts]); bm.verts.index_update()
tt = np.array([[x.index for x in f.verts] for f in bm.faces])
print('REFINE robe', len(t), '->', len(tt))
keep = comp != k; rem2 = -np.ones(len(co), int); rem2[keep] = np.arange(keep.sum()) + len(vv)
ot = rem2[tri[comp[tri[:, 0]] != k]]
D['co'] = np.vstack([vv, co[keep]]); D['tri'] = np.vstack([tt, ot]); D['comp'] = np.r_[np.full(len(vv), k), comp[keep]]
np.savez(OUT, **D); print('SAVED', len(D['co']), len(D['tri']))
