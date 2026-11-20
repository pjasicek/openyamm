"""Frames of an original MM9 clip, textured, for comparisons. Args: <glb> <out png> <clip> <t,t,t> <view front|q34|left> [ortho]"""
import bpy, sys
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
glb, out, clip, ts, view = a[0], a[1], a[2], [float(x) for x in a[3].split(',')], a[4]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
sc = bpy.context.scene
for o in sc.objects:
    if o.name.startswith('Icosphere'): o.hide_render = True
rig = next(o for o in sc.objects if o.type == 'ARMATURE')
act = next(x for x in bpy.data.actions if x.name.split('|')[-1].lower() == clip.lower() or x.name.lower().startswith(clip.lower() + '|') or x.name.lower() == clip.lower())
rig.animation_data_create(); rig.animation_data.action = act
if act.slots: rig.animation_data.action_slot = act.slots[0]
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'TEXTURE'; sh.show_backface_culling = False
sc.render.resolution_x = sc.render.resolution_y = 400; sc.render.fps = 24
w = bpy.data.worlds.new('w'); sc.world = w; w.color = (.42, .42, .42); sh.background_type = 'WORLD'
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = float(a[5]) if len(a) > 5 else 2.4
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
D = {'front': (0, -1, .08), 'q34': (-1, -1.2, .4), 'left': (1, 0, .08)}[view]
D = Vector(D).normalized(); cam.location = D * 8; cam.rotation_euler = (-D).to_track_quat('-Z', 'Y').to_euler()
from_ = []
for k, t in enumerate(ts):
    f = t * 24; sc.frame_set(int(f), subframe=f % 1)
    sc.render.filepath = f'{out}_{k}.png'; bpy.ops.render.render(write_still=True)
print('MM9FRAMES', len(ts))
