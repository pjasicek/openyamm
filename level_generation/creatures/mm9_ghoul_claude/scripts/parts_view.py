"""Views of all mesh objects in a blend. Args: <blend> <outprefix> [size]. VIEWS env"""
import bpy, sys, colorsys
from mathutils import Vector
import numpy as np
argv = sys.argv[sys.argv.index('--') + 1:]
blend, pre = argv[:2]; size = int(argv[2]) if len(argv) > 2 else 600
bpy.ops.wm.open_mainfile(filepath=blend)
sc = bpy.context.scene
ms = [o for o in bpy.data.objects if o.type == 'MESH']
for i, o in enumerate(ms):
    m = bpy.data.materials.new(o.name); m.diffuse_color = (*colorsys.hsv_to_rgb((i * 0.27 + 0.05) % 1, 0.35, 0.85), 1)
    o.data.materials.clear(); o.data.materials.append(m)
    for p in o.data.polygons: p.use_smooth = True
P = np.array([tuple(o.matrix_world @ v.co) for o in ms for v in o.data.vertices])
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'MATERIAL'; sh.show_cavity = True; sh.show_backface_culling = False
sc.render.resolution_x = sc.render.resolution_y = size
w = bpy.data.worlds.new('w'); sc.world = w; w.color = (0.3, 0.3, 0.32); sh.background_type = 'WORLD'
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.clip_end = 100
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
c = Vector((P.min(0) + P.max(0)) / 2); e = float(np.ptp(P, 0).max()) * 1.1
import os
views = {'front': (c, (0, -1, 0.05), e), 'left': (c, (1, 0, 0.05), e), 'q34': (c, (-1, -1.2, 0.4), e), 'back': (c, (0, 1, 0.05), e)}
if os.environ.get('VIEWS'): views = {}
for s in os.environ.get('VIEWS', '').split(';'):
    if s:
        n, v = s.split('='); f = [float(x) for x in v.split(',')]
        views[n] = (Vector(f[:3]), f[3:6], f[6])
for n, (ce, d, ex) in views.items():
    d = Vector(d).normalized(); cd.ortho_scale = ex; cam.location = ce + d * 10
    cam.rotation_euler = (ce - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{pre}_{n}.png'; bpy.ops.render.render(write_still=True)
