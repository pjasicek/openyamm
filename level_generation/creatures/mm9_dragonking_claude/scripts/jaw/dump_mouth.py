"""Dump the mouth hole loop (lip faces removed), its upper/lower labels, and the head shell interior space per station.
Args: -- <blend> <out npz>"""
import bpy, sys, bmesh
import numpy as np
from mathutils.bvhtree import BVHTree
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
rig = bpy.data.objects['MM9_Rig']; body = bpy.data.objects['Body']; me = body.data
UPPER = {'Xheadpiv', 'Xhead', 'Xjawbase', 'Xtopfinpiv', 'Xtopfinpiv01', 'Xfinpiv', 'Xfinpiv01'}
vg = {g.index: g.name for g in body.vertex_groups}
def upw(v):
    s = sum(g.weight for g in v.groups); return sum(g.weight for g in v.groups if vg[g.group] in UPPER) / max(s, 1e-9)
bm = bmesh.new(); bm.from_mesh(me)
lip = bm.faces.layers.bool.get('lip')
bm.verts.ensure_lookup_table()
# component of the main shell only
bmesh.ops.delete(bm, geom=[f for f in bm.faces if f[lip]], context='FACES')
bm.edges.ensure_lookup_table(); bm.verts.ensure_lookup_table()
bnd = [e for e in bm.edges if e.is_boundary]
# loop through vertex with min y among boundary in mouth box
cand = [e for e in bnd if all(-5.3 < v.co.y < -2.7 and 15.0 < v.co.z < 15.7 and abs(v.co.x) < 0.75 for v in e.verts)]
left = set(cand); loops = []
while left:
    e = left.pop(); chain = [e.verts[0], e.verts[1]]
    while True:
        v = chain[-1]; nxt = [x for x in v.link_edges if x in left]
        if not nxt: break
        x = nxt[0]; left.discard(x); chain.append(x.other_vert(v))
    loops.append(chain)
L = max(loops, key=len)
print('loop', len(L), L[0] == L[-1])
ids = [v.index for v in L[:-1]]
P = np.array([tuple(me.vertices[i].co) for i in ids])
U = np.array([upw(me.vertices[i]) for i in ids])
# interior space: BVH of the full shell (all faces incl lips)
bvh = BVHTree.FromObject(body, bpy.context.evaluated_depsgraph_get())
st = []
for y in np.linspace(-5.3, -1.6, 38):
    row = [y]
    for d, o in (((0, 0, 1), (0, y, 15.35)), ((0, 0, -1), (0, y, 15.35))):
        hit = bvh.ray_cast(Vector(o), Vector(d), 5)
        row.append(hit[0].z if hit[0] else np.nan)
    for x0 in (1, -1):
        hit = bvh.ray_cast(Vector((0, y, 15.35)), Vector((x0, 0, 0)), 5)
        row.append(hit[0].x if hit[0] else np.nan)
    st.append(row)
st = np.array(st)
print('stations y, ztop, zbot, xpos, xneg'); print(np.round(st, 3))
np.savez(a[1], loop=P, ids=np.array(ids), upper=U, stations=st,
         hinge=np.array(tuple(rig.data.bones['Xjawpivot'].head_local)))
print('upper frac', np.round(U, 2).tolist())
