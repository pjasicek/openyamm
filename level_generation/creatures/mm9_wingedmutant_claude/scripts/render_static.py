"""Textured renders of a static GLB (Meshy return) on grey: views q34, front, left, back. Args: glb outdir prefix size"""
import bpy, sys, os
import numpy as np
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=argv[0])
sc = bpy.context.scene
P = np.array([tuple(o.matrix_world @ v.co) for o in sc.objects if o.type == 'MESH' for v in o.data.vertices])
lo, hi = P.min(0), P.max(0); c = Vector(((lo + hi) / 2).tolist())
try:
    sc.render.engine = 'BLENDER_WORKBENCH'
except TypeError:
    pass
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = os.environ.get('COLOR_TYPE', 'TEXTURE')
size = int(argv[3]); sc.render.resolution_x = sc.render.resolution_y = size
w = bpy.data.worlds.new('w'); sc.world = w; w.color = (0.3, 0.3, 0.33)
cd = bpy.data.cameras.new('cam'); cd.type = 'ORTHO'; cd.ortho_scale = float((hi - lo).max()) * 1.08; cd.clip_end = 100
cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
os.makedirs(argv[1], exist_ok=True)
for v, d in {'q34': (-1, -1.25, 0.55), 'front': (0, -1, 0.05), 'left': (1, 0, 0.05), 'back': (0, 1, 0.1)}.items():
    d = Vector(d).normalized()
    cam.location = c + d * 10
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(argv[1], f'{argv[2]}_{v}.png')
    bpy.ops.render.render(write_still=True)
