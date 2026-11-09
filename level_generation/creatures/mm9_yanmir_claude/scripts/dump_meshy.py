"""Dump a Meshy glb's world vertices (Blender axes) and faces to npz. Args: <glb> <out npz>"""
import bpy, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a[0])
o = next(x for x in bpy.data.objects if x.type == 'MESH')
P = np.array([o.matrix_world @ v.co for v in o.data.vertices])
F = np.array([p.vertices[:] for p in o.data.polygons if len(p.vertices) == 3])
np.savez(a[1], P=P, F=F); print('DUMP', P.shape, F.shape, P.min(0).round(3), P.max(0).round(3))
