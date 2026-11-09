"""Workbench close-up renders of a blend's mesh objects (rest pose or a clip frame) for review.
Args: -- <blend> <out png> <cx> <cy> <cz> <ortho size> <view: front|back|left|right|quarter|top|<yaw deg>> [action frame]
Multiple views: pass a comma list as view; the images are tiled left to right."""
import bpy, sys, os, math
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
blend, out = a[0], a[1]; c = Vector(map(float, a[2:5])); size = float(a[5]); views = a[6].split(',')
act = a[7] if len(a) > 7 else None; frame = int(a[8]) if len(a) > 8 else 0
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
sc = bpy.context.scene
rig = next((o for o in bpy.data.objects if o.type == 'ARMATURE'), None)
if rig is not None:
    rig.animation_data_create()
    rig.animation_data.action = bpy.data.actions[act] if act else None
    if act and getattr(bpy.data.actions[act], 'slots', None) and len(bpy.data.actions[act].slots):
        rig.animation_data.action_slot = bpy.data.actions[act].slots[0]
    if not act:
        for b in rig.pose.bones:
            b.matrix_basis.identity()
sc.frame_set(frame)
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = os.environ.get('SHOT_COLOR', 'OBJECT')
if os.environ.get('SHOT_COLOR') == 'TEXTURE':
    sh.color_type = 'TEXTURE'
sh.show_cavity = True; sh.show_object_outline = False
sc.render.resolution_x = sc.render.resolution_y = int(os.environ.get('SHOT_RES', '800'))
sc.render.film_transparent = False
if sc.world is None:
    sc.world = bpy.data.worlds.new('w')
cam = bpy.data.objects.new('ShotCam', bpy.data.cameras.new('ShotCam')); sc.collection.objects.link(cam)
cam.data.type = 'ORTHO'; cam.data.ortho_scale = size; sc.camera = cam
DIRS = {'front': (0, -1, 0), 'back': (0, 1, 0), 'left': (1, 0, 0), 'right': (-1, 0, 0), 'quarter': (-0.7, -0.7, 0.25),
        'top': (0, -0.02, 1)}
tiles = []
for i, v in enumerate(views):
    if v in DIRS:
        d = Vector(DIRS[v])
    else:
        y = math.radians(float(v)); d = Vector((math.sin(y), -math.cos(y), 0.15))
    d.normalize(); cam.location = c + d * 20
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    path = out + f'.{i}.png'; sc.render.filepath = path
    bpy.ops.render.render(write_still=True); tiles.append(path)
import numpy as np
ims = [bpy.data.images.load(p) for p in tiles]
arr = [np.array(im.pixels[:], np.float32).reshape(im.size[1], im.size[0], 4) for im in ims]
full = np.concatenate(arr, 1)
o = bpy.data.images.new('tiled', full.shape[1], full.shape[0], alpha=True)
o.pixels = full.ravel(); o.filepath_raw = os.path.abspath(out); o.file_format = 'PNG'; o.save()
for p in tiles:
    os.remove(p)
print('SHOT', out)
