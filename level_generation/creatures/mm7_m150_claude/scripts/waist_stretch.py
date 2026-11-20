"""Edge stretch on the torso shell's waist (piece 0, z 0.85-1.25, |x| < 0.3) per clip: p99 and max of posed/rest edge
length ratio over every 2nd frame. Args: -- <blend> clip [...]"""
import bpy, sys, os
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
co = np.array([tuple(v.co) for v in me.vertices])
pv = np.zeros(len(co), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
E = np.array([tuple(e.vertices) for e in me.edges])
sel = (pv[E[:, 0]] == 0) & (co[E[:, 0], 2] > 0.85) & (co[E[:, 0], 2] < 1.25) & (np.abs(co[E[:, 0], 0]) < 0.3)
E = E[sel]; L0 = np.linalg.norm(co[E[:, 0]] - co[E[:, 1]], axis=1)
for c in a[1:]:
    act = bpy.data.actions[c]; rig.animation_data_create(); rig.animation_data.action = act
    if getattr(act, 'slots', None) is not None and len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    rs = []
    for f in range(int(act.frame_range[0]), int(act.frame_range[1]) + 1, 2):
        bpy.context.scene.frame_set(f)
        ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
        P = np.array([tuple(v.co) for v in m.vertices]); ev.to_mesh_clear()
        rs.append(np.linalg.norm(P[E[:, 0]] - P[E[:, 1]], axis=1) / np.maximum(L0, 1e-6))
    R_ = np.array(rs); R_ = np.maximum(R_, 1 / np.maximum(R_, 1e-6)); r = R_.ravel()
    k = int(np.argmax(R_.max(0))); e = E[k]
    print('WAIST', c, 'edges', len(E), 'p99', round(float(np.percentile(r, 99)), 2), 'max', round(float(r.max()), 2),
          'worst edge at', np.round(co[e[0]], 3).tolist(), 'edges > 2.5x:', int((R_.max(0) > 2.5).sum()))
