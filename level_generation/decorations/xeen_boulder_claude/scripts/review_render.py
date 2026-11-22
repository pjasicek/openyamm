"""Review renders (Blender Cycles): the exported GLB on a sand-coloured ground under a desert sun and sky, eye height
170 units: head-on from 300, 1,000 and 3,000 units (perspective, 60 degree lens like the game's), three-quarter, side,
back, and LOD0-3 side by side. Usage: blender -b --python review_render.py -- <glb> <out_dir>"""
import math
import os
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:]
glb, out = argv[0], argv[1]
os.makedirs(out, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
s = bpy.context.scene
objs = {o.name: o for o in s.objects if o.type == 'MESH'}
lod0 = next(o for n, o in objs.items() if not n.endswith(('_LOD1', '_LOD2', '_LOD3')))
s.render.engine = 'CYCLES'
s.cycles.device = 'CPU'
s.cycles.samples = 48
s.render.threads_mode = 'FIXED'
s.render.threads = 12
s.render.resolution_x, s.render.resolution_y = 1280, 720
s.view_settings.view_transform = 'Standard'
world = bpy.data.worlds.new('sky')
s.world = world
world.use_nodes = True
bg = world.node_tree.nodes['Background']
bg.inputs['Color'].default_value = (0.55, 0.68, 0.9, 1)
bg.inputs['Strength'].default_value = 0.9
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN'))
sun.data.energy = 4.0
sun.data.angle = math.radians(1.5)
sun.rotation_euler = (math.radians(50), 0, math.radians(-35))   # from front-left, mid-afternoon
s.collection.objects.link(sun)
bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, 0))
ground = bpy.context.active_object
gm = bpy.data.materials.new('sand')
gm.use_nodes = True
gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.62, 0.46, 0.25, 1)
gm.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.95
ground.data.materials.append(gm)
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
s.collection.objects.link(cam)
s.camera = cam
cam.data.lens_unit = 'FOV'
cam.data.angle = math.radians(60)
cam.data.clip_end = 200


def show(only):
    for o in objs.values():
        o.hide_render = o is not only


def shoot(name, dist, az, eye=1.7, target_z=1.2, fov=60, x_shift=0.0):
    a = math.radians(az)
    cam.data.angle = math.radians(fov)
    cam.location = Vector((math.sin(a) * dist + x_shift, -math.cos(a) * dist, eye))
    tgt = Vector((x_shift, 0, target_z))
    cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
    s.render.filepath = os.path.join(out, name + '.png')
    bpy.ops.render.render(write_still=True)


show(lod0)
shoot('front_300', 3.0, 0)
shoot('front_1000', 10.0, 0)
shoot('front_3000', 30.0, 0, eye=1.7, target_z=1.2)
shoot('face_close', 3.6, 0, eye=1.7, target_z=1.3, fov=40)
shoot('three_quarter', 5.0, 40)
shoot('side', 5.0, 90)
shoot('back', 5.0, 180)
for n, o in objs.items():
    lv = n[-1] if n.endswith(('_LOD1', '_LOD2', '_LOD3')) else '0'
    show(o)
    shoot('lod%s' % lv, 5.0, 25)
print('REVIEW_DONE')
