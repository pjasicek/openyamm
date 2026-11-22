"""Render the body GLB at clip time(s) with posed extras (model-space GLBs), four views, workbench textured.
blender -b --python render_pose.py -- <body.glb> <out_prefix> <clip> <t> <extras.glb|-> [view_box cx,cy,cz,size]
View box in glTF coords. Writes <out_prefix>_<view>.png for front, q (three-quarter), side, back."""
import sys, math, bpy
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
body, prefix, clip, t, extra = a[0], a[1], a[2], float(a[3]), a[4]
box = [float(x) for x in a[5].split(',')] if len(a) > 5 else [0, 1.0, 0, 2.3]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=body)
sc = bpy.context.scene
arm = next(o for o in sc.objects if o.type == 'ARMATURE')
for o in list(sc.objects):
    if o.type == 'MESH' and ('LOD' in o.name or 'Shadow' in o.name or o.name.startswith('Icosphere')):
        o.hide_render = True
if extra != '-':
    bpy.ops.import_scene.gltf(filepath=extra)
if arm.animation_data is None:
    arm.animation_data_create()
if clip == '-':
    arm.animation_data.action = None
    for pb in arm.pose.bones: pb.matrix_basis.identity()
else:
    act = bpy.data.actions[clip]
    arm.animation_data.action = act
    if hasattr(arm.animation_data, 'action_slot') and len(act.slots):
        arm.animation_data.action_slot = act.slots[0]
    f = t * sc.render.fps / sc.render.fps_base
    sc.frame_set(int(f), subframe=f - int(f))
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading
sh.light = 'STUDIO'; sh.color_type = 'TEXTURE'; sh.show_cavity = True
sh.background_type = 'VIEWPORT'; sh.background_color = (0.18, 0.19, 0.21)
sc.render.resolution_x = 600; sc.render.resolution_y = 600
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = box[3]
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
c = Vector((box[0], -box[2], box[1]))
for name, az in (('front', 0), ('q', 35), ('side', 90), ('back', 180), ('qleft', -35)):
    r = math.radians(az)
    d = Vector((math.sin(r), -math.cos(r), 0.15)).normalized()
    cam.location = c + d * 6
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{prefix}_{name}.png'
    bpy.ops.render.render(write_still=True)
print('RENDER_DONE')
