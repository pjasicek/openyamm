"""Components of a fitted/aligned mesh object: size, centroid, bbox, and min distance between big pieces.
Args: blend object"""
import bpy, bmesh, sys
from mathutils import Vector
from mathutils.kdtree import KDTree
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
o = bpy.data.objects[argv[1]]
bm = bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table()
seen = {}; comps = []
for v in bm.verts:
    if v.index in seen: continue
    st = [v]; seen[v.index] = 1; c = []
    while st:
        x = st.pop(); c.append(x.index)
        for e in x.link_edges:
            y = e.other_vert(x)
            if y.index not in seen: seen[y.index] = 1; st.append(y)
    comps.append(c)
comps.sort(key=len, reverse=True)
big = [c for c in comps if len(c) >= 40]
trees = []
for c in big:
    k = KDTree(len(c))
    for j, i in enumerate(c): k.insert(bm.verts[i].co, j)
    k.balance(); trees.append(k)
for a, c in enumerate(big):
    pts = [bm.verts[i].co for i in c]
    cen = sum(pts, Vector()) / len(pts)
    near = []
    for b, c2 in enumerate(big):
        if b == a: continue
        d = min(trees[b].find(bm.verts[i].co)[2] for i in c[::3])
        if d < 0.03: near.append((b, round(d, 3)))
    print('COMP', a, len(c), [round(x, 3) for x in cen], [round(min(p[i] for p in pts), 2) for i in range(3)],
          [round(max(p[i] for p in pts), 2) for i in range(3)], near)
