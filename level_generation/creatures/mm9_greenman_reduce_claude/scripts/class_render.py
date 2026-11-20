"""Render the installed LOD0 rest mesh coloured by work/glb_sets_<tag>.npz cls (kept classes warm, cut groups cool) into
review/classes_<tag>/: head front, 3/4, profile, back, top and the full body front/back. Usage: blender -b -P class_render.py -- <tag>"""
import os
import sys
import bpy
import numpy as np
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, 'scripts'))
import glbio  # noqa: E402
tag = sys.argv[sys.argv.index('--') + 1]
doc, b, nd, D = glbio.load(os.path.join(HERE, 'before', 'mm9_greenman.glb'), 'Sigmund')
s = np.load(os.path.join(HERE, 'work', f'glb_sets_{tag}.npz')); cls, keep = s['cls'], s['keep']
P = np.concatenate([d['P'] for d in D.values()]); off = np.cumsum([0] + [len(d['P']) for d in D.values()])
T = np.concatenate([d['T'] + off[i] for i, d in enumerate(D.values())])
V = np.c_[P[:, 0], -P[:, 2], P[:, 1]]
COL = {0: (.25, .5, 1), 1: (.2, .9, .9), 2: (1, .4, .1), 3: (1, .1, .1), 4: (.8, .5, .1), 5: (1, .6, .2), 10: (1, .75, .4),
       11: (1, 1, 1), 12: (.3, .3, 1), 13: (.1, .8, .2), 14: (1, .55, .1), 20: (.9, .8, .1), 21: (.5, .2, .9), 22: (1, .2, .5),
       23: (.9, .7, .2), 24: (.2, .7, .5), 25: (1, .9, .5), 15: (.6, .3, .1), 16: (1, 1, .6), 30: (.15, .15, .15), 31: (.4, .4, .4), -1: (1, 0, 1)}
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
me = bpy.data.meshes.new('m'); me.from_pydata(V.tolist(), [], T.tolist()); me.update()
mats = {}
for c in np.unique(cls):
    m = bpy.data.materials.new(f'c{c}'); m.diffuse_color = (*COL[int(c)], 1); me.materials.append(m); mats[int(c)] = len(me.materials) - 1
for p, c in zip(me.polygons, cls):
    p.material_index = mats[int(c)]
o = bpy.data.objects.new('m', me); sc.collection.objects.link(o)
cam = bpy.data.objects.new('c', bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'
sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'MATERIAL'
sc.display.shading.show_object_outline = False; sc.display.shading.show_cavity = True
sc.render.resolution_x = sc.render.resolution_y = 700
out = os.path.join(HERE, 'review', f'classes_{tag}'); os.makedirs(out, exist_ok=True)
head = Vector((0, -0.0, 1.58)); body = Vector((0, 0, 0.87))
shots = [('head_front', head, (0, -1, .05), .42), ('head_q34', head, (-.7, -.7, .1), .42), ('head_side', head, (-1, 0, .05), .42),
         ('head_back', head, (0, 1, .1), .42), ('head_top', head, (0, -.3, 1), .42), ('body_front', body, (0, -1, .1), 1.9),
         ('body_back', body, (0, 1, .1), 1.9), ('hand_R', Vector((-.57, -0.05, 0.965)), (-.3, -1, .3), .4), ('hand_L', Vector((.57, -0.05, 0.965)), (.3, -1, .3), .4)]
for name, c, dv, scale in shots:
    cam.data.ortho_scale = scale
    cam.location = c + Vector(dv).normalized() * 4; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(out, f'{name}.png'); bpy.ops.render.render(write_still=True)
print('RENDERED', out)
