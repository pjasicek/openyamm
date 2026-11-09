"""Sole flatness probe for the gargoyle's clawed feet: per action, frame and foot, the REST sole vertices (Foot/Toe0
weighted > 0.5 and within SOLE_Z of the floor in the rest pose: the toe pads, claws and the pad under the ball) are
measured on the skinned mesh: lowest z, spread (max - min z of the sole set) and the world rotation of B_<s>_Foot and
B_<s>_Toe0 away from their rest orientation. A planted foot (lowest sole < 2 cm) should be flat: spread close to the
rest spread and both rotations near 0. Prints the worst planted frame per action and foot.
Args: -- <blend> <action> [...]"""
import bpy, sys, os, math
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data; sc = bpy.context.scene
SOLE_Z = float(os.environ.get('SOLE_Z', '0.015'))
names = [g.name for g in body.vertex_groups]
rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
rest = np.array([tuple(body.matrix_world @ v.co) for v in me.vertices])
SOLE, RR = {}, {}
for s in 'LR':
    m = np.array([sum(e.weight for e in v.groups if names[e.group] in (f'B_{s}_Foot', f'B_{s}_Toe0')) > 0.5 for v in me.vertices])
    SOLE[s] = np.where(m & (rest[:, 2] < rest[m][:, 2].min() + SOLE_Z))[0]
    for b in ('Foot', 'Toe0'):
        RR[(s, b)] = (rig.matrix_world @ rig.pose.bones[f'B_{s}_{b}'].matrix).to_quaternion()
    print('SOLEFLAT rest', s, 'sole vertices', len(SOLE[s]), 'spread cm', round(float(np.ptp(rest[SOLE[s], 2])) * 100, 2))
for name in a[1:]:
    act = bpy.data.actions[name]; rig.animation_data.action = act
    if getattr(act, 'slots', None) is not None and len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
    worst = {s: None for s in 'LR'}
    for f in range(f0, f1 + 1):
        sc.frame_set(f); deps = bpy.context.evaluated_depsgraph_get()
        ev = body.evaluated_get(deps); mm = ev.to_mesh()
        for s in 'LR':
            z = np.array([(body.matrix_world @ mm.vertices[i].co).z for i in SOLE[s]])
            planted = z.min() <= 0.02
            rf = math.degrees((rig.matrix_world @ rig.pose.bones[f'B_{s}_Foot'].matrix).to_quaternion().rotation_difference(RR[(s, 'Foot')]).angle)
            rt = math.degrees((rig.matrix_world @ rig.pose.bones[f'B_{s}_Toe0'].matrix).to_quaternion().rotation_difference(RR[(s, 'Toe0')]).angle)
            rec = (round(float(np.ptp(z)) * 100, 1), f, round(float(z.min()) * 100, 1), round(rf, 1), round(rt, 1))
            if f == f0:
                print('SOLEFLAT', name, s, 'frame0 (spread cm, frame, lowest cm, foot deg, toe deg):', rec)
            if planted and (worst[s] is None or rec[0] > worst[s][0]):
                worst[s] = rec
        ev.to_mesh_clear()
    for s in 'LR':
        print('SOLEFLAT', name, s, 'worst planted (spread cm, frame, lowest cm, foot deg, toe deg):', worst[s])
