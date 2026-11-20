import bpy, bmesh, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
me = bpy.data.objects['Body'].data
bm = bmesh.new(); bm.from_mesh(me)
lay = bm.faces.layers.int['part']
seen = set(); out = []
for e in [e for e in bm.edges if e.is_boundary]:
    if e in seen: continue
    st = [e]; seen.add(e); cur = []
    while st:
        x = st.pop(); cur.append(x)
        for v in x.verts:
            for y in v.link_edges:
                if y.is_boundary and y not in seen: seen.add(y); st.append(y)
    q = np.array([v.co[:] for e_ in cur for v in e_.verts])
    out.append((len(cur), cur[0].link_faces[0][lay], np.round(q.mean(0), 3).tolist(), np.round(np.ptp(q, axis=0), 3).tolist()))
for x in sorted(out, key=lambda t: -t[0]): print('LOOP', x)
print('LOOP nonman', sum(1 for e in bm.edges if len(e.link_faces) > 2), 'tris', len(bm.faces))
