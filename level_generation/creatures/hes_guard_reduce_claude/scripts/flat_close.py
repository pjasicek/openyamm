"""Flat textured close-ups (workbench FLAT + TEXTURE: base colour only, no lighting) of the rest-pose source and
ladder candidates. The Eevee close-ups of close_<stem>.py shade the welded source differently (its custom normals are
cleared), which showed fake colour bands on parts kept exactly (guard helmet); flat renders compare the texture alone.
Spots (centre, view direction, ortho size) from FLAT_SPOTS json or the defaults below (humanoid facing -y, 1.70 m).
Usage: blender -b -P flat_close.py -- <blend> <Cand_84,...> [spot,...] -> review/flat/<label>_<spot>_flat.png"""
import bpy, sys, os, json
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', a[0])); sc = bpy.context.scene
objs = {'source': bpy.data.objects['Body'], **{c.replace('Cand_', 'r'): bpy.data.objects[c] for c in a[1].split(',')}}
rig = bpy.data.objects['Rig']; rig.animation_data.action = None
for p in rig.pose.bones:
    p.matrix_basis.identity()
bpy.context.view_layer.update()
SPOTS = {'face': ((0, -.05, 1.55), (0, -1, .1), .32), 'face_q34': ((0, -.05, 1.55), (-.7, -.7, .2), .36),
         'head_back': ((0, .02, 1.55), (.3, 1, .4), .4), 'chest': ((0, -.1, 1.2), (0, -1, .05), .55),
         'back': ((0, .1, 1.2), (0, 1, .1), .6), 'skirt_front': ((0, -.1, .7), (0, -1, .05), .6),
         'skirt_r': ((-.22, 0, .7), (-1, -.2, .05), .6), 'skirt_back': ((0, .1, .7), (0, 1, .05), .7),
         'shoulder_r': ((-.25, 0, 1.33), (-.8, -.4, .3), .4), 'shoulder_l': ((.25, 0, 1.33), (.8, -.4, .3), .4),
         'arm_r': ((-.4, 0, 1.0), (-1, -.3, .1), .6), 'arm_l': ((.4, 0, 1.0), (1, -.3, .1), .6),
         'legs_front': ((0, -.05, .4), (0, -1, .05), .8), 'legs_r': ((-.2, 0, .4), (-1, -.1, .05), .8),
         'legs_back': ((0, .05, .4), (0, 1, .05), .8), 'feet': ((0, -.1, .08), (-.3, -1, .4), .7)}
if os.environ.get('FLAT_SPOTS'):
    SPOTS = {k: tuple(tuple(x) if isinstance(x, list) else x for x in v) for k, v in json.load(open(os.environ['FLAT_SPOTS'])).items()}
if len(a) > 2:
    SPOTS = {k: SPOTS[k] for k in a[2].split(',')}
cam = bpy.data.objects.new('FlatCam', bpy.data.cameras.new('FlatCam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'
sc.render.resolution_x = sc.render.resolution_y = int(os.environ.get('CLOSE_RES', '400')); sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.light = 'FLAT'; sc.display.shading.color_type = 'TEXTURE'
for o in bpy.data.objects:
    if o.type == 'MESH':
        o.hide_render = True
out = os.path.join(HERE, 'review', 'flat'); os.makedirs(out, exist_ok=True)
for spot, (c, d, size) in SPOTS.items():
    c = Vector(c); cam.location = c + Vector(d).normalized() * 6; cam.data.ortho_scale = size
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    for label, o in objs.items():
        for p in objs.values():
            p.hide_render = p is not o
        sc.render.filepath = os.path.join(out, f'{label}_{spot}_flat.png'); bpy.ops.render.render(write_still=True)
print('FLAT', list(objs), list(SPOTS))
