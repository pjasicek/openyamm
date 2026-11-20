"""Probe: the faces that stretch most (largest edge length ratio vs rest) over listed actions, with their shell, the
dominant bones of their vertices and their rest centre. Args: -- <blend> <action> [...]   (env TOP=12)"""
import bpy, sys, os
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0])); acts = a[1:]
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data; sc = bpy.context.scene
names = [g.name for g in body.vertex_groups]
pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
rest = np.array([tuple(v.co) for v in me.vertices])
E = np.array([tuple(e.vertices) for e in me.edges]); L0 = np.linalg.norm(rest[E[:, 0]] - rest[E[:, 1]], axis=1)
worst = np.ones(len(E)); wf = [''] * len(E)
for an in acts:
    act = bpy.data.actions[an]; rig.animation_data.action = act
    if len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    for f in range(int(act.frame_range[0]), int(act.frame_range[1]) + 1):
        sc.frame_set(f)
        ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
        co = np.empty(len(m.vertices) * 3); m.vertices.foreach_get('co', co); ev.to_mesh_clear(); co = co.reshape(-1, 3)
        r = np.linalg.norm(co[E[:, 0]] - co[E[:, 1]], axis=1) / np.maximum(L0, 1e-6)
        up = r > worst; worst[up] = r[up]
        for i in np.where(up)[0]:
            wf[i] = f'{an}:{f}'
def dom(v):
    g = sorted(me.vertices[v].groups, key=lambda e: -e.weight)[:2]
    return '/'.join(f'{names[e.group][2:]}{e.weight:.2f}' for e in g)
for i in np.argsort(-worst)[:int(os.environ.get('TOP', '12'))]:
    a_, b_ = E[i]
    print(f'STRETCH edge {a_}-{b_} x{worst[i]:.2f} at {wf[i]} rest {L0[i] * 100:.1f} cm piece {pv[a_]}/{pv[b_]} '
          f'{dom(a_)} | {dom(b_)} centre {np.round((rest[a_] + rest[b_]) / 2, 3)}')
