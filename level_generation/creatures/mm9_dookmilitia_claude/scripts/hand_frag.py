import bpy, bmesh, sys
import numpy as np
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index('--') + 1])
o = bpy.data.objects['Body']; bm = bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table()
seen = set()
for v in bm.verts:
    if v.index in seen: continue
    st = [v]; seen.add(v.index); c = []
    while st:
        x = st.pop(); c.append(x)
        for e in x.link_edges:
            y = e.other_vert(x)
            if y.index not in seen: seen.add(y.index); st.append(y)
    q = np.array([x.co[:] for x in c])
    print('COMP', len(c), q.min(0).round(3), q.max(0).round(3))
