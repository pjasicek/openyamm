"""Print objects, bones, actions and mesh bounds of a GLB. Args: glb"""
import bpy, sys
import numpy as np
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=sys.argv[sys.argv.index('--') + 1])
for o in bpy.data.objects:
    line = f'OBJ {o.name} {o.type} parent={o.parent.name if o.parent else None} scale={tuple(round(s, 4) for s in o.scale)}'
    if o.type == 'MESH':
        co = np.array([tuple(o.matrix_world @ v.co) for v in o.data.vertices])
        line += f' verts={len(co)} lo={co.min(0).round(3)} hi={co.max(0).round(3)} groups={len(o.vertex_groups)}'
    print(line)
    if o.type == 'ARMATURE':
        print('BONES', len(o.data.bones), [b.name for b in o.data.bones])
for a in bpy.data.actions:
    print('ACTION', a.name, tuple(a.frame_range))
