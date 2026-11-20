"""Fresh body UVs on work/graft.blend and the Meshy body retexture upload. The helmet (material slot 1) keeps its own
Meshy UVs and texture at runtime; in the upload it sits small in a corner so Meshy sees the whole knight.
  runtime body layout = upload body layout: smart project 80 degrees, concave packing, scaled into [0, BODY]^2
  upload: helmet islands scaled into a (1 - BODY) square at (BODY, BODY)
Out: work/uv.blend (helmet UVs untouched), work/body_upload.glb (one neutral material, no skin), work/uv_report.json.
Usage: blender -b -P uv_upload.py"""
import json
import math
import os

import bmesh
import bpy
import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BODY = .94
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'graft.blend'))
o = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']; me = o.data
if rig.animation_data:
    rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
uv = me.uv_layers.active
helmet = {li: tuple(uv.data[li].uv) for f in me.polygons if f.material_index == 1 for li in f.loop_indices}

tmp = o.copy(); tmp.data = me.copy(); tmp.parent = None; tmp.modifiers.clear(); bpy.context.collection.objects.link(tmp)
bm = bmesh.new(); bm.from_mesh(tmp.data)
bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index != 0], context='FACES')
bm.to_mesh(tmp.data); bm.free()
for x in bpy.data.objects:
    x.select_set(False)
tmp.select_set(True); bpy.context.view_layer.objects.active = tmp
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=math.radians(80), island_margin=.004, area_weight=0, correct_aspect=True,
                         scale_to_bounds=True)
bpy.ops.uv.select_all(action='SELECT')
bpy.ops.uv.pack_islands(rotate=True, margin=.004, margin_method='FRACTION', shape_method='CONCAVE')
bpy.ops.object.mode_set(mode='OBJECT')
tuv = tmp.data.uv_layers.active
src = [f for f in me.polygons if f.material_index == 0]
assert len(src) == len(tmp.data.polygons)
for f, g in zip(src, tmp.data.polygons):
    for li, lj in zip(f.loop_indices, g.loop_indices):
        u, v = tuv.data[lj].uv; uv.data[li].uv = (u * BODY, v * BODY)
bpy.data.objects.remove(tmp, do_unlink=True)
for li, (u, v) in helmet.items():
    assert tuple(uv.data[li].uv) == (u, v)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'uv.blend'))

dup = o.copy(); dup.data = me.copy(); dup.parent = None; dup.modifiers.clear(); dup.vertex_groups.clear()
bpy.context.collection.objects.link(dup)
duv = dup.data.uv_layers.active
for f in dup.data.polygons:
    if f.material_index == 1:
        for li in f.loop_indices:
            u, v = helmet[li]; duv.data[li].uv = (BODY + u * (1 - BODY), BODY + v * (1 - BODY))
dup.data.materials.clear()
m = bpy.data.materials.new('Neutral'); m.use_nodes = True; dup.data.materials.append(m)
for f in dup.data.polygons:
    f.material_index = 0
for x in bpy.data.objects:
    x.select_set(False)
dup.select_set(True); bpy.context.view_layer.objects.active = dup
bpy.ops.export_scene.gltf(filepath=os.path.join(HERE, 'work', 'body_upload.glb'), use_selection=True,
                          export_format='GLB', export_animations=False, export_skins=False,
                          export_attributes=False, export_morph=False)
area = 0.0
dup.data.calc_loop_triangles()
tris = []
for t in dup.data.loop_triangles:
    p = [tuple(duv.data[li].uv) for li in t.loops]
    tris.append([me.polygons[t.polygon_index].material_index] + [c for q in p for c in q])
    if me.polygons[t.polygon_index].material_index == 0:
        area += abs((p[1][0] - p[0][0]) * (p[2][1] - p[0][1]) - (p[2][0] - p[0][0]) * (p[1][1] - p[0][1])) / 2
np.save(os.path.join(HERE, 'work', 'uv_tris_body.npy'), np.array(tris, np.float32))
rep = {'triangles': len(dup.data.loop_triangles), 'body_uv_area': round(area, 3), 'body_scale': BODY}
json.dump(rep, open(os.path.join(HERE, 'work', 'uv_report.json'), 'w'), indent=1); print('UV', rep)
