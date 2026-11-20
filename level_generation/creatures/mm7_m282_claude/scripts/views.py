"""Workbench renders of the 'Body' mesh in a blend (optionally posed by an action at a frame), loose pieces coloured.
Args: <blend> <out png> [views=front,side,back,tq] [action] [frame] [zoom target x,y,z] [ortho scale]
Views: front (camera at -Y), side (camera at +X: her left side), rside (camera at -X), back (+Y), tq (front-left
three-quarter, above), top. The image tiles are pasted left to right into <out png> (no PIL in Blender: written via
bpy image pixels)."""
import bpy, sys, os, math
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
blend, out = a[0], a[1]
views = (a[2] if len(a) > 2 else 'front,side,back,tq').split(',')
action = a[3] if len(a) > 3 and a[3] != '-' else None
frame = float(a[4]) if len(a) > 4 else 0
zoom = [float(x) for x in a[5].split(',')] if len(a) > 5 and a[5] != '-' else None
oscale = float(a[6]) if len(a) > 6 else (0.6 if zoom else 3.0)
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
sc = bpy.context.scene
body = bpy.data.objects['Body']
rig = next((o for o in bpy.data.objects if o.type == 'ARMATURE'), None)
if rig is not None:
    rig.animation_data_create()
    if action:
        act = bpy.data.actions[action]; rig.animation_data.action = act
        if len(act.slots):
            rig.animation_data.action_slot = act.slots[0]
        sc.frame_set(int(frame), subframe=frame - int(frame))
    else:
        rig.animation_data.action = None
        for pb in rig.pose.bones:
            pb.matrix_basis.identity()
bpy.context.view_layer.update()
me = body.data
if 'piece' in me.attributes and not me.vertex_colors and os.environ.get('PIECES', '1') == '1':
    pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
    rng = np.random.default_rng(3); pal = rng.uniform(0.25, 0.95, (pv.max() + 1, 3)); pal[0] = (0.78, 0.78, 0.76)
    col = me.color_attributes.new('pc', 'FLOAT_COLOR', 'POINT')
    col.data.foreach_set('color', np.c_[pal[pv], np.ones(len(pv))].ravel())
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading
sh.light = 'STUDIO'; sh.color_type = 'VERTEX' if 'pc' in me.color_attributes else os.environ.get('COLOR', 'MATERIAL')
if os.environ.get('COLOR') == 'TEXTURE':
    sh.color_type = 'TEXTURE'
sh.show_cavity = False
sc.render.resolution_x = sc.render.resolution_y = int(os.environ.get('RES', '700'))
sc.render.film_transparent = False
if sc.world is None:
    sc.world = bpy.data.worlds.new('w')
# ground grid line objects are skipped; a plane at z=0 shows floor contact
if os.environ.get('FLOOR', '1') == '1':
    bpy.ops.mesh.primitive_plane_add(size=8, location=(0, 0.5, -0.001))
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = oscale
tgt = Vector(zoom) if zoom else Vector((0, 0.2, 0.95))
D = {'front': (0, -1, 0.05), 'side': (1, 0, 0.05), 'rside': (-1, 0, 0.05), 'back': (0, 1, 0.05),
     'tq': (0.7, -0.7, 0.35), 'tqr': (-0.7, -0.7, 0.35), 'top': (0, -0.01, 1), 'low': (0.3, -1, -0.25)}
tiles = []
for v in views:
    d = Vector(D[v]).normalized()
    cam.location = tgt + d * 6; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    path = out + f'.{v}.png'; sc.render.filepath = path; bpy.ops.render.render(write_still=True); tiles.append(path)
imgs = [bpy.data.images.load(p) for p in tiles]
W = sum(i.size[0] for i in imgs); H = imgs[0].size[1]
big = np.zeros((H, W, 4), np.float32); x = 0
for i in imgs:
    px = np.array(i.pixels[:], np.float32).reshape(i.size[1], i.size[0], 4); big[:, x:x + i.size[0]] = px; x += i.size[0]
o = bpy.data.images.new('o', W, H); o.pixels = big.ravel(); o.filepath_raw = out; o.file_format = 'PNG'; o.save()
for p in tiles:
    os.remove(p)
print('VIEWS', out, views)
