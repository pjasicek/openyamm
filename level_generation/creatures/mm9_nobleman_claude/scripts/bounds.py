"""Open boundary loops per part. Args: <blend>"""
import bpy, bmesh, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
b = bpy.data.objects['Body']; bm = bmesh.new(); bm.from_mesh(b.data); lay = bm.faces.layers.int['part']
seen = set(); comps = []
for e in [e for e in bm.edges if e.is_boundary]:
    if e in seen: continue
    st = [e]; seen.add(e); cur = []
    while st:
        x = st.pop(); cur.append(x)
        for v in x.verts:
            for y in v.link_edges:
                if y.is_boundary and y not in seen: seen.add(y); st.append(y)
    comps.append(cur)
for c in sorted(comps, key=len, reverse=True)[:24]:
    q = np.array([v.co[:] for e in c for v in e.verts]); pp = {e.link_faces[0][lay] for e in c}
    print('BND', len(c), pp, q.min(0).round(3).tolist(), q.max(0).round(3).tolist())
print('BND total', sum(len(c) for c in comps), 'over2', sum(1 for e in bm.edges if len(e.link_faces) > 2))
