"""Ray-cast the main shell (largest part, no teeth/eyes/tongue/frills) per station y: vertical hits at x = 0, +-0.12
(z and normal z), to find Meshy's real mouth gap. Args: -- <blend>"""
import bpy, sys, bmesh
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
body = bpy.data.objects['Body']; me = body.data
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
big = np.bincount(comp).argmax()
bmesh.ops.delete(bm, geom=[f for f in bm.faces if comp[f.verts[0].index] != big], context='FACES')
bvh = BVHTree.FromBMesh(bm)
def hits(o, d, maxd=6):
    out = []; o = Vector(o); d = Vector(d)
    while True:
        h = bvh.ray_cast(o, d, maxd)
        if h[0] is None: break
        out.append((round(h[0].z if d.z else h[0].x, 3), round(h[1].z if d.z else h[1].x, 2)))
        o = h[0] + d * 1e-4
    return out
for y in np.round(np.arange(-5.15, -2.95, 0.05), 3):
    row = [f'{y:6.2f}']
    for x in (0.0, 0.12):
        row.append(f'x{x}: ' + ' '.join(f'{z:.3f}({n:+.1f})' for z, n in hits((x, y, 17.5), (0, 0, -1))))
    print(' | '.join(row))
