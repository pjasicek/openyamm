"""Clay renders of the upload figure (true-handed: x negated, as make_upload.py writes it; staff left out), the geometry the Codex paints go on.
1024x1536 portrait, orthographic, transparent. Views front, left (camera on the figure's left), back, right. Args: <uv npz> <out dir>"""
import bpy, sys
from mathutils import Vector
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
D = np.load(a[0]); co = D['co'] * [-1, 1, 1]; tri = D['tri'][:, ::-1]; mat = D['mat']; part = D['comp']; names = [str(x) for x in D['names']]
keep = ((mat == 0) | (mat == 9)) & (part[tri[:, 0]] != names.index('staff'))
tri = tri[keep]
vs, inv = np.unique(tri, return_inverse=True); T = inv.reshape(-1, 3); P = co[vs]
bpy.ops.wm.read_factory_settings(use_empty=True)
me = bpy.data.meshes.new('b'); me.from_pydata(P.tolist(), [], T.tolist()); me.update()
for p in me.polygons: p.use_smooth = True
o = bpy.data.objects.new('b', me); bpy.context.scene.collection.objects.link(o)
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.single_color = (.78, .76, .72); sh.show_cavity = True
sc.render.resolution_x = 1024; sc.render.resolution_y = 1536; sc.render.film_transparent = True; sc.render.image_settings.color_mode = 'RGBA'
H = P[:, 2].max() - P[:, 2].min(); c = Vector((0.0, 0.0, (P[:, 2].max() + P[:, 2].min()) / 2))
cd = bpy.data.cameras.new('C'); cd.type = 'ORTHO'; cd.ortho_scale = H * 1.08; cd.clip_end = 100; cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
for v, d in {'01_front': (0, -1, 0), '03_left': (1, 0, 0), '02_back': (0, 1, 0), '04_right': (-1, 0, 0)}.items():
    d = Vector(d).normalized(); cam.location = c + d * 10; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{a[1]}/clay_{v}.png'; bpy.ops.render.render(write_still=True)
print('BODYCLAY', H)
