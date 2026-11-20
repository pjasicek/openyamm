"""Render the installed LOD0 rest mesh (before/mm9_krohn.glb, all three primitives) coloured by a per-GLB-face label array
(<npz> key <key>, default work/glb_sets_<tag>.npz 'cls'): fixed colours for the class ids of make_sets_kr.py, hashed colours for
other ids (UV charts). -> review/classes_<tag>/: head front, 3/4, profile, back, top, low 3/4, body front/back/side, both hands.
Usage: blender -b -P class_render.py -- <tag> [npz key [hash]]"""
import os
import sys
import bpy
import numpy as np
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, 'scripts'))
import glbio  # noqa: E402
argv = sys.argv[sys.argv.index('--') + 1:]
tag = argv[0]
doc, b, nd, D = glbio.load(os.path.join(HERE, 'before', 'mm9_krohn.glb'), 'Krohn')
if len(argv) > 2:
    cls = np.load(os.path.join(HERE, argv[1]))[argv[2]]
else:
    cls = np.load(os.path.join(HERE, 'work', f'glb_sets_{tag}.npz'))['cls']
P = np.concatenate([d['P'] for d in D.values()]); off = np.cumsum([0] + [len(d['P']) for d in D.values()])
T = np.concatenate([d['T'] + off[i] for i, d in enumerate(D.values())])
V = np.c_[P[:, 0], -P[:, 2], P[:, 1]]
COL = {0: (.25, .5, 1), 1: (.2, .9, .9), 2: (1, .4, .1), 3: (1, .1, .1), 4: (.8, .5, .1), 5: (1, .6, .2), 6: (.9, .3, .6),
       7: (.6, .3, .1), 8: (.4, .9, .4), 9: (.1, .3, .3),
       10: (1, .75, .4), 11: (1, 1, 1), 12: (.3, .3, 1), 13: (.1, .8, .2), 14: (1, .55, .1), 15: (.9, .2, .9), 16: (.5, .5, .5),
       20: (.9, .8, .1), 21: (.5, .2, .9), 22: (1, .2, .5), 23: (.9, .7, .2), 24: (.2, .7, .5), 25: (1, .9, .5)}
rng = np.random.default_rng(3)
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
me = bpy.data.meshes.new('m'); me.from_pydata(V.tolist(), [], T.tolist()); me.update()
mats = {}
for c in np.unique(cls):
    m = bpy.data.materials.new(f'c{c}')
    m.diffuse_color = (*(COL[int(c)] if len(argv) <= 3 and int(c) in COL else tuple(rng.random(3))), 1)
    me.materials.append(m); mats[int(c)] = len(me.materials) - 1
for p, c in zip(me.polygons, cls):
    p.material_index = mats[int(c)]
o = bpy.data.objects.new('m', me); sc.collection.objects.link(o)
cam = bpy.data.objects.new('c', bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'
sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'MATERIAL'
sc.display.shading.show_object_outline = False; sc.display.shading.show_cavity = True
sc.render.resolution_x = sc.render.resolution_y = 700
out = os.path.join(HERE, 'review', f'classes_{tag}'); os.makedirs(out, exist_ok=True)
# glTF +z (front) -> Blender -y; the model faces Blender -y
head = Vector((0, -0.0, 2.45)); body = Vector((0, 0, 1.4))
shots = [('head_front', head, (0, -1, .05), .9), ('head_q34', head, (-.7, -.7, .1), .9), ('head_side', head, (-1, 0, .05), .9),
         ('head_back', head, (0, 1, .1), .9), ('head_top', head, (0, -.3, 1), .9), ('head_low', head, (-.6, -.7, -.45), .9),
         ('body_front', body, (0, -1, .1), 3.0), ('body_back', body, (0, 1, .1), 3.0), ('body_side', body, (1, 0, .1), 3.0),
         ('hand_R', Vector((-1.05, -0.1, 1.65)), (0, -1, .1), .5), ('hand_L', Vector((1.05, -0.1, 1.65)), (0, -1, .1), .5),
         ('hand_Rb', Vector((-1.05, -0.1, 1.65)), (-1, .3, .1), .5), ('hand_Lb', Vector((1.05, -0.1, 1.65)), (1, .3, .1), .5)]
for name, c, dv, scale in shots:
    cam.data.ortho_scale = scale
    cam.location = c + Vector(dv).normalized() * 4; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(out, f'{name}.png'); bpy.ops.render.render(write_still=True)
print('RENDERED', out)
