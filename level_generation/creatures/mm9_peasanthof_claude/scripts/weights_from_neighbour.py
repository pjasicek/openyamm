"""Loose parts (bbox centre within 2 cm of a given point, MM9 frame) take the vertex weights of the nearest vertex of the
REST of the body (a turned-down boot cuff floated 8 mm off the boot in Fidget, detached_parts_audit). Weights only.
Args: <in blend> <out blend> x,y,z[;x,y,z...]"""
import bpy, bmesh, sys
import numpy as np
from mathutils.kdtree import KDTree
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
ob = bpy.data.objects['Body']; me = ob.data; mw = ob.matrix_world
pts = [np.array([float(t) for t in q.split(',')]) for q in a[2].split(';') if q]
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
CO = np.array([tuple(mw @ v.co) for v in me.vertices])
sel = set()
for c in range(k):
    idx = np.nonzero(comp == c)[0]; q = CO[idx]; cen = 0.5 * (q.min(0) + q.max(0))
    if any(np.linalg.norm(cen - p) < 0.02 for p in pts):
        sel.add(c); print('WNB part', len(idx), np.round(cen, 3).tolist())
rest = np.nonzero(~np.isin(comp, list(sel)))[0]
kd = KDTree(len(rest))
for i, j in enumerate(rest): kd.insert(CO[j].tolist(), i)
kd.balance()
n = 0
for c in sel:
    for vi in np.nonzero(comp == c)[0]:
        _, i, _ = kd.find(CO[vi].tolist()); src = me.vertices[int(rest[i])]
        v = me.vertices[int(vi)]
        for g in list(v.groups):
            ob.vertex_groups[g.group].remove([v.index])
        for g in src.groups:
            ob.vertex_groups[g.group].add([v.index], g.weight, 'REPLACE')
        n += 1
print('WEIGHTS_FROM_NEIGHBOUR vertices', n)
bpy.ops.wm.save_as_mainfile(filepath=a[1])
