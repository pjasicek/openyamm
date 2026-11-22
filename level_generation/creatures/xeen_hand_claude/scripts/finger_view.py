"""Render the finger centrelines (work/fingers.json) over the clay hand: rods along each line, a ball every 2 cm
(bigger every 6 cm). review/fingers_<view>.png"""
import bpy, os, sys, json, bmesh
import numpy as np
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'clean_v2.blend'))
Fj = json.load(open(os.path.join(HERE, 'work', 'fingers.json')))['fingers']
bm = bmesh.new()
for k, f in Fj.items():
    pts = [f['tip']] + f['centres']
    for i, p in enumerate(pts):
        if i % 4 == 0:
            bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=6, radius=0.006 if i % 12 else 0.011,
                                      matrix=Matrix.Translation(Vector(p)))
me = bpy.data.meshes.new('Raw'); bm.to_mesh(me); o = bpy.data.objects.new('Raw', me)
bpy.context.scene.collection.objects.link(o)
m = bpy.data.materials.new('r'); m.diffuse_color = (1, 0.1, 0.1, 1); me.materials.append(m)
C.COLOR_OVERRIDE = 'MATERIAL'
for name, d in {'front': (0, -5, 0), 'side': (-5, 0, 0), 'top': (0, 0, 5)}.items():
    C.render((d[0], d[1], 0.25 + d[2]), (0, 0, 0.25), 0.72, os.path.join(HERE, 'review', f'fingers_{name}.png'),
             res=(700, 560), floor=False, bones=True)
