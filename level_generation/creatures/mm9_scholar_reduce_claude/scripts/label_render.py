"""Diagnostic: render a labelled triangle soup (npz: P (n,3) glTF y-up, T (m,3), L (m,) int label, optional C (k,3) colours 0-1)
from several orthographic views with Workbench flat colours. Args (after --): <npz> <out png prefix> <view,...>
views: front, back, left, right, below3q (low 3/4 from the front), top. Each view -> <prefix>_<view>.png (800 px)."""
import bpy, sys, math
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]; d = np.load(a[0]); OUT = a[1]; VIEWS = a[2].split(',')
P = d['P'].astype(float); T = d['T'].astype(int); L = d['L'].astype(int)
C = d['C'] if 'C' in d.files else np.array([[.85, .2, .2], [.9, .75, .1], [.2, .35, .9], [.2, .7, .2], [.6, .6, .6], [.8, .3, .8], [.3, .8, .8], [1, .5, 0]])
bpy.ops.wm.read_factory_settings(use_empty=True)
co = np.c_[P[:, 0], -P[:, 2], P[:, 1]]
me = bpy.data.meshes.new('m'); me.from_pydata(co.tolist(), [], T.tolist()); me.update()
ob = bpy.data.objects.new('m', me); bpy.context.scene.collection.objects.link(ob)
for i, c in enumerate(C):
    m = bpy.data.materials.new(f'c{i}'); m.diffuse_color = (*c, 1); me.materials.append(m)
me.polygons.foreach_set('material_index', np.clip(L, 0, len(C) - 1).tolist()); me.update()
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'
sc.display.shading.color_type = 'MATERIAL'; sc.display.shading.show_backface_culling = False
sc.render.resolution_x = sc.render.resolution_y = 800; sc.world = bpy.data.worlds.new('w'); sc.world.color = (1, 1, 1)
cen = Vector(co.mean(0)); ext = float((co.max(0) - co.min(0)).max())
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = ext * 1.15
DIR = {'front': (0, -1, 0), 'back': (0, 1, 0), 'left': (1, 0, 0), 'right': (-1, 0, 0), 'below3q': (0.5, -0.8, -0.45),
       'top': (0, -0.05, 1), 'front3q': (0.6, -0.8, 0.1)}
for v in VIEWS:
    dv = Vector(DIR[v]).normalized(); cam.location = cen + dv * ext * 3
    cam.rotation_euler = (-dv).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{OUT}_{v}.png'; bpy.ops.render.render(write_still=True)
print('RENDERED', len(T))
