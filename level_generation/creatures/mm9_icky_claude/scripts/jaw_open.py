"""Mouth opening over role clips: mean petal rotation (Xjaw* + Xjawpiv* vs rest) and mouth-tip forward reach per frame."""
import bpy, sys, json, math
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
sc = bpy.context.scene
rig = next(o for o in sc.objects if o.type == 'ARMATURE')
petals = [b for b in rig.pose.bones if b.name.startswith('Xjawpiv')]
out = {}
for name in argv[1:]:
    act = bpy.data.actions[name]
    rig.animation_data.action = act
    f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
    rows = []
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        ang = sum(math.degrees(pb.matrix_basis.to_quaternion().angle) for pb in petals) / len(petals)
        head = rig.matrix_world @ rig.pose.bones['Xhead'].head
        rows.append([f, round(f / sc.render.fps, 3), round(ang, 1), round(head.y, 3), round(head.z, 3)])
    out[name] = rows
print('JAW ' + json.dumps(out))
