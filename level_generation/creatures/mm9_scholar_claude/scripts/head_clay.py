"""Clay renders of the head set (true-handed), the geometry the Codex paints go on; writes work/head_faces.npz for project_head.py. Args: <uv npz> <out dir>"""
import bpy, sys
from mathutils import Vector
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
D = np.load(a[0]); co = D['co'] * [-1, 1, 1]; tri = D['tri'][:, ::-1]; mat = D['mat']; uv = D['uv']; part = D['comp']
tri = tri[mat == 1]
vs, inv = np.unique(tri, return_inverse=True); T = inv.reshape(-1, 3); P = co[vs]
fn = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]]); N = np.zeros_like(P)
key = np.round(P, 5); _, k = np.unique(key, axis=0, return_inverse=True); k = k.ravel(); Ns = np.zeros((k.max() + 1, 3))
for c in range(3): np.add.at(Ns, k[T[:, c]], fn)
N = Ns[k]; N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
np.savez(a[0].replace('uv_v1.npz', 'head_faces.npz'), co=P[T], nor=N[T], uv=uv[vs][T], part=part[vs][T[:, 0]])
bpy.ops.wm.read_factory_settings(use_empty=True)
me = bpy.data.meshes.new('h'); me.from_pydata(P.tolist(), [], T.tolist()); me.update()
for p in me.polygons: p.use_smooth = True
o = bpy.data.objects.new('h', me); bpy.context.scene.collection.objects.link(o)
print('HEADBOX', P.min(0).round(3), P.max(0).round(3))
c = Vector(((P.min(0) + P.max(0)) / 2).tolist())
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.single_color = (.78, .76, .72); sh.show_cavity = True
sc.render.resolution_x = sc.render.resolution_y = 1254; sc.render.film_transparent = True; sc.render.image_settings.color_mode = 'RGBA'
cd = bpy.data.cameras.new('C'); cd.type = 'ORTHO'; cd.ortho_scale = 0.32; cd.clip_end = 100; cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
for v, d in {'01_front': (0, -1, 0), '03_left': (1, 0, 0), '04_right': (-1, 0, 0), '06_q34r': (-1, -1.2, 0.15), '07_q34l': (1, -1.2, 0.15)}.items():
    d = Vector(d).normalized(); cam.location = c + d * 10; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{a[1]}/clay_{v}.png'; bpy.ops.render.render(write_still=True)
print('HEADCLAY', tuple(c))
