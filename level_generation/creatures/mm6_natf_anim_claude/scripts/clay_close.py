"""Untextured close-up (workbench, random colour per material off; cavity) of the skirt at a clip frame, plus the same
with faces coloured by vertex group dominance hidden. Usage: blender -b -P clay_close.py -- <blend> <out prefix> <Action:frame>"""
import os, sys, bpy
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0])); out = a[1]
sc = bpy.context.scene; rig = bpy.data.objects['Rig']
if a[2] == 'rest':
    rig.animation_data.action = None
    for pb in rig.pose.bones: pb.matrix_basis.identity()
    bpy.context.view_layer.update()
else:
    an, f = a[2].split(':'); act = bpy.data.actions[an]; rig.animation_data.action = act
    if getattr(act, 'slots', None) is not None and len(act.slots): rig.animation_data.action_slot = act.slots[0]
    sc.frame_set(int(f))
sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.color_type = 'SINGLE'; sc.display.shading.show_cavity = True
sc.display.shading.show_backface_culling = True
sc.render.resolution_x = sc.render.resolution_y = 600
for o in bpy.data.objects:
    if o.name in ('ForearmBlade', 'LeafShield'): o.hide_render = True
cam = bpy.data.objects.new('C', bpy.data.cameras.new('C')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = .6
for v, d in (('front', (0, -1, .05)), ('back', (0, 1, .05)), ('fl', (-.6, -1, .05))):
    c = Vector((0, 0, .74)); cam.location = c + Vector(d).normalized() * 5
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{out}_{v}.png'; bpy.ops.render.render(write_still=True)
