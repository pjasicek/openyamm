"""Print the MM9 bind arm angle below horizontal (shoulder->hand) of a converted MM9 GLB. Blender. Args: <glb>"""
import bpy, sys, math
glb = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
arm = next(o for o in bpy.context.scene.objects if o.type == 'ARMATURE')
if arm.animation_data: arm.animation_data.action = None
for pb in arm.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
for s in 'LR':
    a = arm.matrix_world @ arm.pose.bones[f'Bip01 {s} UpperArm'].head
    f = arm.matrix_world @ arm.pose.bones[f'Bip01 {s} Forearm'].head
    h = arm.matrix_world @ arm.pose.bones[f'Bip01 {s} Hand'].head
    d = h - a
    print('ARM', s, 'shoulder', [round(x, 3) for x in a], 'hand', [round(x, 3) for x in h],
          'deg below horizontal %.1f' % math.degrees(math.atan2(-d.z, math.hypot(d.x, d.y))))
