"""Renders of work/head_parts.blend or any Face object. Args: <blend> <prefix>"""
import bpy, sys
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.single_color = (.72, .72, .72); sh.show_cavity = True; sh.show_backface_culling = False
sc.render.resolution_x = 700; sc.render.resolution_y = 700
sc.world = bpy.data.worlds.new('W'); sc.world.color = (0.25, 0.25, 0.28)
cd = bpy.data.cameras.new('C'); cd.type = 'ORTHO'; cd.ortho_scale = 0.36; cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
for n, d in (('f', (0, -1, 0)), ('q', (-1, -1.2, 0.1)), ('s', (-1, 0, 0)), ('b', (0.5, 1, 0.1)), ('u', (-.3, -.5, -1))):
    d = Vector(d).normalized(); cam.location = d * 5; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{a[1]}_{n}.png'; bpy.ops.render.render(write_still=True)
