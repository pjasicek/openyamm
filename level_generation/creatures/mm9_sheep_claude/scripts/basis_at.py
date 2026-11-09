"""Print pose-bone basis (location, rotation deg) of chosen bones at clip@frame for several clips. Args: <rig blend> <bones,> <clip@frame ...>"""
import bpy, sys, math
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
arm = bpy.data.objects['MM9_Rig']
sc = bpy.context.scene
for cf in argv[2:]:
    c, f = cf.split('@')
    arm.animation_data.action = bpy.data.actions[c]
    sc.frame_set(int(f))
    for b in argv[1].split(','):
        pb = arm.pose.bones[b]
        m = pb.matrix_basis
        q = m.to_quaternion()
        e = [round(math.degrees(x), 1) for x in q.to_euler()]
        print('BASIS', cf, b, [round(x, 4) for x in m.translation], e)
