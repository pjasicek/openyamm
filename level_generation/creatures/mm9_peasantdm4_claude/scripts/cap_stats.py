"""Diagnostic: the cap's loose part (head faces connected to the highest head vertex): vertex height histogram and the
horizontal centre of rings (Blender rest). Args (Blender): <blend>"""
import bpy, bmesh, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
ob = bpy.data.objects['Body']; bm = bmesh.new(); bm.from_mesh(ob.data); bm.verts.ensure_lookup_table()
hl = bm.faces.layers.int.get('head')
hv = [v for f in bm.faces if f[hl] == 1 for v in f.verts]
top = max(hv, key=lambda v: v.co.z)
part = set(); st = [top]
while st:
    v = st.pop()
    if v in part: continue
    part.add(v); st += [e.other_vert(v) for e in v.link_edges]
P = np.array([v.co[:] for v in part])
print('CAPSTAT n', len(P), 'z', P[:, 2].min().round(3), P[:, 2].max().round(3))
for z0 in np.arange(0.455, 0.62, 0.01):
    m = (P[:, 2] >= z0) & (P[:, 2] < z0 + 0.01)
    if m.any():
        q = P[m]; c = q[:, :2].mean(0); r = np.linalg.norm(q[:, :2] - c, axis=1)
        print('CAPSTAT z %.3f n %3d centre %s r mean %.3f max %.3f xext %.3f yext %.3f' % (z0, m.sum(), c.round(3), r.mean(), r.max(), np.ptp(q[:, 0]), np.ptp(q[:, 1])))
