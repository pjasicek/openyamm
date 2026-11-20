"""Render work/<name>_parts_raw.blend coloured by part (workbench): 34, front, left, back, top.
Args: -- <name> <out prefix>"""
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
args = sys.argv[sys.argv.index('--') + 1:]
name, prefix = args[:2]
stage = args[2] if len(args) > 2 else 'parts_raw'
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', f'{name}_{stage}.blend'))
obj = bpy.data.objects[name]
COL = [(0.45, 0.45, 0.45, 1), (0.2, 0.8, 0.2, 1), (0.2, 0.4, 1, 1), (1, 0.6, 0.1, 1), (1, 0.15, 0.15, 1)]
part = np.zeros(len(obj.data.polygons), int); obj.data.attributes['part'].data.foreach_get('value', part)
col = obj.data.color_attributes.new('c', 'FLOAT_COLOR', 'CORNER')
for poly in obj.data.polygons:
    for li in poly.loop_indices:
        col.data[li].color = COL[part[poly.index]]
obj.data.color_attributes.active_color_name = 'c'
scene = bpy.context.scene
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'VERTEX'
scene.render.resolution_x, scene.render.resolution_y = 700, 700
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam'))
scene.collection.objects.link(cam); scene.camera = cam
cam.data.type = 'ORTHO'
co = np.array([v.co[:] for v in obj.data.vertices])
lo, hi = Vector(co.min(0)), Vector(co.max(0)); centre = (lo + hi) / 2; size = max(hi - lo)
cam.data.ortho_scale = size * 1.1
for view, (az, el) in {'34': (-35, 15), 'front': (0, 0), 'left': (-90, 0), 'back': (180, 0), 'top': (0, 89)}.items():
    a, e = math.radians(az), math.radians(el)
    d = Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))
    cam.location = centre + d * size * 3
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = f'{prefix}_{view}.png'
    bpy.ops.render.render(write_still=True)
