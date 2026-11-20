"""Blender helpers of the MM9 Isle of Ashes props: raw converter GLB -> one mesh object in the decoration frame
(Blender Z up, metres, base centre on the ground at the origin, the asset's front toward Blender -Y), texture
materials, vertex occlusion (COLOR_0), review renders with back faces culled.

Frames. The raw GLB holds the ABC model space x 2.56 (glTF = LithTech local axes, node transforms applied on import,
so Blender = (x_LT, -z_LT, y_LT)). The map places a model at OpenYAMM = Rz(-yaw_LT) * swap(model + binding origin)
with swap(x, y, z) = (x, z, y) (checked against the old isle's baked BModels: scripts/check_bake_fit.py), and the
engine maps an asset's Blender (x, y, z) to OpenYAMM (-x, -y, z) at yaw 0. So asset = (-x_LT, -z_LT, y_LT): the raw
import mirrored in X (faces reversed to keep their winding)."""
import json
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
WORK = os.path.join(HERE, 'work')
TEX = os.path.join(HERE, 'textures')
UNITS_PER_METRE = 81.7
MM9_SCALE = 2.56
MM6_PROPS = os.path.join(REPO, 'level_generation', 'decorations', 'mm6_new_sorpigal_3d', 'props', 'scripts')
sys.path.insert(0, MM6_PROPS)
import props_lib as pl  # noqa: E402  (read only: vertex occlusion)


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def binding_origins():
    with open(os.path.join(WORK, 'binding_origins.json')) as f:
        return json.load(f)


# Blender 5's glTF importer adds a bone-display mesh ('Icosphere', 42 vertices, 80 triangles, 2.4 cm) for every
# skinned ('full') import, and import_raw takes every imported mesh, so the ball ended up in the decoration. A build
# sets this True to import without it (opt-in, 2026-10-31: projects whose own per-face skin import counts the same
# meshes pass it to that import too, or their face counts would differ).
SKIP_BONE_SHAPES = False
# MM9's book (BOOK.abc) was first installed with that ball just past its spine, which moved its base centre 1.585 units
# along x. Its builds keep that frame (spec 'frame_x', metres added to the base centre's x) so the book placements of
# every map stay valid.
BOOK_BALL_FRAME_X_M = 1.584959350526334 / UNITS_PER_METRE


def import_raw(path, name, origin_lt, apply_armature=False, pose=None):
    """One mesh object from a raw converter GLB, in the asset frame (metres; not yet re-centred). Each face is wound
    to agree with the ABC's authored vertex normals (whatever the converter's triangle order). pose: optional
    (action name, frame) to deform a skinned import (the book) before baking it."""
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path, merge_vertices=False, disable_bone_shape=SKIP_BONE_SHAPES)
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == 'MESH']
    if pose is not None:
        arm = next(o for o in new if o.type == 'ARMATURE')
        arm.animation_data_create()
        arm.animation_data.action = bpy.data.actions[pose[0]]
        bpy.context.scene.frame_set(pose[1])
    depsgraph = bpy.context.evaluated_depsgraph_get()
    bm = bmesh.new()
    authored = []
    for o in meshes:
        if apply_armature:
            data = bpy.data.meshes.new_from_object(o.evaluated_get(depsgraph), depsgraph=depsgraph,
                                                   preserve_all_data_layers=True)
            data.transform(o.matrix_world)
        else:
            data = o.data.copy()
            data.transform(o.matrix_world)
        corner = [Vector(c.vector) for c in data.corner_normals]
        for poly in data.polygons:
            n = Vector((0, 0, 0))
            for li in poly.loop_indices:
                n += corner[li]
            authored.append(n)
        bm.from_mesh(data)
        bpy.data.meshes.remove(data)
    for o in new:
        if o.name in bpy.data.objects:
            bpy.data.objects.remove(o, do_unlink=True)
    o = Vector(origin_lt) * MM9_SCALE
    offset = Vector((o.x, -o.z, o.y))
    for v in bm.verts:
        v.co = (v.co + offset) / UNITS_PER_METRE
        v.co.x = -v.co.x
    bm.faces.ensure_lookup_table()
    bm.normal_update()
    flip = []
    for f, n in zip(bm.faces, authored):
        n = Vector((-n.x, n.y, n.z))
        if f.normal.dot(n) < 0:
            flip.append(f)
    bmesh.ops.reverse_faces(bm, faces=flip)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    # The glTF import's custom normals ride through bmesh as a plain corner attribute, encoded against corner spaces
    # that the mirror, the face reversal, clean()'s weld and triangulation change: kept, they exported as unrelated
    # per-corner normals (each triangle of a flat panel shaded differently, 2026-11-06) and overrode smooth(). The
    # authored normals have done their job (the winding above); smooth() derives the normals from the geometry.
    if 'custom_normal' in me.attributes:
        me.attributes.remove(me.attributes['custom_normal'])
    obj = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(obj)
    obj['flipped_faces'] = len(flip)
    obj['faces_in'] = len(authored)
    return obj


