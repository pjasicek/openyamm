"""Boundary rings of each mesh object in a blend (count, bbox). Args: <blend>"""
import bpy, bmesh, sys
import numpy as np
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index('--') + 1])
for o in bpy.data.objects:
    if o.type != 'MESH': continue
    bm = bmesh.new(); bm.from_mesh(o.data)
    seen = set()
    for e in [e for e in bm.edges if e.is_boundary]:
        if e in seen: continue
        st = [e]; seen.add(e); cur = []
        while st:
            x = st.pop(); cur.append(x)
            for v in x.verts:
                for y in v.link_edges:
                    if y.is_boundary and y not in seen: seen.add(y); st.append(y)
        q = np.array([v.co[:] for x in cur for v in x.verts])
        print('RING', o.name, len(cur), q.min(0).round(3), q.max(0).round(3))
    print('NM', o.name, [tuple(np.round((e.verts[0].co + e.verts[1].co)[:] , 3) / 2) for e in bm.edges if len(e.link_faces) > 2][:8])
