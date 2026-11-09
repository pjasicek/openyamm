"""Grey orthographic renders of the split model (work/harvester_parts_raw.blend), 1536x1024, transparent: the
geometry authority for redrawn retexture views. Args: -- <out dir>"""
import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = os.path.abspath(sys.argv[sys.argv.index('--') + 1])
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'harvester_parts_raw.blend'))
obj = bpy.data.objects['harvester']
scene = bpy.context.scene
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'SINGLE'
scene.display.shading.single_color = (0.75, 0.75, 0.73)
scene.display.shading.show_cavity = True
scene.render.film_transparent = True
scene.render.resolution_x, scene.render.resolution_y = 1536, 1024
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam'))
scene.collection.objects.link(cam); scene.camera = cam
cam.data.type = 'ORTHO'
pts = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
lo = Vector([min(p[i] for p in pts) for i in range(3)]); hi = Vector([max(p[i] for p in pts) for i in range(3)])
centre = (lo + hi) / 2
for name, (az, scale) in {'front': (0, 7.0), 'back': (180, 7.0), 'left': (90, 11.5), 'right': (-90, 11.5)}.items():
    a = math.radians(az)
    d = Vector((math.sin(a), -math.cos(a), 0))
    cam.data.ortho_scale = scale
    cam.location = centre + d * 30
    cam.data.clip_end = 100
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = os.path.join(out, f'meshy_geometry_{name}.png')
    bpy.ops.render.render(write_still=True)
