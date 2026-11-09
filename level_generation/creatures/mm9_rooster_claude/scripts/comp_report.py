"""Connected components of 'Body' (by mesh topology): counts by size, small ones with their centres. Args: blend"""
import bpy, bmesh, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
bm = bmesh.new(); bm.from_mesh(bpy.data.objects['Body'].data)
seen = set(); out = []
for v in bm.verts:
    if v in seen:
        continue
    c, st = [v], [v]; seen.add(v)
    while st:
        x = st.pop()
        for e in x.link_edges:
            y = e.other_vert(x)
            if y not in seen:
                seen.add(y); st.append(y); c.append(y)
    out.append((len({f for u in c for f in u.link_faces}), np.mean([tuple(u.co) for u in c], 0).round(3).tolist()))
out.sort(key=lambda t: t[0])
print('COMPS', len(out), out[:14])
