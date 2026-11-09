"""Shared Blender helpers of the bones batch: import Meshy GLBs as one mesh, clean and ground them, Smart UV, neutral
export for a Meshy retexture, and materials from Meshy texture sets (base colour, normal, metallic-roughness) kept in
this folder's textures/. Blender Z up, base centre on the ground at the origin."""
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(HERE, '..', 'scripts'))
import dungeon_lib as dl  # noqa: E402

pl = dl.pl
u = dl.units
TEXTURES = os.path.join(HERE, 'textures')
WORK = os.path.join(HERE, 'work')


def import_mesh(path, name):
    """Import a GLB and return its meshes joined into one object with transforms applied (materials dropped)."""
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == 'MESH']
    for o in bpy.data.objects:
        o.select_set(o in meshes)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    for o in new:
        if o is not obj and o.name in bpy.data.objects:
            bpy.data.objects.remove(o)
    obj.parent = None
    obj.matrix_world = obj.matrix_world.copy()
    bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    obj.name = name; obj.data.name = name
    return obj


def drop_small_pieces(obj, keep_fraction=0.002):
    """Delete loose parts with fewer than keep_fraction of the vertices (Meshy crumbs)."""
    bm = bmesh.new(); bm.from_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    seen = set(); pieces = []
    for v in bm.verts:
        if v.index in seen:
            continue
        stack = [v]; part = []
        seen.add(v.index)
        while stack:
            w = stack.pop(); part.append(w)
            for e in w.link_edges:
                o = e.other_vert(w)
                if o.index not in seen:
                    seen.add(o.index); stack.append(o)
        pieces.append(part)
    limit = keep_fraction * len(bm.verts)
    doomed = [v for part in pieces if len(part) < limit for v in part]
    bmesh.ops.delete(bm, geom=doomed, context='VERTS')
    bm.to_mesh(obj.data); bm.free()
    return len(pieces), sum(1 for p in pieces if len(p) < limit)


def ground(obj, height=None):
    """Base centre to the origin, min z = 0; optionally scale uniformly to the given height (metres)."""
    co = np.array([v.co[:] for v in obj.data.vertices])
    lo, hi = co.min(0), co.max(0)
    centre = Vector(((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, lo[2]))
    scale = 1.0 if height is None else height / (hi[2] - lo[2])
    for v in obj.data.vertices:
        v.co = (v.co - centre) * scale
    obj.data.update()
    return scale


def smart_uv(obj, angle=1.15, margin=0.003):
    for uv in list(obj.data.uv_layers):
        obj.data.uv_layers.remove(uv)
    obj.data.uv_layers.new(name='UVMap')
    bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=angle, island_margin=margin, area_weight=0.0, scale_to_bounds=False)
    bpy.ops.uv.pack_islands(margin=margin, rotate=True)
    bpy.ops.object.mode_set(mode='OBJECT')


def export_neutral(obj, path):
    """Unrigged, material-free GLB of one object (the Meshy retexture upload)."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.gltf(filepath=path, use_selection=True, export_format='GLB', export_yup=True,
                              export_skins=False, export_animations=False, export_materials='NONE')


def texture_material(name, prefix, extras=None):
    """Principled material from textures/<prefix>_basecolor.png, _normal.png and _mr.png (G rough, B metal)."""
    pl.TEX = TEXTURES
    try:
        return pl.material(name, prefix, extras=extras)
    finally:
        pl.TEX = dl.PROPS_TEXTURES


def triangulate(obj):
    bm = bmesh.new(); bm.from_mesh(obj.data)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    bm.to_mesh(obj.data); bm.free()


def duplicate(obj, name):
    dup = obj.copy(); dup.data = obj.data.copy(); dup.name = name; dup.data.name = name
    bpy.context.scene.collection.objects.link(dup)
    return dup


def srgb_to_linear(c):
    c = np.asarray(c, np.float64)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def linear_to_srgb(c):
    c = np.maximum(np.asarray(c, np.float64), 0)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)
