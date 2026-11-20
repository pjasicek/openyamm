"""Delete tiny loose slivers that float off the body already in the bind pose (mm9_greenman: detached_parts_audit found 1-5
triangle Meshy leaf slivers 2.7-4.4 cm off any other surface in the bind pose and in every clip). A loose part of 'Body' with
at most MAXT triangles whose nearest point on any other part is more than GAP away is deleted. Positions of everything else,
UVs, weights unchanged. Args: <in blend> <out blend> [MAXT 6] [GAP 0.01]"""
import bpy, bmesh, sys
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
MAXT = int(a[2]) if len(a) > 2 else 6; GAP = float(a[3]) if len(a) > 3 else 0.01
bpy.ops.wm.open_mainfile(filepath=a[0])
me = bpy.data.objects['Body'].data
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
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
drop = []
for k, P in enumerate(parts):
    if len(P) > MAXT: continue
    others = [f for f in bm.faces if comp[f] != k]
    vs = sorted({v for f in others for v in f.verts}, key=lambda v: v.index)
    idx = {v: i for i, v in enumerate(vs)}
    bvh = BVHTree.FromPolygons([v.co for v in vs], [[idx[v] for v in f.verts] for f in others])
    d = min(bvh.find_nearest(v.co)[3] for f in P for v in f.verts)
    if d > GAP:
        drop.append((k, len(P), round(d, 4)))
dv = [v for k, n, d in drop for f in parts[k] for v in f.verts]
bmesh.ops.delete(bm, geom=list(set(dv)), context='VERTS')
bm.to_mesh(me); me.update()
print('FLOATERS dropped', drop)
bpy.ops.wm.save_as_mainfile(filepath=a[1])
