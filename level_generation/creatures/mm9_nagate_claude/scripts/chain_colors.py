"""Render the fitted 'Body' coloured by its 'chain' attribute (grey = core, colours = chains) from 6 views.
Args: blend outdir prefix"""
import bpy, sys, os
import numpy as np
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
sc = bpy.context.scene
for o in list(bpy.data.objects):
    if o.type == 'MESH' and o.name != 'Body':
        o.hide_render = True
ob = bpy.data.objects['Body']; me = ob.data
ch = [d.value for d in me.attributes['chain'].data]
pc = [d.value for d in me.attributes['piece'].data]
pal = [(1, .2, .2), (.2, 1, .2), (.2, .4, 1), (1, 1, .2), (1, .2, 1), (.2, 1, 1), (1, .6, .1), (.6, .3, 1)]
col = me.color_attributes.new('dbg', 'FLOAT_COLOR', 'POINT')
for i, c in enumerate(ch):
    col.data[i].color = (*(pal[c % len(pal)] if c >= 0 else ((.9, .9, .9) if pc[i] == 0 else (.3, .3, .3))), 1)
me.color_attributes.active_color = col
P = np.array([tuple(v.co) for v in me.vertices]); lo, hi = P.min(0), P.max(0); c = Vector(((lo + hi) / 2).tolist())
try:
    sc.render.engine = 'BLENDER_WORKBENCH'
except TypeError:
    pass
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'VERTEX'
sc.render.resolution_x = sc.render.resolution_y = 420
cd = bpy.data.cameras.new('cam'); cd.type = 'ORTHO'; cd.ortho_scale = float((hi - lo).max()) * 1.1; cd.clip_end = 100
cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
os.makedirs(argv[1], exist_ok=True)
for v, dv in {'front': (0, -1, 0), 'left': (1, 0, 0), 'back': (0, 1, 0), 'right': (-1, 0, 0), 'top': (0, 0.0001, 1),
              'bottom': (0, 0.0001, -1)}.items():
    dv = Vector(dv).normalized()
    cam.location = c + dv * 10
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(argv[1], f'{argv[2]}_{v}.png')
    bpy.ops.render.render(write_still=True)
