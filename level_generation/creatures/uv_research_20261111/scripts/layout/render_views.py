"""Render a static GLB with one texture from fixed orthographic cameras (front, side, back, above), flat workbench
shading with the texture colour, so the same cameras compare layouts.

blender.sh render_views.py <log> <glb> <texture png> <out prefix> [yaw_deg=0] [res=640]
Views: azimuth yaw+0 (front), +90 (side), +180 (back), and from above (elevation 55 deg, azimuth yaw+30).
"""
import math
import os
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:]
GLB, TEX, OUT = argv[:3]
opts = dict(a.split('=', 1) for a in argv[3:])
YAW = float(opts.get('yaw', 0))
RES = int(opts.get('res', 640))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
img = bpy.data.images.load(TEX)
mat = bpy.data.materials.new('review')
mat.use_nodes = True
bsdf = next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
tex = mat.node_tree.nodes.new('ShaderNodeTexImage')
tex.image = img
tex.interpolation = 'Closest'
mat.node_tree.links.new(tex.outputs[0], bsdf.inputs[0])
for o in meshes:
    o.data.materials.clear()
    o.data.materials.append(mat)
pts = [o.matrix_world @ v.co for o in meshes for v in o.data.vertices]
lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
centre, radius = (lo + hi) / 2, (hi - lo).length / 2
scene = bpy.context.scene
try:
    scene.render.engine = 'BLENDER_WORKBENCH'
except TypeError:
    scene.render.engine = 'WORKBENCH'
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'TEXTURE'
scene.display.shading.show_cavity = False
scene.render.resolution_x = scene.render.resolution_y = RES
scene.render.film_transparent = False
scene.world = bpy.data.worlds.new('w') if scene.world is None else scene.world
cam_data = bpy.data.cameras.new('cam')
cam_data.type = 'ORTHO'
cam_data.ortho_scale = radius * 2.05
cam = bpy.data.objects.new('cam', cam_data)
scene.collection.objects.link(cam)
scene.camera = cam
views = [('front', 0, 8), ('side', 90, 8), ('back', 180, 8), ('above', 30, 55)]
for name, az, el in views:
    a, e = math.radians(YAW + az), math.radians(el)
    d = Vector((math.cos(e) * math.cos(a), math.cos(e) * math.sin(a), math.sin(e)))
    cam.location = centre + d * radius * 4
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = f'{OUT}_{name}.png'
    bpy.ops.render.render(write_still=True)
print('RENDER done', OUT)
