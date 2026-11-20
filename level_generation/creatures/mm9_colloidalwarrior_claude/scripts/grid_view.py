"""Ortho clay views of Body with a labelled 10 cm grid (diagnosis). Args: <blend> <out prefix> <cx,cy,cz> <ortho>
front: image x = world X, image y = world Z; side (from +X): image x = world Y."""
import bpy, sys, os
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
for o in list(bpy.data.objects):
    if o.type == 'MESH' and o.name not in os.environ.get('OBJ', 'Body').split(','): bpy.data.objects.remove(o)
C = Vector([float(x) for x in a[2].split(',')]); S = float(a[3]); R = 900
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.show_cavity = True
sc.render.resolution_x = sc.render.resolution_y = R
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = S
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
for v, d in {'front': (0, -1, 0), 'side': (1, 0, 0)}.items():
    d = Vector(d); cam.location = C + d * 10; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{a[1]}_{v}.png'; bpy.ops.render.render(write_still=True)
