"""Workbench contact sheet of an action: rows = views, columns = frames (all meshes, pieces coloured on the body).
Args: <blend> <action> <frames comma list> <views comma list> <out png> [ortho scale] [target x,y,z]
Env RES (tile px, default 360)."""
import bpy, sys, os, math
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
blend, action, frames, views, out = a[0], a[1], [float(x) for x in a[2].split(',')], a[3].split(','), a[4]
oscale = float(a[5]) if len(a) > 5 else 2.6
tgt = Vector([float(x) for x in a[6].split(',')]) if len(a) > 6 else Vector((0, 0.1, 0.9))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
sc = bpy.context.scene
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
rig.animation_data_create(); act = bpy.data.actions[action]; rig.animation_data.action = act
if len(act.slots):
    rig.animation_data.action_slot = act.slots[0]
if 'piece' in me.attributes and os.environ.get('PIECES', '1') == '1':
    pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
    rng = np.random.default_rng(3); pal = rng.uniform(0.25, 0.95, (pv.max() + 1, 3)); pal[0] = (0.78, 0.78, 0.76)
    col = me.color_attributes.new('pc', 'FLOAT_COLOR', 'POINT')
    col.data.foreach_set('color', np.c_[pal[pv], np.ones(len(pv))].ravel())
for o in bpy.data.objects:
    if o.type == 'MESH' and o is not body and 'pc' not in o.data.color_attributes:
        c = o.data.color_attributes.new('pc', 'FLOAT_COLOR', 'POINT')
        tint = (0.15, 0.12, 0.1) if 'Bow' in o.name else (0.9, 0.85, 0.3) if 'String' in o.name else (0.85, 0.2, 0.2)
        c.data.foreach_set('color', np.tile([*tint, 1.0], len(o.data.vertices)))
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'VERTEX'
R = int(os.environ.get('RES', '360'))
sc.render.resolution_x = sc.render.resolution_y = R
bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0.5, -0.001))
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = oscale
DIRS = {'front': (0, -1, 0.08), 'side': (1, 0, 0.08), 'rside': (-1, 0, 0.08), 'back': (0, 1, 0.08), 'tq': (0.7, -0.7, 0.3),
        'tqr': (-0.7, -0.7, 0.3), 'top': (0, -0.01, 1), 'low': (0.3, -1, -0.2)}
rows = []
for v in views:
    d = Vector(DIRS[v]).normalized(); cam.location = tgt + d * 6; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    row = []
    for f in frames:
        sc.frame_set(int(f), subframe=f - int(f))
        p = out + f'.{v}.{f}.png'; sc.render.filepath = p; bpy.ops.render.render(write_still=True); row.append(p)
    rows.append(row)
big = np.zeros((R * len(rows), R * len(frames), 4), np.float32)
for i, row in enumerate(rows):
    for j, p in enumerate(row):
        im = bpy.data.images.load(p); px = np.array(im.pixels[:], np.float32).reshape(R, R, 4)
        big[(len(rows) - 1 - i) * R:(len(rows) - i) * R, j * R:(j + 1) * R] = px; os.remove(p)
o = bpy.data.images.new('o', R * len(frames), R * len(rows)); o.pixels = big.ravel(); o.filepath_raw = out
o.file_format = 'PNG'; o.save()
print('SHEET', out, len(frames), 'x', len(rows))
