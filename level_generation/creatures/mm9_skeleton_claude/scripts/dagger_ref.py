"""Render the MM9 scimitar flat on its blade plane. Args: <true glb> <out png>"""
import bpy, sys
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a[0])
sc = bpy.context.scene
for o in bpy.data.objects:
    if o.type == 'MESH' and not o.name.startswith('Dagger'): o.hide_render = True
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
if arm.animation_data: arm.animation_data.action = None
for b in arm.pose.bones: b.matrix_basis.identity()
bpy.context.view_layer.update()
o = next(o for o in bpy.data.objects if o.name.startswith('Dagger'))
dg = bpy.context.evaluated_depsgraph_get()
em = o.evaluated_get(dg).to_mesh()
v = np.array([tuple(o.matrix_world @ x.co) for x in em.vertices])
c = v.mean(0); u, s, vt = np.linalg.svd(v - c, full_matrices=False)
print('PLANE axes', vt.tolist(), s.tolist(), 'bounds', v.min(0), v.max(0))
n = Vector(vt[2]); x = Vector(vt[0])
if (v[np.argmax((v - c) @ vt[0])][2] - c[2]) < 0: x = -x
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'FLAT'; sh.color_type = 'TEXTURE'; sh.show_backface_culling = False
sc.render.resolution_x = 1536; sc.render.resolution_y = 640
w = bpy.data.worlds.new('w'); sc.world = w; w.color = (.35, .35, .38); sh.background_type = 'WORLD'
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = 0.46; cd.clip_end = 30
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
cam.location = Vector(c) + n * 4
up = n.cross(x).normalized()
from mathutils import Matrix
cam.matrix_world = Matrix((list(x) + [cam.location.x], list(up) + [cam.location.y], list(n) + [cam.location.z], (0, 0, 0, 1))).transposed().transposed() if False else Matrix(((x.x, up.x, n.x, cam.location.x), (x.y, up.y, n.y, cam.location.y), (x.z, up.z, n.z, cam.location.z), (0, 0, 0, 1)))
sc.render.filepath = a[1]
bpy.ops.render.render(write_still=True)
