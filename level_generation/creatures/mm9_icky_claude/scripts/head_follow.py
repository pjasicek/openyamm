"""Close renders around a bone at action@frame: head_follow.py blend outdir prefix bone views size action@frame ortho"""
import bpy, sys, os
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
blend, outdir, prefix, bone, views, size, pose, ortho = argv
os.makedirs(outdir, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=blend)
sc = bpy.context.scene
arm = next(o for o in sc.objects if o.type == 'ARMATURE')
name, frame = pose.split('@')
act = bpy.data.actions[name]
arm.animation_data_create(); arm.animation_data.action = act
try:
    arm.animation_data.action_slot = act.slots[0]
except Exception:
    pass
sc.frame_set(int(float(frame)))
bpy.context.view_layer.update()
c = arm.matrix_world @ arm.pose.bones[bone].head
for o in sc.objects:
    if os.environ.get('SHOWALL') != '1' and o.type == 'MESH' and o.name not in ('Body', 'Wings') and not o.name.startswith('Icky'):
        o.hide_render = True
try:
    sc.render.engine = 'BLENDER_WORKBENCH'
except TypeError:
    pass
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'TEXTURE'; sh.show_backface_culling = False
sc.render.resolution_x = sc.render.resolution_y = int(size); sc.render.film_transparent = True
cd = bpy.data.cameras.new('cam'); cd.type = 'ORTHO'; cd.ortho_scale = float(ortho); cd.clip_end = 100
cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
dirs = {'q34': (-1.0, -1.25, 0.55), 'front': (0, -1, 0), 'left': (1, 0, 0), 'below': (0, -0.6, -1),
        'top': (0, 0.0001, 1), 'q34l': (1.0, -1.25, 0.55)}
for v in views.split(','):
    d = Vector(dirs[v]).normalized()
    cam.location = c + d * 10
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(outdir, f'{prefix}_{v}.png')
    bpy.ops.render.render(write_still=True)
