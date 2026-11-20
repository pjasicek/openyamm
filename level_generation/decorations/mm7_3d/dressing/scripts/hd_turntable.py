"""Turntable of a GLB (8 yaws, studio light) into one sheet for orientation checks.
Usage: blender -b --python hd_turntable.py -- <glb> <out.png> [rot_z degrees]"""
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dlib  # noqa: E402

pl = dlib.pl
args = sys.argv[sys.argv.index('--') + 1:]
glb, out = args[0], args[1]
turn = float(args[2]) if len(args) > 2 else 0.0
pl.reset()
bpy.ops.import_scene.gltf(filepath=glb)
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
for o in meshes:
    o.rotation_euler.z += math.radians(turn)
bpy.context.view_layer.update()
pl.setup_render((300, 400))
tmp = os.path.join(os.path.dirname(out), '_tt'); os.makedirs(tmp, exist_ok=True)
paths = pl.render_views(meshes, tmp, 'tt', views=tuple((y, 8) for y in range(0, 360, 45)))
import numpy as np
imgs = []
for p in paths:
    im = bpy.data.images.load(p); px = np.array(im.pixels[:]).reshape(400, 300, 4)[::-1]; imgs.append(px)
sheet = np.concatenate(imgs, 1)
img = bpy.data.images.new('sheet', sheet.shape[1], sheet.shape[0], alpha=True)
img.pixels.foreach_set(sheet[::-1].astype(np.float32).ravel())
img.filepath_raw = out; img.file_format = 'PNG'; img.save()
print('TURNTABLE', out)
