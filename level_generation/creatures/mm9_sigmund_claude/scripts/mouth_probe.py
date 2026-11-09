"""Boundary edges and front profile around the mouth of the head shell. Args: <blend> <z0> <z1>"""
import bpy, bmesh, sys, numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0]); z0, z1 = float(a[1]), float(a[2])
me = bpy.data.objects['Body'].data; bm = bmesh.new(); bm.from_mesh(me)
hl = bm.faces.layers.int['head']
bv = sorted({v for e in bm.edges if e.is_boundary and any(f[hl] for f in e.link_faces) for v in e.verts
             if z0 < v.co.z < z1 and abs(v.co.x) < 0.04 and v.co.y < -0.05}, key=lambda v: v.co.x)
print('MOUTH boundary', len(bv), [tuple(round(c, 4) for c in v.co) for v in bv][:40])
co = np.array([v.co[:] for v in bm.verts])
for z in np.arange(z0, z1, 0.003):
    m = (np.abs(co[:, 2] - z) < 0.0015) & (np.abs(co[:, 0]) < 0.004) & (co[:, 1] < -0.05)
    print('MOUTH z %.4f front_y %s' % (z, round(float(co[m, 1].min()), 4) if m.any() else '-'))
