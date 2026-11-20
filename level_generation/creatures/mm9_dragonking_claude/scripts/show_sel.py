"""Highlight a vertex selection on MeshyPosed (red) and render. Args: fit blend outpng 'expr' (numpy on P, wing)"""
import bpy, sys, os
import numpy as np
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
arm = bpy.data.objects['MM9_Rig']; bones = [b.name for b in arm.data.bones]
mp = bpy.data.objects['MeshyPosed']; body = bpy.data.objects['Body']
lm = np.array([d.value for d in body.data.attributes['label_meshy'].data])
P = np.array([tuple(v.co) for v in mp.data.vertices])
wing = np.array([bones[l].startswith('Y') for l in lm])
sel = eval(argv[2])
print('SELECTED', int(sel.sum()))
col = mp.data.color_attributes.new('s', 'FLOAT_COLOR', 'POINT')
for i, d in enumerate(col.data):
    d.color = (1, 0.1, 0.1, 1) if sel[i] else (0.8, 0.8, 0.8, 1)
for o in bpy.data.objects:
    if o.type == 'MESH':
        o.hide_render = o != mp
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'VERTEX'
sc.render.resolution_x = sc.render.resolution_y = 600
cd = bpy.data.cameras.new('cam'); cd.type = 'ORTHO'; cd.ortho_scale = 26; cd.clip_end = 1000
cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
c = Vector((0, 0, 9))
imgs = []
for k, dv in enumerate([(0, -1, 0.15), (-1, -1.25, 0.55), (0, 0.0001, 1)]):
    dv = Vector(dv).normalized(); cam.location = c + dv * 80
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = argv[1].replace('.png', f'_{k}.png'); bpy.ops.render.render(write_still=True)
