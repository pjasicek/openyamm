"""Deformation check of the fitted body before texturing: clay renders of MM9 clips at given times.
Args: <blend> <mm9 glb> <out prefix> <clip>:<t> [...]  (fit-stage: weights only, MM9 local rotations applied)"""
import bpy, sys
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
rig = bpy.data.objects['MM9_Rig']; body = bpy.data.objects['Body']
ex = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=a[1])
src = next(o for o in bpy.data.objects if o not in ex and o.type == 'ARMATURE')
acts = {x.name.split('|')[-1].lower(): x for x in bpy.data.actions}
print('STRESS actions', list(acts)[:6])
for o in list(bpy.data.objects):
    if o not in ex and o is not src:
        bpy.data.objects.remove(o)
src.hide_render = True
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.single_color = (.75, .75, .75); sh.show_cavity = True
sc.render.resolution_x = sc.render.resolution_y = 500; sc.render.fps = 30
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = 2.4; cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
rig.animation_data_create(); src.animation_data_create()
for spec in a[3:]:
    clip, t = spec.split(':'); t = float(t)
    act = acts[clip.lower()]
    src.animation_data.action = act
    if act.slots: src.animation_data.action_slot = act.slots[0]
    sc.frame_set(int(round(t * 30)))
    bpy.context.view_layer.update()
    for pb in rig.pose.bones:
        s = src.pose.bones.get(pb.name)
        if s is None: continue
        pb.rotation_mode = 'QUATERNION'; s.rotation_mode = 'QUATERNION'
        pb.rotation_quaternion = s.rotation_quaternion
        if pb.name in ('Scene Root', 'Bip01 Spine', 'Bip01 Pelvis'):
            pb.location = s.location
    bpy.context.view_layer.update()
    for n, d in {'front': (0, -1, .1), 'q34': (-1, -1.2, .3), 'side': (1, 0, .1)}.items():
        d = Vector(d).normalized(); cam.location = Vector((0, 0, 0)) + d * 6
        cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = f'{a[2]}_{clip}_{t}_{n}.png'; bpy.ops.render.render(write_still=True)
print('STRESS done')
