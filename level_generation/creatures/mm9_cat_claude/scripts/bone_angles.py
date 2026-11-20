"""Per clip: max rotation (deg) of the listed bones against the bind pose, and when it peaks.
Args: <glb> <bone,bone,...>"""
import bpy, sys, math
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=argv[0])
sc = bpy.context.scene
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
names = argv[1].split(',')
for act in bpy.data.actions:
    arm.animation_data.action = act
    try:
        arm.animation_data.action_slot = act.slots[0]
    except Exception:
        pass
    f0, f1 = act.frame_range
    res = {}
    f = f0
    while f <= f1 + 1e-6:
        sc.frame_set(int(f), subframe=f - int(f))
        for n in names:
            pb = arm.pose.bones[n]
            q = pb.matrix_basis.to_quaternion()
            a = math.degrees(q.angle if q.angle <= math.pi else 2 * math.pi - q.angle)
            if a > res.get(n, (-1, 0))[0]:
                res[n] = (a, f / (sc.render.fps / sc.render.fps_base))
        f += 0.5
    print('ANG %-12s' % act.name, ' '.join('%s %.1f@%.2fs' % (n, *res[n]) for n in names))
