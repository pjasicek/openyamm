"""Clay close-ups of both hands and cuffs. Args: <blend> <out png prefix>"""
import bpy, sys
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
rig = bpy.data.objects['MM9_Rig']
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.single_color = (.75, .75, .75); sh.show_cavity = True; sh.show_backface_culling = True
sc.render.resolution_x = sc.render.resolution_y = 500
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = .55; cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
for s in 'LR':
    c = rig.matrix_world @ rig.data.bones[f'Bip01 {s} Hand'].head_local
    sx = 1 if c.x > 0 else -1
    for n, d in {'top': (0.2 * sx, -.3, 1), 'under': (.2 * sx, -.2, -1), 'end': (1 * sx, -.2, -.5), 'front': (0, -1, 0)}.items():
        D = Vector(d).normalized(); cam.location = c + D * 3; cam.rotation_euler = (-D).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = f'{a[1]}_{s}_{n}.png'; bpy.ops.render.render(write_still=True)
