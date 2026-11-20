"""Small pieces with a large extent in the aligned Meshy (align blend 'Meshy'): extent and per-vertex singular values.
Args: <align blend>"""
import bpy, bmesh, sys
import numpy as np
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
bm = bmesh.new(); bm.from_mesh(bpy.data.objects['Meshy'].data); bm.verts.ensure_lookup_table()
seen = np.full(len(bm.verts), -1); comps = []
for v in bm.verts:
    if seen[v.index] >= 0: continue
    st = [v]; seen[v.index] = len(comps); c = []
    while st:
        x = st.pop(); c.append(x.index)
        for e in x.link_edges:
            y = e.other_vert(x)
            if seen[y.index] < 0: seen[y.index] = len(comps); st.append(y)
    comps.append(c)
for k, c in enumerate(comps):
    X = np.array([tuple(bm.verts[i].co) for i in c])
    ext = float(np.linalg.norm(X.max(0) - X.min(0)))
    if ext > 0.35 and len(c) < 250:
        sv = np.linalg.svd(X - X.mean(0), compute_uv=False) / np.sqrt(len(c))
        print('THIN', k, len(c), 'ext %.3f' % ext, 'sv', np.round(sv, 4), np.round(X.min(0), 2), np.round(X.max(0), 2))
