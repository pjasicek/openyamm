import bpy, sys, os, json
import numpy as np
PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(PROJ, 'work/before_rebuild/mm6_ttn.glb'))
for o in bpy.data.objects:
    print('OBJ', o.name, o.type, o.parent.name if o.parent else None, [m.type for m in getattr(o, 'modifiers', [])])
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
for b in rig.data.bones:
    print('BONE', b.name, b.parent.name if b.parent else None, [round(x, 3) for x in (rig.matrix_world @ b.head_local)], [round(x, 3) for x in (rig.matrix_world @ b.tail_local)])
body = next(o for o in bpy.data.objects if o.type == 'MESH')
print('MESH', body.name, len(body.data.vertices), len(body.data.polygons), [u.name for u in body.data.uv_layers], len(body.vertex_groups), body.matrix_world)
print('ACTIONS', [a.name for a in bpy.data.actions])
