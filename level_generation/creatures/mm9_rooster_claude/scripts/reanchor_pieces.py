"""Re-weight the small separate pieces of the UV-mapped 'Body': the head model's pieces (eyes, wattles, earlobes,
comb: attribute head_rz set by the graft) rigid on Xhead, the others rigidly to the main-body vertex nearest each piece's
centre (rig_chicken.py's rule since 2026-10-30: a wing sheet's nearest point can lie on the neck). Pieces whose centre
is behind TAIL_Y (the rooster's labelled sickle feathers) keep their weights. UVs and topology unchanged.
Args: <uv blend> <out blend> [tail_y]"""
import bpy, bmesh, sys, json
import numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree
a = sys.argv[sys.argv.index('--') + 1:]
TAIL_Y = float(a[2]) if len(a) > 2 else 9.0
bpy.ops.wm.open_mainfile(filepath=a[0])
ob = bpy.data.objects['Body']; me = ob.data
P = np.array([tuple(v.co) for v in me.vertices])
piece = np.array([d.value for d in me.attributes['piece'].data])
hz = np.array([d.value for d in me.attributes['head_rz'].data])
bid = np.nonzero(piece == 0)[0]
kb = KDTree(len(bid))
for j, i in enumerate(bid):
    kb.insert(Vector(P[i]), j)
kb.balance()
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
seen = set(); n = 0
for v in bm.verts:
    if piece[v.index] != 2 or v.index in seen:
        continue
    comp, st = [], [v]; seen.add(v.index)
    while st:
        x = st.pop(); comp.append(x.index)
        for e in x.link_edges:
            y = e.other_vert(x)
            if y.index not in seen:
                seen.add(y.index); st.append(y)
    c = P[comp].mean(0)
    if c[1] > TAIL_Y:
        continue
    if np.median(hz[comp]) > -4:           # a head piece (body vertices carry -9)
        w = {'Xhead': 1.0}
    else:
        src = me.vertices[int(bid[kb.find(Vector(c))[1]])]
        w = {ob.vertex_groups[g.group].name: g.weight for g in src.groups}
    for i in comp:
        for g in list(me.vertices[i].groups):
            ob.vertex_groups[g.group].remove([i])
        for name, x in w.items():
            ob.vertex_groups[name].add([i], x, 'REPLACE')
    n += 1
bpy.ops.wm.save_as_mainfile(filepath=a[1])
print('REANCHOR', n)
