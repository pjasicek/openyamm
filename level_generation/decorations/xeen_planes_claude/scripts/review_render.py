"""Review renders (Blender, Cycles) of exported GLBs from the party's eye height (170 units = 1.7 model metres
over the floor) under a sun and a hazy sky: front, three-quarter, side and back, plus a close view. A stand-in for
the map's plinth (grey box) is drawn under statues that stand on A6's plinth.
Usage: blender -b --python review_render.py -- <out_dir> <glb>[:plinth_w:plinth_h] ... [far]"""
import math
import os
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:]
out_dir = argv[0]
items = [a for a in argv[1:] if a != 'far']
os.makedirs(out_dir, exist_ok=True)
EYE = 1.7


def reset(ground=(0.10, 0.095, 0.09)):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s = bpy.context.scene
    s.render.engine = 'CYCLES'
    s.cycles.device = 'CPU'
    s.cycles.samples = 40
    s.cycles.use_denoising = True
    s.view_settings.view_transform = 'Standard'
    s.render.resolution_x, s.render.resolution_y = 560, 720
    w = bpy.data.worlds.new('w')
    s.world = w
    w.use_nodes = True
    bg = next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND')
    bg.inputs['Color'].default_value = (0.45, 0.45, 0.47, 1)
    bg.inputs['Strength'].default_value = 0.9
    sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN'))
    sun.data.energy = 3.0
    sun.data.color = (1.0, 0.95, 0.88)
    sun.data.angle = math.radians(2)
    sun.rotation_euler = (math.radians(42), 0, math.radians(-35))
    s.collection.objects.link(sun)
    bpy.ops.mesh.primitive_plane_add(size=200)
    g = bpy.context.active_object
    gm = bpy.data.materials.new('ground')
    gm.use_nodes = True
    b = next(n for n in gm.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    b.inputs['Base Color'].default_value = (*ground, 1)
    b.inputs['Roughness'].default_value = 1.0
    g.data.materials.append(gm)
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
    s.collection.objects.link(cam)
    s.camera = cam
    return s, cam


def load(path, offset=(0, 0, 0)):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    for o in new:
        o.location = Vector(o.location) + Vector(offset)
    # show LOD0 only
    for o in new:
        if '_LOD' in o.name:
            o.hide_render = True
    meshes = [o for o in new if o.type == 'MESH' and not o.hide_render]
    pts = [o.matrix_world @ v.co for o in meshes for v in o.data.vertices]
    lo = Vector([min(p[i] for p in pts) for i in range(3)])
    hi = Vector([max(p[i] for p in pts) for i in range(3)])
    return lo, hi


def shoot(s, cam, eye, target, path, lens=35):
    cam.data.lens = lens
    cam.location = eye
    cam.rotation_euler = (Vector(target) - Vector(eye)).to_track_quat('-Z', 'Y').to_euler()
    s.render.filepath = path
    bpy.ops.render.render(write_still=True)


for item in items:
    parts = item.split(':')
    glb = parts[0]
    pw, ph = (float(parts[1]), float(parts[2])) if len(parts) > 2 else (0.0, 0.0)
    tag = os.path.basename(glb).replace('xeen_deco_', '').replace('.glb', '')
    s, cam = reset()
    if pw:
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, ph / 2))
        pl = bpy.context.active_object
        pl.scale = (pw, pw, ph)
        pm = bpy.data.materials.new('pl')
        pm.use_nodes = True
        next(n for n in pm.node_tree.nodes if n.type == 'BSDF_PRINCIPLED').inputs['Base Color'].default_value = (0.25, 0.25, 0.25, 1)
        pl.data.materials.append(pm)
    lo, hi = load(glb, (0, 0, ph))
    h = hi.z
    mid = (0, 0, h * 0.5)
    dist = max(3.0, h * 2.2, (hi - lo).length * 1.4)
    for view, az in (('front', 0), ('q', 40), ('side', 90), ('back', 180)):
        a = math.radians(az)
        eye = (math.sin(a) * dist, -math.cos(a) * dist, EYE)
        shoot(s, cam, eye, mid, os.path.join(out_dir, f'{tag}_{view}.png'))
    shoot(s, cam, (dist * 0.25, -dist * 0.42, EYE), (0, 0, h * 0.62), os.path.join(out_dir, f'{tag}_close.png'), lens=35)
    if 'far' in argv:
        shoot(s, cam, (0, -20, EYE), mid, os.path.join(out_dir, f'{tag}_far.png'), lens=35)
print('REVIEW_DONE')
