"""Review renders (Blender, Cycles) of exported sleeper GLBs from the party's eye height (1.7 model metres = 170
units) in a dim hall light (a soft key, a cool fill and a low sky) so the glow panels read; dark stone ground.
Views: front (the open long side, from -Y), q (three-quarter from the front-right, the foot end), head (from the
head end), back, face (close, above the face) and far. Usage: blender -b --python review_render.py -- <out_dir> <glb>..."""
import json
import math
import os
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:]
out_dir, glbs = argv[0], argv[1:]
os.makedirs(out_dir, exist_ok=True)
EYE = 1.7
HERE = os.path.dirname(os.path.abspath(__file__))
info = json.load(open(os.path.join(HERE, '..', 'work', 'body.json')))


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s = bpy.context.scene
    s.render.engine = 'CYCLES'
    s.cycles.device = 'CPU'
    s.cycles.samples = 40
    s.cycles.use_denoising = True
    s.view_settings.view_transform = 'Standard'
    s.render.resolution_x, s.render.resolution_y = 800, 560
    w = bpy.data.worlds.new('w')
    s.world = w
    w.use_nodes = True
    bg = next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND')
    bg.inputs['Color'].default_value = (0.22, 0.24, 0.27, 1)
    bg.inputs['Strength'].default_value = 0.6
    for nm, energy, rot, col in (('key', 2.6, (48, 0, -40), (1.0, 0.95, 0.88)), ('fill', 0.7, (60, 0, 150), (0.8, 0.88, 1.0))):
        sun = bpy.data.objects.new(nm, bpy.data.lights.new(nm, 'SUN'))
        sun.data.energy = energy
        sun.data.color = col
        sun.data.angle = math.radians(8)
        sun.rotation_euler = [math.radians(a) for a in rot]
        s.collection.objects.link(sun)
    bpy.ops.mesh.primitive_plane_add(size=200)
    g = bpy.context.active_object
    gm = bpy.data.materials.new('ground')
    gm.use_nodes = True
    b = next(n for n in gm.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    b.inputs['Base Color'].default_value = (0.06, 0.055, 0.05, 1)
    b.inputs['Roughness'].default_value = 0.9
    g.data.materials.append(gm)
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
    s.collection.objects.link(cam)
    s.camera = cam
    return s, cam


def load(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    return [o for o in bpy.data.objects if o not in before]


def shoot(s, cam, eye, target, path, lens=30):
    cam.data.lens = lens
    cam.location = eye
    cam.rotation_euler = (Vector(target) - Vector(eye)).to_track_quat('-Z', 'Y').to_euler()
    s.render.filepath = path
    bpy.ops.render.render(write_still=True)


for glb in glbs:
    tag = os.path.basename(glb).replace('xeen_deco_sleeper_', '').replace('.glb', '')
    s, cam = reset()
    load(glb)
    c = (0, 0, 1.1)
    shoot(s, cam, (0, -8.5, EYE), c, os.path.join(out_dir, f'{tag}_front.png'))
    shoot(s, cam, (5.6, -6.6, EYE), c, os.path.join(out_dir, f'{tag}_q.png'))
    shoot(s, cam, (-8.5, -1.2, EYE), c, os.path.join(out_dir, f'{tag}_head.png'))
    shoot(s, cam, (-3.0, 7.5, EYE), c, os.path.join(out_dir, f'{tag}_back.png'))
    e = Vector(info['eye_centre'])
    shoot(s, cam, e + Vector((0.9, -1.6, 0.9)), e, os.path.join(out_dir, f'{tag}_face.png'), lens=45)
    shoot(s, cam, (2.5, -22, EYE), c, os.path.join(out_dir, f'{tag}_far.png'), lens=40)
print('REVIEW_DONE')
