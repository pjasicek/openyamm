"""Orthographic side/top/front renders of the rat mesh with a labelled world grid (for placing joints).
Args: glb_or_blend_mesh out_prefix"""
import bpy, sys, json, math
import numpy as np
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view
args = sys.argv[sys.argv.index('--') + 1:]
src, out = args[0], args[1]
if src.endswith('.glb'):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=src)
ms = [o for o in bpy.data.objects if o.type == 'MESH' and not o.hide_render]
co = np.concatenate([np.array([tuple(o.matrix_world @ v.co) for v in o.data.vertices]) for o in ms])
lo, hi = co.min(0), co.max(0); c = (lo + hi) / 2
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'
sc.display.shading.show_cavity = True; sc.display.shading.show_xray = True; sc.display.shading.xray_alpha = 0.6
sc.render.resolution_x = 1600; sc.render.resolution_y = 800
views = {'side': ((-1, 0, 0), (0, 0, 1)), 'top': ((0, 0, 1), (0, -1, 0)), 'front': ((0, -1, 0), (0, 0, 1))}
meta = {}
for name, (d, up) in views.items():
    cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = 1.15
    cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam)
    dv = Vector(d); u = Vector(up)
    z = -dv; x = u.cross(z).normalized(); y = z.cross(x)
    cam.matrix_world = Matrix.Translation(Vector(c) - dv * -3 + dv * 0) @ Matrix((x, y, z)).transposed().to_4x4()
    cam.location = Vector(c) + dv * -1 * -3 if False else Vector(c) - dv * 3
    sc.camera = cam; bpy.context.view_layer.update()
    sc.render.filepath = f'{out}_{name}.png'; bpy.ops.render.render(write_still=True)
    ticks = []
    for gx in np.arange(-0.6, 0.61, 0.05):
        for gy in np.arange(-0.6, 0.61, 0.05):
            p = Vector(c)
            if name == 'side':
                w = Vector((c[0], gx, gy))
            elif name == 'top':
                w = Vector((gx, gy, c[2]))
            else:
                w = Vector((gx, c[1], gy))
            v = world_to_camera_view(sc, cam, w)
            ticks.append((round(gx, 2), round(gy, 2), v.x * 1600, (1 - v.y) * 800))
    meta[name] = ticks
json.dump(meta, open(out + '_grid.json', 'w'))
print('GRID', lo.round(3), hi.round(3))
