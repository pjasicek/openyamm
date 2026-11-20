"""Hair-shell height above the face shell (signed, along the face normal) per hair vertex, by region. Args: blend"""
import bpy, bmesh, sys
import numpy as np
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
body = bpy.data.objects['Body']; me = body.data
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
comp = -np.ones(len(bm.verts), np.int32); cid = 0
for v in bm.verts:
    if comp[v.index] >= 0: continue
    st = [v]; comp[v.index] = cid
    while st:
        x = st.pop()
        for e in x.link_edges:
            y = e.other_vert(x)
            if comp[y.index] < 0: comp[y.index] = cid; st.append(y)
    cid += 1
CO = np.array([v.co[:] for v in bm.verts])
for k in range(cid):
    m = comp == k
    if m.sum() > 100: print('PART', k, int(m.sum()), CO[m].min(0).round(3), CO[m].max(0).round(3))
FACE, HAIR = int(a[1]), int(a[2])
fv = [f for f in bm.faces if comp[f.verts[0].index] == FACE]
t = BVHTree.FromPolygons([v.co for v in bm.verts], [[v.index for v in f.verts] for f in fv])
hv = np.where(comp == HAIR)[0]
d = []
for i in hv:
    loc, n, fi, dist = t.find_nearest(bm.verts[i].co)
    d.append((bm.verts[i].co - loc).dot(n))
d = np.array(d); P = CO[hv]
c = CO[comp == FACE].mean(0)
print('centre', c.round(3))
el = np.degrees(np.arctan2(P[:, 2] - c[2], np.hypot(P[:, 0] - c[0], P[:, 1] - c[1])))
az = np.degrees(np.arctan2(P[:, 0] - c[0], -(P[:, 1] - c[1])))  # 0 = front (-y), 90 = +x
for e0 in range(-40, 90, 10):
    row = f'el {e0:3d}:'
    for a0 in range(-180, 180, 30):
        s = (el >= e0) & (el < e0 + 10) & (az >= a0) & (az < a0 + 30)
        row += f' {d[s].mean()*1000:5.1f}' if s.any() else '     .'
    print(row)
np.save(a[3], np.concatenate([hv[:, None], d[:, None], el[:, None], az[:, None]], 1))
