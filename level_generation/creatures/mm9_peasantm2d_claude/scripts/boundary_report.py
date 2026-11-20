"""Boundary loops per part of a blend's Body: size, centre. Args: <blend>"""
import bpy, bmesh, sys
import numpy as np
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index('--') + 1])
me = bpy.data.objects['Body'].data
bm = bmesh.new(); bm.from_mesh(me); lay = bm.faces.layers.int['part']
seen = set()
for e0 in [e for e in bm.edges if e.is_boundary]:
    if e0 in seen: continue
    st = [e0]; seen.add(e0); cur = []
    while st:
        x = st.pop(); cur.append(x)
        for v in x.verts:
            for y in v.link_edges:
                if y.is_boundary and y not in seen: seen.add(y); st.append(y)
    vs = np.array([v.co[:] for e in cur for v in e.verts])
    print('LOOP part', cur[0].link_faces[0][lay], 'edges', len(cur), 'centre', vs.mean(0).round(3).tolist(), 'ext', np.ptp(vs, 0).round(3).tolist())
print('NONMANIFOLD', [(np.array(e.verts[0].co[:]).round(3).tolist(), [f[lay] for f in e.link_faces]) for e in bm.edges if len(e.link_faces) > 2][:12])
