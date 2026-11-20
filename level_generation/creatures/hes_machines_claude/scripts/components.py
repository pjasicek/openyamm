"""Orient a Meshy return (machines_common.orient), list its connected components and render them in random colours
(workbench, orthographic): 34, front, left, back, top. Component marks per view go to <prefix>_<view>_marks.json.
Args: -- <name> <out prefix> [turn degrees]"""
import json
import math
import os
import random
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, 'scripts'))
import machines_common as mc  # noqa: E402

args = sys.argv[sys.argv.index('--') + 1:]
name, prefix = args[:2]
turn = float(args[2]) if len(args) > 2 else None
obj = mc.orient(mc.import_glb(mc.RAW[name]), name, turn)
bm = bmesh.new(); bm.from_mesh(obj.data)
labels = mc.component_labels(bm)
co = np.array([v.co[:] for v in bm.verts])
rows = []
for c in range(labels.max() + 1):
    p = co[labels == c]
    rows.append({'c': c, 'n': int(len(p)), 'lo': p.min(0).round(3).tolist(), 'hi': p.max(0).round(3).tolist(),
                 'mid': p.mean(0).round(3).tolist()})
rows.sort(key=lambda r: r['mid'][2])
print('TRIS', sum(len(f.verts) - 2 for f in bm.faces), 'VERTS', len(bm.verts), 'COMPONENTS', len(rows))
for r in rows:
    if r['n'] >= 30:
        print('COMP', r['c'], r['n'], 'lo', r['lo'], 'hi', r['hi'], 'mid', r['mid'])
json.dump(rows, open(prefix + '_components.json', 'w'), indent=0)
print('BOUNDS', co.min(0).round(3), co.max(0).round(3))
random.seed(3)
cols = [(random.random(), random.random(), random.random(), 1) for _ in range(labels.max() + 1)]
layer = bm.loops.layers.color.new('c')
for f in bm.faces:
    for l in f.loops:
        l[layer] = cols[labels[l.vert.index]]
bm.to_mesh(obj.data); bm.free()
obj.data.color_attributes.active_color_name = 'c'
obj.data.color_attributes.render_color_index = 0
scene = bpy.context.scene
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'VERTEX'
scene.render.resolution_x, scene.render.resolution_y = 800, 800
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam'))
scene.collection.objects.link(cam); scene.camera = cam
cam.data.type = 'ORTHO'
lo, hi = Vector(co.min(0)), Vector(co.max(0)); centre = (lo + hi) / 2; size = max(hi - lo)
cam.data.ortho_scale = size * 1.1
from bpy_extras.object_utils import world_to_camera_view  # noqa: E402
for view, (az, el) in {'34': (-35, 15), 'front': (0, 0), 'left': (-90, 0), 'back': (180, 0), 'top': (0, 89)}.items():
    a, e = math.radians(az), math.radians(el)
    d = Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))
    cam.location = centre + d * size * 3
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = f'{prefix}_{view}.png'
    bpy.ops.render.render(write_still=True)
    marks = []
    for r in rows:
        if r['n'] < 30:
            continue
        p = world_to_camera_view(scene, cam, Vector(r['mid']))
        marks.append((r['c'], p.x, 1 - p.y))
    json.dump(marks, open(f'{prefix}_{view}_marks.json', 'w'))
