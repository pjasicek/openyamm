import bpy, sys
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.import_scene.gltf(filepath=argv[0])
arm = next(o for o in bpy.context.scene.objects if o.type == 'ARMATURE')
for n in argv[1:]:
    b = arm.data.bones[n]; print('BONE', n, [round(x, 3) for x in (arm.matrix_world @ b.head_local)])
ms = [o for o in bpy.context.scene.objects if o.type == 'MESH' and not o.name.startswith('Icosphere')]
pts = [o.matrix_world @ v.co for o in ms for v in o.data.vertices]
print('BBOX', [(round(min(p[i] for p in pts), 3), round(max(p[i] for p in pts), 3)) for i in range(3)])
