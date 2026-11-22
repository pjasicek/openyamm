"""Review renders (Blender, Cycles) of the exported idol GLBs from the party's eye height (1.7 model metres = 170
units) under an afternoon sun and a hazy sky, on a dark ash ground. Views per idol: front, three-quarter, side, back,
a head close-up and the LOD chain; plus both idols together flanking a stand-in cave mouth.
Usage: blender -b --python review_render.py -- <out_dir> <demon.glb> <devil.glb> [lods]"""
import math
import os
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:]
out_dir, glbs = argv[0], argv[1:3]
do_lods = 'lods' in argv[3:]
os.makedirs(out_dir, exist_ok=True)
EYE = 1.7


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s = bpy.context.scene
    s.render.engine = 'CYCLES'
    s.cycles.device = 'CPU'
    s.cycles.samples = 48
    s.cycles.use_denoising = True
    s.view_settings.view_transform = 'Standard'
    s.render.resolution_x, s.render.resolution_y = 640, 800
    w = bpy.data.worlds.new('w')
    s.world = w
    w.use_nodes = True
    bg = next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND')
    bg.inputs['Color'].default_value = (0.42, 0.40, 0.40, 1)
    bg.inputs['Strength'].default_value = 0.9
    sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN'))
    sun.data.energy = 3.2
    sun.data.color = (1.0, 0.93, 0.85)
    sun.data.angle = math.radians(2)
    sun.rotation_euler = (math.radians(42), 0, math.radians(-35))
    s.collection.objects.link(sun)
    bpy.ops.mesh.primitive_plane_add(size=200)
    g = bpy.context.active_object
    gm = bpy.data.materials.new('ground')
    gm.use_nodes = True
    b = next(n for n in gm.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    b.inputs['Base Color'].default_value = (0.05, 0.042, 0.038, 1)
    b.inputs['Roughness'].default_value = 1.0
    g.data.materials.append(gm)
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
    cam.data.lens = 35
    s.collection.objects.link(cam)
    s.camera = cam
    return s, cam


def load(path, offset=(0, 0, 0), lod=0):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == 'MESH']
    for o in new:
        o.location = Vector(o.location) + Vector(offset)
    return meshes


def shoot(s, cam, eye, target, path, lens=35):
    cam.data.lens = lens
    cam.location = eye
    cam.rotation_euler = (Vector(target) - Vector(eye)).to_track_quat('-Z', 'Y').to_euler()
    s.render.filepath = path
    bpy.ops.render.render(write_still=True)


for glb in glbs:
    tag = os.path.basename(glb).replace('xeen_deco_idol_', '').replace('.glb', '')
    s, cam = reset()
    load(glb)
    for view, az, dist in (('front', 0, 12), ('q', 40, 11), ('side', 90, 11), ('back', 180, 11)):
        a = math.radians(az)
        eye = (math.sin(a) * dist, -math.cos(a) * dist, EYE)
        shoot(s, cam, eye, (0, 0, 4.0), os.path.join(out_dir, f'{tag}_{view}.png'))
    shoot(s, cam, (1.2, -4.5, EYE), (0, 0, 6.4), os.path.join(out_dir, f'{tag}_head.png'), lens=50)
print('REVIEW_DONE')

s, cam = reset()
s.render.resolution_x, s.render.resolution_y = 1280, 800
load(glbs[0], (-4.35, 0, 0))
load(glbs[1], (4.35, 0, 0))
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 3.5, 2.5))
rock = bpy.context.active_object
rock.scale = (6, 3, 5)
shoot(s, cam, (0, -20, EYE), (0, 0, 3.4), os.path.join(out_dir, 'pair_front.png'), lens=32)
shoot(s, cam, (-14, -16, EYE), (0, 0, 3.4), os.path.join(out_dir, 'pair_q.png'), lens=32)
shoot(s, cam, (0, -60, EYE + 2), (0, 0, 3.4), os.path.join(out_dir, 'pair_far.png'), lens=32)
print('PAIR_DONE')
