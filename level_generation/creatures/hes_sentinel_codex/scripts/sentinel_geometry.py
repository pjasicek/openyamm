"""Shared Sentinel geometry: measured rigid parts, LOD0 reduction study, then the selected neutral UV upload.

Adapted from hes_turrets_claude's parts.py and prepare_uv.py. Raw component IDs belong only to the hash in
meshy/sentinel_geometry_v1. Usage (Blender): -- study | uv <ratio>. Does not alter the downloaded source.
"""
import json
import math
import sys
from pathlib import Path

import bmesh
import bpy
import numpy as np
from mathutils import Vector

P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P / 'scripts'))
import sentinel_common as tc

SHARP = math.radians(38)
CABLES = {14, 28, 29, 45, 53, 70, 76, 80, 100, 116, 141}
PIVOT = (0.012, -0.215, 0.910)
RING = 0.315


def select(objects):
    for o in bpy.context.scene.objects:
        o.select_set(o in objects)
    bpy.context.view_layer.objects.active = objects[0]


def tris(obj):
    return sum(len(f.vertices) - 2 for f in obj.data.polygons)


def shade(obj):
    bm = bmesh.new(); bm.from_mesh(obj.data)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    for f in bm.faces:
        f.smooth = True
    for e in bm.edges:
        e.smooth = len(e.link_faces) == 2 and e.calc_face_angle(0) <= SHARP
        if not e.smooth:
            e.seam = True
    bm.to_mesh(obj.data); bm.free()


def render(objects, prefix):
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_WORKBENCH'
    scene.display.shading.light = 'STUDIO'
    scene.display.shading.color_type = 'SINGLE'
    scene.display.shading.single_color = (0.65, 0.65, 0.63)
    scene.display.shading.show_cavity = True
    scene.render.resolution_x = scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = True
    cam = bpy.data.objects.get('ReviewCam')
    if cam is None:
        cam = bpy.data.objects.new('ReviewCam', bpy.data.cameras.new('ReviewCam'))
        scene.collection.objects.link(cam)
    scene.camera = cam; cam.data.type = 'ORTHO'; cam.data.ortho_scale = 3.25
    for view, (az, el) in {'q': (-35, 15), 'side': (90, 0), 'front': (0, 0)}.items():
        a, e = math.radians(az), math.radians(el)
        d = Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))
        cam.location = Vector((0, 0.1, 0.8)) + d * 9
        cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
        scene.render.filepath = str(P / 'review/sentinel_geometry' / f'{prefix}_{view}.png')
        bpy.ops.render.render(write_still=True)


def make_parts():
    obj = tc.import_raw('sentinel')
    bm = bmesh.new(); bm.from_mesh(obj.data)
    labels = tc.component_labels(bm)
    co = np.array([v.co[:] for v in bm.verts])
    layer = bm.faces.layers.int.new('part')
    assignment = {}
    for c in range(int(labels.max()) + 1):
        pts = co[labels == c]; low, high, mid = pts.min(0), pts.max(0), pts.mean(0)
        if len(pts) < 4:
            part = -1
        elif c in CABLES:
            part = 5
        elif mid[2] < RING:
            part = 0
        elif abs(mid[0]) < 0.24 and mid[1] < -0.20 and low[2] > 0.45:
            part = 3
        else:
            part = 2
        assignment[c] = part
    for f in bm.faces:
        f[layer] = assignment[int(labels[f.verts[0].index])]
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f[layer] < 0], context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bm.to_mesh(obj.data); bm.free()
    parts = {}
    for part in (0, 2, 3, 5):
        me = obj.data.copy(); bm = bmesh.new(); bm.from_mesh(me)
        layer = bm.faces.layers.int['part']
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if f[layer] != part], context='FACES')
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
        bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=0.0001)
        bm.to_mesh(me); bm.free()
        o = bpy.data.objects.new(f'Sentinel_p{part}', me)
        bpy.context.scene.collection.objects.link(o)
        o['part_id'] = part; parts[part] = o
        shade(o)
        assert len(o.data.polygons), part
    bpy.data.objects.remove(obj)
    (P / 'work/sentinel_parts.json').write_text(json.dumps({
        'source_sha256': '9de09edb25761fde14835b7b6fa0ca2eb807b180cb31578f69811581ea14a14b',
        'components': assignment, 'pivot': PIVOT, 'ring_top': RING,
        'part_names': {0: 'base', 2: 'head', 3: 'paired_barrels', 5: 'coupling_cables'},
        'triangles': {k: tris(v) for k, v in parts.items()}}, indent=2) + '\n')
    bpy.ops.wm.save_as_mainfile(filepath=str(P / 'work/sentinel_parts.blend'))
    return parts


