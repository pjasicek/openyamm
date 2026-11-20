"""Reduce, shade and unwrap the split machine; the neutral upload for the Meshy retexture (adapted from
hes_turrets_claude/scripts/prepare_uv.py).

- Planar dissolve (DISSOLVE_DEG) per part, then a collapse decimation of the parts over their budget (RATIO), so the
  flat panels lose their extra triangles first and round silhouettes keep their segments; triangulated.
- Shading: every face smooth, edges sharp where the faces meet at more than SHARP_DEG (real breaks: panel edges,
  caps, collars), so the curved housings and barrels shade smoothly (the user disliked faceting in round 1).
- UVs: Smart UV Project per part group. The turret: the turning parts are packed into the TOP half of the atlas
  (v 0.5..1), the mount into the BOTTOM half (v 0..0.5), each half 2:1 like its later crop (2048x1024); the cell and
  the conduit fill the whole square: islands are stretched x2 in v
  before packing and squashed back after, so the texel density stays isotropic. Seams = sharp edges where possible
  (Smart UV splits at its angle limit, which is close to SHARP_DEG).
Reads work/<name>_parts_raw.blend; writes work/<name>_uv.blend and work/<name>_neutral_upload.glb.
UV_VERSION=v2 (the conduit's second retexture): xatlas charts instead of Smart UV (scripts/xatlas_uv.py, run with
LOD_REPAIR_PYTHON), written to work/<name>_uv_v2.blend and work/<name>_neutral_upload_v2.glb. Smart UV split the
conduit's thin cables into hundreds of tiny islands and its first retexture painted them as a gold/navy mosaic.
Args: -- <name>"""
import json
import math
import os
import subprocess
import sys

import bmesh
import bpy
import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAME = sys.argv[sys.argv.index('--') + 1]
SHARP_DEG = 38.0
DISSOLVE_DEG = 2.0
FIXED_LAYOUT = True
MIN_FACES = 12
RATIO = {"starport_turret": {0: 0.55, 1: 1.0, 2: 0.7, 3: 0.65, 4: 0.55}, "capacitor_column": {1: 0.55}, "throne_conduit": {1: 0.6}}[NAME]

bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', f'{NAME}_parts_raw.blend'))
src = bpy.data.objects[NAME]
pivot, ring = list(src['pivot']), src['ring_top']


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
    bpy.ops.uv.smart_project(angle_limit=math.radians(SHARP_DEG), island_margin=0.0, area_weight=0.0,
                             scale_to_bounds=False)
    if FIXED_LAYOUT:
        merge_small_islands(objs)
    bpy.ops.uv.average_islands_scale()
    bpy.ops.object.mode_set(mode='OBJECT')
    aspect = 1.0 / (v1 - v0)                       # band is `aspect` times wider than tall
    for o in objs:
        uv = o.data.uv_layers.active.data
        for d in uv:
            d.uv = (d.uv[0], d.uv[1] * aspect)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.uv.select_all(action='SELECT')
    bpy.ops.uv.pack_islands(rotate=not FIXED_LAYOUT, margin=0.006, shape_method='CONCAVE')
    bpy.ops.object.mode_set(mode='OBJECT')
    for o in objs:
        uv = o.data.uv_layers.active.data
        for d in uv:
            d.uv = (d.uv[0], v0 + d.uv[1] * (v1 - v0))


VERSION = os.environ.get('UV_VERSION', '')
SUFFIX = f'_{VERSION}' if VERSION else ''


def xatlas_unwrap(objs):
    """Join-free xatlas unwrap of all objects together (one atlas): triangles and positions to a temporary npz, the
    xatlas helper in the LOD venv, UVs back per corner."""
    co, tri, owners = [], [], []
    base = 0
    for o in objs:
        me = o.data
        me.calc_loop_triangles()
        co.extend(v.co[:] for v in me.vertices)
        for t in me.loop_triangles:
            tri.append([base + i for i in t.vertices]); owners.append((o, t.loops[:]))
        base += len(me.vertices)
    tmp = os.path.join(HERE, 'work', f'{NAME}_xatlas_in.npz')
    out = os.path.join(HERE, 'work', f'{NAME}_xatlas_out.npz')
    np.savez(tmp, co=np.array(co, np.float32), tri=np.array(tri, np.int64))
    python = os.environ.get('LOD_REPAIR_PYTHON', '/tmp/lancer_lod_venv/bin/python')
    print(subprocess.run([python, os.path.join(HERE, 'scripts', 'xatlas_uv.py'), tmp, out, '2048'], check=True,
                         capture_output=True, text=True).stdout.strip())
    uv = np.load(out)['uv']
    for o in objs:
        if not o.data.uv_layers:
            o.data.uv_layers.new(name='UVMap')
    for (o, loops), corners in zip(owners, uv):
        layer = o.data.uv_layers.active.data
        for li, c in zip(loops, corners):
            layer[li].uv = (float(c[0]), float(c[1]))


if VERSION == 'v2':
    xatlas_unwrap(list(parts.values()))
elif 0 in parts:
    unwrap([o for p, o in parts.items() if p != 0], 0.5, 1.0)
    unwrap([parts[0]], 0.0, 0.5)
else:
    unwrap(list(parts.values()), 0.0, 1.0)
for x in bpy.context.scene.objects:
    x.select_set(True)
bpy.context.view_layer.objects.active = parts[min(parts)]
bpy.ops.object.join()
obj = bpy.context.view_layer.objects.active
obj.name = obj.data.name = NAME
obj['pivot'], obj['ring_top'] = pivot, ring
part = np.zeros(len(obj.data.polygons), int); obj.data.attributes['part'].data.foreach_get('value', part)
counts = {int(p): int(sum(len(obj.data.polygons[i].vertices) - 2 for i in np.where(part == p)[0])) for p in set(part)}
print('PART_TRIS', json.dumps(counts), 'actor', sum(v for k, v in counts.items() if k), 'mount', counts.get(0, 0))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', f'{NAME}_uv{SUFFIX}.blend'))
for x in bpy.context.scene.objects:
    x.select_set(x is obj)
bpy.ops.export_scene.gltf(filepath=os.path.join(HERE, 'work', f'{NAME}_neutral_upload{SUFFIX}.glb'), use_selection=True,
                          export_format='GLB', export_yup=True, export_skins=False, export_animations=False,
                          export_materials='NONE', export_attributes=False)
print('UV_DONE')
