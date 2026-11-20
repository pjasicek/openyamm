"""Clay renders of the head set from work/head_faces.npz (true-handed), 1254 px, transparent; ortho cameras known exactly
(project_head.py uses the same). Args: <out dir> [head faces npz, default work/head_faces.npz; work/head_faces_shp.npz
is the reshaped head of head fixes 3, the clay of the Concubine face repaint (2026-11-01 evening)]"""
import bpy, sys, numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
D = np.load(a[1] if len(a) > 1 else 'work/head_faces.npz'); CO = D['co'].reshape(-1, 3); T = np.arange(len(CO)).reshape(-1, 3)
bpy.ops.wm.read_factory_settings(use_empty=True)
me = bpy.data.meshes.new('h'); me.from_pydata(CO.tolist(), [], T[:, ::-1].tolist()); me.update()
import bmesh
bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
for p in me.polygons: p.use_smooth = True
ob = bpy.data.objects.new('h', me); bpy.context.collection.objects.link(ob)
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading
sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.single_color = (.78, .76, .72); sh.show_cavity = True; sh.show_backface_culling = False
sc.render.resolution_x = sc.render.resolution_y = 1254; sc.render.film_transparent = True; sc.render.image_settings.color_mode = 'RGBA'
cd = bpy.data.cameras.new('C'); cd.type = 'ORTHO'; cd.clip_end = 100; cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
C = Vector((0.0, 0.10, 0.85)); ORTHO = 0.56; FC = Vector((0.0, -0.02, 0.872)); FO = 0.22
V = {'01_front': (0, -1, 0), '03_left': (1, 0, 0), '02_back': (0, 1, 0), '04_right': (-1, 0, 0), '05_top': (0, 0.0001, 1), '06_q34r': (-1, -1.2, 0.15), '07_q34l': (1, -1.2, 0.15), '08_face': (0, -1, 0)}
for n, d in V.items():
    d = Vector(d).normalized(); cc = FC if n == '08_face' else C; cd.ortho_scale = FO if n == '08_face' else ORTHO
    cam.location = cc + d * 10; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{a[0]}/clay_{n}.png'; bpy.ops.render.render(write_still=True)
