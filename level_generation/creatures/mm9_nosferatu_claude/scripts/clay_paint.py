"""Exact orthographic clay views of the frozen figure for the Codex paint: 1024x1536, true alpha. Args: <asm npz> <out dir>"""
import bpy, sys
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
D = np.load(a[0]); co, tri, comp = D['co'], D['tri'], D['comp']; names = [str(x) for x in D['names']]
keep = ~np.isin(comp, [names.index(n) for n in ('rlining', 'slining', 'feet', 'plug')])
ft = keep[tri].all(1); vs, inv = np.unique(tri[ft], return_inverse=True); T = inv.reshape(-1, 3); P = co[vs]
bpy.ops.wm.read_factory_settings(use_empty=True)
me = bpy.data.meshes.new('b'); me.from_pydata(P.tolist(), [], T.tolist()); me.update()
for p in me.polygons: p.use_smooth = True
o = bpy.data.objects.new('b', me); bpy.context.scene.collection.objects.link(o)
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.single_color = (.78, .76, .72); sh.show_cavity = True; sh.show_backface_culling = True
sc.render.resolution_x = 1024; sc.render.resolution_y = 1536; sc.render.film_transparent = True; sc.render.image_settings.color_mode = 'RGBA'
cd = bpy.data.cameras.new('C'); cd.type = 'ORTHO'; cd.sensor_fit = 'VERTICAL'; cd.ortho_scale = 2.05; cd.clip_end = 100; cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
c = Vector((0, 0, 0.98))
for v, d in {'01_front': (0, -1, 0), '03_left': (1, 0, 0), '02_back': (0, 1, 0), '04_right': (-1, 0, 0)}.items():
    d = Vector(d).normalized(); cam.location = c + d * 10; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{a[1]}/clay_{v}.png'; bpy.ops.render.render(write_still=True)
