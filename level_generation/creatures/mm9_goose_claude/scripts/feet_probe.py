"""Foot orientation probe at a clip time: per foot, MM9 or ours: ankle (Xfoot joint), toe-tip mean direction in the
ground plane, sole tilt (best-fit plane normal of the foot vertices against vertical). Args: <blend> <action> <frame> [mesh]"""
import bpy, sys, math
import numpy as np
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
sc = bpy.context.scene
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
if argv[1] == '-':
    if arm.animation_data:
        arm.animation_data.action = None
    for pb in arm.pose.bones:
        pb.matrix_basis.identity()
else:
    act = bpy.data.actions[argv[1]]
    arm.animation_data.action = act
    try:
        arm.animation_data.action_slot = act.slots[0]
    except Exception:
        pass
    sc.frame_set(int(argv[2]))
bpy.context.view_layer.update()
ob = next(o for o in bpy.data.objects if o.type == 'MESH' and not o.name.startswith('Icosphere'))
dg = bpy.context.evaluated_depsgraph_get()
ev = ob.evaluated_get(dg).to_mesh()
P = np.array([tuple(ob.matrix_world @ v.co) for v in ev.vertices])
gi = {g.index: g.name for g in ob.vertex_groups}
W = {}
for v in ob.data.vertices:
    for g in v.groups:
        W.setdefault(gi[g.group], []).append((v.index, g.weight))
for foot, toes in (('Xfoot', ('Xtoea', 'Xtoeb', 'Xtoec')), ('Xfoot01', ('Xtoea01', 'Xtoeb01', 'Xtoec01'))):
    ids = sorted({i for t in toes for i, w in W.get(t, []) if w > 0.15})
    Q = P[ids]
    a = np.array(arm.matrix_world @ arm.pose.bones[foot].head)
    c = Q.mean(0)
    u, s, vt = np.linalg.svd(Q - c)
    n = vt[2] if vt[2][2] > 0 else -vt[2]
    tilt = math.degrees(math.acos(min(1, n[2])))
    d = Q[np.argmax(np.linalg.norm((Q - a)[:, :2], axis=1))] - a
    print('FOOT', foot, 'ankle', np.round(a, 3).tolist(), 'toe centroid', np.round(c, 3).tolist(), 'tilt %.1f' % tilt,
          'normal', np.round(n, 2).tolist(), 'yaw(toe centroid) %.1f' % math.degrees(math.atan2(c[1] - a[1], c[0] - a[0])), 'zmin %.3f' % Q[:, 2].min())
