import bpy, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cfg
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data; sc = bpy.context.scene
P0 = np.array([v.co[:] for v in me.vertices]); pv = np.array([x.value for x in me.attributes['piece'].data])
JB = lambda n: np.array(rig.data.bones[n].head_local)
GI = {g.index: g.name for g in body.vertex_groups}
act = bpy.data.actions['Standing']; rig.animation_data.action = act; rig.animation_data.action_slot = act.slots[0]; sc.frame_set(0)
e = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = e.to_mesh(); P = np.array([v.co[:] for v in m.vertices]); e.to_mesh_clear()
E = np.array([ed.vertices[:] for ed in me.edges]); L0 = np.linalg.norm(P0[E[:, 0]] - P0[E[:, 1]], axis=1); L = np.linalg.norm(P[E[:, 0]] - P[E[:, 1]], axis=1)
for s in 'LR':
    hm = cfg.hand_mask(P0, pv, s, JB(f'B_{s}_Hand'), JB(f'B_{s}_Forearm'), 0.0)
    ef = hm[E[:, 0]] & hm[E[:, 1]]; st = L / np.maximum(L0, 1e-6); st[~ef] = 0
    for k in np.argsort(-st)[:6]:
        i, j = E[k]
        w = lambda v: sorted(((g.weight, GI[g.group]) for g in me.vertices[v].groups), reverse=True)[:2]
        print('HSTR', s, round(st[k], 2), 'rest mm', round(L0[k] * 1000, 1), [(n, round(x, 2)) for x, n in w(i)], [(n, round(x, 2)) for x, n in w(j)])
