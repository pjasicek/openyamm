"""Clay close-ups of a clip pose, around a named joint. Args: glb out_prefix clip frame(30fps) joint ortho [views a,b]"""
import bpy, sys, os
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
glb, pre, clip, fr, joint, ortho = a[0], a[1], a[2], float(a[3]), a[4], float(a[5])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
sc = bpy.context.scene
arm = next(o for o in sc.objects if o.type == 'ARMATURE')
act = bpy.data.actions[clip]; arm.animation_data.action = act
try: arm.animation_data.action_slot = act.slots[0]
except Exception: pass
sc.render.fps = 30
sc.frame_set(int(fr * bpy.context.scene.render.fps / 30 * (act.frame_range[1] / max(act.frame_range[1], 1))))
bpy.context.view_layer.update()
pb = arm.pose.bones[joint]; c = arm.matrix_world @ pb.head
print('JOINT', c)
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.single_color = (.75, .72, .68); sh.show_cavity = True; sh.show_backface_culling = True
sc.render.resolution_x = sc.render.resolution_y = 500
w = bpy.data.worlds.new('w'); sc.world = w; w.color = (0.35, 0.38, 0.42); sc.display.shading.background_type = 'WORLD'
cd = bpy.data.cameras.new('cam'); cd.type = 'ORTHO'; cd.ortho_scale = ortho; cd.clip_end = 100
cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
for k, d in {'q': (-1, -1.25, .3), 'f': (0, -1, .1), 'l': (1, -.3, .1)}.items():
    d = Vector(d).normalized(); cam.location = c + d * 5
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{pre}_{k}.png'; bpy.ops.render.render(write_still=True)
