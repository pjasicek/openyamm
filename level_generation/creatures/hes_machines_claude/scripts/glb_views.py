"""Workbench views of any GLB (texture colour, backface culling on, so holes show the background): front, right,
back, left, top, bottom three-quarter. Args: -- <glb> <out prefix>"""
import math
import sys

import bpy
import numpy as np
from mathutils import Vector

glb, prefix = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
scene = bpy.context.scene
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'TEXTURE'
scene.display.shading.show_backface_culling = True
scene.render.resolution_x, scene.render.resolution_y = 600, 600
scene.render.film_transparent = False
scene.world = bpy.data.worlds.new('w'); scene.world.color = (0.6, 0.0, 0.6)
scene.display.shading.background_type = 'WORLD' if hasattr(scene.display.shading, 'background_type') else None
meshes = [o for o in scene.objects if o.type == 'MESH' and 'LOD' not in o.name and 'Shadow' not in o.name]
for o in scene.objects:
    if o.type == 'MESH' and o not in meshes:
        o.hide_render = True
co = np.array([(o.matrix_world @ v.co)[:] for o in meshes for v in o.data.vertices])
lo, hi = Vector(co.min(0)), Vector(co.max(0)); centre = (lo + hi) / 2; size = max(hi - lo)
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); scene.collection.objects.link(cam); scene.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = size * 1.15
for view, (az, el) in {'front': (0, 10), 'right': (90, 10), 'back': (180, 10), 'left': (-90, 10), 'top': (0, 89),
                       'low34': (-40, -20)}.items():
    a, e = math.radians(az), math.radians(el)
    d = Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))
    cam.location = centre + d * size * 3
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = f'{prefix}_{view}.png'
    bpy.ops.render.render(write_still=True)
