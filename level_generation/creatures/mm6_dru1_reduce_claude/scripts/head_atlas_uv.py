"""work/head_uv.blend -> work/ladder_head.blend: the head faces' UVMap takes the new HeadUV layout mapped into the
atlas's head half (merge_head_material.py layout: body 1024 | 32 gutter | head 1024, u = (1056 + 1024 u) / 2080);
HeadUV is removed. Usage: blender -b -P head_atlas_uv.py"""
import os, bpy
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'head_uv.blend'))
me = bpy.data.objects[os.environ.get('REA_CAND', 'Cand_66')].data
hp = np.zeros(len(me.polygons), np.int32); me.attributes['hpart'].data.foreach_get('value', hp)
a, h = me.uv_layers['UVMap'].data, me.uv_layers['HeadUV'].data
n = 0
for p in me.polygons:
    if hp[p.index] > 0:
        for l in p.loop_indices:
            u, v = h[l].uv; a[l].uv = ((1056 + 1024 * u) / 2080, v); n += 1
me.uv_layers.active = me.uv_layers['UVMap']; me.uv_layers.remove(me.uv_layers['HeadUV'])
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'ladder_head.blend'))
print('ATLASUV', n, 'head corners remapped')
