"""Bake a native indoor map's (BLV) lighting with Cycles. Run using Blender's background Python.

    blender --background --factory-startup --python-exit-code 1 --python tools/lighting/bake_indoor.py -- \\
        --profile tools/lighting/baked_indoors/<map>.yml --output <dir> [--assets <runtime root>] [--recompose]

The scene (faces in their load pose, static lights, sector ambient) comes from the game itself
(`openyamm --headless-export-indoor-bake-scene`). Door-moved faces that move rigidly are baked in the BLV's stored pose
(the game moves their lightmap with them). `--extra-lights <json>` adds bake-only point or spot lights (a converter's lights
over the runtime's four-per-point cap, MM9's directional lights); the profile's `emitters` make sky faces and outward window panes area lights
(a separate pair of passes, scaled by `sky_scale`). Translucent faces (the scene's `translucency`,
devdocs/INDOOR_TRANSLUCENT_FACES.md) scatter their alpha of the light and let the rest through. Output in <dir>: `<map>.lighting` (format: devdocs/
INDOOR_BAKED_LIGHTING.md), its recipe `<map>.bake.json`, report.json and the raw passes (*.npy). Nothing is installed:
copy the lighting/recipe pair beside the map (or, for a review root, install it with its own tool).

Lighting units are the indoor renderer's (the multiplier on the texture colour): a lit texel facing a light carries
exactly the runtime's static light, `1.35 * alpha * colour * (1 - d^2/r^2)^2`, times the surface's cosine and its
soft-shadow visibility. Cycles adds the bounce of that light off the surfaces' mean texture colours. The sector
ambient is added as a floor. `--recompose` rebuilds the file from the saved passes with new scales (no Cycles).
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import subprocess
import sys
import time

import bpy
from mathutils import Vector
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from bake_geometry import (fnv, group_coplanar_faces, newell_normal, pack_lightmap_charts, plane_chart_basis,  # noqa
                           rgbm, rle_bgra)
from bake_assets import bake_texture_paths, source_roots  # noqa: E402

MAGIC = b'OYILIT1\0'
VERSION = 1
HEADER = 64
NO_PAGE = 0xffff
# The face attribute of an indoor sky face (FaceEnums.h IndoorSky): it shows the sky, so it neither casts nor receives.
INDOOR_SKY = 0x00400000
# Cycles light-only DIFFUSE response of a point light of power P with constant falloff: P * cos / (4 pi^2).
CYCLES_POINT_RESPONSE = 1 / (4 * math.pi ** 2)
# On its axis a Cycles spot responds at 2 / pi of a point light of the same strength (measured: 120 / 189).
CYCLES_SPOT_FACTOR = math.pi / 2
TO_BAKE = 1 / 128
TERMS = ['direct', 'indirect']
SKY_TERMS = ['sky_direct', 'sky_indirect']


def load_profile(path, samples):
    profile = json.loads(path.read_text())
    defaults = {'units_per_texel': 16, 'page_size': 2048, 'padding': 2, 'samples': 128, 'bounces': 3,
                'light_size': 24, 'direct_scale': 1.0, 'bounce_scale': 1.0, 'ambient_scale': 0.5, 'blur_radius': 2,
                'emitters': [], 'sky_scale': 1.0, 'outward_distance': 4096, 'glass': [], 'max_lighting': 4.0,
                'ambient_colour': [1.0, 1.0, 1.0], 'shadowless_faces': []}
    profile = dict(defaults, **profile)
    profile.setdefault('sky_bounce_scale', profile['bounce_scale'])
    for emitter in profile['emitters']:
        if not emitter.get('textures') or len(emitter.get('colour', [])) != 3:
            raise ValueError('An emitter needs textures and an RGB colour')
        emitter.setdefault('strength', 1.0)
        emitter.setdefault('display', 1.0)
        emitter.setdefault('outward', False)
    for glass in profile['glass']:
        if not glass.get('textures') or len(glass.get('colour', [])) != 3 or 'display' not in glass:
            raise ValueError('A glass level needs textures, an RGB colour and a display brightness')
    if samples is not None:
        profile['samples'] = samples
    if not 64 <= profile['page_size'] <= 4096 or profile['page_size'] & (profile['page_size'] - 1):
        raise ValueError('page_size must be a power of two between 64 and 4096')
    if not 0 < profile['max_lighting'] <= 4:
        raise ValueError('max_lighting must be within (0, 4]: the file stores RGBM up to 4')
    if profile['samples'] < 1 or profile['units_per_texel'] <= 0:
        raise ValueError('Samples and texel spacing must be positive')
    return profile


def texture_alpha(path):
    """The mean alpha of a bitmap's texels without its magenta key (MM9 glass blends at its texture's alpha)."""
    image = bpy.data.images.load(str(path), check_existing=True)
    pixels = np.array(image.pixels[:], dtype=np.float32).reshape(-1, 4)
    bpy.data.images.remove(image)
    transparent = (pixels[:, 0] >= 248 / 255) & (pixels[:, 1] <= 8 / 255) & (pixels[:, 2] >= 248 / 255)
    kept = pixels[~transparent, 3]
    return float(kept.mean()) if len(kept) else 0.0


def texture_albedo(path):
    """The mean linear colour of a native bitmap, without its magenta-keyed transparent texels, and its coverage."""
    image = bpy.data.images.load(str(path), check_existing=True)
    pixels = np.array(image.pixels[:], dtype=np.float32).reshape(-1, 4)
    bpy.data.images.remove(image)
    transparent = (pixels[:, 0] >= 248 / 255) & (pixels[:, 1] <= 8 / 255) & (pixels[:, 2] >= 248 / 255)
    opaque = pixels[~transparent, :3]
    if len(opaque) == 0:
        return (0.0, 0.0, 0.0), 0.0
    linear = np.where(opaque <= 0.04045, opaque / 12.92, ((opaque + 0.055) / 1.055) ** 2.4)
    return tuple(float(value) for value in linear.mean(axis=0)), float(len(opaque) / len(pixels))


def is_receiver(face):
    """Visible faces that do not show the sky; of the door-moved faces, those the game bakes (mover_receiver: a single
    door moves the whole face a short way, IndoorBakedLighting indoorMoverFaceBakeable)."""
    if not face['visible'] or face['attributes'] & INDOOR_SKY:
        return False
    return not face['mover'] or face.get('mover_receiver', False)


def receiver_points(face):
    """A receiver's vertices: a mover's in the BLV's stored pose, which its lightmap mapping is relative to."""
    return face['stored_points'] if face['mover'] else face['points']


