"""Per clip: frame range and the max rotation (deg) of each bone away from its bind, plus jaw angle stats.
Args: <glb>"""
import bpy, sys, json, math
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=argv[0])
sc = bpy.context.scene
arm = next(o for o in sc.objects if o.type == 'ARMATURE')
out = {}
for act in bpy.data.actions:
    arm.animation_data.action = act
    f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
    mx = {}
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        for pb in arm.pose.bones:
            q = pb.matrix_basis.to_quaternion()
            a = math.degrees(q.angle) if q.angle <= math.pi else 360 - math.degrees(q.angle)
            t = pb.matrix_basis.translation.length
            m = mx.setdefault(pb.name, [0, 0])
            m[0] = max(m[0], a); m[1] = max(m[1], t)
    out[act.name] = {'frames': [f0, f1], 'bones': {k: [round(v[0], 1), round(v[1], 4)] for k, v in mx.items() if v[0] > 2 or v[1] > 0.005}}
print('CLIPS ' + json.dumps(out))
