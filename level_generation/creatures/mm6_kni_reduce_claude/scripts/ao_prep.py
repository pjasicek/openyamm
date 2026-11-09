"""work/uv.blend -> work/ao_prep.blend: helmet UVs moved into the upload's corner square (BODY..1), so a
single-material AO bake of the body layout does not overlap them. Usage: blender -b -P ao_prep.py"""
import os, bpy
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); BODY = .94
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'uv.blend'))
me = bpy.data.objects['Body'].data; uv = me.uv_layers.active
for f in me.polygons:
    if f.material_index == 1:
        for li in f.loop_indices:
            u, v = uv.data[li].uv; uv.data[li].uv = (BODY + u * (1 - BODY), BODY + v * (1 - BODY))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'ao_prep.blend'))
