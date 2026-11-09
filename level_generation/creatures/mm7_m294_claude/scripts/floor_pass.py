"""Sole floor pass (necromancer; playbook "Feet and locomotion": a floor pass per frame on the lowest sole). Per frame
of each listed clip the lowest foot vertex (Foot/Toe weight > 0.5) is measured on the skinned mesh and the pelvis is
moved vertically so it sits at FLOOR (0.3 cm); the per-frame offsets are smoothed (Gaussian SIG frames, circular for
loops) so the bob of the source survives. sole_probe.py found the heeled boots floating 1-6 cm through the whole
RelaxWalkFemale cycle and up to 9.5 cm in the planted hit (the pelvis tilt lifts held legs).
Args: -- <in blend> <out blend> <Action> [...]"""
import bpy, sys, os
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
src, out, acts = a[0], a[1], a[2:]
FLOOR, SIG = 0.003, float(os.environ.get('FLOOR_SIG', '1.0'))
LOOPS = {'Standing', 'Walking', 'Fidget'}
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
scene = bpy.context.scene; rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
AW = rig.matrix_world
names = [g.name for g in body.vertex_groups]
FOOT = np.array([sum(e.weight for e in v.groups if names[e.group].startswith(('B_L_Foot', 'B_R_Foot', 'B_L_Toe', 'B_R_Toe'))) > 0.5
                 for v in me.vertices])
for an in acts:
    act = bpy.data.actions[an]; rig.animation_data.action = act
    if len(act.slots): rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(round(x)) for x in act.frame_range); n = f1 - f0 + 1
    low = []
    for f in range(f0, f1 + 1):
        scene.frame_set(f)
        ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
        z = np.array([(body.matrix_world @ v.co).z for v in m.vertices])[FOOT]; ev.to_mesh_clear()
        low.append(float(z.min()))
    d = FLOOR - np.array(low)
    k = np.exp(-0.5 * (np.arange(-4, 5) / max(SIG, 1e-3)) ** 2); k /= k.sum()
    if an in LOOPS and n > 9:
        pad = np.concatenate([d[-4:], d, d[:4]])
    else:
        pad = np.concatenate([np.repeat(d[:1], 4), d, np.repeat(d[-1:], 4)])
    ds = np.convolve(pad, k, 'valid')
    pb = rig.pose.bones['B_Pelvis']
    for i, f in enumerate(range(f0, f1 + 1)):
        scene.frame_set(f)
        M = AW @ pb.matrix; M.translation.z += float(ds[i])
        pb.matrix = AW.inverted() @ M; bpy.context.view_layer.update()
        pb.keyframe_insert('location', frame=f)
    print(f'FLOOR {an}: lowest sole before {min(low) * 100:.1f}..{max(low) * 100:.1f} cm, shift {ds.min() * 100:.1f}..{ds.max() * 100:.1f} cm')
rig.animation_data.action = None
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
