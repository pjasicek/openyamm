"""Drop Meshy's jewellery pieces from 'Body' (design 1's necklace collar, beads, pendant and the two bust brooches: the
four MM9 designs paint different jewellery on one shared body, so it is paint, as in MM9) and specks.
Rule: loose parts with <= 125 vertices, bbox diagonal <= 0.1 m, centre height 0.18..0.40 m (between bust and chin), the collar ring (<= 200 vertices, centred, 0.30..0.35 m), or
any part with <= 4 vertices. Eyes (0.436 m) and wrist bracelets (|x| > 0.4) stay. Args: <in blend> <out blend>"""
import bpy, bmesh, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
ob = bpy.data.objects['Body']; me = ob.data
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
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
    collar = len(comp) <= 200 and dg <= 0.22 and 0.30 <= c[2] <= 0.35 and abs(c[0]) < 0.02   # the necklace's collar ring
    if collar or len(comp) <= 4 or (len(comp) <= 125 and dg <= 0.1 and 0.18 <= c[2] <= 0.40):
        drop += comp; print('DROP', len(comp), round(float(dg), 3), np.round(c, 3).tolist())
bmesh.ops.delete(bm, geom=drop, context='VERTS')
bm.to_mesh(me); me.update()
print('TRINKETS dropped verts', len(drop), 'left', len(me.vertices))
bpy.ops.wm.save_as_mainfile(filepath=a[1])
