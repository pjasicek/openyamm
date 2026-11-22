"""Import meshy/smart_topology_v1/model_urls_glb.glb and dump vertices/triangles (Blender axes, transforms applied) to
work/raw.npz."""
import bpy, os
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, 'meshy/smart_topology_v1/model_urls_glb.glb'))
mesh = next(o for o in bpy.data.objects if o.type == 'MESH')
for o in list(bpy.data.objects):
    if o is not mesh:
        bpy.data.objects.remove(o, do_unlink=True)
mesh.parent = None
bpy.context.view_layer.objects.active = mesh; mesh.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
me = mesh.data; me.calc_loop_triangles()
co = np.array([v.co[:] for v in me.vertices]); tris = np.array([t.vertices[:] for t in me.loop_triangles])
np.savez(os.path.join(HERE, 'work', 'raw.npz'), co=co, tris=tris)
print('DUMPED', len(co), len(tris))
