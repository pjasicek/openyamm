"""Survey (Blender): UV boxes of the titan's face (rest pose) for eyelid painting; face close-up renders.
Usage: blender -b --python face_probe.py -- <out_dir>"""
import os, sys
import bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import posing
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
out = sys.argv[sys.argv.index('--') + 1]; os.makedirs(out, exist_ok=True)
arm, body = posing.import_creature(os.path.join(REPO, 'assets_source/worlds/mm6/models/mm6_ttn.glb'))
me = body.data
uv = me.uv_layers.active.data
sel = []
for p in me.polygons:
    c = body.matrix_world @ p.center
    if abs(c.x - 0.01) < 0.07 and 1.27 < c.z < 1.37 and c.y < -0.09:
        us = [uv[li].uv for li in p.loop_indices]
        sel.append((c, us))
print('FACE polys', len(sel))
import collections
for c, us in sel:
    print('P %.3f %.3f %.3f  uv %.4f %.4f' % (c.x, c.y, c.z, sum(u.x for u in us) / 3, sum(u.y for u in us) / 3))
scene = bpy.context.scene
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'FLAT'
scene.display.shading.color_type = 'TEXTURE'
scene.render.resolution_x, scene.render.resolution_y = 600, 600
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); scene.collection.objects.link(cam); scene.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = 0.22
cam.location = (0.01, -2, 1.31); cam.rotation_euler = (1.5708, 0, 0)
scene.render.filepath = os.path.join(out, 'face_front.png'); bpy.ops.render.render(write_still=True)
