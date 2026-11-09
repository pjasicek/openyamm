"""Tuck Meshy's human ears under the hair/hood shell (MM9's PeasantDF1-4 hair and hoods cover the ears; Meshy modelled
ears that stick out in front of the hair's front edge, PF1's lesson). On the head shell, vertices in the ear box
(|x| > X0, z Z0..Z1, y Y0..Y1) that stand out further than the skull beside the ear (per 1 cm height band: the 60th
percentile of |x| of head-shell vertices 0-3 cm in front of and behind the box) are pulled in to that radius - 3 mm;
two Laplacian passes over the moved vertices and their ring soften the step. Positions only (before the UV pass).
Args: <in blend> <out blend>"""
import bpy, bmesh, sys, json
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
X0, Z0, Z1, Y0, Y1 = 0.05, 0.39, 0.475, -0.062, 0.04
bpy.ops.wm.open_mainfile(filepath=a[0])
ob = bpy.data.objects['Body']; me = ob.data
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
comp = -np.ones(len(bm.verts), int); k = 0
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
co = np.array([tuple(v.co) for v in bm.verts]); new = co.copy()
moved = set(); rep = {}
for s in (-1, 1):
    sh = (comp == big) & (co[:, 0] * s > 0.02)
    box = sh & (co[:, 0] * s > X0) & (co[:, 2] > Z0) & (co[:, 2] < Z1) & (co[:, 1] > Y0) & (co[:, 1] < Y1)
    ring = sh & (co[:, 2] > Z0 - 0.01) & (co[:, 2] < Z1 + 0.01) & (((co[:, 1] > Y0 - 0.03) & (co[:, 1] < Y0)) | ((co[:, 1] > Y1) & (co[:, 1] < Y1 + 0.03)))
    n = 0
    for i in np.nonzero(box)[0]:
        r = ring & (np.abs(co[:, 2] - co[i, 2]) < 0.01)
        if r.sum() < 3: continue
        ref = np.percentile(np.abs(co[r, 0]), 60) - 0.003
        if abs(co[i, 0]) > ref:
            new[i, 0] = s * ref; moved.add(int(i)); n += 1
    rep[s] = n
nb = {v.index: [e.other_vert(v).index for e in v.link_edges] for v in bm.verts}
zone = set(moved) | {j for i in moved for j in nb[i]}
for _ in range(2):
    nn = new.copy()
    for i in zone:
        nn[i] = 0.5 * new[i] + 0.5 * new[nb[i]].mean(0)
    new = nn
for i in zone:
    bm.verts[i].co = new[i]
bm.to_mesh(me); me.update()
print('EARTUCK', json.dumps({'moved': rep, 'smoothed': len(zone)}))
bpy.ops.wm.save_as_mainfile(filepath=a[1])
