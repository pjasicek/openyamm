"""Print, per height slice (Blender z, bind pose), the back extent (max y; +y is the back) near the midline (|x| < 4 cm) of the
hair shell, the face/skull shell, the neck shell and the body (non-head faces), and the weights of the hair shell.
Args: -- <blend>"""
import bpy, bmesh, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
body = bpy.data.objects['Body']; me = body.data
head = np.zeros(len(me.polygons), np.int32); me.attributes['head'].data.foreach_get('value', head)
hand = np.zeros(len(me.polygons), np.int32); me.attributes['hand'].data.foreach_get('value', hand)
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
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
hv = set(); bv = set()
for p in me.polygons:
    (hv if head[p.index] else (set() if hand[p.index] else bv)).update(p.vertices)
hparts = sorted({comp[i] for i in hv}, key=lambda k: -(comp == k).sum())
print('HEADPARTS', [(int(k), int((comp == k).sum()), CO[comp == k].min(0).round(3).tolist(), CO[comp == k].max(0).round(3).tolist()) for k in hparts])
hair = max(hparts, key=lambda k: CO[comp == k][:, 1].max())
groups = {g.index: g.name for g in body.vertex_groups}
from collections import Counter
cnt = Counter()
for i in np.where(comp == hair)[0]:
    v = me.vertices[i]
    if v.groups:
        g = max(v.groups, key=lambda g: g.weight); cnt[groups[g.group]] += 1
print('HAIR', int(hair), 'dominant groups', cnt.most_common(8))
bvl = np.array(sorted(bv))
for z in np.arange(0.50, 0.95, 0.03):
    row = []
    for name, idx in (('hair', np.where(comp == hair)[0]),) + tuple((f'p{k}', np.where(comp == k)[0]) for k in hparts if k != hair) + (('body', bvl),):
        m = idx[(np.abs(CO[idx, 2] - z) < 0.015) & (np.abs(CO[idx, 0]) < 0.04)]
        row.append(f'{name} {CO[m, 1].max():+.3f}' if len(m) else f'{name}   -  ')
    print(f'z {z:.2f}', ' | '.join(row))
