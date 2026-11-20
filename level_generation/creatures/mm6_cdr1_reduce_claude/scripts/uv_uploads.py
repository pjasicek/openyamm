"""Fresh UVs for the body and head texture sets of work/horns_master.blend (wings keep theirs) and the two Meshy
retexture uploads. Both uploads carry the whole dragon so Meshy paints the head and neck scales at one size (user
2026-10-14: "make sure somehow the scaling/color matches the body"): the target set fills most of the layout and
the other sets sit small in a strip beside it.
  body upload: body islands in [0, 0.92]^2 (also the runtime body layout), head and wings in 0.08 squares
  head upload: head islands in [0, 0.86]^2 (also the runtime head layout), body and wings in 0.14 squares
Out: work/uv_master.blend, work/{body,head}_upload.glb, work/uv_layout_{body,head}.png (coverage check)."""
import json
import math
import os

import bmesh
import bpy
import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BODY_SCALE, HEAD_SCALE = .92, .86
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'horns_master.blend'))
o = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']; me = o.data
rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
uv = me.uv_layers.active
wing_uv = {li: tuple(uv.data[li].uv) for f in me.polygons if f.material_index == 2 for li in f.loop_indices}
layouts = {}
for slot, angle in ((0, 80), (1, 85)):
    # project and pack on a copy holding only this set's faces (packing in place also moved the wing islands)
    tmp = o.copy(); tmp.data = me.copy(); tmp.parent = None; tmp.modifiers.clear(); bpy.context.collection.objects.link(tmp)
    bm = bmesh.new(); bm.from_mesh(tmp.data)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index != slot], context='FACES')
    bm.to_mesh(tmp.data); bm.free()
    bpy.ops.object.select_all(action='DESELECT'); tmp.select_set(True); bpy.context.view_layer.objects.active = tmp
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(angle), island_margin=.004, area_weight=0, correct_aspect=True,
                             scale_to_bounds=True)
    bpy.ops.uv.select_all(action='SELECT')
    bpy.ops.uv.pack_islands(rotate=True, margin=.004, margin_method='FRACTION', shape_method='CONCAVE')
    bpy.ops.object.mode_set(mode='OBJECT')
    tuv = tmp.data.uv_layers.active
    src_faces = [f for f in me.polygons if f.material_index == slot]
    assert len(src_faces) == len(tmp.data.polygons)
    layouts[slot] = {}
    for f, g in zip(src_faces, tmp.data.polygons):
        assert len(f.loop_indices) == len(g.loop_indices)
        for li, lj in zip(f.loop_indices, g.loop_indices):
            layouts[slot][li] = tuple(tuv.data[lj].uv)
    bpy.data.objects.remove(tmp, do_unlink=True)
bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
# runtime layout: body and head scaled into their upload regions, wings untouched
for slot, scale in ((0, BODY_SCALE), (1, HEAD_SCALE)):
    for li, (u, v) in layouts[slot].items():
        uv.data[li].uv = (u * scale, v * scale)
for li, (u, v) in wing_uv.items():
    assert uv.data[li].uv[0] == u and uv.data[li].uv[1] == v
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'uv_master.blend'))

placement = {
    'body': {0: (BODY_SCALE, 0, 0), 1: (.08, BODY_SCALE, 0), 2: (.08, BODY_SCALE, .08)},
    'head': {1: (HEAD_SCALE, 0, 0), 0: (.14, HEAD_SCALE, 0), 2: (.14, HEAD_SCALE, .14)},
}
source = {0: layouts[0], 1: layouts[1], 2: wing_uv}
report = {}
for label, place in placement.items():
    dup = o.copy(); dup.data = me.copy(); dup.parent = None; dup.modifiers.clear(); dup.vertex_groups.clear()
    bpy.context.collection.objects.link(dup)
    duv = dup.data.uv_layers.active
    for f in dup.data.polygons:
        s, ox, oy = place[f.material_index]
        for li in f.loop_indices:
            u, v = source[f.material_index][li]
            duv.data[li].uv = (ox + u * s, oy + v * s)
    dup.data.materials.clear()
    m = bpy.data.materials.new('Neutral'); m.use_nodes = True; dup.data.materials.append(m)
    for f in dup.data.polygons:
        f.material_index = 0
    bpy.ops.object.select_all(action='DESELECT'); dup.select_set(True); bpy.context.view_layer.objects.active = dup
    bpy.ops.export_scene.gltf(filepath=os.path.join(HERE, 'work', f'{label}_upload.glb'), use_selection=True,
                              export_format='GLB', export_animations=False, export_skins=False,
                              export_attributes=False, export_morph=False)
    # coverage: triangles per set (drawn by draw_uv_layouts.py)
    area = {0: 0.0, 1: 0.0, 2: 0.0}; tris = []
    dup.data.calc_loop_triangles()
    for t in dup.data.loop_triangles:
        mi = me.polygons[t.polygon_index].material_index
        p = [tuple(duv.data[li].uv) for li in t.loops]
        tris.append([mi] + [c for q in p for c in q])
        area[mi] += abs((p[1][0] - p[0][0]) * (p[2][1] - p[0][1]) - (p[2][0] - p[0][0]) * (p[1][1] - p[0][1])) / 2
    np.save(os.path.join(HERE, 'work', f'uv_tris_{label}.npy'), np.array(tris, np.float32))
    report[label] = {'triangles': len(dup.data.loop_triangles), 'uv_area': {k: round(v, 3) for k, v in area.items()}}
    bpy.data.objects.remove(dup, do_unlink=True)
json.dump(report, open(os.path.join(HERE, 'work', 'uv_report.json'), 'w'), indent=1)
print('UV', report)
