"""Fine cross-sections of the snout coloured by part (shell / teeth / tongue part / eyes) and face normal.
Args: -- <blend> <out npz>"""
import bpy, sys, bmesh
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
body = bpy.data.objects['Body']; me = body.data
CO = np.array([tuple(v.co) for v in me.vertices])
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
comp = -np.ones(len(bm.verts), int); cid = 0
for v in bm.verts:
    if comp[v.index] >= 0: continue
    st = [v]; comp[v.index] = cid
    while st:
        x = st.pop()
        for e in x.link_edges:
            y = e.other_vert(x)
            if comp[y.index] < 0: comp[y.index] = cid; st.append(y)
    cid += 1
bm.free()
tris = [tuple(p.vertices) for p in me.polygons]
FN = np.array([tuple(p.normal) for p in me.polygons])
def cut(axis, c):
    out = []
    for fi, t in enumerate(tris):
        P = CO[list(t)]; d = P[:, axis] - c
        if d.min() > 0 or d.max() < 0: continue
        pts = []
        for i in range(3):
            j = (i + 1) % 3
            if (d[i] > 0) != (d[j] > 0):
                w = d[i] / (d[i] - d[j]); pts.append(P[i] + w * (P[j] - P[i]))
        if len(pts) == 2:
            out.append(np.concatenate([pts[0], pts[1], [comp[t[0]], fi], FN[fi]]))
    return np.array(out)
res = {}
for y in np.round(np.arange(-5.2, -3.0, 0.1), 2):
    res[f'y{y}'] = cut(1, y)
for x in (0.0, 0.1, 0.2, 0.3, 0.4, 0.5):
    res[f'x{x}'] = cut(0, x)
np.savez(a[1], **res)
