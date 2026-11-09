"""List open boundary loops of 'Body' forward of a y limit (head and neck), with face parts around them.
Args: blend ymax"""
import bpy, bmesh, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
ob = bpy.data.objects['Body']
bm = bmesh.new(); bm.from_mesh(ob.data)
bnd = [e for e in bm.edges if e.is_boundary]
pl = bm.faces.layers.int.get('part')
es = set(bnd); seen = set()
for e in bnd:
    if e in seen:
        continue
    st, lp = [e], []; seen.add(e)
    while st:
        x = st.pop(); lp.append(x)
        for v in x.verts:
            for y in v.link_edges:
                if y in es and y not in seen:
                    seen.add(y); st.append(y)
    P = np.array([tuple(v.co) for e2 in lp for v in e2.verts])
    if P[:, 1].mean() < float(a[1]):
        parts = sorted({f[pl] for e2 in lp for f in e2.link_faces}) if pl else []
        print('LOOP', len(lp), P.mean(0).round(3), np.ptp(P, 0).round(3), 'parts', parts, 'verts', sorted({v.index for e2 in lp for v in e2.verts})[:40] if len(lp) < 20 else '')
