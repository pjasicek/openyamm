import bpy, sys, json
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=argv[0])
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
if arm.animation_data: arm.animation_data.action = None
for pb in arm.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
J = {b.name: list(arm.matrix_world @ b.head_local) for b in arm.data.bones}
json.dump(J, open(argv[1], 'w'), indent=0)
for k in ('Bip01 Head', 'Bip01 Neck', 'Bip01 R Hand', 'Bip01 L Hand', 'Bip01 Spine', 'Bip01 R Foot', 'Bip01 Ponytail1'): print('JOINT', k, J[k])