def clean(obj, weld=1e-5, min_piece_faces=2):
    """Weld coincident vertices (UVs stay per loop), drop degenerate faces, loose geometry and pieces of fewer than
    min_piece_faces faces (the cookpot's one-triangle fire socket)."""
    bm = bmesh.new(); bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=weld)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-6)
    # exact duplicate faces (same vertex set): keep one
    seen = {}
    dup = []
    for f in bm.faces:
        key = tuple(sorted(v.index for v in f.verts))
        if key in seen:
            dup.append(f)
        else:
            seen[key] = f
    if dup:
        bmesh.ops.delete(bm, geom=dup, context='FACES')
    # small loose pieces
    bm.faces.ensure_lookup_table()
    seen_f, small = set(), []
    for f in bm.faces:
        if f.index in seen_f:
            continue
        stack, piece = [f], []
        seen_f.add(f.index)
        while stack:
            g = stack.pop(); piece.append(g)
            for e in g.edges:
                for h in e.link_faces:
                    if h.index not in seen_f:
                        seen_f.add(h.index); stack.append(h)
        if len(piece) < min_piece_faces:
            small.extend(piece)
    if small:
        bmesh.ops.delete(bm, geom=small, context='FACES')
    loose = [v for v in bm.verts if not v.link_faces]
    bmesh.ops.delete(bm, geom=loose, context='VERTS')
    bmesh.ops.triangulate(bm, faces=bm.faces)
    bm.to_mesh(obj.data); bm.free()
    return len(dup), len(small)


def base_centre(objects):
    pts = np.array([v.co[:] for o in objects for v in o.data.vertices])
    lo, hi = pts.min(0), pts.max(0)
    return Vector(((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, lo[2])), lo, hi


def shift(objects, offset):
    for o in objects:
        o.data.transform(Matrix.Translation(-offset))
        o.data.update()


def smooth(obj, angle):
    """Normals from the geometry: smooth within `angle` degrees, hard beyond (vertex splits that the glTF export
    makes, the same as at UV seams)."""
    for o in bpy.data.objects:
        o.select_set(o is obj)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(angle))


def texture_material(name, texture, alpha=False, roughness=0.85, metallic=0.0, emission=None):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    tex = nt.nodes.new('ShaderNodeTexImage')
    img = bpy.data.images.load(os.path.join(TEX, texture)); img.colorspace_settings.name = 'sRGB'
    tex.image = img
    nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    if alpha:
        nt.links.new(tex.outputs['Alpha'], bsdf.inputs['Alpha'])
    bsdf.inputs['Roughness'].default_value = roughness
    bsdf.inputs['Metallic'].default_value = metallic
    if emission is not None:
        bsdf.inputs['Emission Color'].default_value = (*emission, 1.0)
        bsdf.inputs['Emission Strength'].default_value = 1.0
    m.use_backface_culling = True
    return m


def occlusion(obj, distance, strength=0.6):
    pl.vertex_occlusion(obj, rays=48, distance=distance, strength=strength, floor=True)


def triangles(obj):
    return sum(len(p.vertices) - 2 for p in obj.data.polygons)


def decimate(obj, ratio):
    mod = obj.modifiers.new('dec', 'DECIMATE'); mod.ratio = ratio; mod.use_collapse_triangulate = True
    for o in bpy.data.objects:
        o.select_set(o is obj)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=mod.name)


def export(objects, path):
    for o in bpy.data.objects:
        o.select_set(o in objects)
    bpy.ops.export_scene.gltf(filepath=path, use_selection=True, export_format='GLB', export_yup=True,
                              export_extras=True, export_normals=True, export_vertex_color='ACTIVE',
                              export_tangents=False, export_animations=False, export_skins=False,
                              export_morph=False, export_image_format='AUTO', export_apply=True)


# ---------------------------------------------------------------- review renders
def setup_render(resolution=(512, 512)):
    scene = bpy.context.scene
    for engine in ('BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT'):
        try:
            scene.render.engine = engine; break
        except TypeError:
            continue
    scene.eevee.taa_render_samples = 16
    scene.render.resolution_x, scene.render.resolution_y = resolution
    scene.render.film_transparent = True
    scene.view_settings.view_transform = 'Standard'
    world = scene.world or bpy.data.worlds.new('World'); scene.world = world; world.use_nodes = True
    bg = next(n for n in world.node_tree.nodes if n.type == 'BACKGROUND')
    bg.inputs['Color'].default_value = (0.55, 0.6, 0.68, 1.0); bg.inputs['Strength'].default_value = 0.8
    sun = bpy.data.lights.new('Sun', 'SUN'); sun.energy = 3.0; sun.angle = math.radians(3)
    so = bpy.data.objects.new('Sun', sun); scene.collection.objects.link(so)
    so.rotation_euler = (math.radians(40), 0, math.radians(-35))
    cam = bpy.data.objects.new('Camera', bpy.data.cameras.new('Camera'))
    scene.collection.objects.link(cam); scene.camera = cam
    return scene


def render(objects, path, yaw, elevation, lens=50):
    """yaw 0 looks at the asset's front (from Blender -Y)."""
    scene = bpy.context.scene
    for o in bpy.data.objects:
        if o.type == 'MESH':
            o.hide_render = o not in objects
    pts = [o.matrix_world @ Vector(c) for o in objects for c in o.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    centre, radius = (lo + hi) / 2, (hi - lo).length / 2
    cam = scene.camera; cam.data.lens = lens
    fov = 2 * math.atan(cam.data.sensor_width / (2 * lens))
    y, e = math.radians(yaw), math.radians(elevation)
    d = Vector((math.sin(y) * math.cos(e), -math.cos(y) * math.cos(e), math.sin(e)))
    cam.location = centre + d * radius * 1.05 / math.sin(fov / 2)
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    cam.data.clip_start = radius * 0.01; cam.data.clip_end = radius * 20
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
