"""Worst stretched edges of one garment at one frame: rest positions of both ends, opening (cm), top bones.
Args: -- <blend> <action> <frame> <garment> [n]"""
import bpy, sys, os
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
act = bpy.data.actions[a[1]]; rig.animation_data.action = act
if len(act.slots): rig.animation_data.action_slot = act.slots[0]
bpy.context.scene.frame_set(int(float(a[2])), subframe=float(a[2]) % 1)
g = int(a[3]); n = int(a[4]) if len(a) > 4 else 8
gv = np.array([x.value for x in me.attributes['garment'].data]); rest = np.array([v.co[:] for v in me.vertices])
ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
P = np.array([(body.matrix_world @ v.co)[:] for v in m.vertices]); ev.to_mesh_clear()
E = np.array([tuple(e.vertices) for e in me.edges]); E = E[(gv[E[:, 0]] == g) & (gv[E[:, 1]] == g)]
op = np.linalg.norm(P[E[:, 0]] - P[E[:, 1]], axis=1) - np.linalg.norm(rest[E[:, 0]] - rest[E[:, 1]], axis=1)
names = {gr.index: gr.name for gr in body.vertex_groups}
top = lambda i: ','.join(f'{names[x.group]}:{x.weight:.2f}' for x in sorted(me.vertices[i].groups, key=lambda x: -x.weight)[:3])
for k in np.argsort(-op)[:n]:
    i, j = E[k]
    print('EDGE', round(op[k] * 100, 1), 'cm', np.round(rest[i], 3), top(i), '|', np.round(rest[j], 3), top(j))
