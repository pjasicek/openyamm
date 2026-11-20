"""Import a Smart Topology GLB as one joined mesh 'Body': height-normalised to `height` m, soles at z=0, centred, faces -Y
(as returned). Args: -- <glb> <out blend> [height]"""
import bpy, sys, os
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
glb, out = a[0], a[1]
height = float(a[2]) if len(a) > 2 else 1.7
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
for o in bpy.data.objects:
    o.select_set(o in meshes)
bpy.context.view_layer.objects.active = meshes[0]
if len(meshes) > 1:
    bpy.ops.object.join()
ob = bpy.context.view_layer.objects.active
ob.parent = None
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
co = np.array([tuple(v.co) for v in ob.data.vertices])
s = height / (co[:, 2].max() - co[:, 2].min())
ob.scale = (s, s, s)
ob.location = (-(co[:, 0].max() + co[:, 0].min()) / 2 * s, -(co[:, 1].max() + co[:, 1].min()) / 2 * s, -co[:, 2].min() * s)
bpy.ops.object.transform_apply(location=True, scale=True)
ob.name = ob.data.name = 'Body'
for o in list(bpy.data.objects):
    if o is not ob:
        bpy.data.objects.remove(o, do_unlink=True)
print('LOADED', len(ob.data.vertices), 'verts', sum(len(p.vertices) - 2 for p in ob.data.polygons), 'tris')
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
