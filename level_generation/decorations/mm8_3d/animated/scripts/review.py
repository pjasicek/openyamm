"""Review renders of a model's exported (unlinked) GLB into review/<prop>/: LOD0 from the front (low, sprite-like),
three-quarter and side, every LOD from the three-quarter view, and, for animated surfaces, a motion strip: the
engine's static-model vertex animation (game/shaders/model_static.sh: wind sway growing with height squared, cloth
flutter along the normal weighted by COLOR_0 alpha) evaluated on the CPU at a few times, or the swing about the
bounds top. The glTF importer multiplies base colour by COLOR_0 as the engine does; flipbook, halo and unlit
materials show texture x COLOR_0 (+ emission) unshaded, and billboard cards are turned toward each camera as the
engine turns them. Light: `indoor` = white environment at strength one plus a weak key (a self-lit sprite's flat
light), `outdoor` = the props' sky and sun.
Usage: blender --background --python review.py -- <prop> <export.glb> <indoor|outdoor> [swing degrees]"""
import math
import os
import re
import sys

import bpy
import numpy as np
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as al  # noqa: E402
from finish_table import FINISH  # noqa: E402

pl = al.pl
args = sys.argv[sys.argv.index('--') + 1:]
prop, glb, light = args[:3]
swing = float(args[3]) if len(args) > 3 else 0.0
out = os.path.join(al.HERE, 'review', prop)
os.makedirs(out, exist_ok=True)
pl.reset()
bpy.ops.import_scene.gltf(filepath=glb)
cards, card_mats, unlit, wind, flutter = set(), set(), set(), {}, {}
for m in bpy.data.materials:
    if not m.node_tree:
        continue
    nt = m.node_tree
    bsdf = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    tex = next((n for n in nt.nodes if n.type == 'TEX_IMAGE' and n.image and 'basecolor' in n.image.name.lower()
                or n.type == 'TEX_IMAGE' and n.image and 'flame' in n.image.name.lower()), None)
    if tex is None:
        tex = next((n for n in nt.nodes if n.type == 'TEX_IMAGE'), None)
    if bsdf is None or tex is None:
        continue
    bsdf.inputs['Specular IOR Level'].default_value = 0.1 if light == 'outdoor' else 0.0
    if m.get('openyamm_wind'):
        wind[m.name] = float(m['openyamm_wind'])
    if m.get('openyamm_flutter'):
        flutter[m.name] = float(m['openyamm_flutter'])
    flip = m.get('openyamm_flipbook')
    if flip is not None:
        coord = nt.nodes.new('ShaderNodeTexCoord')
        mapping = nt.nodes.new('ShaderNodeMapping')
        mapping.inputs['Scale'].default_value = (1 / flip[0], 1 / flip[1], 1)
        mapping.inputs['Location'].default_value = (0, 1 - 1 / flip[1], 0)     # first frame (top left)
        nt.links.new(coord.outputs['UV'], mapping.inputs['Vector'])
        nt.links.new(mapping.outputs['Vector'], tex.inputs['Vector'])
    if flip is not None or m.get('openyamm_unlit_review') or m.name.startswith(('Embers', 'Unlit')):
        unlit.add(m.name)
        emission = tuple(bsdf.inputs['Emission Color'].default_value)[:3]
        strength = bsdf.inputs['Emission Strength'].default_value
        colour = bsdf.inputs['Base Color'].links[0].from_socket if bsdf.inputs['Base Color'].links else tex.outputs[0]
        if strength > 0 and max(emission) > 0:
            add = nt.nodes.new('ShaderNodeMix')
            add.data_type = 'RGBA'
            add.blend_type = 'ADD'
            add.inputs[0].default_value = 1.0
            nt.links.new(colour, add.inputs[6])
            add.inputs[7].default_value = tuple(c * strength for c in emission) + (1,)
            colour = add.outputs[2]
        nt.links.new(colour, bsdf.inputs['Emission Color'])
        bsdf.inputs['Emission Strength'].default_value = 1.0
        bsdf.inputs['Base Color'].default_value = (0, 0, 0, 1)
        if bsdf.inputs['Base Color'].links:
            nt.links.remove(bsdf.inputs['Base Color'].links[0])
        bsdf.inputs['Specular IOR Level'].default_value = 0.0
        if m.get('openyamm_additive'):
            # Additive glow (the engine's SRC_ALPHA, ONE): emission of colour x alpha over a transparent surface.
            output = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
            # The engine adds display (sRGB) colour x alpha; over a dark background that equals adding
            # linear((display colour) x alpha), so encode, scale by alpha and decode again.
            encode = nt.nodes.new('ShaderNodeGamma')
            encode.inputs['Gamma'].default_value = 1 / 2.2
            nt.links.new(colour, encode.inputs['Color'])
            scaled = nt.nodes.new('ShaderNodeMix')
            scaled.data_type = 'RGBA'
            scaled.blend_type = 'MULTIPLY'
            scaled.inputs[0].default_value = 1.0
            nt.links.new(encode.outputs[0], scaled.inputs[6])
            nt.links.new(tex.outputs['Alpha'], scaled.inputs[7])
            decode = nt.nodes.new('ShaderNodeGamma')
            decode.inputs['Gamma'].default_value = 2.2
            nt.links.new(scaled.outputs[2], decode.inputs['Color'])
            glow = nt.nodes.new('ShaderNodeEmission')
            nt.links.new(decode.outputs[0], glow.inputs['Color'])
            clear = nt.nodes.new('ShaderNodeBsdfTransparent')
            both = nt.nodes.new('ShaderNodeAddShader')
            nt.links.new(glow.outputs[0], both.inputs[0])
            nt.links.new(clear.outputs[0], both.inputs[1])
            nt.links.new(both.outputs[0], output.inputs['Surface'])
            m.surface_render_method = 'BLENDED'
    if m.get('openyamm_billboard') == 'card':
        card_mats.add(m.name)
    if m.get('openyamm_billboard'):
        cards.add(m.name)
    # The engine culls back faces unless finish.py makes the material double-sided; so does the review.
    family = FINISH[prop]['materials'].get(m.name.split('.')[0],
                                           FINISH[prop]['materials'].get(re.sub(r'[0-9.]+$', '', m.name), {}))
    m.use_backface_culling = not family.get('double', False)
    if bsdf.inputs['Alpha'].links:
        # The importer multiplies COLOR_0 alpha (the flutter weight) into the surface alpha; the engine does not.
        nt.links.remove(bsdf.inputs['Alpha'].links[0])
        if m.blend_method != 'OPAQUE' or m.surface_render_method == 'BLENDED':
            nt.links.new(tex.outputs['Alpha'], bsdf.inputs['Alpha'])
    if m.get('openyamm_translucency') is not None and bsdf.inputs['Alpha'].links:
        # Alpha-tested foliage (finish MASK 0.5): a hard cut instead of the importer's blend.
        source = bsdf.inputs['Alpha'].links[0].from_socket
        cut = nt.nodes.new('ShaderNodeMath')
        cut.operation = 'GREATER_THAN'
        cut.inputs[1].default_value = 0.5
        nt.links.new(source, cut.inputs[0])
        nt.links.new(cut.outputs[0], bsdf.inputs['Alpha'])
        m.surface_render_method = 'DITHERED'
    if m.get('openyamm_edge_darkening'):
        # Edge darkening (fs_model): darken toward the silhouette by the facing.
        lw = nt.nodes.new('ShaderNodeLayerWeight')
        lw.inputs['Blend'].default_value = 0.5
        ramp = nt.nodes.new('ShaderNodeMapRange')
        ramp.inputs['From Min'].default_value = 0.0
        ramp.inputs['From Max'].default_value = 1.0
        ramp.inputs['To Min'].default_value = 1.0
        ramp.inputs['To Max'].default_value = 1.0 - float(m['openyamm_edge_darkening'])
        nt.links.new(lw.outputs['Facing'], ramp.inputs['Value'])
        mul = nt.nodes.new('ShaderNodeMix')
        mul.data_type = 'RGBA'
        mul.blend_type = 'MULTIPLY'
        mul.inputs[0].default_value = 1.0
        src = bsdf.inputs['Base Color'].links[0].from_socket
        nt.links.new(src, mul.inputs[6])
        nt.links.new(ramp.outputs['Result'], mul.inputs[7])
        nt.links.new(mul.outputs[2], bsdf.inputs['Base Color'])

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
    # Card billboards turn about their own centre (the engine's per-primitive pivot).
    for part in lods[level]:
        if part.active_material and part.active_material.name in card_mats:
            bpy.ops.object.select_all(action='DESELECT')
            part.select_set(True)
            bpy.context.view_layer.objects.active = part
            bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')

