"""Pose sheet: workbench renders of (clip, frame) pairs from one or two views, tiled in a grid (rows = clips).
Args: -- <blend> <out png> <cx> <cy> <cz> <ortho size> <views comma list> <clip:frame,frame,...> [...]
Env SHOT_RES (tile size, default 300), SHOT_COLOR (OBJECT or TEXTURE)."""
import bpy, sys, os, math
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
blend, out = a[0], a[1]; c = Vector(map(float, a[2:5])); size = float(a[5]); views = a[6].split(',')
specs = [(s.split(':')[0], [int(x) for x in s.split(':')[1].split(',')]) for s in a[7:]]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
sc = bpy.context.scene
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
rig.animation_data_create()
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = os.environ.get('SHOT_COLOR', 'OBJECT')
sh.show_cavity = True
R = int(os.environ.get('SHOT_RES', '300'))
sc.render.resolution_x = sc.render.resolution_y = R
cam = bpy.data.objects.new('C', bpy.data.cameras.new('C')); sc.collection.objects.link(cam)
cam.data.type = 'ORTHO'; cam.data.ortho_scale = size; sc.camera = cam
DIRS = {'front': (0, -1, 0.05), 'back': (0, 1, 0.05), 'left': (1, 0, 0.05), 'right': (-1, 0, 0.05),
        'quarter': (-0.7, -0.7, 0.25), 'quarterL': (0.7, -0.7, 0.25), 'top': (0, -0.02, 1)}
# floor plane for reading contacts
bpy.ops.mesh.primitive_plane_add(size=8, location=(0, 0, 0))
rows = []
ncols = max(len(f) for _, f in specs) * len(views)
for act, frames in specs:
    rig.animation_data.action = bpy.data.actions[act]
    if len(bpy.data.actions[act].slots):
        rig.animation_data.action_slot = bpy.data.actions[act].slots[0]
    tiles = []
    for f in frames:
        sc.frame_set(f)
        for v in views:
            d = Vector(DIRS[v]).normalized(); cam.location = c + d * 20
            cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
            p = f'{out}.tmp.png'; sc.render.filepath = p; bpy.ops.render.render(write_still=True)
            im = bpy.data.images.load(p); arr = np.array(im.pixels[:], np.float32).reshape(R, R, 4)
            bpy.data.images.remove(im); os.remove(p); tiles.append(arr)
    while len(tiles) < ncols:
        tiles.append(np.zeros((R, R, 4), np.float32))
    rows.append(np.concatenate(tiles, 1))
full = np.concatenate(rows[::-1], 0)
img = bpy.data.images.new('sheet', full.shape[1], full.shape[0], alpha=True)
img.pixels = full.ravel(); img.filepath_raw = os.path.abspath(out); img.file_format = 'PNG'; img.save()
print('SHEET', out, full.shape)
