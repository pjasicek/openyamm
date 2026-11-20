"""A Meshy image-to-3D item -> work/meshy/<name>_export.glb, a game model for every icon the design stands for.

The Meshy GLB (meshy/meshy/<name>_i23d_v1/model_urls_glb.glb, textured PBR) is welded and joined, crumbs (loose
pieces under 1 % of its faces) dropped, collapse-decimated to `tris` (its UVs and Meshy's base colour, metallic-
roughness and normal maps kept, scaled to 1024, saved as PNG), centred on its footprint and set on the ground (lowest point at 0,
upright as Meshy made it). The binding's length (the longest horizontal side) sets the world size.
Usage: blender --background --python meshy_item.py -- <name> [<name> ...]"""
import os
import sys

import bmesh
import bpy
from mathutils import Vector

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'projectiles_claude',
                                'scripts'))
import projlib as pl  # noqa: E402

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MESHY = os.path.join(HERE, 'meshy', 'meshy')
# name: triangle budget
DESIGNS = {'helm_full': 2500, 'helm_horned': 2500, 'hat_peasant': 2000,
           'boots_leather': 3000, 'boots_knight': 3000, 'boots_ranger': 3000}
TEXTURE_SIZE = 1024


def find_glb(name):
    folder = os.path.join(MESHY, f'{name}_i23d_v1')
    for root, _, files in os.walk(folder):
        for file in sorted(files):
            if file.endswith('.glb'):
                return os.path.join(root, file)
    raise FileNotFoundError(folder)


def convert(name, tris):
    pl.reset()
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=find_glb(name))
    meshes = [o for o in bpy.data.objects if o not in before and o.type == 'MESH']
    for o in bpy.data.objects:
        o.select_set(o in meshes)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    # Drop crumbs: loose pieces with under 1 % of the faces.
    bm.faces.ensure_lookup_table()
    seen, pieces = set(), []
    for face in bm.faces:
        if face.index in seen:
            continue
        stack, piece = [face], []
        seen.add(face.index)
        while stack:
            current = stack.pop()
            piece.append(current)
            for edge in current.edges:
                for other in edge.link_faces:
                    if other.index not in seen:
                        seen.add(other.index)
                        stack.append(other)
        pieces.append(piece)
    limit = len(bm.faces) * 0.01
    crumbs = [f for piece in pieces if len(piece) < limit for f in piece]
    bmesh.ops.delete(bm, geom=crumbs, context='FACES')
    bm.to_mesh(obj.data)
    bm.free()
    faces = len(obj.data.polygons)
    if faces > tris:
        modifier = obj.modifiers.new('decimate', 'DECIMATE')
        modifier.ratio = tris / faces
        modifier.use_collapse_triangulate = True
        with bpy.context.temp_override(object=obj, active_object=obj):
            bpy.ops.object.modifier_apply(modifier=modifier.name)
    xs, ys, zs = ([(obj.matrix_world @ v.co)[i] for v in obj.data.vertices] for i in range(3))
    shift = Vector(((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, min(zs)))
    for v in obj.data.vertices:
        v.co -= shift
    for image in bpy.data.images:
        if image.size[0] > TEXTURE_SIZE:
            image.scale(TEXTURE_SIZE, TEXTURE_SIZE)
    # Meshy ships JPEG maps and the model cook takes PNG only; glTF export 'AUTO' keeps a JPEG file's bytes, so each map
    # is copied into a new in-memory image (exported as PNG).
    for material in obj.data.materials:
        for node in material.node_tree.nodes if material and material.use_nodes else []:
            if node.type == 'TEX_IMAGE' and node.image is not None and node.image.size[0] > 0:
                source = node.image
                copy = bpy.data.images.new(source.name + '_png', source.size[0], source.size[1], alpha=False)
                copy.colorspace_settings.name = source.colorspace_settings.name
                copy.pixels[:] = source.pixels[:]
                node.image = copy
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    obj.name = name
    print('MESHY ITEM', name, faces, '->', len(obj.data.polygons), 'triangles')
    return obj


def main():
    names = sys.argv[sys.argv.index('--') + 1:]
    out_dir = os.path.join(HERE, 'work', 'meshy')
    os.makedirs(out_dir, exist_ok=True)
    pl.WORK = out_dir
    for name in names:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        obj = convert(name, DESIGNS[name])
        pl.export(obj, name)


main()
