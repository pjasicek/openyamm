"""Part-coloured workbench views of work/<name>_<stage>.blend, at rest and with the pitching part rotated about the
pivot (+max and -min degrees) and the turning parts yawed 40 degrees, to check the split and the clearances.
Args: -- <name> <stage: parts_raw|parts> <out prefix> [max_pitch min_pitch]"""
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
args = sys.argv[sys.argv.index('--') + 1:]
name, stage, prefix = args[:3]
up, down = (float(args[3]), float(args[4])) if len(args) > 4 else (45.0, -20.0)
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', f'{name}_{stage}.blend'))
obj = bpy.data.objects[name]
me = obj.data
part = np.zeros(len(me.polygons), int); me.attributes['part'].data.foreach_get('value', part)
COL = {0: (0.55, 0.6, 0.55, 1), 1: (0.3, 0.3, 0.9, 1), 2: (0.9, 0.7, 0.2, 1), 3: (0.9, 0.9, 0.85, 1),
       4: (0.9, 0.3, 0.3, 1), 5: (0.2, 0.8, 0.3, 1)}
if 'pc' in me.color_attributes:
    me.color_attributes.remove(me.color_attributes['pc'])
layer = me.color_attributes.new('pc', 'BYTE_COLOR', 'CORNER')
for poly in me.polygons:
    for li in poly.loop_indices:
        layer.data[li].color = COL[int(part[poly.index])]
me.color_attributes.active_color_name = 'pc'
base = np.array([v.co[:] for v in me.vertices])
vpart = np.zeros(len(me.vertices), int)
for poly in me.polygons:
    for vi in poly.vertices:
        vpart[vi] = part[poly.index]
pivot = Vector(obj['pivot']); ring = obj['ring_top']
scene = bpy.context.scene
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'VERTEX'
scene.render.resolution_x, scene.render.resolution_y = 700, 700
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam'))
scene.collection.objects.link(cam); scene.camera = cam
cam.data.type = 'ORTHO'
size = float(max(base.max(0) - base.min(0)))
centre = Vector(((base.max(0) + base.min(0)) / 2).tolist())
cam.data.ortho_scale = size * 1.15


def pose(pitch, yaw):
    """+pitch raises the muzzle (-y end): rotation about +x by +pitch? the front is -y, so raising it is about -x."""
    rp = Matrix.Translation(pivot) @ Matrix.Rotation(math.radians(-pitch), 4, 'X') @ Matrix.Translation(-pivot)
    ry = Matrix.Rotation(math.radians(yaw), 4, 'Z')
    for v, p0, vp in zip(me.vertices, base, vpart):
        c = Vector(p0.tolist())
        if vp in (3, 4):
            c = rp @ c
        elif vp == 5:
            t = min(max((c.z - (pivot.z - 0.2)) / 0.3, 0.0), 1.0)
            c = c.lerp(rp @ c, t)
        if vp != 0:
            c = ry @ c
        v.co = c
    me.update()


shots = []
for tag, (pitch, yaw) in {'rest': (0, 0), 'up': (up, 0), 'down': (down, 0), 'yaw': (0, 40)}.items():
    pose(-pitch if False else pitch, yaw)
    for view, (az, el) in {'side': (90, 0), 'q': (-35, 15)}.items():
        a, e = math.radians(az), math.radians(el)
        d = Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))
        cam.location = centre + d * size * 3
        cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
        scene.render.filepath = f'{prefix}_{tag}_{view}.png'
        bpy.ops.render.render(write_still=True)
        shots.append(scene.render.filepath)
print('SHOTS', len(shots))
