"""Clay filmstrip of clips in a gaits blend (review only): orthographic side (or front) views at evenly spaced phases,
pasted into one PNG.  blender -b <blend> -P clay_strip.py -- <out.png> <rig> <view: left|front|quarter> <clip>:<count> [...]"""
import bpy, sys, math, os
from mathutils import Vector
args = sys.argv[sys.argv.index('--') + 1:]
out, rig_name, view = args[:3]
rig = bpy.data.objects[rig_name]; sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'SINGLE'
sc.display.shading.show_cavity = True
W, H = int(os.environ.get('STRIP_W', 360)), int(os.environ.get('STRIP_H', 300))
sc.render.resolution_x, sc.render.resolution_y = W, H
sc.world = sc.world or bpy.data.worlds.new('W')
meshes = [o for o in bpy.data.objects if o.type == 'MESH' and o.visible_get()]
lo = Vector((min(min((o.matrix_world @ Vector(c))[i] for c in o.bound_box) for o in meshes) for i in range(3)))
hi = Vector((max(max((o.matrix_world @ Vector(c))[i] for c in o.bound_box) for o in meshes) for i in range(3)))
size = max(hi - lo) * float(os.environ.get('STRIP_PAD', 1.25)); mid = (lo + hi) / 2
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = size
a = {'left': 90.0, 'front': 0.0, 'quarter': 35.0}[view]
cam.location = (mid.x + math.sin(math.radians(a)) * 10, mid.y - math.cos(math.radians(a)) * 10, mid.z)
cam.rotation_euler = (math.radians(90), 0, math.radians(a))
paths = []
for item in args[3:]:
    clip, count = item.split(':'); count = int(count)
    act = bpy.data.actions[clip]; rig.animation_data_create(); rig.animation_data.action = act
    if len(getattr(act, 'slots', [])):
        rig.animation_data.action_slot = act.slots[0]
    end = act.frame_range[1]
    for k in range(count):
        f = k * end / count
        sc.frame_set(int(f), subframe=f - int(f))
        sc.render.filepath = f'{out}_{clip}_{k:02d}.png'; bpy.ops.render.render(write_still=True); paths.append(sc.render.filepath)
import numpy as np
ims = [np.array(bpy.data.images.load(p).pixels[:]).reshape(H, W, 4)[::-1] for p in paths]
cols = max(int(i.split(':')[1]) for i in args[3:]); rows = (len(ims) + cols - 1) // cols
sheet = np.ones((rows * H, cols * W, 4))
for i, im in enumerate(ims):
    r, c = divmod(i, cols); sheet[r * H:(r + 1) * H, c * W:(c + 1) * W] = im
img = bpy.data.images.new('sheet', cols * W, rows * H); img.pixels = sheet[::-1].ravel().tolist()
img.filepath_raw = out; img.file_format = 'PNG'; img.save()
for p in paths:
    os.remove(p)
print('SHEET', out)
