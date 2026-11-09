"""(Adapted from hes_turrets_claude/scripts/prepare_uv.py.) Reduce, shade and unwrap the split Custodian; the neutral
upload for the Meshy retexture.

- Planar dissolve (DISSOLVE_DEG) per part, then a collapse decimation of the parts over their budget (RATIO), so the
  flat panels lose their extra triangles first and round silhouettes keep their segments; triangulated.
- Shading: every face smooth, edges sharp where the faces meet at more than SHARP_DEG (real breaks: panel edges,
  caps, collars), so the curved housings and barrels shade smoothly (the user disliked faceting in round 1).
- UVs: Smart UV Project (UV_ANGLE) over every part into one square atlas, islands at equal texel density, packed
  with rotation. Vertex groups (the rig's weights from parts.py) and the
  face attribute `part` survive.
Reads work/parts.blend; writes work/uv.blend and texturing/custodian_neutral_upload.glb. Args: none."""
import json
import math
import os
import sys

import bmesh
import bpy
import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAME = 'Custodian'
SHARP_DEG = 38.0
DISSOLVE_DEG = 2.0
FIXED_LAYOUT = False             # merging small islands made large distorted angle-based islands (review/uv1_sheet.png)
UV_ANGLE = 66.0
BODY_DENSITY = 1.4               # the sphere (sigil, eye, damage) gets 1.4x the texel density of the small parts
MIN_FACES = 12
# parts.py: 1 Body, 2 Sensor, 3/6 Shoulder, 4/7 Elbow (forearm, housing, cables), 5/8 Disc
RATIO = {1: 0.45, 2: 1.0, 3: 0.7, 4: 0.7, 5: 0.7, 6: 0.7, 7: 0.7, 8: 0.7}

bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'parts.blend'))
src = bpy.data.objects[NAME]
joints = src['joints']


def split_parts(obj):
    """One object per part value (a copy each); returns {part: object}."""
    out = {}
    part = np.zeros(len(obj.data.polygons), int); obj.data.attributes['part'].data.foreach_get('value', part)
    for p in sorted(set(part.tolist())):
        me = obj.data.copy()
        bm = bmesh.new(); bm.from_mesh(me)
        layer = bm.faces.layers.int['part']
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if f[layer] != p], context='FACES')
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
        bm.to_mesh(me); bm.free()
        o = bpy.data.objects.new(f'{NAME}_p{p}', me)
        bpy.context.scene.collection.objects.link(o)
        out[p] = o
    return out


def tris(o):
    return sum(len(p.vertices) - 2 for p in o.data.polygons)


parts = split_parts(src)
bpy.data.objects.remove(src)
report = {}
for p, o in parts.items():
    before = tris(o)
    bpy.context.view_layer.objects.active = o
    for x in bpy.context.scene.objects:
        x.select_set(x is o)
    m = o.modifiers.new('planar', 'DECIMATE'); m.decimate_type = 'DISSOLVE'
    m.angle_limit = math.radians(DISSOLVE_DEG); m.delimit = {'NORMAL'}
    bpy.ops.object.modifier_apply(modifier='planar')
    m = o.modifiers.new('tri', 'TRIANGULATE'); m.quad_method = 'SHORTEST_DIAGONAL'; m.min_vertices = 4
    bpy.ops.object.modifier_apply(modifier='tri')
    target = int(before * RATIO.get(p, 1.0))
    if tris(o) > target:
        m = o.modifiers.new('collapse', 'DECIMATE'); m.decimate_type = 'COLLAPSE'
        m.ratio = target / tris(o); m.use_collapse_triangulate = True
        bpy.ops.object.modifier_apply(modifier='collapse')
    report[p] = [before, tris(o)]
print('REDUCE', json.dumps(report))

for o in parts.values():
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        f.smooth = True
    for e in bm.edges:
        e.smooth = not (len(e.link_faces) != 2 or e.calc_face_angle(0.0) > math.radians(SHARP_DEG))
    bm.to_mesh(o.data); bm.free()


