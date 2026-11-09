"""List connected components of the 'Body' in a fit blend: size, centroid, bbox. Args: blend [min_verts]"""
import bpy, bmesh, sys
import numpy as np
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
mn = int(argv[1]) if len(argv) > 1 else 100
me = bpy.data.objects['Body'].data
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
seen = set(); comps = []
for v in bm.verts:
    if v.index in seen:
        continue
    st = [v]; seen.add(v.index); c = []
    while st:
        x = st.pop(); c.append(x.index)
        for e in x.link_edges:
            y = e.other_vert(x)
            if y.index not in seen:
                seen.add(y.index); st.append(y)
    comps.append(c)
comps.sort(key=len, reverse=True)
for k, c in enumerate(comps):
    if len(c) < mn:
        break
    P = np.array([tuple(bm.verts[i].co) for i in c])
    print('COMP', k, len(c), 'cent', P.mean(0).round(3), 'min', P.min(0).round(3), 'max', P.max(0).round(3))
