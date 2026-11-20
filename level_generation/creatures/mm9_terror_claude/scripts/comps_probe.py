"""List the connected components of the aligned Meshy mesh (size, bbox). Args: <align blend>"""
import bpy, bmesh, sys
import numpy as np
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
src = bpy.data.objects['Meshy']
bm = bmesh.new(); bm.from_mesh(src.data); bm.transform(src.matrix_world)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5); bm.verts.ensure_lookup_table()
lab = [-1] * len(bm.verts); comps = []
for v in bm.verts:
    if lab[v.index] >= 0:
        continue
    st = [v]; lab[v.index] = len(comps); c = []
    while st:
        x = st.pop(); c.append(x.index)
        for e in x.link_edges:
            y = e.other_vert(x)
            if lab[y.index] < 0:
                lab[y.index] = len(comps); st.append(y)
    comps.append(c)
for c in sorted(comps, key=len, reverse=True):
    P = np.array([tuple(bm.verts[i].co) for i in c])
    print('COMP', len(c), P.min(0).round(2).tolist(), P.max(0).round(2).tolist())