def face_normal(points, plane_normal):
    n = newell_normal(points)
    length = math.sqrt(sum(v * v for v in n))
    if length < 1e-6:
        return None
    n = tuple(v / length for v in n)
    if plane_normal is not None and sum(a * b for a, b in zip(n, plane_normal)) < 0:
        n = tuple(-v for v in n)
    return n


def classify_emitters(scene, profile):
    """Face index -> the profile emitter it is: faces with an emitter's texture; an `outward` emitter (a window pane)
    only where the ray from its back runs `outward_distance` without hitting a face, or hits a non-outward emitter (the
    sky behind a skylight's glass), so a pane against a wall stays an ordinary face."""
    by_texture = {texture.lower(): index for index, emitter in enumerate(profile['emitters'])
                  for texture in emitter['textures']}
    if not by_texture:
        return {}
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    faces = [f for f in scene['faces'] if f['visible'] and not f['attributes'] & INDOOR_SKY]
    verts, polys = [], []
    for face in faces:
        polys.append(list(range(len(verts), len(verts) + len(face['points']))))
        verts.extend(Vector(p) for p in face['points'])
    tree = BVHTree.FromPolygons(verts, polys, all_triangles=False)
    result = {}
    for face in faces:
        index = by_texture.get(face['texture'].lower())
        if index is None or 'translucency' in face:
            continue
        emitter = profile['emitters'][index]
        if not emitter['outward']:
            result[face['index']] = index
    for face in faces:
        index = by_texture.get(face['texture'].lower())
        # A translucent pane is never an emitter: it lets the light of the room behind it through.
        if index is None or not profile['emitters'][index]['outward'] or 'translucency' in face:
            continue
        points = receiver_points(face) if face['mover'] else face['points']
        normal = face_normal(points, face['plane_normal'])
        if normal is None:
            continue
        centre = Vector(np.mean(np.array(points, dtype=float), axis=0))
        back = -Vector(normal)
        _, _, hit, _ = tree.ray_cast(centre + back * 2, back, profile['outward_distance'])
        if hit is None or faces[hit]['index'] in result:
            result[face['index']] = index
    return result


