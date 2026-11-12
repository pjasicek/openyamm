"""Print a GLB's armature (joint world rest positions, parents), actions and mesh bounds. Args: <glb>"""
import bpy, sys
import numpy as np
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=sys.argv[sys.argv.index('--') + 1])
for o in bpy.context.scene.objects:
    if o.type == 'ARMATURE':
        if o.animation_data: o.animation_data.action = None
        for b in o.data.bones:
            h = o.matrix_world @ b.head_local
            print('BONE', b.name, '<-', b.parent.name if b.parent else None, [round(x, 3) for x in h])
    elif o.type == 'MESH':
        q = np.array([tuple(o.matrix_world @ v.co) for v in o.data.vertices])
        print('MESH', o.name, len(o.data.polygons), q.min(0).round(3).tolist(), q.max(0).round(3).tolist())
for a in bpy.data.actions:
    print('ACT', a.name, [round(x, 2) for x in a.frame_range])
