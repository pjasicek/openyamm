"""Front and right-side renders of the master at rest (no action) and at given clip frames, lower body framed,
workbench textured. Usage: blender -b -P pose_views.py -- <blend> <out prefix> <rest|Action:frame> [...]"""
import os, sys, bpy
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0])); out = a[1]
sc = bpy.context.scene; rig = bpy.data.objects['Rig']
sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.color_type = 'TEXTURE'; sc.display.shading.light = 'STUDIO'
sc.display.shading.show_backface_culling = True
sc.render.resolution_x = sc.render.resolution_y = 500
for o in bpy.data.objects:
    if o.name in ('ForearmBlade', 'LeafShield'): o.hide_render = True
cam = bpy.data.objects.new('C', bpy.data.cameras.new('C')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = 1.1
for spec in a[2:]:
    if spec == 'rest':
        rig.animation_data.action = None
        for pb in rig.pose.bones: pb.matrix_basis.identity()
        sc.frame_set(0)
    else:
        an, f = spec.split(':'); act = bpy.data.actions[an]; rig.animation_data.action = act
        if getattr(act, 'slots', None) is not None and len(act.slots): rig.animation_data.action_slot = act.slots[0]
        sc.frame_set(int(f))
    for v, d in (('front', (0, -1, .05)), ('side', (-1, 0, .05)), ('back', (0, 1, .05)), ('left', (1, 0, .05))):
        c = Vector((0, 0, .75)); cam.location = c + Vector(d).normalized() * 5
        cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = f'{out}_{spec.replace(":", "")}_{v}.png'; bpy.ops.render.render(write_still=True)
