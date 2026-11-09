"""Clay renders of the mesh in the HD pose (the geometry Meshy paints), for the second master pass. Args: <blend> <out dir>"""
import bpy, sys
import numpy as np
from mathutils import Vector
BL, OUT = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=BL)
b = bpy.data.objects['Body']; rig = b.parent; me = b.data
fit = np.zeros(len(me.vertices) * 3); me.attributes['fitco'].data.foreach_get('vector', fit)
b.modifiers.clear(); b.parent = None; b.matrix_world = rig.matrix_world
fit = fit.reshape(-1, 3)
me.vertices.foreach_set('co', (np.c_[fit, np.ones(len(fit))] @ np.linalg.inv(np.array(b.matrix_world)).T)[:, :3].ravel()); me.update()
sc = bpy.context.scene
for o in list(bpy.data.objects):
    if o is not b: o.hide_render = True
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.single_color = (.62, .6, .57); sh.show_backface_culling = False; sh.show_cavity = True; sh.cavity_type = 'BOTH'
sc.render.film_transparent = True; sc.render.image_settings.color_mode = 'RGBA'
sc.render.resolution_x, sc.render.resolution_y = 1024, 1536
lo, hi = fit.min(0), fit.max(0); c = Vector(((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, (lo[2] + hi[2]) / 2))
print('BOUNDS', lo, hi)
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.clip_end = 100; cd.ortho_scale = max((hi[2] - lo[2]) * 1.06, (hi[0] - lo[0]) * 1.06 * 1.5); cd.sensor_fit = 'VERTICAL'
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
for n, d in {'clay_01_front': (0, -1, 0), 'clay_02_back': (0, 1, 0), 'clay_03_left': (1, 0, 0), 'clay_04_right': (-1, 0, 0)}.items():
    cam.location = c + Vector(d) * 6
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{OUT}/{n}.png'; bpy.ops.render.render(write_still=True)