def study():
    make_parts()
    results = []
    for ratio in (1.0, 0.8, 0.6, 0.4):
        bpy.ops.wm.open_mainfile(filepath=str(P / 'work/sentinel_parts.blend'))
        parts = [o for o in bpy.context.scene.objects if o.type == 'MESH']
        for o in parts:
            select([o])
            if ratio < 1:
                m = o.modifiers.new('Planar', 'DECIMATE'); m.decimate_type = 'DISSOLVE'
                m.angle_limit = math.radians(2); m.delimit = {'NORMAL'}
                bpy.ops.object.modifier_apply(modifier=m.name)
                m = o.modifiers.new('Triangulate', 'TRIANGULATE'); m.quad_method = 'SHORTEST_DIAGONAL'
                bpy.ops.object.modifier_apply(modifier=m.name)
                # Flexible coupling cables retain their cross-sections for the yaw deformation check.
                target_ratio = max(ratio, 0.85) if o['part_id'] == 5 else ratio
                m = o.modifiers.new('Reduce', 'DECIMATE'); m.ratio = target_ratio
                m.use_collapse_triangulate = True
                bpy.ops.object.modifier_apply(modifier=m.name)
            shade(o)
        low = min(v.co.z for o in parts for v in o.data.vertices)
        for o in parts:
            for v in o.data.vertices:
                v.co.z -= low
        tag = f'reduction_{round(ratio * 100)}'
        bpy.ops.wm.save_as_mainfile(filepath=str(P / 'work' / f'sentinel_{tag}.blend'))
        render(parts, tag)
        results.append({'ratio': ratio, 'triangles': sum(tris(o) for o in parts),
                        'by_part': {str(o['part_id']): tris(o) for o in parts}, 'ground_adjustment': low})
    (P / 'review/sentinel_geometry/reduction.json').write_text(json.dumps(results, indent=2) + '\n')


def uv(ratio):
    name = 'sentinel_selected.blend' if ratio == 'selected' else f'sentinel_reduction_{round(float(ratio) * 100)}.blend'
    bpy.ops.wm.open_mainfile(filepath=str(P / 'work' / name))
    parts = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    select(parts)
    for o in parts:
        before = tris(o)
        repaired = o.data.validate(verbose=True, clean_customdata=False)
        print('PRE_UV_VALIDATE', o.name, repaired, before, tris(o))
        if not o.data.uv_layers:
            o.data.uv_layers.new(name='UVMap')
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=SHARP, island_margin=0, area_weight=0, scale_to_bounds=False)
    bpy.ops.uv.select_all(action='SELECT')
    bpy.ops.uv.average_islands_scale()
    bpy.ops.uv.pack_islands(rotate=True, margin=0.006, shape_method='CONCAVE')
    bpy.ops.uv.seams_from_islands()
    bpy.ops.object.mode_set(mode='OBJECT')
    neutral = bpy.data.materials.new('Sentinel_Neutral')
    neutral.use_nodes = True
    neutral.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.55, 0.55, 0.55, 1)
    neutral.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.7
    # Clear helper colour attributes so the untextured upload cannot bake diagnostic part colours.
    for o in parts:
        for attr in list(o.data.color_attributes):
            o.data.color_attributes.remove(attr)
        o.data.materials.clear()
        o.data.materials.append(neutral)
        for face in o.data.polygons:
            face.material_index = 0
    select(parts)
    bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    obj.name = obj.data.name = 'Sentinel'
    obj['pivot'] = PIVOT; obj['ring_top'] = RING
    assert not obj.data.validate(verbose=True, clean_customdata=False), 'Repair invalid geometry before unwrapping'
    bpy.ops.wm.save_as_mainfile(filepath=str(P / 'work/sentinel_uv.blend'))
    bpy.ops.export_scene.gltf(filepath=str(P / 'work/sentinel_texture_upload.glb'), use_selection=True,
                              export_format='GLB', export_yup=True, export_skins=False,
                              export_animations=False, export_materials='EXPORT', export_attributes=False)
    print('UV_UPLOAD', tris(obj), len(obj.data.vertices), flush=True)


args = sys.argv[sys.argv.index('--') + 1:]
if args[0] == 'study':
    study()
elif args[0] == 'select':
    bpy.ops.wm.open_mainfile(filepath=str(P / 'work/sentinel_reduction_80.blend'))
    old = bpy.data.objects['Sentinel_p0']
    bpy.data.objects.remove(old, do_unlink=True)
    with bpy.data.libraries.load(str(P / 'work/sentinel_reduction_40.blend'), link=False) as (source, target):
        target.objects = ['Sentinel_p0']
    for obj in target.objects:
        bpy.context.scene.collection.objects.link(obj)
    parts = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    assert sum(tris(o) for o in parts) == 9754
    bpy.ops.wm.save_as_mainfile(filepath=str(P / 'work/sentinel_selected.blend'))
    render(parts, 'selected')
    print('SELECTED 9754 triangles: 40% pedestal, 80% head/barrels, 85% cables')
elif args[0] == 'uv':
    uv(args[1])
else:
    raise ValueError(args)
