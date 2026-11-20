"""Clay close-ups of a GLB at a joint. Args: <glb> <out prefix> <spec> ...  spec = name:clip:seconds:bone:dx,dy,dz:size (camera direction in model space, Blender axes)"""
import bpy, sys, os
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a[0])
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'SINGLE' if not os.environ.get('TEX') else 'TEXTURE'
sh.single_color = (.72, .7, .62); sh.show_cavity = True; sh.show_backface_culling = True
sc.render.resolution_x = sc.render.resolution_y = int(os.environ.get('SIZE', 420))
sc.world = bpy.data.worlds.new('W'); sc.world.color = (0.5, 0.05, 0.4)
sh.background_type = 'WORLD'
cd = bpy.data.cameras.new('C'); cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
cd.type = 'ORTHO'; cd.clip_end = 30
for sp in a[2:]:
    n, clip, t, bone, d, size = sp.split(':')
    act = next(x for x in bpy.data.actions if x.name == clip or x.name.startswith(clip))
    rig.animation_data_create(); rig.animation_data.action = act
    if len(act.slots): rig.animation_data.action_slot = act.slots[0]
    fr = float(t) * 24.0
    sc.frame_set(int(fr), subframe=fr % 1.0); bpy.context.view_layer.update()
    c = rig.matrix_world @ rig.pose.bones[bone].head
    d = Vector([float(x) for x in d.split(',')]).normalized()
    cd.ortho_scale = float(size)
    cam.location = c + d * 6; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{a[1]}_{n}.png'; bpy.ops.render.render(write_still=True)
