"""MM9's own PeasantF3 mesh posed by the PeasantFemale library clips (the clips the F3 rows play), clay close-ups, to compare the veil and
braid motion. Args: <model glb> <library glb> <out prefix> <clip:seconds,...> [views]"""
import bpy, sys, math, os
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a[0]); objs0 = set(bpy.data.objects)
rig = next(o for o in objs0 if o.type == 'ARMATURE')
acts0 = set(bpy.data.actions)
bpy.ops.import_scene.gltf(filepath=a[1])
for o in set(bpy.data.objects) - objs0:
    bpy.data.objects.remove(o, do_unlink=True)
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'TEXTURE'; sh.show_cavity = True
sc.render.resolution_x = sc.render.resolution_y = int(os.environ.get('SIZE', 300)); sc.world = bpy.data.worlds.new('W'); sc.world.color = (0.2, 0.22, 0.26)
cd = bpy.data.cameras.new('C'); cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
cd.type = 'ORTHO'; cd.ortho_scale = float(os.environ.get('ORTHO', 0.8)); cd.clip_end = 30
views = (a[4] if len(a) > 4 else 'front,side,back').split(',')
rows = []
for k, it in enumerate(a[3].split(',')):
    clip, t = it.split(':')
    act = next(x for x in bpy.data.actions if x not in acts0 and x.name.lower().startswith(clip.lower()))
    rig.animation_data_create(); rig.animation_data.action = act
    if getattr(act, 'slots', None) is not None and len(act.slots): rig.animation_data.action_slot = act.slots[0]
    fr = float(t) * 24.0; sc.frame_set(int(fr), subframe=fr % 1.0); bpy.context.view_layer.update()
    pb = rig.pose.bones['FHP Neck']; c = rig.matrix_world @ pb.head; c = Vector((c.x, c.y, c.z - 0.08))
    for j, v in enumerate(views):
        r = math.radians({'front': 0, 'side': 90, 'back': 180, 'q34b': 145}[v])
        cam.location = c + Vector((math.sin(r) * 6, -math.cos(r) * 6, 0.7)); cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = f'{a[2]}.{k}_{j}.png'; bpy.ops.render.render(write_still=True)
print('MM9POSE done')
