"""Import a GLB, join its meshes into one object 'Body' (no armature), save a blend. Args: <glb> <out blend>"""
import bpy, sys
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a[0])
ms = [o for o in bpy.data.objects if o.type == 'MESH']
for o in bpy.data.objects: o.select_set(o in ms)
bpy.context.view_layer.objects.active = ms[0]
if len(ms) > 1: bpy.ops.object.join()
o = bpy.context.view_layer.objects.active; o.name = 'Body'
o.parent = None
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
import numpy as np
c = np.array([v.co[:] for v in o.data.vertices])
print('BOUNDS', c.min(0).round(3).tolist(), c.max(0).round(3).tolist(), 'tris', sum(len(p.vertices) - 2 for p in o.data.polygons))
bpy.ops.wm.save_as_mainfile(filepath=a[1])
