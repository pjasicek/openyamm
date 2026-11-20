"""Locate the most stretched edges at one action frame: posed/rest length ratio, both vertices' piece, rest position and
top weights. Args: -- <blend> <action> <frame> [n]"""
import bpy, sys, os
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
blend, action, frame = a[0], a[1], int(a[2]); n = int(a[3]) if len(a) > 3 else 12
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
rest = np.array([tuple(body.matrix_world @ v.co) for v in me.vertices])
act = bpy.data.actions[action]; rig.animation_data.action = act
if len(act.slots):
    rig.animation_data.action_slot = act.slots[0]
bpy.context.scene.frame_set(frame)
ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
P = np.array([tuple(body.matrix_world @ v.co) for v in m.vertices]); ev.to_mesh_clear()
E = np.array([tuple(e.vertices) for e in me.edges])
r = np.linalg.norm(P[E[:, 0]] - P[E[:, 1]], axis=1) / np.maximum(np.linalg.norm(rest[E[:, 0]] - rest[E[:, 1]], axis=1), 1e-6)
gn = {g.index: g.name for g in body.vertex_groups}
def top(i):
    return sorted([(round(e.weight, 2), gn[e.group]) for e in me.vertices[i].groups if e.weight > 0.02], reverse=True)[:3]
for k in np.argsort(-r)[:n]:
    i, j = E[k]
    print(f'EDGE {r[k]:.2f}x v{i} p{pv[i]} {np.round(rest[i], 3).tolist()} {top(i)} | v{j} p{pv[j]} {top(j)}')
for p in sorted(set(pv.tolist())):
    m_ = (pv[E[:, 0]] == p)
    print(f'PIECE {p}: p99 {np.percentile(r[m_], 99):.2f} max {r[m_].max():.2f}')
