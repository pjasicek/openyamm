import bpy, sys, math
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=argv[0])
arm = next(o for o in bpy.context.scene.objects if o.type == 'ARMATURE')
for pb in arm.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
def head(n): return arm.matrix_world @ arm.pose.bones[n].head
for n in arm.pose.bones.keys():
    print('J', n, tuple(round(x, 3) for x in head(n)))
for s in 'LR':
    a, b, c = head(f'Bip01 {s} UpperArm'), head(f'Bip01 {s} Forearm'), head(f'Bip01 {s} Hand')
    d = c - a
    print('ARM', s, 'below horizontal deg', round(math.degrees(math.atan2(-d.z, math.hypot(d.x, d.y))), 1), 'len', round((b-a).length,3), round((c-b).length,3))
