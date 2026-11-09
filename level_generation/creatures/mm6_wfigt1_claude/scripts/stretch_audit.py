"""Edge stretch around the shoulders: edges whose vertices carry upper-arm or clavicle weight between 0.1 and 0.9
(the armpit/lat/pec transition), length ratio to the bind pose per frame; prints the worst ratio and the share of
those edges stretched beyond 1.35. Args: blend clip[,clip]"""
import bpy, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
args = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, args[0]))
arm = bpy.data.objects['Werewolf_Rig']; mesh = bpy.data.objects['Werewolf']; me = mesh.data
G = {g.index: g.name for g in mesh.vertex_groups}
sel = set()
for v in me.vertices:
    w = sum(g.weight for g in v.groups if G[g.group] in ('LeftArm', 'RightArm', 'LeftShoulder', 'RightShoulder'))
    if 0.1 < w < 0.9:
        sel.add(v.index)
E = np.array([e.vertices[:] for e in me.edges if e.vertices[0] in sel and e.vertices[1] in sel])


def verts():
    ev = mesh.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
    P = np.array([tuple(v.co) for v in m.vertices]); ev.to_mesh_clear(); return P


arm.animation_data.action = None
for pb in arm.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
P0 = verts(); L0 = np.linalg.norm(P0[E[:, 0]] - P0[E[:, 1]], axis=1)
for clip in args[1].split(','):
    a = bpy.data.actions[clip]; arm.animation_data.action = a
    if a.slots: arm.animation_data.action_slot = a.slots[0]
    rows = []
    for f in range(int(a.frame_range[1]) + 1):
        bpy.context.scene.frame_set(f); P = verts()
        r = np.linalg.norm(P[E[:, 0]] - P[E[:, 1]], axis=1) / np.maximum(L0, 1e-6)
        rows.append((f, round(float(np.percentile(r, 99.5)), 2), round(float((r > 1.35).mean() * 100), 1)))
    w = max(rows, key=lambda x: x[2])
    print('STRETCH', clip, 'edges', len(E), 'worst frame', w[0], 'p99.5 ratio', w[1], 'worst % >1.35:', max(x[2] for x in rows))
