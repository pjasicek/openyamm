"""Print the private arms GLB's frame: Camera01, the root and the hands' positions in Blender space after import."""
import sys
import bpy

path = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=path)
for obj in bpy.data.objects:
    if obj.parent is None:
        print('ROOT', obj.name, obj.type, tuple(round(v, 3) for v in obj.matrix_world.to_euler()), tuple(obj.scale))
cam = bpy.data.objects.get('Camera01')
arm = next((o for o in bpy.data.objects if o.type == 'ARMATURE'), None)
print('ARMATURE', arm.name if arm else None)
if arm:
    for name in ('Camera01', 'Bip01 R Hand', 'Bip01 L Hand', 'Weapon', 'Bip01'):
        b = arm.pose.bones.get(name)
        if b:
            m = arm.matrix_world @ b.matrix
            print('BONE', name, tuple(round(v, 2) for v in m.translation), 'y-axis', tuple(round(v, 2) for v in m.to_3x3().col[1]))
if cam:
    print('CAMOBJ', tuple(round(v, 2) for v in cam.matrix_world.translation))
