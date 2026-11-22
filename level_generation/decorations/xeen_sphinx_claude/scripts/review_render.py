"""Review renders (Blender, Cycles) of an exported sphinx GLB from the party's eye height (1.7 model metres = 170
units) under a high desert sun and a pale sky, on X6-coloured sand. Views per sphinx (model space: front = -Y):
north: head-on from 3,000 and 8,000, three-quarter (4,500), side (5,500), at the door between the paws, back
three-quarter; south: head-on 3,000, three-quarter, side, at the door, and from the D-35 crest (6,150 to its right,
768 higher); plus each LOD at 3,000 (lods sheet). Usage: blender -b --python review_render.py -- <id> <raw.glb> <out_dir>"""
import math
import os
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:]
sid, glb, out_dir = argv[:3]
os.makedirs(out_dir, exist_ok=True)
EYE = 1.7


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s = bpy.context.scene
    s.render.engine = 'CYCLES'
    s.cycles.device = 'CPU'
    s.render.threads_mode = 'FIXED'
    s.render.threads = 12
    s.cycles.samples = 40
    s.cycles.use_denoising = True
    s.view_settings.view_transform = 'Standard'
    s.render.resolution_x, s.render.resolution_y = 1280, 720
    w = bpy.data.worlds.new('w')
    s.world = w
    w.use_nodes = True
    bg = next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND')
    bg.inputs['Color'].default_value = (0.50, 0.58, 0.72, 1)
    bg.inputs['Strength'].default_value = 0.8
    sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN'))
    sun.data.energy = 3.6
    sun.data.color = (1.0, 0.95, 0.86)
    sun.data.angle = math.radians(1.5)
    sun.rotation_euler = (math.radians(38), 0, math.radians(-145))
    s.collection.objects.link(sun)
    bpy.ops.mesh.primitive_plane_add(size=2000)
    g = bpy.context.active_object
    gm = bpy.data.materials.new('ground')
    gm.use_nodes = True
    b = next(n for n in gm.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    b.inputs['Base Color'].default_value = (0.58, 0.40, 0.21, 1)
    b.inputs['Roughness'].default_value = 1.0
    g.data.materials.append(gm)
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
    cam.data.lens = 24          # about the game's 75-degree horizontal field of view at 16:9
    cam.data.clip_end = 2000
    s.collection.objects.link(cam)
    s.camera = cam
    return s, cam


def load(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    return [o for o in bpy.data.objects if o not in before and o.type == 'MESH']


def show_lod(meshes, level):
    for o in meshes:
        lv = int(o.name.rsplit('_LOD', 1)[1]) if '_LOD' in o.name else 0
        o.hide_render = lv != level


def shoot(s, cam, eye, target, path, lens=24):
    cam.data.lens = lens
    cam.location = eye
    cam.rotation_euler = (Vector(target) - Vector(eye)).to_track_quat('-Z', 'Y').to_euler()
    s.render.filepath = path
    bpy.ops.render.render(write_still=True)


def polar(az, dist, z=EYE):
    a = math.radians(az)
    return (math.sin(a) * dist, -math.cos(a) * dist, z)


s, cam = reset()
meshes = load(glb)
show_lod(meshes, 0)
if sid == 'north':
    views = [('front3000', polar(0, 30), (0, 0, 9), 24), ('front8000', polar(0, 80), (0, 0, 9), 24),
             ('q', polar(-40, 45), (0, 25, 7), 24), ('side', polar(-90, 55), (0, 28, 7), 24),
             ('door', (0.0, -7.5, EYE), (0, 0, 3.2), 24), ('back_q', polar(-150, 50), (0, 30, 6), 24),
             ('face', polar(-20, 22), (0, 7, 18), 35)]
else:
    views = [('front3000', polar(0, 30), (0, 0, 5), 24), ('q', polar(-45, 30), (0, 10, 4), 24),
             ('side', polar(-90, 32), (0, 12, 4), 24), ('door', (0.0, -6.5, EYE), (0, 0, 2.8), 24),
             ('crest', (-61.4, 7.7, 7.68 + EYE), (0, 6, 5), 35)]
for name, eye, target, lens in views:
    shoot(s, cam, eye, target, os.path.join(out_dir, f'{sid}_{name}.png'), lens)
for level in range(4):
    show_lod(meshes, level)
    shoot(s, cam, polar(-35, 30 if sid == 'north' else 20), (0, 20 if sid == 'north' else 8, 6),
          os.path.join(out_dir, f'{sid}_lod{level}.png'))
print('REVIEW_DONE')
