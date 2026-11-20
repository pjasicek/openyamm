"""Per-triangle UVs and rest-pose positions of work/uv.blend's Body for texel rasterisation:
work/uv3d_body.npz (material slot 0, runtime body layout) and work/uv3d_helmet.npz (slot 1, the helmet's own UVs).
Arrays uv (n, 3, 2), xyz (n, 3, 3). Usage: blender -b -P dump_uv3d.py"""
import os, bpy
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'uv.blend'))
o = bpy.data.objects['Body']; me = o.data; me.calc_loop_triangles(); uv = me.uv_layers.active
for slot, name in ((0, 'body'), (1, 'helmet')):
    tris = [t for t in me.loop_triangles if me.polygons[t.polygon_index].material_index == slot]
    np.savez(os.path.join(HERE, 'work', f'uv3d_{name}.npz'),
             uv=np.array([[uv.data[l].uv[:] for l in t.loops] for t in tris]),
             xyz=np.array([[(o.matrix_world @ me.vertices[v].co)[:] for v in t.vertices] for t in tris]))
    print('UV3D', name, len(tris))
