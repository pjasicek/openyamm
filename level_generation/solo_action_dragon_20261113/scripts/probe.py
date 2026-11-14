# Blender: print the MM8 Dragon's bone head positions in the Standing pose (world space) and the mesh bounds.
import bpy, sys
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=sys.argv[sys.argv.index('--') + 1])
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
act = bpy.data.actions.get('Standing') or next(a for a in bpy.data.actions if 'Standing' in a.name)
arm.animation_data.action = act
bpy.context.scene.frame_set(1)
for b in arm.pose.bones:
    h = arm.matrix_world @ b.head; t = arm.matrix_world @ b.tail
    print('BONE', b.name, tuple(round(v, 3) for v in h), tuple(round(v, 3) for v in t))
for o in bpy.data.objects:
    if o.type == 'MESH' and o.visible_get():
        import mathutils
        cs = [o.matrix_world @ mathutils.Vector(c) for c in o.bound_box]
        print('MESH', o.name, [round(min(c[i] for c in cs), 3) for i in range(3)], [round(max(c[i] for c in cs), 3) for i in range(3)], len(o.data.polygons))
print('ACTIONS', [a.name for a in bpy.data.actions])
