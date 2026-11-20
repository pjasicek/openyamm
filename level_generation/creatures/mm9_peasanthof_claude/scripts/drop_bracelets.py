"""Drop Meshy's wrist bracelets (loose rings at the wrists, crumpled by the reduction; the designs paint their own wrist
band, bracelet or cuff over the graft ring instead, as PeasantDM1's wrist band). Rule: loose parts whose centre is at
|x| > 0.38 m with a bbox diagonal < 0.09 m and no grafted-hand faces. Args: <in blend> <out blend>"""
import bpy, bmesh, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
ob = bpy.data.objects['Body']; me = ob.data
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
lh = bm.faces.layers.int.get('hand')
seen = set(); drop = []
for v in bm.verts:
    if v.index in seen: continue
    st = [v]; comp = []; seen.add(v.index)
    while st:
        x = st.pop(); comp.append(x)
        for e in x.link_edges:
            o = e.other_vert(x)
            if o.index not in seen: seen.add(o.index); st.append(o)
    co = np.array([tuple(x.co) for x in comp]); c = 0.5 * (co.min(0) + co.max(0)); dg = np.linalg.norm(co.max(0) - co.min(0))
    hand = lh is not None and any(f[lh] for x in comp for f in x.link_faces)
    if abs(c[0]) > 0.6 and dg < 0.13 and not hand:  # HOF: cords at x 0.71, diag 0.11
        drop += comp; print('DROP', len(comp), round(float(dg), 3), np.round(c, 3).tolist())
bmesh.ops.delete(bm, geom=drop, context='VERTS')
bm.to_mesh(me); me.update()
print('BRACELETS dropped verts', len(drop), 'tris', sum(len(p.vertices) - 2 for p in me.polygons))
bpy.ops.wm.save_as_mainfile(filepath=a[1])
