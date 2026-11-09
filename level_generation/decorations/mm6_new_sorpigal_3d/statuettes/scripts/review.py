"""Review renders of a statuette pedestal: LOD0 front (camera at -y, the sprite's view), three-quarter and side, a close
view of the statuette on its slab, and every LOD. Usage: blender --background --python review.py -- <animal>"""
import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, '..', 'props', 'scripts'))
import props_lib as pl  # noqa: E402

animal = sys.argv[sys.argv.index('--') + 1]
out = os.path.join(HERE, 'review', animal); os.makedirs(out, exist_ok=True)
pl.reset()
bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, 'work', f'{animal}_export.glb'))
objects = sorted([o for o in bpy.data.objects if o.type == 'MESH'], key=lambda o: len(o.name))
scene = pl.setup_render((512, 512))
lod0 = objects[0]
pl.render_views([lod0], out, 'lod0', views=((0, 6), (40, 22), (90, 8)))
for obj in objects:
    level = '0' if obj is lod0 else obj.name.rsplit('LOD', 1)[1]
    pl.render_views([obj], out, f'level{level}', views=((25, 15),))
# Close view of the top: an orthographic camera on the statuette and slab.
cam = scene.camera
cam.data.type = 'ORTHO'
for name, yaw, elevation in (('top_front', 0, 4), ('top_tq', 35, 18)):
    y, e = math.radians(yaw), math.radians(elevation)
    d = Vector((math.sin(y) * math.cos(e), -math.cos(y) * math.cos(e), math.sin(e)))
    top = max((lod0.matrix_world @ Vector(c)).z for c in lod0.bound_box)
    slab = 150 / 81.7
    centre = Vector((0, 0, (slab - 0.12 + top) / 2))
    cam.data.ortho_scale = max(0.95, (top - slab + 0.3) * 1.7)
    cam.location = centre + d * 6
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    for o in bpy.data.objects:
        if o.type == 'MESH':
            o.hide_render = o is not lod0
    scene.render.filepath = os.path.join(out, f'{name}.png')
    bpy.ops.render.render(write_still=True)
print('REVIEW', out)
