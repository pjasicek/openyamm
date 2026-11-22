import bpy, sys
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=argv[0])
arm = next(o for o in bpy.context.scene.objects if o.type == 'ARMATURE')
print('BONES', ' '.join(b.name for b in arm.data.bones))
ico = [o for o in bpy.context.scene.objects if o.name.startswith('Icosphere')]
for o in ico: print('ICO', o.name, o.parent and o.parent.name, o.parent_bone, o.dimensions[:], o.location[:])
for o in bpy.context.scene.objects: print('OBJ', o.name, o.type, o.parent and o.parent.name, tuple(round(x,3) for x in o.dimensions), o.scale[:], o.rotation_mode, tuple(o.rotation_euler))
