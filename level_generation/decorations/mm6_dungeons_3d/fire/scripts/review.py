"""Review renders of a fixture's exported (unlinked) GLB into review/<prop>/: LOD0 from the front (low, sprite-like),
three-quarter and side, and every LOD from the three-quarter view. The glTF importer multiplies base colour by
COLOR_0 as the engine does; flipbook materials show their first frame, emissive (unlit in the engine), and the
billboard cards are turned toward each camera as the engine turns them. Lighting is a neutral white environment at
strength one (a flat light level of one, like a self-lit sprite) plus a weak key light and no specular, so displayed colours can be
compared with the native sprite. Then sheet.py builds the sheets.
Usage: blender --background --python review.py -- <prop> <export.glb>"""
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fire_lib as fl  # noqa: E402

pl = fl.pl
prop, glb = sys.argv[sys.argv.index('--') + 1:][:2]
out = os.path.join(fl.HERE, 'review', prop)
os.makedirs(out, exist_ok=True)
pl.reset()
bpy.ops.import_scene.gltf(filepath=glb)
cards = set()
for m in bpy.data.materials:
    if not m.node_tree:
        continue
    nt = m.node_tree
    bsdf = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    tex = next((n for n in nt.nodes if n.type == 'TEX_IMAGE'), None)
    if bsdf is None or tex is None:
        continue
    # Diffuse only: the white review environment would otherwise lay a grey sheen over the dark native colours
    # (the engine's indoor reflections are scaled by the dim room light).
    bsdf.inputs['Specular IOR Level'].default_value = 0.0
    flip = m.get('openyamm_flipbook')
    if flip is not None:
        coord = nt.nodes.new('ShaderNodeTexCoord')
        mapping = nt.nodes.new('ShaderNodeMapping')
        mapping.inputs['Scale'].default_value = (1 / flip[0], 1 / flip[1], 1)
        mapping.inputs['Location'].default_value = (0, 1 - 1 / flip[1], 0)     # first frame (top left)
        nt.links.new(coord.outputs['UV'], mapping.inputs['Vector'])
        nt.links.new(mapping.outputs['Vector'], tex.inputs['Vector'])
    if flip is not None or m.name.startswith('Embers') or m.get('openyamm_unlit_review'):
        # Unlit in the engine: show texture x COLOR_0 as emission, no shading.
        colour = bsdf.inputs['Base Color'].links[0].from_socket if bsdf.inputs['Base Color'].links else tex.outputs[0]
        nt.links.new(colour, bsdf.inputs['Emission Color'])
        bsdf.inputs['Emission Strength'].default_value = 1.0
        bsdf.inputs['Base Color'].default_value = (0, 0, 0, 1)
        if bsdf.inputs['Base Color'].links:
            nt.links.remove(bsdf.inputs['Base Color'].links[0])
        bsdf.inputs['Specular IOR Level'].default_value = 0.0
    if m.get('openyamm_billboard'):
        cards.add(m.name)

# Split each LOD into its materials so the billboard parts can turn toward the camera.
objects = [o for o in bpy.data.objects if o.type == 'MESH']
for o in objects:
    o.parent = None
lods = {}
for o in objects:
    bpy.ops.object.select_all(action='DESELECT')
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    name = o.name
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.separate(type='MATERIAL')
    bpy.ops.object.mode_set(mode='OBJECT')
    level = 0 if 'LOD' not in name else int(name.rsplit('LOD', 1)[1])
    lods[level] = [p for p in bpy.context.selected_objects]

scene = pl.setup_render((512, 512))
# No screen-space global illumination: the emissive flame card would otherwise light the fixture's outside.
for attribute in ('use_raytracing', 'use_gtao', 'use_shadows'):
    if hasattr(scene.eevee, attribute):
        setattr(scene.eevee, attribute, attribute == 'use_shadows')
world = scene.world
bg = next(n for n in world.node_tree.nodes if n.type == 'BACKGROUND')
bg.inputs['Color'].default_value = (1.0, 1.0, 1.0, 1.0)
bg.inputs['Strength'].default_value = 1.0
sun = bpy.data.objects['Sun']
sun.data.energy = 0.6
cam = bpy.data.objects.new('Camera', bpy.data.cameras.new('Camera'))
scene.collection.objects.link(cam)
scene.camera = cam
cam.data.lens = 50


def render(parts, path, yaw, elevation):
    for o in bpy.data.objects:
        if o.type == 'MESH':
            o.hide_render = o not in parts
    for o in parts:
        if o.active_material and o.active_material.name in cards:
            o.rotation_mode = 'XYZ'
            o.rotation_euler = (0, 0, math.radians(yaw))
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ Vector(c) for o in parts for c in o.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    centre, radius = (lo + hi) / 2, (hi - lo).length / 2
    fov = 2 * math.atan(cam.data.sensor_width / (2 * cam.data.lens))
    y, e = math.radians(yaw), math.radians(elevation)
    d = Vector((math.sin(y) * math.cos(e), -math.cos(y) * math.cos(e), math.sin(e)))
    cam.location = centre + d * radius * 1.05 / math.sin(fov / 2)
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    sun.rotation_euler = (math.radians(50), 0, y - math.radians(35))
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


YAW = float(sys.argv[sys.argv.index('--') + 3]) if len(sys.argv) > sys.argv.index('--') + 3 else 0.0
for label, yaw, elevation in (('a_front', 0, 4), ('b_threequarter', 40, 22), ('c_side', 90, 8)):
    render(lods[0], os.path.join(out, f'lod0_{label}.png'), YAW + yaw, elevation)
for level in sorted(lods):
    render(lods[level], os.path.join(out, f'level{level}.png'), YAW + 40, 20)
print('REVIEW', out, sorted(lods))
