"""Print the pieces of each limb group of the aligned Meshy (align_stand.py blend): size, PCA length, ends, bend.
Args: <align blend>"""
import bpy, bmesh, sys, json
import numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
sc = bpy.context.scene
arm = bpy.data.objects['MM9_Rig']
act = bpy.data.actions['Stand']; arm.animation_data_create(); arm.animation_data.action = act
try:
    arm.animation_data.action_slot = act.slots[0]
except Exception:
    pass
sc.frame_set(0); bpy.context.view_layer.update()
J = {pb.name: arm.matrix_world @ pb.head for pb in arm.pose.bones}
for b in ('Xarmpiv', 'Xarm', 'Xarmlow', 'Xfin', 'Xlegpiv', 'Xleg', 'Xleglow', 'Xfoot', 'Xtoe01'):
    print('JOINT', b, [round(x, 3) for x in J[b]])
dg = bpy.context.evaluated_depsgraph_get()
mpos, mlab = [], []
for o in bpy.data.objects:
    if o.type != 'MESH' or o.name == 'Meshy':
        continue
    me = o.evaluated_get(dg).to_mesh()
    for v, ve in zip(o.data.vertices, me.vertices):
        g = max(v.groups, key=lambda g: g.weight)
        mpos.append(tuple(o.matrix_world @ ve.co)); mlab.append(o.vertex_groups[g.group].name)
kM = KDTree(len(mpos))
for i, p in enumerate(mpos):
    kM.insert(Vector(p), i)
kM.balance()
bm = bmesh.new(); bm.from_mesh(bpy.data.objects['Meshy'].data); bm.verts.ensure_lookup_table()
P = np.array([tuple(v.co) for v in bm.verts])
seen = np.full(len(P), -1); comps = []
for v in bm.verts:
    if seen[v.index] >= 0: continue
    st = [v]; seen[v.index] = len(comps); c = []
    while st:
        x = st.pop(); c.append(x.index)
        for e in x.link_edges:
            y = e.other_vert(x)
            if seen[y.index] < 0: seen[y.index] = len(comps); st.append(y)
    comps.append(np.array(c))
for k, c in enumerate(comps):
    labs = [mlab[kM.find(Vector(P[i]))[1]] for i in c]
    vals, cnt = np.unique(labs, return_counts=True)
    lab = vals[np.argmax(cnt)]
    if not any(lab.startswith(p) for p in ('Xarm', 'Xfin', 'Xfm', 'Xleg', 'Xfoot', 'Xtoe')):
        continue
    if J[lab].x < 0:
        continue  # right side only
    X = P[c]; m = X.mean(0); _, sv, Vt = np.linalg.svd(X - m, full_matrices=False); t = (X - m) @ Vt[0]
    e0, e1 = m + Vt[0] * t.min(), m + Vt[0] * t.max()
    print('PIECE', k, len(c), lab, 'len %.3f' % (t.max() - t.min()), 'sv', [round(s / np.sqrt(len(c)), 3) for s in sv],
          'ends', [round(x, 2) for x in e0], [round(x, 2) for x in e1])
