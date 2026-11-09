"""Pieces of the rigged 'Body' whose bind-space centroid is far from their dominant bone's bind segment.
Args: <rig blend> [threshold m]"""
import bpy, bmesh, sys
import numpy as np
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
th = float(argv[1]) if len(argv) > 1 else 0.2
arm = bpy.data.objects['MM9_Rig']; ob = bpy.data.objects['Body']; me = ob.data
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
seen = np.full(len(bm.verts), -1); comps = []
for v in bm.verts:
    if seen[v.index] >= 0: continue
    st = [v]; seen[v.index] = len(comps); c = []
    while st:
        x = st.pop(); c.append(x.index)
        for e in x.link_edges:
            y = e.other_vert(x)
            if seen[y.index] < 0: seen[y.index] = len(comps); st.append(y)
    comps.append(c)
names = {g.index: g.name for g in ob.vertex_groups}
for k, c in enumerate(comps):
    w = {}
    for i in c:
        for g in me.vertices[i].groups:
            w[names[g.group]] = w.get(names[g.group], 0) + g.weight
    b = max(w, key=w.get)
    bone = arm.data.bones[b]
    a_, e_ = np.array(tuple(bone.head_local)), np.array(tuple(bone.tail_local))
    P = np.array([tuple(me.vertices[i].co) for i in c]); cen = P.mean(0)
    ab = e_ - a_; u = np.clip((cen - a_) @ ab / max(ab @ ab, 1e-12), 0, 1)
    d = np.linalg.norm(cen - (a_ + u * ab))
    ext = float(np.linalg.norm(P.max(0) - P.min(0)))
    if d > th or ext > 0.35:
        print('PIECE', k, len(c), b, 'dist %.3f' % d, 'extent %.3f' % ext, [round(x, 2) for x in cen])
