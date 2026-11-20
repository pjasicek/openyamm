"""Lineup render (review/lineup.png and review/lineup_air.png): the four finished bush GLBs (work/<id>.glb, re-imported,
LOD0) at game scale beside the installed tree mm7_deco_7tree04 (bound at 1255 units) and the MM7 fern mm7_deco_bush03
(122 units), in the review lighting with the vertex-colour rule, from eye height and from a flying view. 1 m here =
100 game units. Usage: blender --background --python lineup.py"""
import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(HERE, 'scripts'))
from bushes import BUSHES   # noqa: E402
import render_review as rr  # noqa: E402

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = rr.setup_scene()


def place(path, height, location, yaw=0.0):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before and o.type == 'MESH']
    top = max((o.matrix_world @ Vector(c)).z for o in new for c in o.bound_box)
    for o in new:
        o.scale = [s * height / top for s in o.scale]
        o.location = Vector(location)
        o.rotation_euler.z += yaw
    return new


models = os.path.join(REPO, 'assets_source', 'engine', 'models')
place(os.path.join(models, 'mm7_deco_7tree04.glb'), 12.55, (0.0, 4.5, 0.0))
place(os.path.join(models, 'mm7_deco_bush03.glb'), 1.22, (3.6, 0.6, 0.0))
xs = [-3.4, -1.3, 0.9, 2.4]
for x, bid in zip(xs, BUSHES):
    objs = place(os.path.join(HERE, 'work', f'{bid}.glb'), BUSHES[bid]['height'], (x, 0.0, 0.0), 0.4)
    print('IMPORTED', bid, [(o.name, len(o.data.polygons), list(o.data.color_attributes.keys())) for o in objs])
names = {a.name for o in bpy.data.objects if o.type == 'MESH' for a in o.data.color_attributes}
rr.vertex_colour_rule(next(iter(names)) if len(names) == 1 else 'Color')
print('COLOUR ATTRIBUTES', names)
ground = bpy.data.objects.new('Ground', bpy.data.meshes.new('Ground'))
ground.data.from_pydata([(-30, -30, 0), (30, -30, 0), (30, 30, 0), (-30, 30, 0)], [], [(0, 1, 2, 3)])
gm = bpy.data.materials.new('GroundMat'); gm.use_nodes = True
next(n for n in gm.node_tree.nodes if n.type == 'BSDF_PRINCIPLED').inputs['Base Color'].default_value = \
    (0.16, 0.2, 0.1, 1)
ground.data.materials.append(gm); sc.collection.objects.link(ground)
sc.render.film_transparent = False
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.lens = 28
sc.render.resolution_x, sc.render.resolution_y = 1600, 900
for name, location, aim in (('lineup', (0.0, -8.5, 1.75), (0.0, 0.0, 2.6)),
                            ('lineup_air', (0.0, -6.5, 7.5), (0.0, 0.3, 0.3))):
    cam.location = location
    cam.rotation_euler = (Vector(aim) - Vector(location)).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(HERE, 'review', f'{name}.png')
    bpy.ops.render.render(write_still=True)
print('LINEUP done')
