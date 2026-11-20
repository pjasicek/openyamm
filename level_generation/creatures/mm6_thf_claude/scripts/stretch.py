"""Most-stretched edges at a frame (deformed / rest length). Args: blend clip frame."""
import bpy, sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import common
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, a[0]))
arm = bpy.data.objects['Thief_Rig']; mesh = bpy.data.objects['Thief']; me = mesh.data
act = bpy.data.actions[a[1]]; arm.animation_data.action = act; arm.animation_data.action_slot = act.slots[0]
bpy.context.scene.frame_set(int(a[2]))
ev = mesh.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
P = np.array([tuple(v.co) for v in m.vertices]); ev.to_mesh_clear()
R = np.array([tuple(v.co) for v in me.vertices])
E = np.array([tuple(e.vertices) for e in me.edges])
r = np.linalg.norm(R[E[:, 0]] - R[E[:, 1]], axis=1); d = np.linalg.norm(P[E[:, 0]] - P[E[:, 1]], axis=1)
k = d / np.maximum(r, 1e-6)
G = {g.index: g.name for g in mesh.vertex_groups}
for i in np.argsort(-k)[:8]:
    v0, v1 = E[i]
    w = lambda v: sorted(((round(g.weight, 2), G[g.group]) for g in me.vertices[v].groups), reverse=True)[:3]
    print('STRETCH %.1f' % k[i], 'rest', R[v0].round(3), w(v0), '|', R[v1].round(3), w(v1))
