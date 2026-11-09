"""After detail_uv.py: per detail triangle (same order as work/detail_uv.npz) its group index (order of
work/detail_faces.json keys) -> work/detail_groups.npy; and the belt/clasp group reads the body texture again (its
runtime UVs are restored from work/ladder_body.blend, rescaled to the 3136-wide atlas): Meshy's detail paint of the
clasp and belt gem was worse than the body set's. Edits work/ladder_detail.blend in place.
Usage: blender -b -P detail_groups.py"""
import json, os, bpy
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEEP_BODY = {'belt_clasp'}
groups = json.load(open(os.path.join(HERE, 'work', 'detail_faces.json'))); names = list(groups)
gid = {fi: names.index(g) for g, fs in groups.items() for fi in fs}
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'ladder_body.blend'))
me = bpy.data.objects['Cand_62'].data
body_uv = {p.index: [tuple(me.uv_layers[0].data[li].uv) for li in p.loop_indices] for p in me.polygons
           if p.index in gid and names[gid[p.index]] in KEEP_BODY}
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'ladder_detail.blend'))
me = bpy.data.objects['Cand_62'].data; me.calc_loop_triangles()
order = [gid[t.polygon_index] for t in me.loop_triangles if t.polygon_index in gid]
np.save(os.path.join(HERE, 'work', 'detail_groups.npy'), np.array(order))
for fi, uvs in body_uv.items():
    for li, (u, v) in zip(me.polygons[fi].loop_indices, uvs):
        me.uv_layers[0].data[li].uv = (u * 2080 / 3136, v)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'ladder_detail.blend'))
print('GROUPS', dict(zip(names, np.bincount(order, minlength=len(names)).tolist())), 'restored to body texture', len(body_uv))
