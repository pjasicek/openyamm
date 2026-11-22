"""Render review views of exported models (EEVEE, sky-blue world, a sun): side, three-quarter, front, top, under.
Only the LOD0 node is shown unless --lods (then LOD0..LOD3 side by side, side view).
Usage: blender -b --factory-startup --python review.py -- <out_dir> [--lods] a.glb b.glb ..."""
import math
import os
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:]
out_dir = argv[0]
lods = '--lods' in argv
paths = [a for a in argv[1:] if a.endswith('.glb')]
os.makedirs(out_dir, exist_ok=True)
VIEWS = {'side': (1.0, 0.0, 0.12), 'q': (0.75, -0.6, 0.35), 'front': (0.05, -1.0, 0.15), 'top': (0.25, 0.05, 1.0),
         'under': (0.7, -0.35, -0.5), 'back': (-0.6, 0.75, 0.3)}


def setup():
    sc = bpy.context.scene
    sc.world = bpy.data.worlds.new('w')
    sc.world.use_nodes = True
    sc.world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.45, 0.6, 0.85, 1)
    sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.8
    sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN'))
    sun.data.energy = 3.5
    sun.rotation_euler = (math.radians(40), 0, math.radians(35))
    sc.collection.objects.link(sun)
    sc.render.engine = 'BLENDER_EEVEE'
    sc.render.resolution_x, sc.render.resolution_y = 900, 600
    sc.view_settings.view_transform = 'Standard'
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam.data.lens = 50
    return sc, cam


for p in paths:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=p)
    sc, cam = setup()
    meshes = [o for o in sc.objects if o.type == 'MESH']
    stem = os.path.splitext(os.path.basename(p))[0]
    meshes.sort(key=lambda o: o.name)
    base = [o for o in meshes if '_LOD' not in o.name]
    pts = [o.matrix_world @ Vector(c) for o in base for c in o.bound_box]
    lo = Vector([min(q[k] for q in pts) for k in range(3)])
    hi = Vector([max(q[k] for q in pts) for k in range(3)])
    c = (lo + hi) / 2
    r = (hi - lo).length
    if lods:
        jobs = [(f'lod{i}', VIEWS['q'], [o]) for i, o in enumerate(meshes)]
    else:
        jobs = [(tag, d, base) for tag, d in VIEWS.items()]
    for tag, d, shown in jobs:
        for o in meshes:
            o.hide_render = o not in shown
        d = Vector(d).normalized()
        cam.location = c + d * r * 1.55
        cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = os.path.join(out_dir, f'{stem}_{tag}.png')
        bpy.ops.render.render(write_still=True)
    print('DONE', stem)
