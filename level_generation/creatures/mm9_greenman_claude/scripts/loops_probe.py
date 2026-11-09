"""Boundary loops of the largest non-hand loose part of 'Body': edge count, centroid, size. Args: <blend>"""
import bpy, bmesh, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
me = bpy.data.objects['Body'].data
bm = bmesh.new(); bm.from_mesh(me)
bnd = [e for e in bm.edges if e.is_boundary]
adj = {}
for e in bnd:
    for v in e.verts: adj.setdefault(v, []).append(e)
seen = set(); loops = []
for e0 in bnd:
    if e0 in seen: continue
    st = [e0]; seen.add(e0); L = []
    while st:
        e = st.pop(); L.append(e)
        for v in e.verts:
            for e2 in adj[v]:
                if e2 not in seen: seen.add(e2); st.append(e2)
    pts = np.array([v.co[:] for e in L for v in e.verts])
    loops.append((len(L), pts.mean(0), np.ptp(pts, 0)))
for n, c, s in sorted(loops, key=lambda x: -x[0])[:25]:
    print('LOOP edges %3d centre %s size %s' % (n, np.round(c, 3), np.round(s, 3)))
print('LOOP total', len(loops))
