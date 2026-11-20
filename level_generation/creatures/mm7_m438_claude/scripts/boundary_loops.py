"""Report the open boundary loops of each loose part (centre, size, edge count). Args: -- <parts blend>"""
import bpy, bmesh, sys, os
import numpy as np
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(sys.argv[sys.argv.index('--') + 1]))
for o in sorted([o for o in bpy.data.objects if o.type == 'MESH'], key=lambda o: o.name):
    bm = bmesh.new(); bm.from_mesh(o.data)
    be = [e for e in bm.edges if e.is_boundary]
    adj = {}
    for e in be:
        a, b = e.verts; adj.setdefault(a, []).append(b); adj.setdefault(b, []).append(a)
    seen = set()
    for v in adj:
        if v in seen: continue
        comp, st = [], [v]
        while st:
            x = st.pop()
            if x in seen: continue
            seen.add(x); comp.append(x); st.extend(adj[x])
        p = np.array([tuple(o.matrix_world @ x.co) for x in comp])
        print('LOOP', o.name, len(comp), 'centre', np.round(p.mean(0), 3).tolist(), 'extent', np.round(p.max(0) - p.min(0), 3).tolist())
    bm.free()
