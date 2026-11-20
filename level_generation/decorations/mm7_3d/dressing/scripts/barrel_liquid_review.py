"""Review renders of the open stat barrel 7dec32 and its liquids: the barrel export (work/7dec32_export.glb,
LOD0) empty and with each liquid disc (work/liquids/mm7_deco_7dec32_liquid_<colour>.glb) at a three-quarter view from
above, plus every LOD empty and red-filled, into review/7dec32_liquids/ (barrel_liquid_sheet.py composes them).
Glossy liquids need reflections, so this uses the props library's sky and sun.
Usage: blender --background --python barrel_liquid_review.py"""
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dlib  # noqa: E402

pl = dlib.pl
OUT = os.path.join(dlib.REVIEW, '7dec32_liquids')
COLOURS = ['red', 'yellow', 'blue', 'orange', 'green', 'purple', 'white']


def import_glb(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    return [o for o in bpy.data.objects if o not in before and o.type == 'MESH']


def render(objects, name, yaw=35, elevation=38, lens=60):
    scene = bpy.context.scene
    for o in bpy.data.objects:
        if o.type == 'MESH':
            o.hide_render = o not in objects
    lo, hi = pl.bounds(objects)
    centre = (lo + hi) / 2; r = (hi - lo).length / 2
    cam = scene.camera
    if cam is None:
        cam = bpy.data.objects.new('Camera', bpy.data.cameras.new('Camera'))
        scene.collection.objects.link(cam); scene.camera = cam
    cam.data.lens = lens
    fov = 2 * math.atan(cam.data.sensor_width / (2 * lens))
    y, e = math.radians(yaw), math.radians(elevation)
    d = Vector((math.sin(y) * math.cos(e), -math.cos(y) * math.cos(e), math.sin(e)))
    cam.location = centre + d * r * 1.08 / math.sin(fov / 2)
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = os.path.join(OUT, name + '.png')
    bpy.ops.render.render(write_still=True)


def main():
    os.makedirs(OUT, exist_ok=True)
    pl.reset()
    pl.setup_render((480, 640))
    barrel = import_glb(os.path.join(dlib.WORK, '7dec32_export.glb'))
    # the unlinked export holds every LOD as its own node (Barrel, Barrel_LOD1, ...)
    barrel.sort(key=lambda o: (len(o.name), o.name))
    for o in barrel:
        o.location = (0, 0, 0)
    liquids = {}
    for colour in COLOURS:
        objs = import_glb(os.path.join(dlib.WORK, 'liquids', f'mm7_deco_7dec32_liquid_{colour}.glb'))
        liquids[colour] = objs
    print('OBJECTS', [o.name for o in barrel])
    lod0 = barrel[0]
    render([lod0], 'empty')
    for colour in COLOURS:
        render([lod0] + liquids[colour], f'liquid_{colour}')
    for k, obj in enumerate(barrel):
        render([obj], f'lod{k}_empty')
        render([obj] + liquids['red'], f'lod{k}_red')


main()
