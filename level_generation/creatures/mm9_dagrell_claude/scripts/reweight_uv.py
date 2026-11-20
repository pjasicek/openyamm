"""Carry new weights from a full-resolution rig blend onto the existing reduced, UV'd Dagrell 'Body' (keeps its UVs and
so the retexture), matched in the FitPose (Meshy's own geometry), then unpose it again with the new weights.

Args: <uv blend (reduced, UVs, FitPose)> <rig blend (full res, new weights)> <out blend> <report json>
Each reduced vertex takes the weights of the nearest full-resolution vertex in the FitPose, searched only inside the
full-resolution piece that most of its own piece matches; its rest position is then
the inverse of its blended FitPose bone matrices applied to its FitPose position.
"""
import bpy, sys, json
import numpy as np
from mathutils import Matrix
from mathutils.kdtree import KDTree

argv = sys.argv[sys.argv.index('--') + 1:]
UV, RIG, OUT, REP = argv
bpy.ops.wm.open_mainfile(filepath=UV)
sc = bpy.context.scene
rig = bpy.data.objects['MM9_Rig']
body = bpy.data.objects['Body']
with bpy.data.libraries.load(RIG) as (src, dst):
    dst.objects = ['Body']
ref = dst.objects[0]
ref.name = 'RefBody'
sc.collection.objects.link(ref)
ref.parent = rig
for m in ref.modifiers:
    if m.type == 'ARMATURE':
        m.object = rig
fp = bpy.data.actions['FitPose']
rig.animation_data_create(); rig.animation_data.action = fp
try:
    rig.animation_data.action_slot = fp.slots[0]
except Exception:
    pass
sc.frame_set(0); bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()


def posed(o):
    me = o.evaluated_get(dg).to_mesh()
    P = [o.matrix_world @ v.co for v in me.vertices]
    o.evaluated_get(dg).to_mesh_clear()
    return P


Pu, Pr = posed(body), posed(ref)
AW = rig.matrix_world
DEF = {pb.name: AW @ pb.matrix @ pb.bone.matrix_local.inverted() @ AW.inverted() for pb in rig.pose.bones}
import bmesh


def components(me):
    bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
    comp = np.full(len(bm.verts), -1); k = 0
    for v in bm.verts:
        if comp[v.index] >= 0:
            continue
        st = [v]; comp[v.index] = k
        while st:
            x = st.pop()
            for e in x.link_edges:
                y = e.other_vert(x)
                if comp[y.index] < 0:
                    comp[y.index] = k; st.append(y)
        k += 1
    return comp


cu, cr = components(body.data), components(ref.data)
kr = KDTree(len(Pr))
for i, p in enumerate(Pr):
    kr.insert(p, i)
kr.balance()
# each reduced piece matches inside one full-resolution piece (its vertices' majority): a piece whose vertices took
# weights from two neighbouring pieces would fold when unposed
first = np.array([kr.find(p)[1] for p in Pu])
piece_ref = {}
for k in np.unique(cu):
    vals, cnt = np.unique(cr[first[cu == k]], return_counts=True)
    piece_ref[k] = vals[np.argmax(cnt)]
trees = {}
for k in set(piece_ref.values()):
    ids = np.nonzero(cr == k)[0]
    t = KDTree(len(ids))
    for j, i in enumerate(ids):
        t.insert(Pr[i], j)
    t.balance()
    trees[k] = (t, ids)
rnames = {g.index: g.name for g in ref.vertex_groups}
for g in list(body.vertex_groups):
    body.vertex_groups.remove(g)
for b in rig.data.bones:
    body.vertex_groups.new(name=b.name)
dist = []
Z = Matrix(((0.0,) * 4,) * 4)
for i, v in enumerate(body.data.vertices):
    t, ids = trees[piece_ref[cu[i]]]
    _, jj, d = t.find(Pu[i])
    j = int(ids[jj])
    dist.append(d)
    M = Z.copy()
    for g in ref.data.vertices[j].groups:
        body.vertex_groups[rnames[g.group]].add([i], g.weight, 'REPLACE')
        M = M + DEF[rnames[g.group]] * g.weight
    v.co = body.matrix_world.inverted() @ (M.inverted() @ Pu[i])
for g in list(body.vertex_groups):
    if not any(g.index == x.group for v in body.data.vertices for x in v.groups):
        body.vertex_groups.remove(g)
rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.data.objects.remove(ref)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
rep = {'verts': len(body.data.vertices), 'match_dist_max': float(max(dist)), 'match_dist_p99': float(np.percentile(dist, 99))}
json.dump(rep, open(REP, 'w'), indent=1)
print('REWEIGHT ' + json.dumps(rep))
