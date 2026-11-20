"""Overlay renders of a fit blend: MM9 meshes red (x-ray) and the 'Body' grey, views front/left/top/q34.
Args: blend outdir prefix"""
import bpy, sys, os
import numpy as np
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
sc = bpy.context.scene
red = bpy.data.materials.new('red'); red.diffuse_color = (1, 0.1, 0.1, 1)
grey = bpy.data.materials.new('grey'); grey.diffuse_color = (0.85, 0.85, 0.85, 1)
pts = []
for o in bpy.data.objects:
    if o.type == 'MESH':
        o.data.materials.clear(); o.data.materials.append(grey if o.name == 'Body' else red)
        o.hide_render = o.name not in ('Body',) and os.environ.get('NOMM9') == '1'
        pts += [tuple(o.matrix_world @ v.co) for v in o.data.vertices]
P = np.array(pts); lo, hi = P.min(0), P.max(0); c = Vector(((lo + hi) / 2).tolist())
try:
    sc.render.engine = 'BLENDER_WORKBENCH'
except TypeError:
    pass
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'MATERIAL'; sh.show_xray = True; sh.xray_alpha = 0.6
sc.render.resolution_x = sc.render.resolution_y = 512
cd = bpy.data.cameras.new('cam'); cd.type = 'ORTHO'; cd.ortho_scale = float((hi - lo).max()) * 1.1; cd.clip_end = 100
cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
os.makedirs(argv[1], exist_ok=True)
for v, dv in {'front': (0, -1, 0), 'left': (1, 0, 0), 'top': (0, 0.0001, 1), 'q34': (-1, -1.25, 0.55)}.items():
    dv = Vector(dv).normalized()
    cam.location = c + dv * 10
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(argv[1], f'{argv[2]}_{v}.png')
    bpy.ops.render.render(write_still=True)