def merge_small_islands(objs):
    """Edit mode, all selected: islands to seams, clear the seams round islands smaller than MIN_FACES (they merge
    into a neighbour), angle-based unwrap."""
    bpy.ops.uv.select_all(action='SELECT')
    bpy.ops.uv.seams_from_islands()
    for rnd in range(4):
        small = 0
        for o in objs:
            bm = bmesh.from_edit_mesh(o.data)
            seen = set()
            for f in bm.faces:
                if f.index in seen:
                    continue
                stack, island = [f], []
                seen.add(f.index)
                while stack:
                    g = stack.pop(); island.append(g)
                    for e in g.edges:
                        if e.seam:
                            continue
                        for h in e.link_faces:
                            if h.index not in seen:
                                seen.add(h.index); stack.append(h)
                if len(island) < MIN_FACES:
                    small += 1
                    for g in island:
                        for e in g.edges:
                            e.seam = False
            bmesh.update_edit_mesh(o.data)
        print('UV round', rnd, 'small islands', small)
        if not small:
            break
    bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.0)


def unwrap(objs, v0, v1):
    """Smart UV + pack the objects together into the band v0..v1 (full width), isotropic for a 2:1 band."""
    for x in bpy.context.scene.objects:
        x.select_set(x in objs)
    bpy.context.view_layer.objects.active = objs[0]
    for o in objs:
        if not o.data.uv_layers:
            o.data.uv_layers.new(name='UVMap')
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(UV_ANGLE), island_margin=0.0, area_weight=0.0,
                             scale_to_bounds=False)
    if FIXED_LAYOUT:
        merge_small_islands(objs)
    bpy.ops.uv.average_islands_scale()
    bpy.ops.object.mode_set(mode='OBJECT')
    for o in objs:
        if o.name.endswith('_p1'):
            for d in o.data.uv_layers.active.data:
                d.uv = (d.uv[0] * BODY_DENSITY, d.uv[1] * BODY_DENSITY)
    aspect = 1.0 / (v1 - v0)                       # band is `aspect` times wider than tall
    for o in objs:
        uv = o.data.uv_layers.active.data
        for d in uv:
            d.uv = (d.uv[0], d.uv[1] * aspect)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.uv.select_all(action='SELECT')
    bpy.ops.uv.pack_islands(rotate=not FIXED_LAYOUT, margin=0.003, shape_method='CONCAVE')
    bpy.ops.object.mode_set(mode='OBJECT')
    for o in objs:
        uv = o.data.uv_layers.active.data
        for d in uv:
            d.uv = (d.uv[0], v0 + d.uv[1] * (v1 - v0))


unwrap(list(parts.values()), 0.0, 1.0)
for x in bpy.context.scene.objects:
    x.select_set(True)
bpy.context.view_layer.objects.active = parts[1]
bpy.ops.object.join()
obj = bpy.context.view_layer.objects.active
obj.name = obj.data.name = NAME
obj['joints'] = joints
part = np.zeros(len(obj.data.polygons), int); obj.data.attributes['part'].data.foreach_get('value', part)
counts = {int(p): int(sum(len(obj.data.polygons[i].vertices) - 2 for i in np.where(part == p)[0])) for p in set(part)}
print('PART_TRIS', json.dumps(counts), 'total', sum(counts.values()))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'uv.blend'))
os.makedirs(os.path.join(HERE, 'texturing'), exist_ok=True)
for x in bpy.context.scene.objects:
    x.select_set(x is obj)
bpy.ops.export_scene.gltf(filepath=os.path.join(HERE, 'texturing', 'custodian_neutral_upload.glb'), use_selection=True,
                          export_format='GLB', export_yup=True, export_skins=False, export_animations=False,
                          export_materials='NONE', export_attributes=False)
print('UV_DONE')
