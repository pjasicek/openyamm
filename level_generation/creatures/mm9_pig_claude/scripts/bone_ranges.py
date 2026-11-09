"""Per clip and bone: max rotation (deg) of the pose-bone basis from its rest, and max location offset (m).
Args: <rig blend>"""
import bpy, sys, math
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
sc = bpy.context.scene
arm = bpy.data.objects['MM9_Rig']
arm.animation_data_create()
for act in bpy.data.actions:
    arm.animation_data.action = act
    try:
        arm.animation_data.action_slot = act.slots[0]
    except Exception:
        pass
    f0, f1 = act.frame_range
    mx = {}
    f = f0
    while f <= f1 + 1e-6:
        sc.frame_set(int(f), subframe=f - int(f))
        for pb in arm.pose.bones:
            q = pb.matrix_basis.to_quaternion()
            a = math.degrees(min(q.angle, 2 * math.pi - q.angle))
            l = pb.matrix_basis.to_translation().length
            o = mx.get(pb.name, (0, 0))
            mx[pb.name] = (max(o[0], a), max(o[1], l))
        f += 0.5
    print('CLIP', act.name, ' '.join('%s:%.0f/%.3f' % (k, v[0], v[1]) for k, v in mx.items() if v[0] > 1 or v[1] > 0.002))
