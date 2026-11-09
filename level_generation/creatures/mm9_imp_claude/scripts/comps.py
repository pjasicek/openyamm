import bpy, bmesh, sys
import numpy as np
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index('--') + 1])
o = bpy.data.objects['Body']; bm = bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table()
seen = set(); comps = []
for v in bm.verts:
    if v.index in seen: continue
    st = [v]; seen.add(v.index); c = []
    while st:
        x = st.pop(); c.append(x.index)
        for e in x.link_edges:
            y = e.other_vert(x)
            if y.index not in seen: seen.add(y.index); st.append(y)
    comps.append(c)
comps.sort(key=len, reverse=True)
P = np.array([tuple(v.co) for v in bm.verts])
print('NCOMP', len(comps), 'faces', len(bm.faces))
for i, c in enumerate(comps):
    Q = P[c]; print(i, len(c), np.round(Q.mean(0), 3), np.round(np.ptp(Q, 0), 3))
