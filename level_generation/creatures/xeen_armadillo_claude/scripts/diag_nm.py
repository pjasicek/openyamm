"""Print where part 0's non-manifold edges, boundary edges and degenerate faces are (rig_v1.blend)."""
import bpy, bmesh, os
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'rig_v1.blend'))
me = bpy.data.objects['Dillo'].data
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
pl = bm.faces.layers.int.get('part')
for e in bm.edges:
    n = len(e.link_faces)
    if n and e.link_faces[0][pl] == 0 and n != 2:
        fs = e.link_faces
        sets = [tuple(sorted(v.index for v in f.verts)) for f in fs]
        print('EDGE', n, [round(c, 3) for c in (e.verts[0].co + e.verts[1].co) / 2], 'len', round(e.calc_length(), 4),
              'dupfaces', len(sets) - len(set(sets)), 'areas', [round(f.calc_area() * 1e6, 1) for f in fs])
for f in bm.faces:
    if f[pl] == 0 and f.calc_area() < 1e-9:
        print('DEGEN', [round(c, 3) for c in f.calc_center_median()], [round(e.calc_length(), 5) for e in f.edges])
