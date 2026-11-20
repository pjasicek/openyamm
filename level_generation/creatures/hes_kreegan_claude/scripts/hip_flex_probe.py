"""hkr: per clip, each thigh's forward flexion relative to the pelvis (deg, as helper_bones.py measures it: the thigh
axis turned toward -Y about the pelvis X axis), max and the frames above LIM. Args: -- <blend> <clip> [...]"""
import bpy, sys, os, math
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
rig = bpy.data.objects['Rig']; sc = bpy.context.scene; LIM = float(os.environ.get('LIM', '60'))
REST = lambda n: rig.data.bones[n].matrix_local.to_3x3()
for clip in a[1:]:
    act = bpy.data.actions[clip]; rig.animation_data.action = act
    if len(act.slots): rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(x) for x in act.frame_range); out = {}
    for s in 'LR':
        vals = []
        for f in range(f0, f1 + 1):
            sc.frame_set(f)
            pel = rig.pose.bones['B_Pelvis']; Pm = pel.matrix.to_3x3(); Pr = REST('B_Pelvis'); th = rig.pose.bones[f'B_{s}_Thigh']
            d0 = Pr.inverted() @ REST(th.name).col[1]; d1 = Pm.inverted() @ th.matrix.to_3x3().col[1]
            w0, w1 = Pr @ d0, Pr @ d1
            vals.append(math.degrees(math.atan2(-w1.y, -w1.z) - math.atan2(-w0.y, -w0.z)))
        out[s] = (round(max(vals), 1), [f for f, v in zip(range(f0, f1 + 1), vals) if v > LIM])
    print('HIPFLEX', clip, out)
