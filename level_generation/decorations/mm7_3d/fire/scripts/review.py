"""Review renders of an exported (unlinked) GLB into review/<prop>/: LOD0 from the front (low, sprite-like),
three-quarter and side, and every LOD from the three-quarter view. The glTF importer multiplies base colour by COLOR_0
as the engine does; flipbook cards show their first frame as emission (unlit in the engine) and are turned toward
each camera; constant emission (glows, orbs) shows as imported.
Lighting: `outdoor` (sky 0.9 plus a sun, the outdoor props' review light: models are lit by the sun) or `dungeon`
(white environment at one plus a weak key light, no specular: a flat light level like the sprite's).
Usage: blender --background --python review.py -- <prop> <export.glb> outdoor|dungeon [yaw]"""
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import firelib as fl  # noqa: E402

pl = fl.pl
args = sys.argv[sys.argv.index('--') + 1:]
prop, glb, light = args[:3]
YAW = float(args[3]) if len(args) > 3 else 0.0
out = os.path.join(fl.HERE, 'review', prop)
os.makedirs(out, exist_ok=True)
pl.reset()
bpy.ops.import_scene.gltf(filepath=glb)
cards = set()
own_cards = set()
for m in bpy.data.materials:
    if not m.node_tree:
        continue
    nt = m.node_tree
    bsdf = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    tex = next((n for n in nt.nodes if n.type == 'TEX_IMAGE'), None)
    if bsdf is None or tex is None:
        continue
    if light == 'dungeon':
        bsdf.inputs['Specular IOR Level'].default_value = 0.0
    elif m.get('openyamm_specular') is not None:
        # The engine scales sun and sky specular by openyamm_specular (Blender's default level is 0.5).
        bsdf.inputs['Specular IOR Level'].default_value = 0.5 * float(m['openyamm_specular'])
    flip = m.get('openyamm_flipbook')
    if flip is not None:
        coord = nt.nodes.new('ShaderNodeTexCoord')
        mapping = nt.nodes.new('ShaderNodeMapping')
        mapping.inputs['Scale'].default_value = (1 / flip[0], 1 / flip[1], 1)
        mapping.inputs['Location'].default_value = (0, 1 - 1 / flip[1], 0)     # first frame (top left)
        nt.links.new(coord.outputs['UV'], mapping.inputs['Vector'])
        nt.links.new(mapping.outputs['Vector'], tex.inputs['Vector'])
        colour = bsdf.inputs['Base Color'].links[0].from_socket if bsdf.inputs['Base Color'].links else tex.outputs[0]
        nt.links.new(colour, bsdf.inputs['Emission Color'])
        bsdf.inputs['Emission Strength'].default_value = 1.0
        if bsdf.inputs['Base Color'].links:
            nt.links.remove(bsdf.inputs['Base Color'].links[0])
        bsdf.inputs['Base Color'].default_value = (0, 0, 0, 1)
        bsdf.inputs['Specular IOR Level'].default_value = 0.0
    if m.get('openyamm_additive'):
        # Additive in the engine: texture x COLOR_0 x alpha added to what is behind.
        colour = bsdf.inputs['Base Color'].links[0].from_socket if bsdf.inputs['Base Color'].links else tex.outputs[0]
        output = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
        emit = nt.nodes.new('ShaderNodeEmission')
        scale = nt.nodes.new('ShaderNodeVectorMath')
        scale.operation = 'SCALE'
        nt.links.new(colour, scale.inputs[0])
        nt.links.new(tex.outputs['Alpha'], scale.inputs['Scale'])
        nt.links.new(scale.outputs['Vector'], emit.inputs['Color'])
        add = nt.nodes.new('ShaderNodeAddShader')
        nt.links.new(nt.nodes.new('ShaderNodeBsdfTransparent').outputs[0], add.inputs[0])
        nt.links.new(emit.outputs[0], add.inputs[1])
        nt.links.new(add.outputs[0], output.inputs['Surface'])
        m.surface_render_method = 'BLENDED'
    if m.get('openyamm_billboard') == 'card':
        own_cards.add(m.name)
    elif m.get('openyamm_billboard'):
        cards.add(m.name)

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
    lods[level] = list(bpy.context.selected_objects)
    for part in lods[level]:
        if part.active_material and part.active_material.name in own_cards:
            # "card" billboards turn about their own vertical centre line.
            bpy.ops.object.select_all(action='DESELECT')
            part.select_set(True)
            bpy.context.view_layer.objects.active = part
            bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')

scene = pl.setup_render((512, 512))
for attribute in ('use_raytracing', 'use_gtao'):
    if hasattr(scene.eevee, attribute):
        setattr(scene.eevee, attribute, False)
sun = bpy.data.objects['Sun']
if light == 'dungeon':
    bg = next(n for n in scene.world.node_tree.nodes if n.type == 'BACKGROUND')
    bg.inputs['Color'].default_value = (1.0, 1.0, 1.0, 1.0)
    bg.inputs['Strength'].default_value = 1.0
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
        if o.active_material and o.active_material.name in cards | own_cards:
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
    sun.rotation_euler = (math.radians(45), 0, y - math.radians(35))
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


for label, yaw, elevation in (('a_front', 0, 4), ('b_threequarter', 40, 22), ('c_side', 90, 8)):
    render(lods[0], os.path.join(out, f'lod0_{label}.png'), YAW + yaw, elevation)
for level in sorted(lods):
    render(lods[level], os.path.join(out, f'level{level}.png'), YAW + 40, 20)
# Night view (opaque dark background, dim sky): the additive halos only show over a background, and matter most in
# the dark. sheet.py adds it to the LOD row.
scene.render.film_transparent = False
bg = next(n for n in scene.world.node_tree.nodes if n.type == 'BACKGROUND')
bg.inputs['Color'].default_value = (0.02, 0.025, 0.035, 1.0)
bg.inputs['Strength'].default_value = 1.0
sun.data.energy = 0.25
render(lods[0], os.path.join(out, 'night.png'), YAW + 40, 12)
print('REVIEW', out, sorted(lods))
