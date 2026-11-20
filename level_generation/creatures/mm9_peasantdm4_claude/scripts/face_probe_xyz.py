"""Diagnostic: faces of 'Body' whose centre lies within R of a point (Blender rest frame), with normal, attributes, and
the angle of their normal against the mean of their edge neighbours (an inverted face reads ~180). Args (Blender):
<blend> <x,y,z> [r 0.02]"""
import bpy, bmesh, sys
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
P = Vector([float(t) for t in a[1].split(',')]); R = float(a[2]) if len(a) > 2 else 0.02
ob = bpy.data.objects['Body']; bm = bmesh.new(); bm.from_mesh(ob.data); bm.faces.ensure_lookup_table()
hl, kl = bm.faces.layers.int['head'], bm.faces.layers.int['hand']
for f in bm.faces:
    c = f.calc_center_median()
    if (c - P).length < R:
        nb = [g for e in f.edges for g in e.link_faces if g is not f]
        m = sum((g.normal for g in nb), Vector()) 
        ang = f.normal.angle(m) * 57.3 if m.length > 1e-9 else -1
        print('FACEXYZ', f.index, [round(t, 3) for t in c], [round(t, 2) for t in f.normal], 'head', f[hl], 'hand', f[kl],
              'nbrs', len(nb), 'angle_vs_nbrs', round(ang, 0), 'boundary_edges', sum(e.is_boundary for e in f.edges))
