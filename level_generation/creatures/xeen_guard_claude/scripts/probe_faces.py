"""Report suspicious faces of work/clean_v1.blend: high aspect, boundary edges, non-manifold edges, spike vertices."""
import bpy, bmesh, os
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'clean_v1.blend'))
ob = bpy.data.objects['Guard']
bm = bmesh.new(); bm.from_mesh(ob.data)
for f in bm.faces:
    vs = [v.co for v in f.verts]
    e = max((vs[i] - vs[(i + 1) % len(vs)]).length for i in range(len(vs)))
    a = f.calc_area()
    asp = e * e / (2 * a + 1e-12)
    if asp > 5 and e > 0.03:
        c = f.calc_center_median()
        print('ASPECT', round(asp, 1), 'edge', round(e, 3), 'at', [round(x, 3) for x in c])
for e in bm.edges:
    if e.is_boundary:
        c = (e.verts[0].co + e.verts[1].co) / 2
        print('BOUNDARY at', [round(x, 3) for x in c])
    elif not e.is_manifold:
        c = (e.verts[0].co + e.verts[1].co) / 2
        print('NONMANIFOLD at', [round(x, 3) for x in c], len(e.link_faces))
