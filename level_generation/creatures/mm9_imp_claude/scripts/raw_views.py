import bpy, sys
from mathutils import Vector
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a[0])
sc = bpy.context.scene
ms = [o for o in sc.objects if o.type == 'MESH']
print('MESHES', [(o.name, len(o.data.vertices)) for o in ms], [(o.name, tuple(round(x,3) for x in o.rotation_quaternion)) for o in sc.objects])
P = np.array([tuple(o.matrix_world @ v.co) for o in ms for v in o.data.vertices])
print('BB', P.min(0), P.max(0))
c = Vector(tuple((P.min(0) + P.max(0)) / 2))
sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.single_color = (0.75, 0.7, 0.55)
sc.render.resolution_x = sc.render.resolution_y = 900
sc.world = bpy.data.worlds.new('W'); sc.world.color = (0.5, 0.55, 0.6)
cd = bpy.data.cameras.new('C'); cd.type = 'ORTHO'; cd.ortho_scale = float(np.ptp(P, 0).max()) * 1.05; cd.clip_end = 100
cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
for n, d in {'y-': (0, -1, 0), 'x+': (1, 0, 0), 'y+': (0, 1, 0), 'x-': (-1, 0, 0)}.items():
    d = Vector(d)
    cam.location = c + d * 5
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{a[1]}_{n}.png'
    bpy.ops.render.render(write_still=True)
