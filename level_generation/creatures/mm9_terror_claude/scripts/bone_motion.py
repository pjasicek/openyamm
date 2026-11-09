"""Per bone: max basis rotation (deg) and translation (m) over every MM9 clip. Args: <mm9 glb>"""
import bpy, sys, math, json
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=argv[0])
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
sc = bpy.context.scene
res = {}
for act in bpy.data.actions:
    arm.animation_data.action = act
    try:
        arm.animation_data.action_slot = act.slots[0]
    except Exception:
        pass
    f0, f1 = act.frame_range
    for f in range(int(f0), int(f1) + 1, 2):
        sc.frame_set(f)
        for pb in arm.pose.bones:
            q = pb.matrix_basis.to_quaternion(); a = math.degrees(q.angle); a = min(a, 360 - a)
            t = pb.matrix_basis.translation.length
            r = res.setdefault(pb.name, [0, 0, ''])
            if a > r[0]:
                r[0] = a; r[2] = act.name
            r[1] = max(r[1], t)
print('MOTION ' + json.dumps({k: [round(v[0], 1), round(v[1], 3), v[2]] for k, v in res.items()}))
