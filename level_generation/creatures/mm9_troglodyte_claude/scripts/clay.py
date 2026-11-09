"""Quick clay render from npz (co, tri; glTF frame) with Blender. Args: <npz> <out prefix> [size] [center x,y,z] [ortho]; env VIEWS"""
import bpy, sys, os
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
D = np.load(a[0]); co = D['co']; tri = D['tri']
bpy.ops.wm.read_factory_settings(use_empty=True)
me = bpy.data.meshes.new('m'); ob = bpy.data.objects.new('m', me); bpy.context.scene.collection.objects.link(ob)
B = np.c_[co[:, 0], -co[:, 2], co[:, 1]]
me.from_pydata(B.tolist(), [], tri.tolist()); me.update()
for p in me.polygons: p.use_smooth = True
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.single_color = (.72, .72, .72); sh.show_cavity = True; sh.show_backface_culling = False
size = int(a[2]) if len(a) > 2 else 700
sc.render.resolution_x = sc.render.resolution_y = size
sc.world = bpy.data.worlds.new('W'); sc.world.color = (0.25, 0.25, 0.28); sh.background_type = 'WORLD'
cd = bpy.data.cameras.new('C'); cd.type = 'ORTHO'; cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
c = Vector([float(x) for x in a[3].split(',')]) if len(a) > 3 else Vector((B.min(0) + B.max(0)) / 2)
cd.ortho_scale = float(a[4]) if len(a) > 4 else 1.45
views = {'front': (0, -1, 0), 'left': (1, 0, 0), 'back': (0, 1, 0), 'right': (-1, 0, 0), 'q34': (-1, -1.2, 0.3), 'qback': (1, 1.1, 0.4), 'below': (0, -0.8, -0.9), 'qleft': (1, -1, .1)}
sel = os.environ.get('VIEWS', 'q34,front,left,back,qback').split(',')
for n in sel:
    d = Vector(views[n]).normalized()
    cam.location = c + d * 10; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{a[1]}_{n}.png'; bpy.ops.render.render(write_still=True)
