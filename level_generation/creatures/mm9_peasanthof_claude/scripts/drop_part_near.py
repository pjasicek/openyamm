"""Delete the loose parts of 'Body' whose bbox centre lies within 1 cm of the given points (MM9 frame).
Args: <in blend> <out blend> x,y,z[;x,y,z...]"""
import bpy, bmesh, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
ob = bpy.data.objects['Body']; me = ob.data
pts = [np.array([float(t) for t in q.split(',')]) for q in a[2].split(';') if q]
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
    co = np.array([tuple(ob.matrix_world @ x.co) for x in comp]); c = 0.5 * (co.min(0) + co.max(0))
    if any(np.linalg.norm(c - p) < 0.01 for p in pts):
        drop += comp; print('DROPPART', len(comp), np.round(c, 4).tolist())
bmesh.ops.delete(bm, geom=drop, context='VERTS')
bm.to_mesh(me); me.update()
bpy.ops.wm.save_as_mainfile(filepath=a[1])
