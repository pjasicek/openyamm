"""Which candidate face is at an image point: renders a ladder candidate (work/ladder_<label>.blend) with flat colours
encoding the face index from the same camera as glb_close.py's spot, and prints the face (npz order) under pixel
(x, y) of the 420 px close-up. Usage: blender -b -P face_id.py -- <label> <Cand_NN> <spot> <x> <y>"""
import os, sys, bpy, numpy as np
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
label, cand, spot, px, py = sys.argv[sys.argv.index('--') + 1:][:5]
src = open(os.path.join(HERE, 'scripts', 'glb_close.py')).read()
SPOTS = eval(src[src.index('SPOTS = ') + 8:src.index("if os.environ.get('SPOTS')")])
act, frame, b, size, d = SPOTS[spot]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', f'ladder_{label}.blend'))
sc = bpy.context.scene; rig = bpy.data.objects['Rig']; o = bpy.data.objects[cand]
for x in bpy.data.objects:
    if x.type == 'MESH':
        x.hide_render = x is not o
me = o.data; n = len(me.polygons)
col = me.color_attributes.new('fid', 'BYTE_COLOR', 'CORNER')
for p in me.polygons:
    i = p.index + 1; c = ((i & 255) / 255, ((i >> 8) & 255) / 255, ((i >> 16) & 255) / 255, 1)
    for li in p.loop_indices:
        col.data[li].color = c
rig.animation_data.action = bpy.data.actions[act]; sc.frame_set(frame)
pb = rig.pose.bones[b]; c = rig.matrix_world @ ((pb.head + pb.tail) / 2)
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = size
cam.location = c + Vector(d).normalized() * 6; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
sc.render.resolution_x = sc.render.resolution_y = 420; sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.light = 'FLAT'; sc.display.shading.color_type = 'VERTEX'; sc.display_settings.display_device = 'sRGB'
sc.view_settings.view_transform = 'Standard'; sc.render.filter_size = 0; sc.display.render_aa = 'OFF'
sc.render.image_settings.color_management = 'OVERRIDE'; sc.render.image_settings.view_settings.view_transform = 'Raw'
out = os.path.join(HERE, 'work', 'face_id.png'); sc.render.filepath = out; bpy.ops.render.render(write_still=True)
img = bpy.data.images.load(out); W, H = img.size; a = np.array(img.pixels[:]).reshape(H, W, 4)[::-1]
r = np.round(a[..., :3] * 255).astype(int); ids = r[..., 0] + (r[..., 1] << 8) + (r[..., 2] << 16) - 1
x, y = int(px), int(py); win = ids[y - 6:y + 7, x - 6:x + 7]
vals, cnt = np.unique(win[win >= 0], return_counts=True)
print('FACEID at', x, y, 'faces', dict(zip(vals.tolist(), cnt.tolist())))
