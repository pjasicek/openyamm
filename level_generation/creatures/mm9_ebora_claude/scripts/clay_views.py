"""Clay renders of the body (asm npz, true-handed = x negated), 1024x1536, masters' framing, transparent background.
Names follow the masters: 00_three_quarter (front 3/4 from the figure's RIGHT), 01_front, 02_back, 03_left (figure's
LEFT side, faces image left), 04_right. Args: <asm npz> <out dir> <prefix>"""
import bpy, sys, numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
D = np.load(a[0]); co = D['co'] * [-1, 1, 1]; tri = D['tri'][:, ::-1]
bpy.ops.wm.read_factory_settings(use_empty=True)
me = bpy.data.meshes.new('m'); me.from_pydata(co.tolist(), [], tri.tolist()); me.update()
for p in me.polygons: p.use_smooth = True
ob = bpy.data.objects.new('o', me); bpy.context.collection.objects.link(ob)
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading
sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.single_color = (0.78, 0.76, 0.74); sh.show_cavity = True; sh.cavity_type = 'BOTH'
sc.render.resolution_x = 1024; sc.render.resolution_y = 1536; sc.render.film_transparent = True
cd = bpy.data.cameras.new('C'); cd.type = 'ORTHO'; cd.ortho_scale = 2.10; cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
c = Vector((0, 0, 0.14))
V = {'00_three_quarter': (-0.62, -1.0, 0.18), '01_front': (0, -1, 0.0), '02_back': (0, 1, 0.0), '03_left': (-1, 0, 0.0), '04_right': (1, 0, 0.0)}
for n, d in V.items():
    d = Vector(d).normalized(); cam.location = c + d * 10; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{a[1]}/{a[2]}{n}.png'; bpy.ops.render.render(write_still=True)
