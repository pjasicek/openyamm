"""Quick look at a weapon model (README.md): a contact sheet of the whole weapon from the front, the edge and three
quarters, and close-ups of the head and the grip, under Workbench studio light (textured when the GLB has textures).

Usage: blender --background --python render_check.py -- <in.glb|in.blend> <out.png> [head_z_fraction] [grip_z]
"""
import os
import sys

import bpy
import numpy as np
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:]
SRC, OUT = argv[0], argv[1]
HEAD = float(argv[2]) if len(argv) > 2 else 0.8
GRIP = float(argv[3]) if len(argv) > 3 else 0.0

if SRC.endswith('.blend'):
    bpy.ops.wm.open_mainfile(filepath=SRC)
    textured = False
else:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=SRC)
    textured = any(img.size[0] > 8 for img in bpy.data.images)
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
co = np.concatenate([np.array([o.matrix_world @ v.co for v in o.data.vertices]) for o in meshes])
lo, hi = co.min(0), co.max(0)
scene = bpy.context.scene
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'TEXTURE' if textured else 'SINGLE'
scene.display.shading.single_color = (0.62, 0.62, 0.64)
scene.display.shading.show_specular_highlight = True
scene.display.shading.show_cavity = not textured
scene.render.film_transparent = False
scene.world = bpy.data.worlds.new('w')
scene.world.color = (0.18, 0.18, 0.2)
scene.view_settings.view_transform = 'Standard'
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
scene.collection.objects.link(cam)
cam.data.type = 'ORTHO'
cam.data.clip_end = 2000
scene.camera = cam
shots = []
long = hi[2] - lo[2]
centre = (lo + hi) / 2


def shot(name, target, direction, ortho, w, h):
    scene.render.resolution_x, scene.render.resolution_y = w, h
    cam.data.ortho_scale = ortho
    d = Vector(direction).normalized()
    cam.location = Vector(target) + d * 500
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    path = os.path.join(os.path.dirname(OUT), f'_{name}.png')
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    shots.append(path)


full = max(long, (hi[0] - lo[0]) * 1.2) * 1.05
shot('front', centre, (0, -1, 0), full, 360, 1200)
shot('edge', centre, (1, 0, 0), full, 360, 1200)
shot('quarter', centre, (0.7, -0.7, 0.35), full, 360, 1200)
head = Vector((centre[0], centre[1], lo[2] + long * (1 + HEAD) / 2))
span = max(long * (1 - HEAD), hi[0] - lo[0]) * 1.12
shot('head_front', head, (0, -1, 0), span, 560, 600)
shot('head_quarter', head, (0.6, -0.75, 0.3), span, 560, 600)
shot('grip', (0, 0, GRIP), (0.5, -0.8, 0.25), 40, 560, 600)