def build_charts(scene, profile, emitters):
    """Receiver faces grouped into coplanar charts (emitter faces apart from the rest), packed into pages. Returns
    (charts, page dimensions)."""
    receivers = []
    # Faces drawn without their lightmap (an open-air map's terrain: blended materials under the daylight,
    # devdocs/INDOOR_OPEN_SKY.md "Terrain") take no chart; the scene's terrain `exclude_faces` (kept_faces) do.
    skipped = {texture.lower() for texture in profile.get('skip_textures', [])}
    kept = set(profile.get('keep_faces', []))
    for face in scene['faces']:
        if not is_receiver(face) or (face['texture'].lower() in skipped and face['index'] not in kept):
            continue
        points = [tuple(float(v) for v in p) for p in receiver_points(face)]
        n = newell_normal(points)
        length = math.sqrt(sum(v * v for v in n))
        if length < 1e-6:
            continue
        n = tuple(v / length for v in n)
        if face['plane_normal'] is not None and sum(a * b for a, b in zip(n, face['plane_normal'])) < 0:
            n = tuple(-v for v in n)
            points.reverse()
        receivers.append({'face': face, 'points': points, 'normal': n, 'emitter': emitters.get(face['index'])})
    groups = []
    # Emitter faces and translucent faces chart apart from the rest (their light is set per chart in compose).
    for emitting, translucent in ((False, False), (True, False), (False, True), (True, True)):
        subset = [i for i, r in enumerate(receivers) if (r['emitter'] is not None) == emitting
                  and ('translucency' in r['face']) == translucent]
        groups += [[subset[i] for i in group]
                   for group in group_coplanar_faces([(receivers[i]['points'], receivers[i]['normal'])
                                                      for i in subset])]
    upt = profile['units_per_texel']
    charts = []
    for group in groups:
        members = [receivers[i] for i in group]
        axis_u, axis_v = plane_chart_basis(members[0]['normal'])
        coords = [(sum(p[k] * axis_u[k] for k in range(3)), sum(p[k] * axis_v[k] for k in range(3)))
                  for member in members for p in member['points']]
        lo = np.min(coords, axis=0)
        span = np.maximum(np.max(coords, axis=0) - lo, 1)
        # Texel centres on the chart's bounds: the edge texels of neighbouring charts sample the same world points.
        size = tuple(max(3, math.ceil(value / upt) + 1) for value in span)
        sectors = {}
        for member in members:
            sectors[member['face']['sector']] = sectors.get(member['face']['sector'], 0) + 1
        charts.append({'members': members, 'axis_u': axis_u, 'axis_v': axis_v, 'lo': lo, 'span': span,
                       'size': size, 'sector': max(sectors, key=sectors.get), 'emitter': members[0]['emitter'],
                       'translucent': 'translucency' in members[0]['face']})
    placements, dimensions = pack_lightmap_charts([c['size'] for c in charts], profile['page_size'],
                                                  profile['padding'], first_fit=True)
    for chart, (page, x, y, w, h) in zip(charts, placements):
        page_width, page_height = dimensions[page]
        su = (w - 1) / chart['span'][0]
        sv = (h - 1) / chart['span'][1]
        # u = dot(p, uAxis.xyz) + uAxis.w in normalized page coordinates.
        chart.update(page=page, rect=(x, y, w, h),
                     u_axis=[a * su / page_width for a in chart['axis_u']]
                     + [(x + .5 - chart['lo'][0] * su) / page_width],
                     v_axis=[a * sv / page_height for a in chart['axis_v']]
                     + [(y + .5 - chart['lo'][1] * sv) / page_height])
    return charts, dimensions


def map_uv(axis, point):
    return sum(axis[k] * point[k] for k in range(3)) + axis[3]


def chart_ids(charts, dimensions, padding):
    """Per page, the chart owning each texel of its padded rectangle (-1 outside every chart)."""
    pages = [np.full((h, w), -1, dtype=np.int32) for w, h in dimensions]
    for index, chart in enumerate(charts):
        x, y, w, h = chart['rect']
        pages[chart['page']][max(0, y - padding):y + h + padding, max(0, x - padding):x + w + padding] = index
    return pages


def masked_blur(values, coverage, ids, radius):
    """Box blur of the covered texels of each chart, never across charts (the bounce term's sampling noise)."""
    if radius <= 0:
        return values
    total = np.zeros_like(values)
    weight = np.zeros(values.shape[:2], dtype=np.float32)
    height, width = ids.shape
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            ys = slice(max(0, dy), height + min(0, dy))
            yd = slice(max(0, -dy), height + min(0, -dy))
            xs = slice(max(0, dx), width + min(0, dx))
            xd = slice(max(0, -dx), width + min(0, -dx))
            same = (ids[ys, xs] == ids[yd, xd]) & (ids[yd, xd] >= 0)
            w = coverage[ys, xs] * same
            total[yd, xd] += values[ys, xs] * w[:, :, None]
            weight[yd, xd] += w
    result = values.copy()
    filled = weight > 0
    result[filled] = total[filled] / weight[filled][:, None]
    return result


