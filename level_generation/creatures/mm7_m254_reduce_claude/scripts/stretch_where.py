"""Where the G4 arm stretch sits (m254 reduce): the most stretched arm-region edges (verts with upper-arm + forearm +
hand weight > 0.3, the G4 selection) of a gate scene at one frame, with rest midpoints and the count over a ratio.
Args: -- <gate blend> <action:frame> <side L|R> [ratio, default 2.5]"""
import bpy, sys, os
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0])); act, fr = a[1].rsplit(':', 1); s = a[2]
R = float(a[3]) if len(a) > 3 else 2.5
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
names = {g.index: g.name for g in body.vertex_groups}; nv = len(me.vertices)
rest = np.array([tuple(v.co) for v in me.vertices]); armw = np.zeros(nv)
for v in me.vertices:
    armw[v.index] = sum(e.weight for e in v.groups if names[e.group] in (f'B_{s}_UpperArm', f'B_{s}_Forearm', f'B_{s}_Hand'))
E = np.array([tuple(e.vertices) for e in me.edges]); E = E[(armw[E[:, 0]] > .3) & (armw[E[:, 1]] > .3)]
rl = np.linalg.norm(rest[E[:, 0]] - rest[E[:, 1]], axis=1)
A = bpy.data.actions[act]; rig.animation_data.action = A
if len(A.slots):
    rig.animation_data.action_slot = A.slots[0]
bpy.context.scene.frame_set(int(fr))
ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
co = np.empty(nv * 3); m.vertices.foreach_get('co', co); ev.to_mesh_clear(); co = co.reshape(-1, 3)
st = np.linalg.norm(co[E[:, 0]] - co[E[:, 1]], axis=1) / np.maximum(rl, 1e-6)
o = np.argsort(-st)
print('STRETCH', a[1], s, 'edges', len(E), 'p99', round(float(np.percentile(st, 99)), 2), f'over {R}', int((st > R).sum()),
      'rest length of edges over: mean mm', round(float(rl[st > R].mean() * 1000), 1) if (st > R).any() else 0)
for i in o[:8]:
    print('STRETCH  ', round(float(st[i]), 2), 'rest mid', np.round(rest[E[i]].mean(0), 3).tolist(), 'len mm', round(float(rl[i] * 1000), 1))