scene = pl.setup_render((512, 512))
for attribute in ('use_raytracing', 'use_gtao', 'use_shadows'):
    if hasattr(scene.eevee, attribute):
        setattr(scene.eevee, attribute, attribute == 'use_shadows')
sun = bpy.data.objects['Sun']
if light == 'indoor':
    bg = next(n for n in scene.world.node_tree.nodes if n.type == 'BACKGROUND')
    bg.inputs['Color'].default_value = (1.0, 1.0, 1.0, 1.0)
    bg.inputs['Strength'].default_value = 1.0
    sun.data.energy = 0.6
cam = bpy.data.objects.new('Camera', bpy.data.cameras.new('Camera'))
scene.collection.objects.link(cam)
scene.camera = cam
cam.data.lens = 50
FRAME = {}


def frame(parts):
    pts = [o.matrix_world @ Vector(c) for o in parts for c in o.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return (lo + hi) / 2, (hi - lo).length / 2


def render(parts, path, yaw, elevation, fixed=None):
    for o in bpy.data.objects:
        if o.type == 'MESH':
            o.hide_render = o not in parts
    for o in parts:
        if o.active_material and o.active_material.name in cards:
            o.rotation_mode = 'XYZ'
            o.rotation_euler = (0, 0, math.radians(yaw))
    bpy.context.view_layer.update()
    centre, radius = fixed or frame(parts)
    fov = 2 * math.atan(cam.data.sensor_width / (2 * cam.data.lens))
    y, e = math.radians(yaw), math.radians(elevation)
    d = Vector((math.sin(y) * math.cos(e), -math.cos(y) * math.cos(e), math.sin(e)))
    cam.location = centre + d * radius * 1.05 / math.sin(fov / 2)
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    sun.rotation_euler = (math.radians(50), 0, y - math.radians(35))
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


YAW = 0.0
for label, yaw, elevation in (('a_front', 0, 4), ('b_threequarter', 40, 22), ('c_side', 90, 8),
                              ('d_below', 30, -60)):
    render(lods[0], os.path.join(out, f'lod0_{label}.png'), YAW + yaw, elevation)
# Dark background (camera rays only; the light is unchanged) to judge the glow: additive cards add to near black.
world_tree = scene.world.node_tree
background = next(n for n in world_tree.nodes if n.type == 'BACKGROUND')
world_out = next(n for n in world_tree.nodes if n.type == 'OUTPUT_WORLD')
dark = world_tree.nodes.new('ShaderNodeBackground')
dark.inputs['Color'].default_value = (0.012, 0.011, 0.014, 1.0)
path = world_tree.nodes.new('ShaderNodeLightPath')
pick = world_tree.nodes.new('ShaderNodeMixShader')
world_tree.links.new(path.outputs['Is Camera Ray'], pick.inputs[0])
world_tree.links.new(background.outputs[0], pick.inputs[1])
world_tree.links.new(dark.outputs[0], pick.inputs[2])
world_tree.links.new(pick.outputs[0], world_out.inputs['Surface'])
scene.render.film_transparent = False
for label, yaw, elevation in (('a_front', 0, 4), ('b_threequarter', 40, 22)):
    render(lods[0], os.path.join(out, f'dark_{label}.png'), YAW + yaw, elevation)
scene.render.film_transparent = True
world_tree.links.new(background.outputs[0], world_out.inputs['Surface'])
for level in sorted(lods):
    render(lods[level], os.path.join(out, f'level{level}.png'), YAW + 40, 20)

# Motion strip: the shader's vertex animation at a few times (LOD0, front view, fixed framing).
moving = [o for o in lods[0] if o.active_material and (o.active_material.name in wind
                                                        or o.active_material.name in flutter)]
for f in os.listdir(out):
    if f.startswith('motion_'):
        os.remove(os.path.join(out, f))
if moving or swing:
    rest = {o.name: np.array([v.co[:] for v in o.data.vertices]) for o in lods[0]}
    pts = np.concatenate(list(rest.values()))
    height = pts[:, 2].max() - pts[:, 2].min()
    centre, radius = frame(lods[0])
    fixed = (centre, radius * 1.0)
    for k, t in enumerate((0.0, 0.9, 1.8, 2.7, 3.6, 4.5)):
        for o in lods[0]:
            name = o.active_material.name if o.active_material else ''
            co = rest[o.name].copy()
            if name in flutter and o.data.color_attributes:
                attr = o.data.color_attributes[0]
                alpha = np.ones(len(co))
                if attr.domain == 'POINT':
                    alpha = np.array([attr.data[i].color[3] for i in range(len(o.data.vertices))])
                else:
                    for loop in o.data.loops:
                        alpha[loop.vertex_index] = attr.data[loop.index].color[3]
                uvs = np.zeros(len(co))
                for loop in o.data.loops:
                    uvs[loop.vertex_index] = o.data.uv_layers[0].data[loop.index].uv[0]
                normals = np.array([v.normal[:] for v in o.data.vertices])
                wave = np.sin(t * 7.0 - uvs * 9.0) + 0.35 * np.sin(t * 11.3 - uvs * 15.0)
                co += normals * (flutter[name] * alpha * wave)[:, None]
            if name in wind:
                h = np.clip(co[:, 2] / height, 0, 1.5)
                bend = np.array([math.sin(t * 1.1), math.cos(t * 1.1 * 0.83)]) * 0.7
                fp = t * 3.3 + co[:, 0] * 81.7 * 0.011 + co[:, 1] * 81.7 * 0.013
                fl = np.stack([np.sin(fp), np.cos(fp * 1.27)], -1) * 0.3
                co[:, :2] += (bend[None] + fl) * wind[name] * (h * h)[:, None]
            if swing:
                angle = math.radians(swing) * math.sin(2 * math.pi * k / 6)
                top = pts[:, 2].max()
                rot = np.array(Matrix.Rotation(angle, 3, 'X'))
                co = (co - [0, 0, top]) @ rot.T + [0, 0, top]
            for v, p in zip(o.data.vertices, co):
                v.co = p
            o.data.update()
        render(lods[0], os.path.join(out, f'motion_{k}.png'), 90 if swing else 0, 4, fixed)
    for o in lods[0]:
        for v, p in zip(o.data.vertices, rest[o.name]):
            v.co = p
print('REVIEW', out, sorted(lods), 'wind', wind, 'flutter', flutter)
