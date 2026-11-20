"""Eevee review renders of one bush blend (work/<id>.blend): sun + sky, alpha-clipped leaves, Standard view, and the
engine's vertex-colour rule (base colour x COLOR_0 'Color'), with shadow maps off as in the engine default.
Views per level: front (eye level, 1.7 m, 3.3 m away), three_quarter (35 degrees above, 45 degrees round), top
(straight down). Every bush uses the same camera distances, so the sheet shows their true relative sizes.
Writes work/review/<id>_<level>_<view>.png (transparent background).
Usage: blender --background --python render_review.py -- <id> [resolution]"""
import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
BID = args[0] if args else None
RES = int(args[1]) if len(args) > 1 else 420
OUT = os.path.join(HERE, 'work', 'review'); os.makedirs(OUT, exist_ok=True)


def setup_scene(blend=None):
    if blend:
        bpy.ops.wm.open_mainfile(filepath=blend)
    sc = bpy.context.scene
    for engine in ('BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT'):
        try:
            sc.render.engine = engine; break
        except TypeError:
            continue
    sc.view_settings.view_transform = 'Standard'
    sc.render.film_transparent = True
    world = sc.world or bpy.data.worlds.new('W'); sc.world = world; world.use_nodes = True
    bg = next(n for n in world.node_tree.nodes if n.type == 'BACKGROUND')
    bg.inputs['Color'].default_value = (0.55, 0.6, 0.68, 1); bg.inputs['Strength'].default_value = 0.5
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sc.collection.objects.link(sun)
    sun.data.energy = 3.6; sun.data.color = (1.0, 0.95, 0.86)
    sun.rotation_euler = (math.radians(40), 0, math.radians(-35))
    sun.data.use_shadow = False
    sc.eevee.use_shadows = False
    for attr in ('use_fast_gi', 'use_raytracing'):
        if hasattr(sc.eevee, attr):
            setattr(sc.eevee, attr, False)
    return sc


def vertex_colour_rule(attribute='Color'):
    for m in bpy.data.materials:
        if not m.use_nodes:
            continue
        nt = m.node_tree; bsdf = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if bsdf is None or not bsdf.inputs['Base Color'].links:
            continue
        src = bsdf.inputs['Base Color'].links[0].from_socket
        if src.node.type != 'TEX_IMAGE':
            src = next((n.outputs['Color'] for n in nt.nodes if n.type == 'TEX_IMAGE'
                        and n.image and 'normal' not in n.image.name.lower()), src)
        bsdf.inputs['Specular IOR Level'].default_value = 0.15
        attr = nt.nodes.new('ShaderNodeAttribute'); attr.attribute_type = 'GEOMETRY'; attr.attribute_name = attribute
        mul = nt.nodes.new('ShaderNodeVectorMath'); mul.operation = 'MULTIPLY'
        nt.links.new(src, mul.inputs[0]); nt.links.new(attr.outputs['Color'], mul.inputs[1])
        nt.links.new(mul.outputs[0], bsdf.inputs['Base Color'])
        if bsdf.inputs['Alpha'].links or m.blend_method in ('CLIP', 'HASHED'):
            m.surface_render_method = 'DITHERED'


VIEWS = {'front': (0.0, 1.7, 3.3), 'three_quarter': (45.0, None, 3.4), 'top': (0.0, None, 3.6)}


def render(sc, cam, view, path, target_z):
    yaw, height, dist = VIEWS[view]
    if view == 'top':
        cam.location = (0, 0, dist)
        cam.rotation_euler = (0, 0, 0)
    else:
        if height is None:
            el = math.radians(35)
            cam.location = (math.sin(math.radians(yaw)) * dist * math.cos(el),
                            -math.cos(math.radians(yaw)) * dist * math.cos(el), target_z + dist * math.sin(el))
        else:
            cam.location = (math.sin(math.radians(yaw)) * dist, -math.cos(math.radians(yaw)) * dist, height)
        aim = Vector((0, 0, target_z))
        cam.rotation_euler = (aim - Vector(cam.location)).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)


if __name__ == '__main__':
    sc = setup_scene(os.path.join(HERE, 'work', f'{BID}.blend'))
    vertex_colour_rule()
    sc.render.resolution_x = sc.render.resolution_y = RES
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.lens = 50
    levels = [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith(BID)]
    for o in levels:
        for x in levels:
            x.hide_render = x is not o
        level = 'LOD0' if o.name == BID else o.name.rsplit('_', 1)[1]
        for view in VIEWS:
            render(sc, cam, view, os.path.join(OUT, f'{BID}_{level}_{view}.png'), 0.9)
    print('REVIEW', BID)
