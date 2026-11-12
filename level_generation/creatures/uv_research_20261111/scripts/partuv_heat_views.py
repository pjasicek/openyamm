"""PartUV study: density heatmaps on the model. Generic version of mm9_magreeb_claude/scripts/texpass_views.py: the
measurement GLB of partuv_apply_uv.py, its blank images replaced by texture_quality.py heatmaps, rest pose, Eevee,
four cameras around the mesh bounds (front, three-quarter, side, back; front is -Y in Blender, the glTF +Z).

Args: <measure glb> <out png> <image substring>=<heat png> [...] [forward=-y|+y|+x|-x]
Writes one 2 x 2 sheet (each view 700 x 700).
"""
import os
import sys
import tempfile

import bpy
from mathutils import Vector

args = sys.argv[sys.argv.index('--') + 1:]
glb, out = args[0], args[1]
opts = dict(a.split('=', 1) for a in args[2:])
forward_key = opts.pop('forward', '-y')
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
for mat in bpy.data.materials:
    if not mat.node_tree:
        continue
    for node in mat.node_tree.nodes:
        if node.type == 'TEX_IMAGE' and node.image:
            for key, path in opts.items():
                if key in node.image.name:
                    node.image = bpy.data.images.load(path)
                    node.interpolation = 'Closest'
        if node.type == 'BSDF_PRINCIPLED':
            node.inputs['Roughness'].default_value = 0.8
bpy.context.view_layer.update()
sc = bpy.context.scene
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
pts = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
lo = Vector([min(p[i] for p in pts) for i in range(3)])
hi = Vector([max(p[i] for p in pts) for i in range(3)])
centre, size = (lo + hi) / 2, max(hi - lo)
up = Vector((0, 0, 1))
forward = {'-y': Vector((0, -1, 0)), '+y': Vector((0, 1, 0)), '+x': Vector((1, 0, 0)), '-x': Vector((-1, 0, 0))}[
    forward_key]
side = forward.cross(up)
try:
    sc.render.engine = 'BLENDER_EEVEE_NEXT'
except TypeError:
    sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x = sc.render.resolution_y = 700
world = bpy.data.worlds.new('w')
sc.world = world
world.use_nodes = True
world.node_tree.nodes['Background'].inputs[0].default_value = (0.32, 0.33, 0.35, 1)
world.node_tree.nodes['Background'].inputs[1].default_value = 1.4
sc.view_settings.view_transform = 'Standard'
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
sc.collection.objects.link(cam)
sc.camera = cam
cam.data.lens = 50
tmp = tempfile.mkdtemp()
shots = []
for name, d in (('front', forward + up * 0.2), ('q34', forward + side + up * 0.4), ('side', side + up * 0.1),
                ('back', -forward + up * 0.3)):
    cam.location = centre + d.normalized() * size * 1.9
    cam.rotation_euler = (centre - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(tmp, name + '.png')
    bpy.ops.render.render(write_still=True)
    shots.append(sc.render.filepath)
sheet = bpy.data.images.new('sheet', 1400, 1400)
pixels = [0.0] * (1400 * 1400 * 4)
for k, path in enumerate(shots):
    img = bpy.data.images.load(path)
    px = list(img.pixels)
    ox, oy = (k % 2) * 700, (1 - k // 2) * 700
    for y in range(700):
        row = px[y * 700 * 4:(y + 1) * 700 * 4]
        start = ((oy + y) * 1400 + ox) * 4
        pixels[start:start + 700 * 4] = row
sheet.pixels = pixels
sheet.filepath_raw = out
sheet.file_format = 'PNG'
sheet.save()
print('HEAT_VIEWS', out)