def light_material(light, profile, light_scale):
    """A point light whose emission follows the runtime's window (1 - d^2/r^2)^2 with no inverse-square falloff. With
    `direction` and `fov` (degrees, the full cone) a spot: a Cycles spot with full blend, a smoothstep of MM9's linear
    cone term (dot - cos(fov/2)) / (1 - cos(fov/2)), equal to it at the axis, half way and the edge."""
    spot = 'direction' in light
    data = bpy.data.lights.new('light', 'SPOT' if spot else 'POINT')
    if spot:
        data.spot_size = math.radians(light['fov'])
        data.spot_blend = 1.0
    data.energy = 1.0
    data.shadow_soft_size = profile['light_size'] * TO_BAKE
    data.use_nodes = True
    tree = data.node_tree
    output = next(node for node in tree.nodes if node.type == 'OUTPUT_LIGHT')
    for node in list(tree.nodes):
        if node != output:
            tree.nodes.remove(node)
    emission = tree.nodes.new('ShaderNodeEmission')
    falloff = tree.nodes.new('ShaderNodeLightFalloff')
    path = tree.nodes.new('ShaderNodeLightPath')
    falloff.inputs['Strength'].default_value = (light_scale * light['alpha'] / CYCLES_POINT_RESPONSE
                                                * (CYCLES_SPOT_FACTOR if spot else 1.0))
    falloff.inputs['Smooth'].default_value = 0
    emission.inputs['Color'].default_value = tuple(channel / 255 for channel in light['color']) + (1,)

    def math_node(operation, first=None, second=None, clamp=False):
        node = tree.nodes.new('ShaderNodeMath')
        node.operation = operation
        node.use_clamp = clamp
        for index, value in enumerate((first, second)):
            if isinstance(value, (int, float)):
                node.inputs[index].default_value = value
            elif value is not None:
                tree.links.new(value, node.inputs[index])
        return node

    ratio = math_node('DIVIDE', path.outputs['Ray Length'], light['radius'] * TO_BAKE)
    square = math_node('POWER', ratio.outputs[0], 2)
    window = math_node('SUBTRACT', 1, square.outputs[0], clamp=True)
    weight = math_node('POWER', window.outputs[0], 2)
    strength = math_node('MULTIPLY', weight.outputs[0], falloff.outputs['Constant'])
    tree.links.new(strength.outputs[0], emission.inputs['Strength'])
    tree.links.new(emission.outputs[0], output.inputs['Surface'])
    obj = bpy.data.objects.new('light', data)
    obj.location = tuple(value * TO_BAKE for value in light['position'])
    if spot:
        obj.rotation_mode = 'QUATERNION'
        obj.rotation_quaternion = Vector((0.0, 0.0, -1.0)).rotation_difference(Vector(light['direction']))
    bpy.context.scene.collection.objects.link(obj)
    return obj


