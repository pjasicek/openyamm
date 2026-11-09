"""Terror probe: Meshy main-body extremities (geodesic from the chest) and their bin spreads. Args: <align blend>"""
import bpy, bmesh, sys, heapq
import numpy as np
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
arm = bpy.data.objects['MM9_Rig']
src = bpy.data.objects['Meshy']
bm = bmesh.new(); bm.from_mesh(src.data); bm.transform(src.matrix_world)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5); bm.verts.ensure_lookup_table()
# main component
seen = {0}; comps = []
lab = [-1] * len(bm.verts)
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
main = set(max(comps, key=len))
chest = Vector(arm.data.bones['Bip01 Spine1'].head_local)
c0 = min(main, key=lambda i: (bm.verts[i].co - chest).length)


def geo(src, allowed, limit=9):
    d = {src: 0.0}; pq = [(0.0, src)]
    while pq:
        dd, i = heapq.heappop(pq)
        if dd > d[i] or dd > limit:
            continue
        for e in bm.verts[i].link_edges:
            j = e.other_vert(bm.verts[i]).index
            if j in allowed:
                nd = dd + e.calc_length()
                if nd < d.get(j, 1e9):
                    d[j] = nd; heapq.heappush(pq, (nd, j))
    return d


g = geo(c0, main)
ext = []
for i, d in sorted(g.items(), key=lambda x: -x[1]):
    if all(g.get(e.other_vert(bm.verts[i]).index, 0) <= d for e in bm.verts[i].link_edges) and \
            all((bm.verts[i].co - bm.verts[j].co).length > 0.3 for j in ext):
        ext.append(i)
    if len(ext) == 10:
        break
for i in ext:
    gt = geo(i, main, 3.0)
    bw = 0.04
    bins = {}
    for j, d in gt.items():
        bins.setdefault(int(d / bw), []).append(np.array(tuple(bm.verts[j].co)))
    sp = []
    for k in sorted(bins)[:60]:
        b = np.array(bins[k]); sp.append(round(float(np.linalg.norm(b - b.mean(0), axis=1).mean()), 3))
    print('TIP', i, tuple(round(c, 2) for c in bm.verts[i].co), round(g[i], 2), sp)
