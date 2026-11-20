"""Print armature bone head/tail world positions (Blender frame) of a GLB. Args: <glb>"""
import bpy, sys
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a[0])
arm = next(o for o in bpy.context.scene.objects if o.type == 'ARMATURE')
if arm.animation_data: arm.animation_data.action = None
for pb in arm.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
for pb in arm.pose.bones:
    h = arm.matrix_world @ pb.head
    print('BONE', pb.name, [round(x, 3) for x in h])