def make_mesh(name, faces, materials, with_uv=False):
    """One mesh object of polygon faces (native vertex order, oriented to the face's front)."""
    verts, polys, mats, uvs = [], [], [], []
    slots = {}
    for points, material, uv in faces:
        offset = len(verts)
        verts.extend(tuple(value * TO_BAKE for value in point) for point in points)
        polys.append(list(range(offset, offset + len(points))))
        if material not in slots:
            slots[material] = len(slots)
        mats.append(slots[material])
        uvs.extend(uv if uv is not None else [(0, 0)] * len(points))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], polys)
    mesh.update()
    for material in slots:
        mesh.materials.append(materials[material])
    for poly, slot in zip(mesh.polygons, mats):
        poly.material_index = slot
    if with_uv:
        layer = mesh.uv_layers.new(name='lighting')
        for poly in mesh.polygons:
            for loop in poly.loop_indices:
                layer.data[loop].uv = uvs[mesh.loops[loop].vertex_index]
        layer.active = True
        layer.active_render = True
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def bake_passes(scene, charts, dimensions, profile, texture_paths, out, lights, emitters):
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    blender_scene = bpy.context.scene
    blender_scene.render.engine = 'CYCLES'
    blender_scene.cycles.samples = profile['samples']
    blender_scene.cycles.seed = 17
    blender_scene.cycles.max_bounces = profile['bounces'] + 1
    blender_scene.cycles.diffuse_bounces = profile['bounces']
    blender_scene.cycles.glossy_bounces = 0
    blender_scene.cycles.transmission_bounces = 0
    blender_scene.render.threads_mode = 'FIXED'
    blender_scene.render.threads = 16
    blender_scene.world.use_nodes = True
    blender_scene.world.node_tree.nodes['Background'].inputs[1].default_value = 0

    materials = {}

    # Emitter materials: (material, strength, colour) to switch their emission on for the sky passes only.
    emissive = []
    # Translucent faces' materials: their alpha in the bake (report).
    translucent_alphas = {}

    shadowless = set(profile['shadowless_faces'])

    def material(texture, emitter=None, translucency=None, no_shadow=False):
        key = texture.lower() + ('' if emitter is None else f'#emit{emitter}')
        if translucency is not None:
            key += '#glass{opacity}#{tint}'.format(**translucency)
        if no_shadow:
            key += '#noshadow'
        if key not in materials:
            albedo, _ = texture_albedo(texture_paths[texture.lower()])
            mat = bpy.data.materials.new(key)
            mat.use_nodes = True
            bsdf = next(node for node in mat.node_tree.nodes if node.type == 'BSDF_PRINCIPLED')
            bsdf.inputs['Base Color'].default_value = albedo + (1,)
            bsdf.inputs['Roughness'].default_value = 1
            bsdf.inputs['Specular IOR Level'].default_value = 0
            if translucency is not None:
                # A translucent face (devdocs/INDOOR_TRANSLUCENT_FACES.md) as the runtime blends it: its tinted
                # colour scatters alpha of the light (alpha = opacity x the texture's mean alpha) and the rest passes
                # straight through, so a pane between two rooms lets light (and shadow rays) through. The diffuse
                # bake divides by the diffuse weight, so the pane's own lightmap is the light arriving at it.
                alpha = min(max(translucency['opacity'] * texture_alpha(texture_paths[texture.lower()]), 0.0), 1.0)
                bsdf.inputs['Base Color'].default_value = tuple(
                    a * t for a, t in zip(albedo, translucency['tint'])) + (1,)
                nodes, links = mat.node_tree.nodes, mat.node_tree.links
                output = next(node for node in nodes if node.type == 'OUTPUT_MATERIAL')
                clear = nodes.new('ShaderNodeBsdfTransparent')
                mix = nodes.new('ShaderNodeMixShader')
                mix.inputs['Fac'].default_value = alpha
                links.new(clear.outputs['BSDF'], mix.inputs[1])
                links.new(bsdf.outputs['BSDF'], mix.inputs[2])
                links.new(mix.outputs['Shader'], output.inputs['Surface'])
                translucent_alphas[key] = alpha
            if no_shadow and translucency is None:
                # The profile's `shadowless_faces` (opt-in): lit and bouncing light, but transparent to shadow rays,
                # as MM9's world models (DestructableBrush pillars) are in its lightmaps: a face that a script can
                # remove leaves no shadow behind (Dragon Stadium).
                nodes, links = mat.node_tree.nodes, mat.node_tree.links
                output = next(node for node in nodes if node.type == 'OUTPUT_MATERIAL')
                path = nodes.new('ShaderNodeLightPath')
                clear = nodes.new('ShaderNodeBsdfTransparent')
                mix = nodes.new('ShaderNodeMixShader')
                links.new(path.outputs['Is Shadow Ray'], mix.inputs['Fac'])
                links.new(bsdf.outputs['BSDF'], mix.inputs[1])
                links.new(clear.outputs['BSDF'], mix.inputs[2])
                links.new(mix.outputs['Shader'], output.inputs['Surface'])
            if emitter is not None:
                source = profile['emitters'][emitter]
                bsdf.inputs['Emission Color'].default_value = tuple(source['colour']) + (1,)
                bsdf.inputs['Emission Strength'].default_value = 0
                emissive.append((bsdf, source['strength']))
            materials[key] = mat
        return key

    light_objects = [light_material(light, profile, scene['light_scale']) for light in lights]
    # Every visible face casts and bounces: receivers in the pose they are baked in (a baked mover in its stored pose),
    # the other doors in their load pose.
    casters = [(f['points'], material(f['texture'], translucency=f.get('translucency'),
                                      no_shadow=f['index'] in shadowless), None)
               for f in scene['faces']
               if f['visible'] and not f['attributes'] & INDOOR_SKY and not is_receiver(f)]
    if casters:
        make_mesh('movers', casters, materials)

    passes = {}
    objects = []
    for page in range(len(dimensions)):
        entries = []
        for chart in charts:
            if chart['page'] != page:
                continue
            for member in chart['members']:
                uv = [(map_uv(chart['u_axis'], p), map_uv(chart['v_axis'], p)) for p in member['points']]
                entries.append((member['points'], material(member['face']['texture'], member['emitter'],
                                                           member['face'].get('translucency'),
                                                           member['face']['index'] in shadowless), uv))
        objects.append(make_mesh(f'page_{page}', entries, materials, with_uv=True))
    # Every page's receivers are in the scene (casting and bouncing) while each page bakes.
    if translucent_alphas:
        print('TRANSLUCENT', {key: round(alpha, 3) for key, alpha in translucent_alphas.items()}, flush=True)
    for page, (width, height) in enumerate(dimensions):
        obj = objects[page]
        target = bpy.data.images.new(f'page_{page}', width=width, height=height, float_buffer=True, alpha=True)
        for mat in obj.data.materials:
            node = mat.node_tree.nodes.get('BakeTarget') or mat.node_tree.nodes.new('ShaderNodeTexImage')
            node.name = 'BakeTarget'
            node.image = target
            mat.node_tree.nodes.active = node
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bake = blender_scene.render.bake
        bake.use_pass_color = False
        bake.margin = profile['padding']
        bake.margin_type = 'EXTEND'
        for term in TERMS + (SKY_TERMS if emissive else []):
            # The lamps' passes, then the emitters' (sky light): each with the other's sources off.
            sky = term in SKY_TERMS
            for obj in light_objects:
                obj.hide_render = sky
            for bsdf, strength in emissive:
                bsdf.inputs['Emission Strength'].default_value = strength if sky else 0
            bake.use_pass_direct = term in ('direct', 'sky_direct')
            bake.use_pass_indirect = term in ('indirect', 'sky_indirect')
            target.pixels.foreach_set(np.zeros(width * height * 4, dtype=np.float32))
            start = time.monotonic()
            bpy.ops.object.bake(type='DIFFUSE')
            pixels = np.empty(width * height * 4, dtype=np.float32)
            target.pixels.foreach_get(pixels)
            pixels = pixels.reshape(height, width, 4)
            np.save(out / f'page_{page}_{term}.npy', pixels)
            passes[(page, term)] = pixels
            print('BAKED', page, term, f'{width}x{height}', round(time.monotonic() - start, 1), 's',
                  float(pixels[:, :, :3].max()), flush=True)
        bpy.data.images.remove(target)
    return passes


