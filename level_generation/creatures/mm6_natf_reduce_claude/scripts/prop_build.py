"""Reduced LOD0 of static decorations: the opaque faces from deco_ladder.py's pick (work/<name>_r<NN>.npz) plus the
untouched alpha-mask/blend faces of the source (leaf cards, foam), materials by the u + 100 x material offset;
vertex colour (COLOR_0, a baked grey AO multiplier) and custom normals by data transfer from the source surface.
Exports work/<name>_lod0.glb (one node `<name>`, the source's materials) for deco_swap_glb.py.
PROP_NORMALS_ANGLE=<degrees>: hard-surface props take sharp-by-angle normals instead of the transferred ones (the
shield's flat back smeared across the long reduced triangles).
Usage: blender -b -P prop_build.py -- name:step [name:step ...]   (step e.g. r55)"""
import math
import os
import sys

import bmesh
import bpy
import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.abspath(os.path.join(HERE, '../../..'))
for spec in sys.argv[sys.argv.index('--') + 1:]:
    name, step = spec.split(':')
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=os.path.join(ROOT, f'assets_source/worlds/mm6/models/mm6_natf_{name}.glb'))
    src = next(o for o in bpy.data.objects if o.type == 'MESH')
    src.data.transform(src.matrix_world); src.matrix_world.identity()
    mats = list(src.data.materials)
    opaque = [not any(n.type == 'BSDF_PRINCIPLED' and (n.inputs['Alpha'].is_linked or n.inputs['Alpha'].default_value < 1)
                      for n in m.node_tree.nodes) if m.node_tree else True for m in mats]
    # alpha faces stay as authored
    keep = src.copy(); keep.data = src.data.copy(); bpy.context.scene.collection.objects.link(keep)
    bm = bmesh.new(); bm.from_mesh(keep.data)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if opaque[f.material_index]], context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bm.to_mesh(keep.data); bm.free()
    # reduced opaque faces
    d = np.load(os.path.join(HERE, 'work', f'{name}_{step}.npz'))
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in d['verts'].tolist()], [], [tuple(f) for f in d['faces'].tolist()])
    me.update()
    for m in mats:
        me.materials.append(m)
    uvl = me.uv_layers.new(name=src.data.uv_layers.active.name)
    w = d['wuv']
    for p in me.polygons:
        mat = int((w[p.index * 3][0] + 50) // 100)   # tiling UVs reach below 0 (burning rock: u -4)
        p.material_index = mat; p.use_smooth = True
        for k, li in enumerate(p.loop_indices):
            u, v = w[p.index * 3 + k]
            uvl.data[li].uv = (u - 100.0 * mat, v)
    red = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(red)
    # join the untouched alpha faces first (they keep their authored colour and normals), then transfer colour and
    # normals onto the reduced vertices only (vertex group): a colour attribute created before the join lost the leaf
    # cards' values (leaves rendered without their baked darkening)
    red.vertex_groups.new(name='reduced').add(list(range(len(me.vertices))), 1.0, 'REPLACE')
    for o in bpy.data.objects:
        o.select_set(False)
    if len(keep.data.polygons):
        keep.select_set(True); red.select_set(True); bpy.context.view_layer.objects.active = red
        bpy.ops.object.join()
    else:
        bpy.data.objects.remove(keep, do_unlink=True)
    colour = src.data.color_attributes.active_color
    if colour is not None and colour.name not in red.data.color_attributes:
        red.data.color_attributes.new(colour.name, colour.data_type, colour.domain)
    tmp = src.copy(); tmp.data = src.data.copy(); bpy.context.scene.collection.objects.link(tmp)
    dt = red.modifiers.new('T', 'DATA_TRANSFER'); dt.object = tmp; dt.use_object_transform = False
    dt.vertex_group = 'reduced'
    dt.use_loop_data = True; dt.loop_mapping = 'POLYINTERP_NEAREST'
    angle = os.environ.get('PROP_NORMALS_ANGLE')
    loops = {'COLOR_CORNER'} if colour is not None and colour.domain == 'CORNER' else set()
    hybrid = bool(angle) and 'nkept' in d  # prop_parts.py: kept parts keep transferred normals, the rest by angle
    dt.data_types_loops = loops if angle and not hybrid else loops | {'CUSTOM_NORMAL'}
    dt.use_loop_data = bool(dt.data_types_loops)
    if colour is not None and colour.domain == 'POINT':
        dt.use_vert_data = True; dt.data_types_verts = {'COLOR_VERTEX'}; dt.vert_mapping = 'POLYINTERP_NEAREST'
    for o in bpy.data.objects:
        o.select_set(o == red)
    bpy.context.view_layer.objects.active = red
    bpy.ops.object.modifier_apply(modifier=dt.name)
    bpy.data.objects.remove(tmp, do_unlink=True)
    red.vertex_groups.remove(red.vertex_groups['reduced'])
    if hybrid:
        me2 = red.data; kept_n = np.array([c.vector[:] for c in me2.corner_normals])
        flat = me2.copy(); flat.attributes.remove(flat.attributes['custom_normal'])
        flat.set_sharp_from_angle(angle=math.radians(float(angle)))
        angle_n = np.array([c.vector[:] for c in flat.corner_normals]); bpy.data.meshes.remove(flat)
        nk = int(d['nkept']); out = kept_n.copy()
        for p in me2.polygons:
            if p.index >= nk:
                out[p.loop_start:p.loop_start + p.loop_total] = angle_n[p.loop_start:p.loop_start + p.loop_total]
        me2.normals_split_custom_set(out.tolist())
    elif angle:
        red.data.set_sharp_from_angle(angle=math.radians(float(angle)))
    bpy.data.objects.remove(src, do_unlink=True)
    if red.data.color_attributes:
        red.data.color_attributes.active_color = red.data.color_attributes[0]
    for o in bpy.data.objects:
        o.select_set(o == red)
    if os.environ.get('DECO_DEBUG'):
        for c in red.data.color_attributes:
            vals = {}
            for p in red.data.polygons:
                vals.setdefault(p.material_index, []).extend(c.data[li].color[0] for li in p.loop_indices)
            print('DEBUG', c.name, c.domain, {k: round(sum(v) / len(v), 3) for k, v in vals.items()})
    bpy.ops.export_scene.gltf(filepath=os.path.join(HERE, 'work', f'{name}_lod0.glb'), use_selection=True,
                              export_format='GLB', export_yup=True, export_animations=False, export_skins=False,
                              export_vertex_color='ACTIVE', export_all_vertex_colors=False, export_image_format='NONE')
    print('BUILT', name, step, sum(len(p.vertices) - 2 for p in red.data.polygons), 'triangles')
