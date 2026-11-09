"""Where the worst-stretched edges are at one action frame: rest midpoint, garment, piece, top weights.
Args: -- <blend> <action> <frame> [N] [garments comma]"""
import bpy, sys, numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
act = bpy.data.actions[a[1]]; rig.animation_data.action = act; rig.animation_data.action_slot = act.slots[0]
bpy.context.scene.frame_set(int(float(a[2])), subframe=float(a[2]) % 1)
N = int(a[3]) if len(a) > 3 else 15
G = [int(x) for x in a[4].split(',')] if len(a) > 4 else None
P0 = np.array([v.co[:] for v in me.vertices])
ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh(); P = np.array([v.co[:] for v in m.vertices]); ev.to_mesh_clear()
gv = np.array([x.value for x in me.attributes['garment'].data]); pv = np.array([x.value for x in me.attributes['piece'].data])
E = np.array([e.vertices[:] for e in me.edges])
s = np.linalg.norm(P[E[:, 0]] - P[E[:, 1]], axis=1) / np.maximum(np.linalg.norm(P0[E[:, 0]] - P0[E[:, 1]], axis=1), 1e-6)
if G is not None:
    s[~(np.isin(gv[E[:, 0]], G) & np.isin(gv[E[:, 1]], G))] = 0
names = [g.name for g in body.vertex_groups]
for k in np.argsort(-s)[:N]:
    i, j = E[k]
    wi = sorted([(names[e.group], round(e.weight, 2)) for e in me.vertices[i].groups], key=lambda t: -t[1])[:3]
    wj = sorted([(names[e.group], round(e.weight, 2)) for e in me.vertices[j].groups], key=lambda t: -t[1])[:3]
    print('EDGE', round(float(s[k]), 2), 'g', gv[i], 'p', pv[i], np.round((P0[i] + P0[j]) / 2, 3).tolist(), wi, '|', wj)
