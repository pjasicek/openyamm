"""Delete loose slivers of at most MAXT triangles standing off the body/head shells by more than GAP in the bind pose
(mm9_greenman pass 2b: 1-5 triangle Meshy leaf scraps 0.5-4 cm off the skin read as floating flecks and keep the
detached audit red). Args: <in blend> <out blend> [MAXT 5] [GAP 0.004] [CARRIER 500]"""
import bpy, bmesh, sys
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
MAXT = int(a[2]) if len(a) > 2 else 5; GAP = float(a[3]) if len(a) > 3 else 0.004; CAR = int(a[4]) if len(a) > 4 else 500
bpy.ops.wm.open_mainfile(filepath=a[0])
me = bpy.data.objects['Body'].data
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
comp = {}; parts = []
for f0 in bm.faces:
    if f0 in comp: continue
    st = [f0]; comp[f0] = len(parts); P = [f0]
    while st:
        f = st.pop()
        for v in f.verts:
            for g in v.link_faces:
                if g not in comp: comp[g] = len(parts); st.append(g); P.append(g)
    parts.append(P)
tri = lambda P: sum(len(f.verts) - 2 for f in P)
car = [f for P in parts if tri(P) > CAR for f in P]
vs = sorted({v for f in car for v in f.verts}, key=lambda v: v.index); ix = {v: i for i, v in enumerate(vs)}
bvh = BVHTree.FromPolygons([v.co.copy() for v in vs], [[ix[v] for v in f.verts] for f in car])
drop = []
for P in parts:
    if tri(P) > MAXT: continue
    d = min(bvh.find_nearest(v.co)[3] for f in P for v in f.verts)
    if d > GAP: drop.append((tri(P), round(d, 4)))
    if d > GAP:
        for f in P: f.tag = True
bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.tag], context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
bm.to_mesh(me); me.update()
print('SLIVERDROP', len(drop), sorted(drop, key=lambda x: -x[1])[:20])
bpy.ops.wm.save_as_mainfile(filepath=a[1])
