"""Measure the mouth frame on the outer skin of work/clean_v1.blend: plane fit to the outer palm skin in an annulus
around the Meshy lips -> normal n (outward), O (mouth centre on the plane), U (along the slit, ~+X), V (~+Z);
palm thickness along -n from O; prints skin heights over the ellipse grid. Writes work/mouth_frame.json."""
import bpy, os, json
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'clean_v1.blend'))
ob = bpy.data.objects['Hand']; me = ob.data
hid = np.zeros(len(me.polygons), np.int32); me.attributes['hidden'].data.foreach_get('value', hid)
pc = np.zeros(len(me.polygons), np.int32); me.attributes['piece'].data.foreach_get('value', pc)
cen = np.array([tuple(p.center) for p in me.polygons]); nrm = np.array([tuple(p.normal) for p in me.polygons])
area = np.array([p.area for p in me.polygons])
M = np.array([-0.001, -0.023, 0.164])
d = cen - M
r = np.hypot(d[:, 0] / 1.0, d[:, 2] / 0.75)
sel = (hid == 0) & (pc == 0) & (r > 0.11) & (r < 0.16) & (nrm[:, 1] < -0.3)
P = cen[sel]; W = area[sel]
c = (P * W[:, None]).sum(0) / W.sum()
u, s, vt = np.linalg.svd((P - c) * np.sqrt(W)[:, None], full_matrices=False)
n = vt[2]
if n[1] > 0: n = -n
U = np.array([1.0, 0, 0]); U = U - n * (U @ n); U /= np.linalg.norm(U)
V = np.cross(n, U)
if V[2] < 0: V = -V
O = M - n * ((M - c) @ n)
print('FRAME n', np.round(n, 3).tolist(), 'O', np.round(O, 4).tolist(), 'U', np.round(U, 3).tolist(),
      'V', np.round(V, 3).tolist(), 'annulus faces', int(sel.sum()), 'plane rms', round(float(s[2] / np.sqrt(W.sum())), 4))
# outer skin BVH (piece 0, not hidden)
import bmesh
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
bmesh.ops.delete(bm, geom=[f for f in bm.faces if hid[f.index] or pc[f.index]], context='FACES')
bvh = BVHTree.FromBMesh(bm)
On, nn = Vector(O.tolist()), Vector(n.tolist())
hit = bvh.ray_cast(On - nn * 0.01, -nn, 1.0)
back = (hit[3] if hit[0] else None)
print('THICKNESS behind O (m)', None if back is None else round(back + 0.01, 4))
for vv in (0.08, 0.06, 0.04, 0.0, -0.04, -0.06, -0.08):
    row = []
    for uu in (-0.12, -0.09, -0.06, -0.03, 0, 0.03, 0.06, 0.09, 0.12):
        p = On + Vector(U.tolist()) * uu + Vector(V.tolist()) * vv + nn * 0.2
        h = bvh.ray_cast(p, -nn, 0.5)
        row.append('  --  ' if h[0] is None else f'{(h[0] - On).dot(nn):+.3f}')
    print(f'HEIGHT v={vv:+.2f}', ' '.join(row))
json.dump({'O': O.tolist(), 'n': n.tolist(), 'U': U.tolist(), 'V': V.tolist(), 'thickness': back},
          open(os.path.join(HERE, 'work', 'mouth_frame.json'), 'w'), indent=1)
