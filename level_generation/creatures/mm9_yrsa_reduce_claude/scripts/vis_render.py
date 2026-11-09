"""Face-visibility renders of the installed rest LOD0 (both prims): every triangle drawn in a unique flat colour (Workbench,
no AA) from a ring of views around the head; work/vis/<view>.png decoded by vis_decode.py.
Also writes a textured-look class render when work/head_cls_render.npy exists (per-face class colours).
Usage: blender -b -P vis_render.py -- <mode: id|cls> [<npz with cls>]"""
import os, sys, math
import bpy
import numpy as np
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, 'scripts'))
import glbio  # noqa: E402
args = sys.argv[sys.argv.index('--') + 1:]
mode = args[0]
doc, b, nd, D = glbio.load(os.path.join(HERE, 'before', 'mm9_yrsa.glb'), 'Yrsa')
names = ['Yrsa', 'YrsaHead']
P = np.concatenate([D[n]['P'] for n in names]); off = np.cumsum([0] + [len(D[n]['P']) for n in names])
T = np.concatenate([D[n]['T'] + off[i] for i, n in enumerate(names)])
V = np.c_[P[:, 0], -P[:, 2], P[:, 1]]  # Blender frame: front of the model is +GLB z -> -Y
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
me = bpy.data.meshes.new('m'); me.from_pydata(V.tolist(), [], T.tolist()); me.update()
nf = len(T)
if mode == 'id':
    ids = np.arange(nf) + 1
    rgb = np.c_[(ids >> 16) & 255, (ids >> 8) & 255, ids & 255].astype(float) / 255
else:
    cls = np.load(args[1])['cls']
    pal = {0: (.95, .55, .45), 1: (.2, .4, 1), 2: (.35, .2, .08), 3: (0, .9, 0), 4: (1, 1, 0), 5: (1, 0, 1), 6: (0, 1, 1),
           7: (1, .5, 0), 8: (.6, 0, .9), 9: (.7, .7, .7), 10: (1, 1, 1), 11: (.1, .5, .1), 12: (.5, .5, 0), 13: (.9, .1, .1)}
    rgb = np.array([pal.get(int(c), (0, 0, 0)) for c in cls])
ca = me.color_attributes.new('col', 'FLOAT_COLOR', 'CORNER')
cols = np.repeat(np.c_[rgb, np.ones(nf)], 3, axis=0)
# srgb->linear inverse so the view transform 'Standard' gives exact bytes
lin = np.where(cols[:, :3] <= 0.04045, cols[:, :3] / 12.92, ((cols[:, :3] + 0.055) / 1.055) ** 2.4)
cols[:, :3] = lin
ca.data.foreach_set('color', cols.ravel())
o = bpy.data.objects.new('m', me); sc.collection.objects.link(o)
cam = bpy.data.objects.new('c', bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'
sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'FLAT' if mode == 'id' else 'STUDIO'
sc.display.shading.color_type = 'VERTEX'
sc.display.shading.show_object_outline = False
sc.display.render_aa = 'OFF' if mode == 'id' else 'FXAA'
sc.view_settings.view_transform = 'Standard'
sc.render.image_settings.color_depth = '8'
sc.render.resolution_x = sc.render.resolution_y = 900 if mode == 'id' else 700
outd = os.path.join(HERE, 'work' if mode == 'id' else 'review', 'vis' if mode == 'id' else 'head_cls')
os.makedirs(outd, exist_ok=True)
head = Vector((0, -0.29, 1.50))
views = []
for yaw in range(-110, 111, 20):
    for pitch in (-35, -15, 0, 15, 35):
        views.append((f'y{yaw}_p{pitch}', yaw, pitch))
if mode != 'id':
    views = [('front', 0, 0), ('q34', 45, 5), ('profile', 90, 0), ('low34', 40, -30), ('back', 180, 5), ('top', 0, 80), ('q34r', -45, 5)]
for name, yaw, pitch in views:
    cam.data.ortho_scale = 0.42
    y, p = math.radians(yaw), math.radians(pitch)
    d = Vector((math.sin(y) * math.cos(p), -math.cos(y) * math.cos(p), math.sin(p)))
    cam.location = head + d * 3; cam.rotation_euler = (head - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(outd, f'{name}.png'); bpy.ops.render.render(write_still=True)
print('RENDERED', outd, len(views))
