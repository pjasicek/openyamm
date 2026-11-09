"""Posed-mesh outliers: per action and frame, vertices whose edges stretch more than K x their rest length; prints the
worst pieces, their vertex groups and the frame. Args: -- <blend> <K> <action...>"""
import bpy, sys, os
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
blend, K = a[0], float(a[1]); acts = a[2:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
E = np.array([tuple(e.vertices) for e in me.edges])
rest = np.array([tuple(v.co) for v in me.vertices]); L0 = np.linalg.norm(rest[E[:, 0]] - rest[E[:, 1]], axis=1)
E = E[L0 > 0.002]; L0 = L0[L0 > 0.002]          # degenerate decimated edges are no stretch measure
rig.animation_data_create()
for act in acts:
    A = bpy.data.actions[act]; rig.animation_data.action = A
    if len(A.slots): rig.animation_data.action_slot = A.slots[0]
    f0, f1 = map(int, A.frame_range); worst = (0, None, None)
    for f in range(f0, f1 + 1, 2):
        bpy.context.scene.frame_set(f)
        dg = bpy.context.evaluated_depsgraph_get(); ev = body.evaluated_get(dg); m = ev.to_mesh()
        P = np.array([tuple(v.co) for v in m.vertices]); ev.to_mesh_clear()
        r = np.linalg.norm(P[E[:, 0]] - P[E[:, 1]], axis=1) / np.maximum(L0, 1e-6)
        i = int(np.argmax(r))
        if r[i] > worst[0]:
            worst = (float(r[i]), f, int(E[i, 0]))
    v = worst[2]; grp = sorted(((g.weight, body.vertex_groups[g.group].name) for g in me.vertices[v].groups), reverse=True)[:4]
    print('OUTLIER', act, 'max edge stretch', round(worst[0], 2), 'frame', worst[1], 'vert', v, 'piece', pv[v],
          'rest', np.round(rest[v], 3), 'groups', [(n, round(w, 2)) for w, n in grp])
