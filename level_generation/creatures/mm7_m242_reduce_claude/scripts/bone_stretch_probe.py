"""Where the bone-class (cloth == 0) edges stretch most in a clip of a gate copy: top edges with rest position,
dominant bones of both ends, and the piece. Args: -- <gate blend> <clip> [n]"""
import bpy, sys, os
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0])); clip = a[1]; N = int(a[2]) if len(a) > 2 else 8
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
cl = np.zeros(len(me.vertices), np.int32); me.attributes['cloth'].data.foreach_get('value', cl)
pc = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pc)
E = np.array([tuple(e.vertices) for e in me.edges]); E = E[(cl[E[:, 0]] == 0) & ((cl[E[:, 1]] == 0) | (os.environ.get('MIXED') == '1'))]
R0 = np.array([tuple(v.co) for v in me.vertices]); L0 = np.linalg.norm(R0[E[:, 0]] - R0[E[:, 1]], axis=1)
names = [g.name for g in body.vertex_groups]
dom = lambda i: max(((names[g.group], round(g.weight, 2)) for g in me.vertices[i].groups), key=lambda t: t[1])
act = bpy.data.actions[clip]; rig.animation_data_create(); rig.animation_data.action = act
if len(act.slots): rig.animation_data.action_slot = act.slots[0]
best = np.zeros(len(E))
for f in range(int(act.frame_range[0]), int(act.frame_range[1]) + 1, 3):
    bpy.context.scene.frame_set(f); ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
    P = np.array([tuple(v.co) for v in m.vertices]); ev.to_mesh_clear()
    r = np.linalg.norm(P[E[:, 0]] - P[E[:, 1]], axis=1) / np.maximum(L0, 1e-6); best = np.maximum(best, np.maximum(r, 1 / np.maximum(r, 1e-6)))
for k in np.argsort(-best)[:N]:
    i, j = E[k]
    print('BONEPROBE', round(float(best[k]), 2), 'len mm', round(float(L0[k]) * 1000, 1), np.round(R0[i], 3).tolist(), 'piece', pc[i], pc[j], dom(i), dom(j))
