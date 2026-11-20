"""Edge stretch per clip (posed/rest edge length over every frame): p99 and max, the dominant bone at the worst edge.
Args: -- <blend> <action> [...]"""
import bpy, sys, os
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data; sc = bpy.context.scene
E = np.array([tuple(e.vertices) for e in me.edges]); rest = np.array([tuple(v.co) for v in me.vertices])
L0 = np.linalg.norm(rest[E[:, 0]] - rest[E[:, 1]], axis=1)
vg = [g.name for g in body.vertex_groups]
dom = [vg[max(v.groups, key=lambda e: e.weight).group] if len(v.groups) else '-' for v in me.vertices]
for an in a[1:]:
    act = bpy.data.actions[an]; rig.animation_data.action = act
    if getattr(act, 'slots', None) is not None and len(act.slots): rig.animation_data.action_slot = act.slots[0]
    worst = np.zeros(len(E)); wf = np.zeros(len(E))
    for f in range(int(act.frame_range[1]) + 1):
        sc.frame_set(f); ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
        p = np.array([tuple(v.co) for v in m.vertices]); ev.to_mesh_clear()
        r = np.linalg.norm(p[E[:, 0]] - p[E[:, 1]], axis=1) / np.maximum(L0, 1e-6)
        upd = r > worst; worst[upd] = r[upd]; wf[upd] = f
    i = int(np.argmax(worst))
    print(f'STRETCH {an}: p99 {np.percentile(worst, 99):.2f} max {worst[i]:.2f} at frame {int(wf[i])} ({dom[E[i, 0]]})')
