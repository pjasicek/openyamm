"""Posed render with faces coloured by rest orientation: green = skirt-zone faces whose rest normal points inward
(toward the pelvis axis), grey = the rest; backface culling on. Shows inner layers pushing through the outer one.
Usage: blender -b -P orient_views.py -- <blend> <out prefix> <Action:frame>"""
import os, sys, bpy
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0])); out = a[1]
sc = bpy.context.scene; rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
ax = rig.data.bones['B_Pelvis'].head_local
mg = bpy.data.materials.new('G'); mg.diffuse_color = (.7, .7, .7, 1)
mi = bpy.data.materials.new('I'); mi.diffuse_color = (.1, .8, .2, 1)
me.materials.clear(); me.materials.append(mg); me.materials.append(mi)
n_in = 0
for p in me.polygons:
    c = p.center; r = Vector((c.x - ax.x, c.y - ax.y, 0))
    inward = 0.5 < c.z < 0.95 and r.length > 0.05 and p.normal.dot(r.normalized()) < -0.3
    p.material_index = 1 if inward else 0; n_in += inward
print('INWARD faces', n_in)
act = bpy.data.actions[a[2].split(':')[0]]; rig.animation_data.action = act
if len(act.slots): rig.animation_data.action_slot = act.slots[0]
sc.frame_set(int(a[2].split(':')[1]))
sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.color_type = 'MATERIAL'; sc.display.shading.show_backface_culling = True
sc.render.resolution_x = sc.render.resolution_y = 500
for o in bpy.data.objects:
    if o.name in ('ForearmBlade', 'LeafShield'): o.hide_render = True
cam = bpy.data.objects.new('C', bpy.data.cameras.new('C')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = .7
for v, d in (('front', (0, -1, .05)), ('back', (0, 1, .05))):
    c = Vector((0, 0, .74)); cam.location = c + Vector(d).normalized() * 5
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{out}_{v}.png'; bpy.ops.render.render(write_still=True)
