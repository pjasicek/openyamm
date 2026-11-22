"""Pose preview (Blender): pose a statue's source from statues.json (or a pose file) and render workbench front,
three-quarter and side views plus bone positions. Usage: blender -b --python pose_preview.py -- <id> <out_prefix> [pose.json]"""
import json
import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
sys.path.insert(0, HERE)
import posing  # noqa: E402

argv = sys.argv[sys.argv.index('--') + 1:]
sid, prefix = argv[0], argv[1]
cfg = json.load(open(os.path.join(HERE, 'statues.json')))[sid]
pose = json.load(open(argv[2])) if len(argv) > 2 else cfg['pose']
arm, bodies = posing.import_creature(os.path.join(REPO, cfg['source']), cfg['mesh'], cfg['materials'])
posing.apply_pose(arm, pose)
for b in cfg.get('report_bones', []):
    pb = arm.pose.bones[b]
    print('BONE', b, tuple(round(x, 3) for x in arm.matrix_world @ pb.head), tuple(round(x, 3) for x in arm.matrix_world @ pb.tail))
fig = posing.bake_static(arm, bodies)
vs = [v.co for v in fig.data.vertices]
lo = Vector([min(p[i] for p in vs) for i in range(3)])
hi = Vector([max(p[i] for p in vs) for i in range(3)])
print('BOUNDS', tuple(round(x, 3) for x in lo), tuple(round(x, 3) for x in hi))
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.light = 'STUDIO'
sc.display.shading.color_type = 'SINGLE'
sc.display.shading.single_color = (0.6, 0.6, 0.62)
sc.display.shading.show_cavity = True
sc.render.resolution_x, sc.render.resolution_y = 360, 440
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
cam.data.type = 'ORTHO'
sc.collection.objects.link(cam)
sc.camera = cam
c = (lo + hi) / 2
size = max(hi - lo) * 1.15
cam.data.ortho_scale = size
for view, az, el in (('front', 0, 0.1), ('q', 40, 0.15), ('side', 90, 0.05), ('top', 0, 2.5)):
    a = math.radians(az)
    d = Vector((math.sin(a), -math.cos(a), el)).normalized()
    cam.location = c + d * size * 3
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{prefix}_{view}.png'
    bpy.ops.render.render(write_still=True)
print('PREVIEW_DONE')
