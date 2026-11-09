import bpy, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a[0])
o = next(x for x in bpy.data.objects if x.type == 'MESH')
me = o.data; Mw = o.matrix_world
V = np.array([tuple(Mw @ v.co) for v in me.vertices]); F = np.array([p.vertices[:3] for p in me.polygons if len(p.vertices)==3])
print('tris', len(F), 'polys', len(me.polygons))
np.savez(a[1], V=V, F=F)