def compose(scene, charts, dimensions, profile, passes):
    """Final lighting pages and the per-sector actor ambient, in renderer lighting units."""
    ids = chart_ids(charts, dimensions, profile['padding'])
    pages = []
    sector_sum = np.zeros((scene['sector_count'], 3))
    sector_weight = np.zeros(scene['sector_count'])
    floors = np.array([profile['ambient_scale'] * scene['sector_ambient'][chart['sector']] for chart in charts]
                      + [0.0], dtype=np.float32)
    ambient_colour = np.array(profile['ambient_colour'], dtype=np.float32)
    emitter_display = {index: np.array(emitter['colour'], dtype=np.float32) * emitter['display']
                       for index, emitter in enumerate(profile['emitters'])}
    glass_floor = {texture.lower(): np.array(glass['colour'], dtype=np.float32) * glass['display']
                   for glass in profile['glass'] for texture in glass['textures']}
    for page, (width, height) in enumerate(dimensions):
        direct = passes[(page, 'direct')]
        indirect = passes[(page, 'indirect')]
        coverage = np.minimum(direct[:, :, 3], 1)
        bounce = masked_blur(indirect[:, :, :3], coverage, ids[page], profile['blur_radius'])
        # `ambient_colour` (opt-in, default white) tints the ambient floor: MM9's WorldInfo AmbientLight is coloured
        # (Connecting Tunnels: 15/25/35), and its lightmaps show it wherever no light reaches.
        floor = floors[ids[page]][:, :, None] * ambient_colour
        # The bounce is of the unscaled direct light, so it scales with it too.
        fill = profile['direct_scale'] * profile['bounce_scale'] * bounce + floor
        if (page, 'sky_direct') in passes:
            # Sky light through windows and skylights: soft, so its direct part is blurred with its bounce; it counts
            # as fill for the actors' ambient.
            sky_direct = masked_blur(passes[(page, 'sky_direct')][:, :, :3], coverage, ids[page], 1)
            sky_bounce = masked_blur(passes[(page, 'sky_indirect')][:, :, :3], coverage, ids[page],
                                     profile['blur_radius'])
            fill = fill + profile['sky_scale'] * (sky_direct + profile['sky_bounce_scale'] * sky_bounce)
        # MM9's lightmaps clip at their full value where its lights overlap; `max_lighting` is that ceiling per channel.
        lighting = np.minimum(profile['direct_scale'] * direct[:, :, :3] + fill, profile['max_lighting'])
        lighting[ids[page] < 0] = 0
        # Translucent glass at least as bright as the profile's `glass` level for its texture (MM9's preprocessor
        # lights a translucent surface from both sides, unshadowed; the bake gives a pane only its front's light).
        for index, chart in enumerate(charts):
            texture = chart['members'][0]['face']['texture'].lower() if chart['translucent'] else None
            if texture in glass_floor and chart['page'] == page:
                x, y, w, h = chart['rect']
                pad = profile['padding']
                region = ids[page][max(0, y - pad):y + h + pad, max(0, x - pad):x + w + pad] == index
                block = lighting[max(0, y - pad):y + h + pad, max(0, x - pad):x + w + pad]
                block[region] = np.maximum(block[region], glass_floor[texture])
        # An emitter's own faces show the light: the sky or the lit pane at its display brightness.
        for index, chart in enumerate(charts):
            if chart['page'] == page and chart['emitter'] is not None:
                x, y, w, h = chart['rect']
                pad = profile['padding']
                region = ids[page][max(0, y - pad):y + h + pad, max(0, x - pad):x + w + pad] == index
                lighting[max(0, y - pad):y + h + pad, max(0, x - pad):x + w + pad][region] = \
                    np.minimum(emitter_display[chart['emitter']], 4)
        pages.append(np.concatenate([lighting, np.ones((height, width, 1), dtype=np.float32)], axis=2))
        for index, chart in enumerate(charts):
            if chart['page'] != page or chart['emitter'] is not None:
                continue
            x, y, w, h = chart['rect']
            region = fill[y:y + h, x:x + w][coverage[y:y + h, x:x + w] > 0]
            if len(region):
                sector_sum[chart['sector']] += region.sum(axis=0)
                sector_weight[chart['sector']] += len(region)
    sector_ambient = []
    for sector in range(scene['sector_count']):
        if sector_weight[sector] > 0:
            sector_ambient.append(tuple(float(v) for v in np.clip(sector_sum[sector] / sector_weight[sector], 0, 4)))
        else:
            value = profile['ambient_scale'] * scene['sector_ambient'][sector]
            sector_ambient.append(tuple(float(value * c) for c in ambient_colour))
    return pages, sector_ambient


