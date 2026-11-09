"""Render MM9's TREASUREBAG.abc with its five skins (BAG1-5) side by side, for comparing tier readability.
Run: blender -b --python scripts/render_mm9_bags.py  ->  mm9_reference/mm9_bags.png"""
import os, sys
import bpy
from mathutils import Vector

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(REPO, 'mm9', 'io_scene_lithtech'))
from src.reader_abc_pc import ABCModelReader
from src.reader_abc_v6_pc import ABCV6ModelReader

OUT = os.path.join(REPO, 'level_generation', 'props', 'loot_satchel_claude', 'mm9_reference')
path = os.path.join(REPO, 'mm9', 'extracted', 'MODELS', 'MODELS', 'PICKUPITEMS', 'TREASUREBAG.abc')
bpy.ops.wm.read_factory_settings(use_empty=True)
try:
    model = ABCModelReader().from_file(path)
except Exception:
    model = ABCV6ModelReader().from_file(path)
# Build the mesh directly (the bundled importer predates this Blender): each piece's LOD0 faces in bind space.
# Vertex locations are relative to their weighted node; the bag is rigid, so the first weight's node bind matrix
# places them.
verts, faces, uvs = [], [], []
for piece in model.pieces:
    lod = piece.lods[0]
    base = len(verts)
    for vertex in lod.vertices:
        weight = vertex.weights[0]
        verts.append(tuple(model.nodes[weight.node_index].bind_matrix @ weight.location))
    for face in lod.faces:
        faces.append(tuple(base + fv.vertex_index for fv in face.vertices))
        uvs.append([(fv.texcoord.x, 1.0 - fv.texcoord.y) for fv in face.vertices])
mesh = bpy.data.meshes.new('bag')
mesh.from_pydata(verts, [], faces)
layer = mesh.uv_layers.new()
for poly, face_uvs in zip(mesh.polygons, uvs):
    for loop, uv in zip(poly.loop_indices, face_uvs):
        layer.data[loop].uv = uv
mesh.update()
src = bpy.data.objects.new('bag', mesh)
bpy.context.collection.objects.link(src)
src.rotation_euler = (1.5708, 0, 0)   # LithTech is Y-up
bpy.context.view_layer.update()
print('MESH', len(verts), len(faces))
bb = [src.matrix_world @ Vector(c) for c in src.bound_box]
size = max(max(v[i] for v in bb) - min(v[i] for v in bb) for i in range(3))
center = sum(bb, Vector()) / 8
for n in range(1, 6):
    obj = src if n == 1 else src.copy()
    if n > 1:
        obj.data = src.data.copy()
        bpy.context.collection.objects.link(obj)
    obj.location = Vector(((n - 3) * size * 1.3, 0, 0))
    mat = bpy.data.materials.new(f'bag{n}')
    mat.use_nodes = True
    bsdf = next(x for x in mat.node_tree.nodes if x.type == 'BSDF_PRINCIPLED')
    tex = mat.node_tree.nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(os.path.join(OUT, f'bag{n}_skin.png'))
    mat.node_tree.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = 0.8
    obj.data.materials.clear()
    obj.data.materials.append(mat)
bpy.context.view_layer.update()
bags = [o for o in bpy.data.objects if o.type == 'MESH']
corners = [o.matrix_world @ Vector(c) for o in bags for c in o.bound_box]
center = sum(corners, Vector()) / len(corners)
scene = bpy.context.scene
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
scene.collection.objects.link(cam)
scene.camera = cam
cam.data.type = 'ORTHO'
cam.data.ortho_scale = size * 8.6
# three-quarter view from above (z up after import)
direction = Vector((0.0, -1.0, 0.55)).normalized()
cam.location = center + direction * size * 10
cam.rotation_euler = (-direction).to_track_quat('-Z', 'Y').to_euler()
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN'))
sun.data.energy = 3.0
sun.rotation_euler = (0.7, 0.2, 0.6)
scene.collection.objects.link(sun)
scene.world = bpy.data.worlds.new('w')
scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs[0].default_value = (0.45, 0.47, 0.42, 1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value = 0.8
scene.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE'
scene.render.resolution_x, scene.render.resolution_y = 1800, 420
scene.render.filepath = os.path.join(OUT, 'mm9_bags.png')
bpy.ops.render.render(write_still=True)
