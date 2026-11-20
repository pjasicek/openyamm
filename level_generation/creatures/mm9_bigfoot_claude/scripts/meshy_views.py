"""Workbench texture views of a Meshy return. Args: <glb> <prefix>"""
import bpy, sys
from mathutils import Vector
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a[0])
sc = bpy.context.scene
o = next(x for x in sc.objects if x.type == 'MESH')
for p in o.data.polygons: p.use_smooth = True
P = np.array([o.matrix_world @ v.co for v in o.data.vertices])
c = Vector((P.min(0) + P.max(0)) / 2); h = np.ptp(P[:, 2])
sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'FLAT'; sh.color_type = 'TEXTURE'
sc.render.resolution_x = 600; sc.render.resolution_y = 900
sc.world = bpy.data.worlds.new('W'); sc.world.color = (0.42, 0.42, 0.42); sh.background_type = 'WORLD'
cd = bpy.data.cameras.new('C'); cd.type = 'ORTHO'; cd.ortho_scale = h * 1.05; cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
for n, d in {'front': (0, -1, 0.05), 'left': (1, 0, 0.05), 'back': (0, 1, 0.05), 'right': (-1, 0, 0.05)}.items():
    d = Vector(d).normalized(); cam.location = c + d * 10; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{a[1]}_{n}.png'; bpy.ops.render.render(write_still=True)