def write_lighting(path, scene, charts, dimensions, pages, sector_ambient, deps, geometry_hash):
    faces = [None] * scene['face_count']
    for chart in charts:
        for member in chart['members']:
            faces[member['face']['index']] = (chart['page'], chart['u_axis'], chart['v_axis'])
    face_records = b''.join(
        struct.pack('<HH8f', NO_PAGE, 0, *([0.0] * 8)) if record is None
        else struct.pack('<HH8f', record[0], 1, *record[1], *record[2]) for record in faces)
    sector_records = b''.join(struct.pack('<3f', *value) for value in sector_ambient)
    dependency_records = b''
    for name, digest in sorted(deps.items()):
        encoded = name.encode()
        dependency_records += struct.pack('<IQ', len(encoded), digest) + encoded
    payloads = [rle_bgra(rgbm(page)) for page in pages]
    page_offset = HEADER
    face_offset = page_offset + 16 * len(pages)
    sector_offset = face_offset + len(face_records)
    dependency_offset = sector_offset + len(sector_records)
    pixel_offset = dependency_offset + len(dependency_records)
    page_records = b''
    cursor = pixel_offset
    for (width, height), payload in zip(dimensions, payloads):
        page_records += struct.pack('<4I', width, height, cursor, len(payload))
        cursor += len(payload)
    header = MAGIC + struct.pack('<IIQ10I', VERSION, HEADER, geometry_hash, scene['face_count'],
                                 scene['sector_count'], len(pages), len(deps), page_offset, face_offset,
                                 sector_offset, dependency_offset, pixel_offset, cursor)
    assert len(header) == HEADER
    data = header + page_records + face_records + sector_records + dependency_records + b''.join(payloads)
    assert len(data) == cursor
    path.write_bytes(data)
    return sum(len(p) for p in payloads)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--profile', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--samples', type=int)
    parser.add_argument('--assets', type=Path, default=ROOT / 'assets_dev',
                        help='Runtime asset tree holding the map (default assets_dev; a review root: its root)')
    parser.add_argument('--sources', type=Path, action='append', default=[],
                        help='Extra source art root beside the sibling assets_source')
    parser.add_argument('--game-binary', type=Path, default=ROOT / 'build/game/openyamm')
    parser.add_argument('--recompose', action='store_true',
                        help='Reuse the saved Cycles passes in --output; only the scales of the profile change')
    parser.add_argument('--layout-only', action='store_true',
                        help='chart and pack the faces only: flat grey pages, no render (the base of a lightmap '
                             'transfer, which fills nearly every texel; devdocs/mm9_rework/MM9_LIGHTMAP_TRANSFER.md)')
    parser.add_argument('--skip-textures', default='',
                        help='comma-separated textures whose faces take no chart (terrain drawn without lightmaps)')
    parser.add_argument('--keep-faces', default='',
                        help='comma-separated face indices charted despite --skip-textures (terrain exclude_faces)')
    parser.add_argument('--units-per-texel', type=float,
                        help="texel spacing in native units (default: the profile's)")
    parser.add_argument('--extra-lights', type=Path,
                        help='JSON list of bake-only lights ({position, radius, color, alpha}, native units; '
                             'with direction and fov (full cone, degrees): a spot)')
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    assets = args.assets.resolve()
    extra_sources = [path.resolve() for path in args.sources]
    profile = load_profile(args.profile, args.samples)
    if args.units_per_texel:
        profile['units_per_texel'] = args.units_per_texel
    if args.layout_only:
        profile['layout_only'] = True
    if args.skip_textures:
        profile['skip_textures'] = sorted({t.strip().lower() for t in args.skip_textures.split(',') if t.strip()})
    if args.keep_faces:
        profile['keep_faces'] = sorted({int(f) for f in args.keep_faces.split(',') if f.strip()})
    out = args.output
    out.mkdir(parents=True, exist_ok=True)
    scene_path = out / 'scene.json'
    if not args.recompose:
        subprocess.check_call([str(args.game_binary), '--asset-root', str(assets), '--world', profile['world'],
                               '--headless-export-indoor-bake-scene', profile['map'], str(scene_path)], cwd=ROOT,
                              stdout=subprocess.DEVNULL)
    scene = json.loads(scene_path.read_text())
    if scene['map'].lower() != profile['map'].lower():
        raise ValueError('The exported scene is of another map')
    deps = {}

    def dependency(path):
        base = next((root for root in source_roots(assets, extra_sources) if path.is_relative_to(root)), assets)
        deps[str(path.relative_to(base))] = fnv(path.read_bytes())

    geometry = assets / scene['geometry_path']
    geometry_bytes = geometry.read_bytes()
    geometry_hash = fnv(geometry_bytes)
    # The saved passes belong to the geometry they were baked from: recomposing them for a changed map is refused.
    baked_geometry = out / 'baked_geometry.json'
    if args.recompose:
        if json.loads(baked_geometry.read_text())['hash'] != geometry_hash:
            raise ValueError('The map changed since its passes were baked; bake it again (without --recompose)')
    else:
        baked_geometry.write_text(json.dumps({'hash': geometry_hash}) + '\n')
    dependency(geometry)
    if scene['scene_path']:
        dependency(assets / scene['scene_path'])
    recipe_name = Path(scene['geometry_path']).with_suffix('.bake.json')
    # Bake-only lights (the converter's lights over the runtime's cap) are part of the recipe: the saved passes hold them.
    extra_lights_path = out / 'extra_lights.json'
    if not args.recompose:
        extra = json.loads(args.extra_lights.read_text()) if args.extra_lights else []
        extra_lights_path.write_text(json.dumps(extra) + '\n')
    extra_lights = json.loads(extra_lights_path.read_text()) if extra_lights_path.exists() else []
    for light in extra_lights:
        if light['radius'] <= 0 or len(light['position']) != 3 or len(light['color']) != 3:
            raise ValueError('Invalid extra light: ' + json.dumps(light))
    recipe = {'profile': profile, 'extra_lights': extra_lights, 'backend': bpy.app.version_string,
              'producer_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'geometry_helper_sha256': hashlib.sha256(
                  Path(__file__).with_name('bake_geometry.py').read_bytes()).hexdigest()}
    (out / recipe_name.name).write_text(json.dumps(recipe, sort_keys=True, indent=2) + '\n')
    deps[str(recipe_name)] = fnv((out / recipe_name.name).read_bytes())

    emitters = classify_emitters(scene, profile)
    charts, dimensions = build_charts(scene, profile, emitters)
    print('EMITTERS', len(emitters), 'faces;', 'extra lights', len(extra_lights), flush=True)
    texels = sum(w * h for w, h in dimensions)
    print('CHARTS', len(charts), 'pages', dimensions, 'texels', texels, flush=True)
    start = time.monotonic()
    # Every drawn face's texture (its mean colour is what light bounces off).
    texture_paths, _ = bake_texture_paths(assets, scene['world'], extra_sources)
    for texture in sorted({f['texture'].lower() for f in scene['faces']
                           if f['visible'] and not f['attributes'] & INDOOR_SKY}):
        if texture not in texture_paths:
            raise ValueError('Missing authoritative bake material: ' + texture)
        dependency(texture_paths[texture])
    if args.layout_only:
        # Flat mid grey on every chart (its padding too): the transfer replaces it with MM9's own lightmap texels and
        # scales what remains to the MM9 light around it; the transfer also recomputes the actor ambient.
        ids = chart_ids(charts, dimensions, profile['padding'])
        pages = []
        for page, (width, height) in enumerate(dimensions):
            lighting = np.where((ids[page] >= 0)[:, :, None], np.float32(0.5), np.float32(0.0))
            lighting = np.repeat(lighting, 3, axis=2)
            pages.append(np.concatenate([lighting, np.ones((height, width, 1), dtype=np.float32)], axis=2))
        sector_ambient = [tuple(float(profile['ambient_scale'] * value) for _ in range(3))
                          for value in scene['sector_ambient']]
        bake_seconds = time.monotonic() - start
    else:
        if args.recompose:
            terms = TERMS + (SKY_TERMS if emitters else [])
            passes = {(page, term): np.load(out / f'page_{page}_{term}.npy')
                      for page in range(len(dimensions)) for term in terms}
        else:
            passes = bake_passes(scene, charts, dimensions, profile, texture_paths, out,
                                 scene['lights'] + extra_lights, emitters)
        bake_seconds = time.monotonic() - start
        pages, sector_ambient = compose(scene, charts, dimensions, profile, passes)
    output = out / Path(scene['geometry_path']).with_suffix('.lighting').name
    compressed = write_lighting(output, scene, charts, dimensions, pages, sector_ambient, deps, geometry_hash)
    report = {'profile': profile, 'blender': bpy.app.version_string, 'charts': len(charts),
              'faces_lightmapped': sum(len(c['members']) for c in charts), 'face_count': scene['face_count'],
              'movers_lightmapped': sum(1 for c in charts for m in c['members'] if m['face']['mover']),
              'emitter_faces': len(emitters),
              'translucent_faces': sum(1 for f in scene['faces'] if 'translucency' in f),
              'lights': len(scene['lights']), 'extra_lights': len(extra_lights), 'pages': dimensions, 'texels': texels,
              'compressed_bytes': compressed, 'output_bytes': output.stat().st_size,
              'bake_seconds': round(bake_seconds, 1), 'recomposed': args.recompose,
              'sector_ambient': sector_ambient, 'dependencies': deps,
              'output_sha256': hashlib.sha256(output.read_bytes()).hexdigest()}
    (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print('OUTPUT', output, flush=True)


if __name__ == '__main__':
    main()
