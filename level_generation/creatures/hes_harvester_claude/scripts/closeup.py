"""Close-up of the oriented raw return with components in random colours (or a highlight set in red).
Args: -- <out.png> <azimuth> <elevation> <cx> <cy> <cz> <ortho size> [highlight component ids, comma separated]"""
import math
import os
import random
import sys

import bmesh
import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harvester_common as tc  # noqa: E402

a = sys.argv[sys.argv.index('--') + 1:]
out, az, el, cx, cy, cz, size = a[0], *map(float, a[1:7])
hl = {int(x) for x in a[7].split(',')} if len(a) > 7 else None
obj = tc.import_raw()
bm = bmesh.new(); bm.from_mesh(obj.data)
labels = tc.component_labels(bm)
random.seed(3)
cols = [(random.random(), random.random(), random.random(), 1) for _ in range(labels.max() + 1)]
layer = bm.loops.layers.color.new('c')
for f in bm.faces:
    c = labels[f.verts[0].index]
    col = cols[c] if hl is None else ((0.9, 0.1, 0.1, 1) if c in hl else (0.7, 0.7, 0.7, 1))
    for loop in f.loops:
        loop[layer] = col
bm.to_mesh(obj.data); bm.free()
obj.data.color_attributes.render_color_index = 0
scene = bpy.context.scene
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'VERTEX'
scene.display.shading.show_cavity = True
scene.render.resolution_x, scene.render.resolution_y = 900, 900
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam'))
scene.collection.objects.link(cam); scene.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = size
A, E = math.radians(az), math.radians(el)
d = Vector((math.sin(A) * math.cos(E), -math.cos(A) * math.cos(E), math.sin(E)))
cam.location = Vector((cx, cy, cz)) + d * 30
cam.data.clip_end = 100
cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
scene.render.filepath = os.path.abspath(out)
bpy.ops.render.render(write_still=True)
