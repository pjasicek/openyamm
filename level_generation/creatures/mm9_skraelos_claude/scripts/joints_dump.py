"""Print every joint's rest head (world) of a GLB's armature. Args: <glb>"""
import bpy, sys
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a[0])
arm = next(o for o in bpy.context.scene.objects if o.type == 'ARMATURE')
for b in arm.data.bones:
    h = arm.matrix_world @ b.head_local
    print('JOINT %-22s %7.3f %7.3f %7.3f' % (b.name, h.x, h.y, h.z))
