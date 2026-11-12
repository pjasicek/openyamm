"""Pole in the plane of its blade. Args: <glb> <out prefix>"""
import bpy, sys
import numpy as np
from mathutils import Vector, Matrix
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a[0])
sc = bpy.context.scene
ob = next(o for o in sc.objects if o.name.startswith('pole'))
for o in sc.objects:
    if o.type == 'MESH' and o is not ob: o.hide_render = True
arm = next(o for o in sc.objects if o.type == 'ARMATURE'); arm.animation_data.action = None
for pb in arm.pose.bones: pb.matrix_basis.identity()
P = np.array([ob.matrix_world @ v.co for v in ob.data.vertices])
c = P.mean(0); u, s, vt = np.linalg.svd(P - c)
print('PCA', s, vt.tolist()); L = (P - c) @ vt[0]; print('LEN', L.min(), L.max(), L.max() - L.min())
print('WIDTH', ((P - c) @ vt[1]).min(), ((P - c) @ vt[1]).max(), 'DEPTH', ((P - c) @ vt[2]).min(), ((P - c) @ vt[2]).max())
print(np.round(np.c_[L, (P - c) @ vt[1], (P - c) @ vt[2]][np.argsort(L)], 3).tolist())
sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'FLAT'; sh.color_type = 'TEXTURE'; sh.show_backface_culling = False
sc.render.resolution_x = 1600; sc.render.resolution_y = 400
sc.world = bpy.data.worlds.new('W'); sc.world.color = (0.5, 0.5, 0.5)
cd = bpy.data.cameras.new('C'); cd.type = 'ORTHO'; cd.ortho_scale = (L.max() - L.min()) * 1.05; cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
for name, axis, up in (('plane', vt[2], vt[1]), ('edge', vt[1], vt[2])):
    d = Vector(axis); cen = Vector(c + vt[0] * (L.max() + L.min()) / 2)
    cam.location = cen + d * 10
    x = Vector(vt[0]); y = Vector(up); z = d
    if x.cross(y).dot(z) < 0: y = -y
    cam.matrix_world = Matrix((x, y, z)).transposed().to_4x4(); cam.location = cen + d * 10
    sc.render.filepath = f'{a[1]}_{name}.png'; bpy.ops.render.render(write_still=True)
