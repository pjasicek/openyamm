import bpy, bmesh, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
ob = bpy.data.objects['Body']; me = ob.data
co = np.array([v.co for v in me.vertices])
# loose parts
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
comp = -np.ones(len(co), int); k = 0
for v in bm.verts:
    if comp[v.index] >= 0: continue
    st = [v]; comp[v.index] = k
    while st:
        x = st.pop()
        for e in x.link_edges:
            o = e.other_vert(x)
            if comp[o.index] < 0: comp[o.index] = k; st.append(o)
    k += 1
big = np.bincount(comp).argmax()
for s in (-1, 1):
    m = (comp == big) & (co[:, 0] * s > 0.055) & (co[:, 2] > 0.38) & (co[:, 2] < 0.48) & (co[:, 1] > -0.06) & (co[:, 1] < 0.04)
    q = co[m]
    print('EAR', s, m.sum(), np.round(q.min(0), 3), np.round(q.max(0), 3))
hair = co[comp == np.bincount(comp)[[c for c in range(k)]].argsort()[-2]] if False else None
for c in range(k):
    q = co[comp == c]
    if q[:, 2].mean() > 0.4 and len(q) > 300 and c != big:
        for z in (0.40, 0.42, 0.44, 0.46):
            r = q[np.abs(q[:, 2] - z) < 0.01]
            fr = r[r[:, 1] < -0.0]
            print('HAIR z', z, 'x range', np.round(r[:, 0].min(), 3), np.round(r[:, 0].max(), 3), 'front y min', np.round(r[:, 1].min(), 3))
