"""Print rest directions of key Mixamo bones and frame-0 pose summary. Args: -- <fbx>"""
import bpy, sys
f = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=f)
arm = next(o for o in bpy.context.scene.objects if o.type == 'ARMATURE')
print('BONES', len(arm.data.bones), 'scale', tuple(round(s, 3) for s in arm.scale))
for n in ('Hips', 'LeftArm', 'LeftForeArm', 'RightArm', 'LeftUpLeg', 'Head'):
    b = arm.data.bones.get('mixamorig:' + n)
    if b:
        v = (arm.matrix_world.to_3x3() @ (b.tail_local - b.head_local)).normalized()
        h = arm.matrix_world @ b.head_local
        print('REST', n, 'dir', tuple(round(x, 2) for x in v), 'head', tuple(round(x, 2) for x in h))
