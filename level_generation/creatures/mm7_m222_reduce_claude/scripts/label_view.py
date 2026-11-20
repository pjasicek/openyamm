"""Review the face labels of the welded rest mesh (work/source.blend, faces in mesh_in.npz order): each label gets a
flat colour (label -1 = textured grey), rendered front, back, both sides and three-quarter, whole body and head.
Usage: blender -b -P label_view.py -- <labels .npy (int or bool per face)> <out prefix>  -> review/labels/<prefix>_*.png"""
import colorsys, os, sys, bpy, numpy as np
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
args = sys.argv[sys.argv.index('--') + 1:]
lab = np.load(os.path.join(HERE, args[0])).astype(int); prefix = args[1]
out = os.path.join(HERE, 'review', 'labels'); os.makedirs(out, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'source.blend'))
sc = bpy.context.scene; body = bpy.data.objects['Body']; me = body.data
for o in bpy.data.objects:
    o.hide_render = o.type == 'MESH' and o is not body
assert len(me.polygons) == len(lab)
ca = me.color_attributes.new('Lab', 'BYTE_COLOR', 'CORNER')
pal = {k: colorsys.hsv_to_rgb((k * 0.37) % 1, .75, .95) for k in np.unique(lab)}
pal[0] = (.55, .55, .55)
for p in me.polygons:
    r, g, b = pal[int(lab[p.index])]
    for li in p.loop_indices:
        ca.data[li].color = (r, g, b, 1)
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; sc.render.resolution_x = sc.render.resolution_y = 600
sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'VERTEX'
sc.view_settings.view_transform = 'Standard'
for spot, (c, size) in {'body': ((0, 0, .86), 1.85), 'head': ((0, -.02, 1.55), .42), 'hips': ((0, 0, .95), .8)}.items():
    for vn, d in {'front': (0, -1, .05), 'back': (0, 1, .05), 'left': (1, 0, .05), 'right': (-1, 0, .05), 'q34': (.7, -.7, .3)}.items():
        c = Vector(c); cam.location = c + Vector(d).normalized() * 3; cam.data.ortho_scale = size
        cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = os.path.join(out, f'{prefix}_{spot}_{vn}.png'); bpy.ops.render.render(write_still=True)
print('LABELS', {int(k): int((lab == k).sum()) for k in np.unique(lab)})
