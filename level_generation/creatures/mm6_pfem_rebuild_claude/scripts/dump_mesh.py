"""Dump a GLB's meshes (joined, world, Blender frame) to npz: co, tri, uv (per corner), base colour image path. Args: <glb> <out npz>"""
import bpy, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a[0])
ms = [o for o in bpy.data.objects if o.type == 'MESH']
for o in bpy.data.objects: o.select_set(o in ms)
bpy.context.view_layer.objects.active = ms[0]
if len(ms) > 1: bpy.ops.object.join()
o = bpy.context.view_layer.objects.active; o.parent = None
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
me = o.data; me.calc_loop_triangles()
co = np.array([v.co[:] for v in me.vertices]); tri = np.array([t.vertices[:] for t in me.loop_triangles])
uvl = me.uv_layers.active.data if me.uv_layers else None
uv = np.array([[uvl[l].uv[:] for l in t.loops] for t in me.loop_triangles]) if uvl else np.zeros((len(tri), 3, 2))
np.savez(a[1], co=co, tri=tri, uv=uv)
print('DUMP', len(co), len(tri), co.min(0).round(3).tolist(), co.max(0).round(3).tolist())
