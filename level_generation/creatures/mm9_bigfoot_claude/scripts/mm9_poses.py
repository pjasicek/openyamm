"""Contact sheet of the raw MM9 clips: one Blender file, each clip N frames, from the quarter. Args: <true glb> <out dir> [clips]"""
import bpy, sys, os
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=a[0])
sc = bpy.context.scene; arm = next(o for o in sc.objects if o.type == 'ARMATURE'); arm.animation_data_create()
sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'FLAT'; sh.color_type = 'TEXTURE'; sh.show_backface_culling = False
sc.render.resolution_x = sc.render.resolution_y = 260
sc.world = bpy.data.worlds.new('w'); sc.world.color = (0.42, 0.42, 0.42); sh.background_type = 'WORLD'
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = 3.6; cd.clip_end = 100; cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
d = Vector((-1, -0.7, 0.2)).normalized(); c = Vector((0, -0.2, -0.1)); cam.location = c + d * 10; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
os.makedirs(a[1], exist_ok=True)
N = 6
for act in bpy.data.actions:
    nm = act.name.split('|')[-1]
    arm.animation_data.action = act
    try: arm.animation_data.action_slot = act.slots[0]
    except Exception: pass
    f0, f1 = act.frame_range
    for k in range(N):
        sc.frame_set(int(round(f0 + (f1 - f0) * k / (N - 1)))); bpy.context.view_layer.update()
        sc.render.filepath = f'{a[1]}/{nm}_{k}.png'; bpy.ops.render.render(write_still=True)
print('DONE', [x.name for x in bpy.data.actions])
