"""Owned ground props: explicit low-poly parts, UV-painted surfaces, grounded resting poses.

Run Blender --background --python this_file -- [icon ...]. No shared bindings are written.
"""
import json
import math
from pathlib import Path
import random
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

PROJECT = Path(__file__).resolve().parents[1]
ROOT = PROJECT.parents[2]
TAU = math.tau


def linear(v):
    return v / 12.92 if v < .04045 else ((v + .055) / 1.055) ** 2.4


def material(name, colour, metallic=0, rough=.55, texture=None, alpha=1):
    old = bpy.data.materials.get(name)
    if old:
        return old
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*[linear(c) for c in colour], alpha)
    bsdf.inputs['Metallic'].default_value = metallic
    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Alpha'].default_value = alpha
    if alpha < 1:
        mat.surface_render_method = 'BLENDED'
    if texture:
        tex = mat.node_tree.nodes.new('ShaderNodeTexImage')
        tex.image = bpy.data.images.load(str(PROJECT / 'textures' / f'{texture}.png'), check_existing=True)
        mat.node_tree.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
        if texture in ('puzzle', 'drum_spirals', 'skull_book'):
            # Identify the gold/silver inlays on these deliberately separated painted UV templates.
            pixels = np.array(tex.image.pixels[:], dtype=np.float32).reshape(-1, 4)
            r, g, b = pixels[:, 0], pixels[:, 1], pixels[:, 2]
            metal = (r > b * 1.5) & (g > b * 1.3) & (r > .12)
            if texture == 'skull_book':
                metal |= (np.maximum.reduce([r, g, b]) - np.minimum.reduce([r, g, b]) < .08) & (r > .15)
            packed = np.ones_like(pixels)
            packed[:, 1] = np.where(metal, .38, .75)
            packed[:, 2] = metal.astype(np.float32)
            assert set(np.unique(packed[:, 2])) <= {0, 1}
            mr = bpy.data.images.new(texture + '_mr', *tex.image.size, alpha=False)
            mr.colorspace_settings.name = 'Non-Color'
            mr.pixels[:] = packed.ravel()
            mr.filepath_raw = str(PROJECT / 'textures' / f'{texture}_mr.png')
            mr.file_format = 'PNG'
            mr.save()
            node = mat.node_tree.nodes.new('ShaderNodeTexImage')
            node.image = mr
            separate = mat.node_tree.nodes.new('ShaderNodeSeparateColor')
            mat.node_tree.links.new(node.outputs['Color'], separate.inputs['Color'])
            mat.node_tree.links.new(separate.outputs['Green'], bsdf.inputs['Roughness'])
            mat.node_tree.links.new(separate.outputs['Blue'], bsdf.inputs['Metallic'])
    return mat


def mats():
    return {
        'gold': material('brass', (.72, .51, .18), 1, .35),
        'silver': material('steel', (.59, .63, .65), 1, .33),
        'iron': material('dark iron', (.27, .29, .3), 1, .48),
        'oak': material('oak', (.5, .3, .13), texture='oak', rough=.72),
        'walnut': material('walnut', (.3, .15, .07), texture='walnut', rough=.68),
        'paper': material('parchment', (.77, .67, .45), rough=.82),
        'linen': material('linen', (.68, .6, .4), texture='linen', rough=.9),
        'stone': material('stone', (.42, .43, .44), texture='stone', rough=.86),
        'goldwork': material('engraved brass', (.72, .51, .18), 1, .4, 'gold'),
        'black': material('charcoal', (.13, .12, .11), rough=.85),
        'red': material('red', (.57, .07, .08), rough=.55),
        'blue': material('blue', (.13, .2, .48), rough=.52),
        'purple': material('purple', (.28, .11, .45), rough=.32),
        'green': material('green', (.2, .43, .1), rough=.55),
        'ivory': material('ivory', (.8, .74, .56), rough=.48),
        'glass': material('glass', (.32, .58, .64), rough=.17, alpha=.18),
        'jade': material('green glazed ceramic', (.12, .34, .28), rough=.24),
    }


def mesh(name, verts, faces, mat, uvs=None, smooth=False):
    data = bpy.data.meshes.new(name)
    data.from_pydata(verts, [], faces)
    data.materials.append(mat)
    data.update()
    uv = data.uv_layers.new()
    for face in data.polygons:
        face.use_smooth = smooth
        if uvs:
            for loop, point in zip(face.loop_indices, uvs[face.index]):
                uv.data[loop].uv = point
        else:
            axis = max(range(3), key=lambda i: abs(face.normal[i]))
            axes = [i for i in range(3) if i != axis]
            lo = [min(v[i] for v in verts) for i in axes]
            hi = [max(v[i] for v in verts) for i in axes]
            for loop in face.loop_indices:
                co = data.vertices[data.loops[loop].vertex_index].co
                uv.data[loop].uv = tuple(.02 + .96 * (co[a] - l) / max(h - l, 1e-6)
                                         for a, l, h in zip(axes, lo, hi))
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    return obj


def box(name, pos, size, mat, bevel=.008):
    bpy.ops.mesh.primitive_cube_add(size=1, location=pos)
    obj = bpy.context.object
    obj.name = name
    obj.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    if bevel:
        mod = obj.modifiers.new('edge bevel', 'BEVEL')
        mod.width = bevel
        mod.segments = 1
        bpy.ops.object.modifier_apply(modifier=mod.name)
    # Cube projection with a separate island per hard face.
    uv = obj.data.uv_layers.active or obj.data.uv_layers.new()
    for p in obj.data.polygons:
        axes = sorted(range(3), key=lambda i: abs(p.normal[i]))[:2]
        axes.sort(key=lambda i: size[i])
        for loop in p.loop_indices:
            co = obj.data.vertices[obj.data.loops[loop].vertex_index].co
            uv.data[loop].uv = (tuple(.02 + .96 * (co[i] / size[i] + .5) for i in axes)
                                if mat.name == 'blue marble' else tuple(.5 + .9 * co[i] for i in axes))
    return obj


def lathe(name, profile, mat, pos=(0, 0, 0), segments=16, smooth=True):
    # Tiny closed end rings are capped by a strip triangulation, never a high-valence fan.
    verts = [(pos[0] + r * math.cos(TAU * i / segments), pos[1] + r * math.sin(TAU * i / segments),
              pos[2] + z) for r, z in profile for i in range(segments)]
    faces, uvs = [], []
    total = sum(math.dist(a, b) for a, b in zip(profile, profile[1:]))
    distance = 0
    for j in range(len(profile) - 1):
        a = distance / total
        distance += math.dist(profile[j], profile[j + 1])
        b = distance / total
        for i in range(segments):
            k = (i + 1) % segments
            faces.append((j * segments + i, j * segments + k, (j + 1) * segments + k, (j + 1) * segments + i))
            uvs.append(((i / segments, a), ((i + 1) / segments, a), ((i + 1) / segments, b), (i / segments, b)))
    for row in (0, len(profile) - 1):
        # Alternate ears from the two ends of the ring to avoid a pole.
        ids = list(range(row * segments, (row + 1) * segments))
        reverse = row == 0
        while len(ids) > 2:
            tri = (ids.pop(0), ids[0], ids[-1])
            if reverse:
                tri = tri[::-1]
            faces.append(tri)
            radius = max(profile[row][0], 1e-6)
            uvs.append(tuple((.5 + .48 * (verts[t][0] - pos[0]) / radius,
                              .5 + .48 * (verts[t][1] - pos[1]) / radius) for t in tri))
            if len(ids) > 2:
                tri = (ids.pop(), ids[0], ids[-1])
                if reverse:
                    tri = tri[::-1]
                faces.append(tri)
                uvs.append(tuple((.5 + .48 * (verts[t][0] - pos[0]) / radius,
                                  .5 + .48 * (verts[t][1] - pos[1]) / radius) for t in tri))
    return mesh(name, verts, faces, mat, uvs, smooth)


def tube(name, path, radii, mat, sides=8, closed=False):
    path = [Vector(p) for p in path]
    verts = []
    for i, p in enumerate(path):
        tangent = path[(i + 1) % len(path)] - path[i - 1] if closed else (
            path[min(i + 1, len(path) - 1)] - path[max(i - 1, 0)])
        tangent.normalize()
        x = tangent.cross(Vector((0, 0, 1)))
        if x.length < .01:
            x = tangent.cross(Vector((0, 1, 0)))
        x.normalize()
        y = tangent.cross(x).normalized()
        r = radii[i] if isinstance(radii, list) else radii
        verts.extend(tuple(p + r * (math.cos(TAU * j / sides) * x + math.sin(TAU * j / sides) * y))
                     for j in range(sides))
    faces, uvs = [], []
    rows = len(path) if closed else len(path) - 1
    for i in range(rows):
        k = (i + 1) % len(path)
        for j in range(sides):
            l = (j + 1) % sides
            faces.append((i * sides + j, i * sides + l, k * sides + l, k * sides + j))
            uvs.append(((j / sides, i / rows), ((j + 1) / sides, i / rows),
                        ((j + 1) / sides, (i + 1) / rows), (j / sides, (i + 1) / rows)))
    if not closed:
        for i in (0, len(path) - 1):
            ids = list(range(i * sides, (i + 1) * sides))
            for j in range(1, sides - 1):
                tri = (ids[0], ids[j + 1], ids[j]) if i == 0 else (ids[0], ids[j], ids[j + 1])
                faces.append(tri)
                uvs.append(((.5, .5), (.1, .1), (.9, .9)))
    return mesh(name, verts, faces, mat, uvs, True)


def ring(name, centre, radius, thickness, mat, axis='Z', segments=24):
    path = []
    for i in range(segments):
        a = TAU * i / segments
        v = (radius * math.cos(a), radius * math.sin(a), 0)
        if axis == 'Y':
            v = (v[0], 0, v[1])
        if axis == 'X':
            v = (0, v[0], v[1])
        path.append(tuple(c + d for c, d in zip(centre, v)))
    return tube(name, path, thickness, mat, closed=True)


def ellipsoid(name, pos, scale, mat, subdivisions=2, roughness=0):
    if roughness == 0 and subdivisions >= 2:
        # Continuous longitude UVs avoid visible mineral/nacre seams across smart-projected triangle islands.
        profile = []
        for i in range(11):
            a = -math.pi / 2 + .015 + (math.pi - .03) * i / 10
            profile.append((math.cos(a), math.sin(a)))
        obj = lathe(name, profile, mat, segments=24 if subdivisions >= 3 else 16)
        obj.location = pos
        obj.scale = scale
        return obj
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdivisions, radius=1)
    rng = random.Random(name)
    for v in bm.verts:
        factor = 1 + rng.uniform(-roughness, roughness)
        v.co = Vector(tuple(a * b * factor for a, b in zip(v.co, scale)))
    data = bpy.data.meshes.new(name)
    bm.to_mesh(data)
    bm.free()
    obj = bpy.data.objects.new(name, data)
    obj.location = pos
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=.025)
    bpy.ops.object.mode_set(mode='OBJECT')
    obj.select_set(False)
    for p in data.polygons:
        p.use_smooth = roughness == 0
    return obj


def rod(name, a, b, radius, mat, sides=12):
    return tube(name, [a, b], radius, mat, sides)


def gem(name, colour, size=(.4, .55, .25), cut=8):
    mat = material(name, colour, rough=.19)
    profile = [(.23, -.16), (.5, -.01), (.5, .025), (.29, .2)]
    obj = lathe(name, profile, mat, segments=cut, smooth=False)
    obj.scale = (size[0] * 2, size[1] * 2, size[2] * 3)
    return obj


def sphere_prop(icon, m):
    colours = {'blkperl': (.17, .13, .24), 'wytprl': (.75, .78, .82), 'item282': (.72, .15, .04),
               'item283': (.48, .72, .47), 'crysball': (.26, .15, .43), 'item166': (.42, .28, .13),
               'item325': (.76, .72, .61), 'item269': (.65, .56, .35), 'egg': (.59, .49, .31),
               'jewelegg': (.72, .54, .16), 'item376': (.36, .36, .33)}
    c = colours[icon]
    textures = {'egg': 'egg', 'item269': 'egg', 'jewelegg': 'gold', 'item325': 'flour',
                'item376': 'meteorite', 'blkperl': 'pearl_dark', 'wytprl': 'pearl_white',
                'item282': 'fire_stone', 'item283': 'green_stone', 'crysball': 'crystal_violet'}
    texture = textures.get(icon)
    mat = material('body', c, 1 if icon == 'jewelegg' else 0, .3 if icon != 'item325' else .9, texture)
    scale = (.46, .55, .32) if icon in ('egg', 'item269', 'jewelegg') else (.45, .45, .45)
    ellipsoid('body', (0, 0, 0), scale, mat, 3)
    if icon == 'crysball':
        lathe('stand', [(.34, -.55), (.36, -.51), (.26, -.46), (.3, -.4)], m['gold'])
    if icon == 'item376':
        ring('engraved rim', (0, -.03, .36), .23, .012, m['iron'])
        for path in [[(-.14, .11, .43), (-.07, -.12, .445), (.015, .13, .445)],
                     [(.04, .11, .445), (.1, .15, .43), (.16, .08, .42), (.06, -.13, .445), (.16, -.13, .42)]]:
            tube('dominion rune', path, .014, m['iron'], 4)
    if icon == 'jewelegg':
        for x, y, z in ((0, 0, .32), (-.22, .15, .26), (.22, -.15, .26)):
            ellipsoid('inset jewel', (x, y, z), (.035, .045, .018), m['blue'], 1)


def ore(icon, m):
    suffix = int(icon[-3:])
    textures = ['ore_iron', 'ore_siertal', 'ore_phylt', 'ore_kergar', 'ore_erudine', 'ore_stalt']
    tex = textures[suffix - 353]
    mat = material(tex, (.4, .4, .4), rough=.82, texture=tex)
    ellipsoid('ore_' + icon, (0, 0, 0), (.43, .5, .35), mat, 2, .2)


def crystal(icon, m):
    colours = {'7item200': (.73, .05, .06), 'item163': (.86, .16, .035), '7item201': (.74, .57, .09),
               'item171': (.84, .65, .06), '7item362': (.12, .55, .045), 'item297': (.38, .23, .46),
               'item366': (.75, .045, .34), 'shard': (.6, .75, .81)}
    size = (.32, .55, .45) if icon in ('7item362', 'shard') else (.48, .4, .23)
    cut = 4 if icon in ('7item362', 'item297', 'shard') else (6 if icon in ('7item200', 'item163', 'item366') else 8)
    if icon in ('7item362', 'item297', 'shard', 'item366'):
        height = .55 if icon in ('7item362', 'shard') else .32
        width = .24 if icon in ('7item362', 'shard') else .32
        verts = [(0, -height, 0), (0, height, 0), (-width, 0, 0), (width, 0, 0),
                 (0, 0, .24), (0, 0, -.24)]
        faces = [(0, 2, 4), (2, 1, 4), (1, 3, 4), (3, 0, 4),
                 (2, 0, 5), (1, 2, 5), (3, 1, 5), (0, 3, 5)]
        mesh('pointed crystal', verts, faces, material('crystal', colours[icon], rough=.12))
    elif icon == '7item201':
        corners = [(-.4, -.24), (.4, -.24), (.48, -.16), (.48, .16),
                   (.4, .24), (-.4, .24), (-.48, .16), (-.48, -.16)]
        verts = [(x * s, y * s, z) for s, z in ((.55, -.15), (1, 0), (.98, .025), (.7, .19))
                 for x, y in corners]
        faces = [(j * 8 + i, j * 8 + (i + 1) % 8, (j + 1) * 8 + (i + 1) % 8, (j + 1) * 8 + i)
                 for j in range(3) for i in range(8)]
        faces += [tuple(range(7, -1, -1)), tuple(range(24, 32))]
        mesh('emerald cut yellow garnet', verts, faces, material('garnet', colours[icon], rough=.18))
    else:
        obj = gem(icon, colours[icon], size, cut)
        if icon in ('7item200', 'item163'):
            # The two red stones are elongated irregular cuts, not round cabochons.
            obj.scale.y *= .62 if icon == '7item200' else 1.1
            obj.scale.x *= 1.18 if icon == '7item200' else .8


def scroll(icon, m):
    m['paper'] = material('scroll parchment', (.77, .67, .45), texture='parchment', rough=.82)
    ribbon = 'blue' if icon in ('item199', '7item183') else ('black' if icon == '7item185' else 'red')
    if icon == 'item200':
        m['red'] = material('orange ribbon', (.69, .36, .06), rough=.7)
    if icon == '7item186':
        ribbon = 'linen'
    body = lathe('rolled parchment', [(.105, -.5), (.12, -.47), (.12, .47), (.105, .5)], m['paper'])
    body.rotation_euler.x = math.pi / 2
    for y in (-.51, .51):
        ring('paper spiral', (0, y, 0), .084, .014, m['paper'], 'Y', 20)
        rod('roll core', (0, y - .003, 0), (0, y + .003, 0), .058, m['black'])
        path = []
        for i in range(33):
            a = i / 32 * TAU * 2
            r = .018 + .077 * i / 32
            path.append((r * math.cos(a), y + math.copysign(.004, y), r * math.sin(a)))
        tube('paper spiral', path, .007, m['paper'], 4)
        if icon not in ('7item184', 'item199'):
            rod('spindle', (0, y, 0), (0, y + math.copysign(.08, y), 0), .04, m['gold'])
            ellipsoid('finial', (0, y + math.copysign(.08, y), 0), (.045, .045, .045), m['gold'], 1)
    # A real band around the roll and two loose textile tails.
    band = lathe('ribbon band', [(.124, -.055), (.124, .055)], m[ribbon], segments=16)
    band.rotation_euler.x = math.pi / 2
    for x, angle in ((-.045, .23), (.045, -.23)):
        tail = box('ribbon tail', (x, -.13, .09), (.065, .22, .009), m[ribbon], .001)
        tail.rotation_euler.z = angle
    ellipsoid('wax seal', (0, 0, .126), (.065, .065, .018), m['red'], 2)
    if icon in ('item200', 'item202'):
        ellipsoid('seal jewel', (0, 0, .145), (.04, .04, .014), m['purple' if icon == 'item200' else 'blue'], 1)
    if icon == 'item201':
        for side in (-1, 1):
            tube('cross lacing', [(-.09, side * .15, .085), (.09, -side * .15, .085)], .012, m['red'], 6)


def crate(icon, m):
    open_crate = icon in ('item315', 'item317', 'item319')
    w, d, h = .92, .72, .7
    for x in (-w / 2, w / 2):
        for y in (-d / 2, d / 2):
            box('corner post', (x, y, h / 2), (.075, .075, h + .06), m['walnut'])
    for z in (.08, .28, .48, .68):
        for y in (-d / 2, d / 2):
            box('wall plank', (0, y, z), (w, .045, .18), m['oak'])
        for x in (-w / 2, w / 2):
            box('end plank', (x, 0, z), (.045, d, .18), m['oak'])
    box('base', (0, 0, 0), (w, d, .06), m['walnut'])
    if not open_crate:
        for y in (-.27, -.09, .09, .27):
            box('lid plank', (0, y, h + .02), (w, .17, .05), m['oak'])
        brace = box('lid brace', (0, 0, h + .06), (.08, 1.03, .035), m['walnut'])
        brace.rotation_euler.z = -.82
        painted = material('crate stencil', (.5, .3, .15), rough=.8, texture=icon + '_panel')
        panel('stencilled crate face', [(-w / 2, -d / 2 - .024, 0), (w / 2, -d / 2 - .024, 0),
                                       (w / 2, -d / 2 - .024, h), (-w / 2, -d / 2 - .024, h)], painted)
        panel('stencilled crate lid', [(-w / 2, -d / 2, h + .047), (w / 2, -d / 2, h + .047),
                                      (w / 2, d / 2, h + .047), (-w / 2, d / 2, h + .047)], painted)
    else:
        box('inner shadow', (0, 0, .55), (.84, .64, .03), m['black'])
        if icon == 'item315':
            for i in range(7):
                x, y = ((i % 3 - 1) * .24, (i // 3 - 1) * .22)
                ring('amulet chain', (x, y, .65), .09, .012, m['gold'], segments=12)
                ellipsoid('purple jewel', (x, y + .07, .65), (.055, .08, .03), m['purple'], 1)
        elif icon == 'item319':
            for i in range(5):
                x = (i - 2) * .15
                bottle = lathe('ingredient bottle', [(.06, .59), (.06, .78), (.034, .8), (.034, .88)],
                               m['ivory'], (x, 0, 0), 10)
                lathe('cork', [(.035, .87), (.035, .9)], m['walnut'], (x, 0, 0), 10)
        else:
            for i in range(3):
                tube('silver sea sample', [(-.32, -.2 + i * .2, .62), (0, -.05 + i * .18, .7),
                                           (.25, .12 + i * .12, .85)], [.035, .025, .012], m['ivory'])
    for x in (-w * .4, w * .4):
        for y in (-d / 2 - .03, d / 2 + .03):
            box('iron strap', (x, y, h / 2), (.035, .012, h), m['iron'], .001)


def bottle(icon, m):
    metallic = icon == '7item158'
    mat = m['silver'] if metallic else (m['goldwork'] if icon in ('item312', 'item313') else m['glass'])
    profiles = {
        '7item158': [(.17, 0), (.22, .05), (.2, .15), (.1, .5), (.045, .78), (.05, .83)],
        '7item152': [(.22, 0), (.25, .03), (.25, .6), (.1, .7), (.08, .85)],
        'item312': [(.15, 0), (.24, .12), (.23, .38), (.12, .65), (.06, .9)],
        'item313': [(.15, 0), (.23, .08), (.24, .3), (.13, .57), (.08, .78)],
        '7item288': [(.28, 0), (.29, .04), (.29, .55), (.11, .7), (.06, .9)],
    }
    profile = profiles[icon]
    lathe('vessel', profile, mat)
    top = profile[-1][1]
    lathe('rim', [(profile[-1][0] * 1.15, top - .02), (profile[-1][0] * 1.15, top + .015)],
          m['gold'] if metallic else mat)
    if icon == '7item152':
        lathe('fae dust', [(.21, .02), (.21, .5)], material('yellow dust', (.8, .59, .08), rough=.95))
    if icon == '7item288':
        box('temple nave', (0, 0, .2), (.27, .23, .32), m['ivory'])
        for x in (-.13, .13):
            for y in (-.13, .13):
                lathe('temple turret', [(.045, .05), (.045, .4), (.008, .53)], m['ivory'], (x, y, 0), 8)
                lathe('red turret roof', [(.05, .4), (.006, .54)], m['red'], (x, y, 0), 8, False)
        box('temple door', (0, -.12, .12), (.07, .012, .16), m['black'], .001)
    if icon in ('item312', 'item313'):
        for z in (.11, .36):
            ring('gold band', (0, 0, z), .23, .015, m['gold'])
        if icon == 'item313':
            tube('handle', [(.1, 0, .72), (.27, 0, .69), (.31, 0, .5), (.21, 0, .42)], .025, m['gold'])
        for a in range(4):
            angle = TAU * a / 4
            ellipsoid('amethyst inset', (.21 * math.cos(angle), .21 * math.sin(angle), .22),
                      (.05, .05, .07), m['purple'], 1)
    lathe('stopper', [(profile[-1][0] * .9, top), (profile[-1][0] * .9, top + .07)],
          m['purple'] if metallic or icon in ('item312', 'item313') else m['walnut'], segments=10)
    # Lie bottles on their side; no implausible balancing on a cork or a point.
    bpy.context.view_layer.update()
    for obj in list(bpy.context.scene.objects):
        if obj.type == 'MESH':
            obj.matrix_world = Matrix.Rotation(math.pi / 2, 4, 'X') @ obj.matrix_world


def lamp(icon, m):
    mat = m['goldwork'] if icon == 'aladnlmp' else m['gold']
    lathe('oil reservoir', [(.18, 0), (.23, .035), (.11, .07), (.3, .12), (.34, .21), (.24, .3), (.09, .34)], mat)
    lathe('lid', [(.09, .33), (.13, .35), (.04, .39), (.025, .43)], m['gold'])
    tube('spout', [(0, -.2, .21), (0, -.43, .24), (0, -.63, .32), (0, -.8, .38)],
         [.13, .09, .045, .025], mat, 10)
    tube('handle', [(0, .23, .25), (0, .45, .39), (0, .58, .29), (0, .48, .13), (0, .26, .14)],
         .027, m['gold'], 8)


def cup(icon, m):
    profiles = {
        '7item268': [(.14, 0), (.18, .05), (.25, .28), (.2, .5), (.12, .65), (.21, .8),
                     (.2, .82), (.1, .65), (.18, .5), (.23, .28), (.12, .08)],
        'chalice': [(.26, 0), (.28, .03), (.1, .09), (.06, .27), (.22, .33), (.34, .62), (.35, .69),
                    (.32, .69), (.31, .61), (.2, .36), (.04, .33)],
        'bell': [(.35, 0), (.35, .04), (.22, .17), (.15, .48), (.08, .6), (.04, .62),
                 (.06, .58), (.12, .47), (.19, .17), (.32, .04)],
        'item267': [(.18, 0), (.22, .03), (.09, .09), (.2, .24), (.25, .5), (.2, .67),
                    (.23, .7), (.19, .71), (.17, .65), (.22, .49), (.17, .26), (.04, .2)],
    }
    mat = m['stone'] if icon == '7item268' else m['goldwork']
    lathe('vessel', profiles[icon], mat, segments=20)
    if icon == 'bell':
        ring('hanging loop', (0, 0, .69), .065, .017, m['gold'], 'Y', 16)
        ellipsoid('clapper', (0, 0, .1), (.05, .05, .06), m['iron'], 2)
    if icon == 'item267':
        for side in (-1, 1):
            tube('urn handle', [(side * .2, 0, .58), (side * .36, 0, .56),
                                (side * .37, 0, .3), (side * .2, 0, .29)], .022, m['gold'])
    if icon in ('bell', '7item268'):
        bpy.context.view_layer.update()
        for obj in list(bpy.context.scene.objects):
            if obj.type == 'MESH':
                obj.matrix_world = Matrix.Rotation(math.pi / 2, 4, 'X') @ obj.matrix_world


def rope(icon, m):
    count = 4 if icon == '7item293' else 2
    fibre = material('twisted hemp fibre', (.58, .42, .23), rough=.9)
    steps = 32 if count == 4 else 48
    for j in range(count):
        centre = (0, 0, .048 + .085 * j)
        for strand in range(3):
            path = []
            for i in range(steps):
                a = TAU * i / steps
                twist = a * (steps // 4) + TAU * strand / 3
                radius = .021 * math.cos(twist)
                path.append(((.43 + radius) * math.cos(a), (.35 + radius) * math.sin(a),
                             centre[2] + .021 * math.sin(twist)))
            tube('twisted hemp strand', path, .025, fibre, 4, True)
    tube('free rope end', [(.43, 0, .048), (.45, -.2, .048), (.3, -.36, .048), (.13, -.38, .048)],
         .043, fibre, 6)


def flute(icon, m):
    if icon == '7item276':
        for i in range(6):
            x = (i - 2.5) * .12
            length = .96 - i * .11
            rod('pan pipe', (x, -.48, .055), (x, -.48 + length, .055), .048, m['walnut'])
            ring('pipe opening', (x, -.48 + length, .055), .036, .009, m['oak'], 'Y', 12)
        for y in (-.24, -.36):
            box('brass binding', (0, y, .055), (.75, .045, .13), m['gold'], .003)
    else:
        rod('flute body', (0, -.5, 0), (0, .5, 0), .045, m['walnut'])
        for y in (-.48, -.26, .05, .34, .48):
            ring('ferrule', (0, y, 0), .048, .008, m['gold'], 'Y', 12)
        for y in (-.25, -.08, .09, .25):
            lathe('finger hole', [(.018, .044), (.018, .046)], m['black'], (0, y, 0), 8)


def trumpet(icon, m):
    # A long straight ceremonial trumpet, with a genuinely hollow bell.
    obj = lathe('trumpet', [(.14, -.5), (.135, -.46), (.06, -.25), (.025, -.1), (.025, .55),
                             (.035, .59), (.035, .62), (.014, .62), (.014, -.09), (.045, -.25),
                             (.12, -.46), (.125, -.5)], m['gold'], segments=20)
    obj.rotation_euler.x = math.pi / 2
    banner = box('heraldic banner', (.18, .12, .025), (.3, .45, .018), m['red'], .002)
    for y in (-.1, .12, .33):
        box('banner ivory trim', (.18, y, .038), (.3, .018, .008), m['ivory'], .001)


def ring_prop(icon, m):
    if icon == 'item299':
        ring('heavy brass ring', (0, 0, .1), .38, .095, m['gold'], segments=32)
    elif icon in ('7item290', 'horsshu', 'item326'):
        path = [(.35 * math.cos(math.radians(40) + i / 20 * math.radians(280)),
                 .43 * math.sin(math.radians(40) + i / 20 * math.radians(280)), .035) for i in range(21)]
        shoe = tube('horseshoe', path, .052, m['silver'], 4)
        for v in shoe.data.vertices:
            v.co.z = .035 + (v.co.z - .035) * .32
        for i in (1, 3, 5, 7, 13, 15, 17, 19):
            x, y, z = path[i]
            lathe('nail hole', [(.009, .052), (.009, .053)], m['black'], (x, y, 0), 6)
    else:
        raise ValueError(icon)


def rock(icon, m):
    if icon in ('7item156', 'item173'):
        glassy = material('volcanic glass', (.16, .17, .19), rough=.17)
        for i in range(5):
            obj = lathe('obsidian shard', [(.11, 0), (.12, .15), (.035, .36), (.004, .43)],
                        glassy, (math.sin(i * 3) * .18, math.cos(i * 3) * .2, 0), 5, False)
            obj.rotation_euler = (.3 * math.sin(i), .55 * math.cos(i), i)
            if icon == 'item173':
                obj.scale.z = .35
    else:
        scale = (.48, .5, .3)
        mat = m['stone']
        if icon == '7item148':
            mat = material('blue meteorite', (.13, .23, .37), texture='meteorite_blue', rough=.7)
        elif icon == 'item165':
            mat = material('meteorite', (.3, .3, .3), texture='meteorite', rough=.85)
        elif icon == 'item176':
            mat = material('olive philosopher stone', (.29, .3, .22), rough=.84)
        ellipsoid('stone_' + icon, (0, 0, 0), scale, mat, 2, .14)


def mushroom(icon, m):
    group = icon == '7item142'
    cap = material('mushroom cap', (.3, .3, .3), texture='cap_blue' if icon == '7item151' else 'cap_grey', rough=.8)
    if icon == 'item159':
        cap = material('olive mushroom cap', (.24, .26, .16), rough=.65)
    for x, y, s in ([(0, 0, 1), (-.28, .16, .37), (.28, .18, .3)] if group else [(0, 0, 1)]):
        lathe('stem', [(.08 * s, 0), (.07 * s, .33 * s)], m['ivory'], (x, y, 0), 10)
        lathe('cap', [(.05 * s, .31 * s), (.32 * s, .34 * s), (.3 * s, .38 * s),
                      (.13 * s, .55 * s), (.03 * s, .58 * s)], cap, (x, y, 0), 16)


def fruit(icon, m):
    if icon in ('7item274', 'apple', 'item329', 'item311'):
        tex = 'fruit_purple' if icon == 'item311' else ('apple_green' if icon == 'item329' else 'apple_red')
        mat = material('fruit skin', (.4, .2, .1), texture=tex, rough=.45)
        obj = lathe('fruit', [(.12, 0), (.3, .04), (.41, .2), (.4, .4), (.25, .56), (.05, .52)], mat)
        if icon == 'item311':
            obj.scale = (.7, .7, 1.5)
            for side in (-1, 1):
                for i in range(3):
                    y = (i - 1) * .16
                    verts = [(side * .08, y, .05), (side * .28, y - .08, .08),
                             (side * .4, y, .27), (side * .2, y + .08, .14)]
                    verts += [(x, yy, z - .006) for x, yy, z in verts[:]]
                    mesh('leaf', verts, [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1),
                                        (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)], m['green'])
        rod('stem', (0, 0, .51), (.04, 0, .68), .018, m['walnut'], 6)
        if icon == 'item311':
            rod('fruit stalk', (0, 0, .76), (.09, 0, .95), .023, m['green'], 6)
    elif icon == 'item160':
        ellipsoid('poppy pod', (0, .18, .09), (.14, .19, .14), m['green'], 2)
        tube('stem', [(0, .1, .08), (0, -.2, .04), (-.1, -.5, .04)], .014, m['green'], 6)
        for side in (-1, 1):
            leaf = ellipsoid('leaf', (side * .15, -.22, .04), (.18, .05, .012), m['green'], 1)
            leaf.rotation_euler.z = side * .4


def horn(icon, m):
    if icon == 'item172':
        path = [(0, -.5 + i / 10, .09) for i in range(11)]
        tube('ivory horn', path, [.085 * (1 - i / 10) + .002 for i in range(11)], m['ivory'], 8)
        ridge = []
        for i in range(97):
            t = i / 96
            r = .083 * (1 - t) + .002
            ridge.append((r * math.cos(t * TAU * 7), -.5 + t, .09 + r * math.sin(t * TAU * 7)))
        tube('spiral growth ridge', ridge, [.013 * (1 - i / 96) + .001 for i in range(97)], m['ivory'], 4)
    else:
        path = [(0, -.5, 0), (.05, -.22, .02), (.02, .05, .07), (.13, .3, .12), (.2, .48, .15)]
        tube('turtle fang', path, [.11, .1, .06, .035, .003], m['purple'], 8)
        for x, y, z in ((.08, -.28, .02), (.065, -.05, .05), (.1, .17, .09)):
            tube('fang barb', [(x, y, z), (x + .07, y - .1, z)], [.04, .003], m['purple'], 5)


def food(icon, m):
    if icon == 'item323':
        n = 20
        angles = [math.radians(45) + math.radians(270) * i / n for i in range(n + 1)]
        verts = [(0, 0, z) for z in (0, .3)]
        verts += [(math.cos(a) * .5, math.sin(a) * .5, z) for z in (0, .3) for a in angles]
        faces = []
        for i in range(n):
            faces.extend([(0, 2 + i + 1, 2 + i), (1, 2 + n + 1 + i, 2 + n + 2 + i),
                          (2 + i, 2 + i + 1, 2 + n + 2 + i, 2 + n + 1 + i)])
        faces += [(0, 2, 2 + n + 1, 1), (0, 1, 2 + 2 * n + 1, 2 + n)]
        obj = mesh('cheese', verts, faces, m['ivory'])
        obj.data.materials.append(m['red'])
        for i, p in enumerate(obj.data.polygons):
            if i % 3 == 2 and i < n * 3 or i < n * 3 and i % 3 == 1:
                p.material_index = 1
    elif icon == 'item324':
        mat = material('bread crust', (.6, .4, .2), texture='bread', rough=.88)
        obj = lathe('bread loaf', [(.08, -.5), (.17, -.44), (.18, .44), (.08, .5)], mat, segments=16)
        obj.rotation_euler.x = math.pi / 2


def mortar(m):
    lathe('mortar', [(.2, 0), (.31, .1), (.36, .25), (.33, .27), (.26, .12), (.05, .1)], m['stone'])
    ellipsoid('sulfur powder', (0, 0, .14), (.22, .22, .035),
              material('sulfur yellow', (.79, .67, .17), rough=.95), 2)
    tube('pestle', [(-.08, .04, .15), (.12, .07, .45), (.2, .08, .62)], [.06, .045, .065], m['stone'], 10)


def mercury(m):
    ellipsoid('mercury pool', (0, 0, 0), (.36, .45, .065), m['silver'], 3)
    ellipsoid('mercury drop', (.27, .5, 0), (.13, .16, .055), m['silver'], 2)


def block_prop(icon, m):
    if icon in ('7item361', 'cube', 'item277'):
        mat = material('blue marble', (.12, .17, .44), rough=.28,
                       texture='puzzle' if icon == 'item277' else 'blue_marble')
        box('cube', (0, 0, .38), (.72, .72, .72), mat, .018)
        for axis in range(3):
            for side in (-1, 1):
                for other in (-1, 1):
                    pos = [side * .36, other * .36, .38]
                    size = [.025, .025, .72]
                    if axis == 1:
                        pos, size = [side * .36, 0, .38 + other * .36], [.025, .72, .025]
                    elif axis == 2:
                        pos, size = [0, side * .36, .38 + other * .36], [.72, .025, .025]
                    box('metal edging', pos, size, m['gold'], .002)
    elif icon == 'pyramid':
        for i in range(6):
            z0, z1 = i * .1, (i + 1) * .1 - .003
            r0, r1 = .5 * (1 - z0 / .65), .5 * (1 - z1 / .65)
            verts = [(x * r, y * r, z) for r, z in ((r0, z0), (r1, z1))
                     for x, y in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
            mesh('pyramid stone course', verts, [(0, 3, 2, 1), (4, 5, 6, 7),
                 (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)], m['goldwork'])
        mesh('pyramid capstone', [(-.04, -.04, .598), (.04, -.04, .598), (.04, .04, .598),
             (-.04, .04, .598), (0, 0, .65)], [(0, 3, 2, 1), (0, 1, 4), (1, 2, 4),
             (2, 3, 4), (3, 0, 4)], m['gold'])
    elif icon == '7item351':
        box('tray base', (0, 0, .035), (.9, .8, .07), m['oak'])
        for y in (-.4, .4):
            box('tray side', (0, y, .14), (.95, .045, .22), m['oak'])
        for x in (-.45, .45):
            box('tray end', (x, 0, .14), (.045, .8, .22), m['oak'])
        for x in (-.22, .22):
            for y in (-.2, .2):
                lathe('soul jar', [(.13, .07), (.16, .11), (.16, .4), (.12, .5), (.14, .53),
                                  (.11, .53), (.1, .49), (.13, .39), (.12, .13)], m['jade'], (x, y, 0), 12)
    elif icon == '7item365':
        cyl = lathe('rolled tapestry', [(.11, -.5), (.11, .5)], m['linen'])
        cyl.rotation_euler.x = math.pi / 2
        sheet = box('tapestry loose edge', (.15, 0, -.04), (.2, 1, .02), m['linen'], .001)
    else:
        raise ValueError(icon)


def drum(m):
    shell = material('spiral drum shell', (.2, .15, .08), texture='drum_spirals', rough=.7)
    lathe('drum shell', [(.42, 0), (.44, .04), (.44, .43), (.42, .47)], shell, segments=24)
    for z in (0, .47):
        lathe('drum head', [(.44, z), (.44, z + .018)], m['linen'], segments=24)
        ring('brass rim', (0, 0, z + .01), .44, .018, m['gold'])
    for i in range(12):
        a = i * TAU / 12
        rod('tension rod', (.445 * math.cos(a), .445 * math.sin(a), .04),
            (.445 * math.cos(a), .445 * math.sin(a), .43), .009, m['silver'], 6)
    for direction in (-1, 1):
        rod('drum stick', (-.35, direction * -.2, .5), (.35, direction * .2, .5), .015, m['oak'], 6)


def keg(m):
    obj = lathe('barrel staves', [(.27, -.5), (.32, -.44), (.39, 0), (.32, .44), (.27, .5)], m['oak'], segments=20)
    obj.rotation_euler.x = math.pi / 2
    for y, r in ((-.43, .33), (0, .39), (.43, .33)):
        ring('iron hoop', (0, y, 0), r, .025, m['iron'], 'Y', 20)
    for y in (-.5, .5):
        cap = lathe('barrel end', [(.265, -.01), (.265, .01)], m['oak'], segments=20)
        cap.rotation_euler.x = math.pi / 2
        cap.location.y = y
    tube('tap', [(0, -.51, -.08), (0, -.65, -.08), (0, -.67, -.16)], .025, m['iron'])


def lighting_prop(icon, m):
    if icon == 'cndlabra':
        lathe('base and stem', [(.22, 0), (.24, .035), (.065, .09), (.045, .65), (.07, .72)], m['gold'])
        for side in (-1, 1):
            tube('curved arm', [(0, 0, .3), (side * .28, 0, .4), (side * .35, 0, .62),
                                (side * .35, 0, .72)], .025, m['gold'])
        for x in (-.35, 0, .35):
            lathe('candle cup', [(.09, .72), (.11, .75), (.09, .78)], m['gold'], (x, 0, 0), 12)
            lathe('candle', [(.035, .78), (.035, .87)], m['ivory'], (x, 0, 0), 10)
    elif icon == '7item292':
        lathe('lantern base', [(.13, 0), (.23, .06), (.17, .13)], m['goldwork'])
        lathe('amber panes', [(.17, .13), (.17, .48)], material('amber light', (.81, .43, .07), rough=.28), segments=8)
        lathe('lantern roof', [(.17, .48), (.25, .5), (.13, .65), (.035, .69)], m['goldwork'])
        for i in range(6):
            a = TAU * i / 6
            rod('lantern frame', (.17 * math.cos(a), .17 * math.sin(a), .12),
                (.17 * math.cos(a), .17 * math.sin(a), .5), .013, m['iron'], 6)
        ring('hanging loop', (0, 0, .8), .1, .02, m['iron'], 'Y', 16)
    elif icon == 'item268':
        lathe('brazier', [(.2, .2), (.32, .35), (.33, .42), (.3, .42), (.27, .35), (.15, .25)], m['iron'])
        for i in range(4):
            a = TAU * i / 4
            tube('brazier leg', [(.25 * math.cos(a), .25 * math.sin(a), 0),
                                 (.2 * math.cos(a), .2 * math.sin(a), .22)], .03, m['gold'])
        ellipsoid('coals', (0, 0, .32), (.24, .24, .065), m['red'], 2, .1)
        for i in range(10):
            a = TAU * i / 10
            lathe('brazier rim spike', [(.035, .4), (.025, .48), (.004, .57)], m['iron'],
                  (.31 * math.cos(a), .31 * math.sin(a), 0), 5, False)
        for z in (.27, .39):
            ring('brazier trim', (0, 0, z), .29, .014, m['gold'])
    elif icon == '6hglass':
        for z in (0, .9):
            box('hourglass wood plate', (0, 0, z), (.6, .5, .065), m['walnut'])
            box('hourglass brass trim', (0, 0, z + .02), (.63, .53, .02), m['gold'], .003)
        for x in (-.23, .23):
            for y in (-.18, .18):
                rod('wood post', (x, y, .02), (x, y, .88), .023, m['walnut'], 8)
        lathe('glass bulbs', [(.17, .04), (.18, .15), (.14, .29), (.022, .45),
                              (.14, .61), (.18, .75), (.17, .86)], m['glass'])
        lathe('lower sand', [(.14, .045), (.13, .1), (.02, .2)], m['paper'])
        lathe('upper sand', [(.02, .47), (.12, .64), (.13, .68)], m['paper'])
    elif icon == 'chime':
        lathe('chime roof', [(.28, .6), (.3, .62), (.04, .75)], m['oak'])
        for i in range(5):
            a = TAU * i / 5
            x, y = .18 * math.cos(a), .18 * math.sin(a)
            rod('chime thread', (x, y, .6), (x, y, .4), .006, m['black'], 4)
            rod('chime pipe', (x, y, .42), (x, y, -.1 + i * .035), .025, m['silver'], 10)
        ring('hanging eye', (0, 0, .81), .045, .012, m['iron'], 'Y', 12)


def panel(name, corners, mat):
    return mesh(name, corners, [(0, 1, 2, 3)], mat,
                [[(.01, .01), (.99, .01), (.99, .99), (.01, .99)]])


def cards(icon, m):
    mat = material('card face', (.6, .5, .3), texture='arcomage' if icon == '7item295' else 'tarot', rough=.8)
    for i in range(3):
        before = set(bpy.context.scene.objects)
        z = .015 + i * .025
        box('card stack', (0, 0, z), (.58, .84, .022), m['paper'], .002)
        panel('card painting', [(-.285, -.415, z + .012), (.285, -.415, z + .012),
                                (.285, .415, z + .012), (-.285, .415, z + .012)], mat)
        for obj in set(bpy.context.scene.objects) - before:
            obj.rotation_euler.z = (i - 1) * .22


def book(m):
    box('page block', (0, 0, .12), (.66, .9, .2), m['paper'], .005)
    for z in (0, .24):
        box('leather cover board', (0, 0, z), (.74, 1, .04), m['walnut'], .008)
    box('rounded spine', (-.36, 0, .12), (.07, 1, .23), m['walnut'], .02)
    mat = material('horned skull cover', (.3, .2, .12), texture='skull_book', rough=.6)
    panel('painted front cover', [(-.36, -.49, .261), (.36, -.49, .261),
                                  (.36, .49, .261), (-.36, .49, .261)], mat)


def special(icon, m):
    if icon == '7item153':
        leather = material('sulfur pouch leather', (.4, .23, .12), texture='leather', rough=.86)
        lathe('open pouch', [(.16, 0), (.26, .07), (.29, .25), (.23, .45), (.25, .5),
                             (.22, .5), (.2, .44), (.25, .25), (.22, .09), (.13, .06)], leather, segments=12)
        sulfur = material('sulfur crystals', (.85, .7, .06), rough=.7)
        for i in range(8):
            a = i * 2.4
            ellipsoid('sulfur lump', (.13 * math.cos(a), .13 * math.sin(a), .48 + .03 * math.sin(i)),
                      (.07, .07, .065), sulfur, 1, .22)
        ring('draw cord', (0, 0, .43), .23, .012, m['linen'])
        tube('drawstring', [(.23, 0, .44), (.34, 0, .29), (.32, 0, .05), (.4, 0, .04)], .012, m['linen'], 6)
    elif icon == '7item277':
        ellipsoid('pear shaped lute bowl', (0, -.2, .09), (.3, .38, .15), m['walnut'], 3)
        lathe('soundboard', [(.29, .205), (.29, .217)], m['oak'], (0, -.2, 0), 24)
        box('neck', (0, .35, .15), (.07, .65, .08), m['walnut'])
        box('pegbox', (0, .7, .12), (.1, .15, .08), m['oak'])
        lathe('soundhole', [(.07, .22), (.07, .223)], m['black'], (0, -.05, 0), 16)
        ring('rosette', (0, -.05, .225), .08, .008, m['gold'], segments=20)
        box('bridge', (0, -.39, .24), (.2, .035, .02), m['ivory'], .002)
        outline = [(-.07, .18, .246), (-.19, .07, .246), (-.28, -.13, .246), (-.27, -.36, .246),
                   (-.15, -.5, .246), (.15, -.5, .246), (.27, -.36, .246), (.28, -.13, .246),
                   (.19, .07, .246), (.07, .18, .246)]
        uvs = [[((x + .3) / .6, (y + .52) / .72) for x, y, z in outline]]
        mesh('inlaid lute soundboard', outline, [tuple(range(len(outline)))],
             material('lute inlay', (.5, .3, .15), texture='lute', rough=.65), uvs)
        for i in range(4):
            x = (i - 1.5) * .012
            rod('string', (x, -.4, .256), (x, .7, .2), .0025, m['ivory'], 4)
        for y in (.64, .72):
            rod('tuning peg', (-.09, y, .12), (.09, y, .12), .015, m['gold'], 6)
    elif icon == '7item280':
        blue = material('blue stone tile', (.17, .23, .3), rough=.8)
        lathe('eight sided tile', [(.5, 0), (.5, .06)], blue, segments=8, smooth=False)
        for z in (.045, .065):
            ring('tile edge', (0, 0, z), .47, .012, m['gold'], segments=8)
        lathe('moon medallion', [(.28, .06), (.28, .07)], m['gold'], segments=24)
        lathe('moon negative space', [(.245, .069), (.245, .073)], blue, (.09, .02, 0), segments=24)
    elif icon == 'infrod':
        rod('infused metal rod', (0, -.5, .04), (0, .5, .04), .055, m['silver'], 12)
    elif icon == 'gong':
        for x in (-.42, .42):
            rod('gong frame post', (x, -.5, .06), (x, .5, .06), .05, m['walnut'], 12)
            for y in (-.5, .5):
                ellipsoid('frame finial', (x, y, .06), (.07, .07, .07), m['gold'], 2)
        rod('crossbar', (-.42, .4, .06), (.42, .4, .06), .027, m['silver'])
        lathe('gong disc', [(.31, .04), (.33, .055), (.31, .07)], m['silver'], segments=24)
        lathe('gong boss', [(.09, .07), (.07, .105)], m['gold'], segments=12)
        diamond = box('gong blue diamond', (0, 0, .075), (.2, .2, .015), m['blue'], .002)
        diamond.rotation_euler.z = math.pi / 4
        for x, y in ((-.17, 0), (.17, 0), (0, -.17), (0, .17)):
            ellipsoid('gong ornament', (x, y, .08), (.035, .035, .018), m['gold'], 1)
        ring('suspension', (0, .32, .07), .04, .011, m['gold'])
    elif icon == 'item281':
        ellipsoid('purple stone', (0, 0, .15), (.35, .35, .24), m['purple'], 3)
        for i in range(3):
            obj = gem('crystal inclusion', (.69, .58, .74), (.11, .17, .1), 4)
            obj.location = ((i - 1) * .13, .04 * math.sin(i * 2), .39)
            obj.rotation_euler.z = i * .7
    elif icon == 'item306':
        ring('circlet rim', (0, 0, .075), .38, .035, m['gold'], segments=32)
        for i in range(8):
            a = TAU * i / 8
            x, y = .38 * math.cos(a), .38 * math.sin(a)
            path = []
            for j in range(12):
                t = TAU * j / 12
                offset = .065 * math.cos(t)
                path.append((x - offset * math.sin(a), y + offset * math.cos(a), .17 + .1 * math.sin(t)))
            tube('filigree loop', path, .012, m['gold'], 6, True)
            mid = a + math.pi / 8
            rod('crown point', (.38 * math.cos(mid), .38 * math.sin(mid), .08),
                (.38 * math.cos(mid), .38 * math.sin(mid), .34), .012, m['gold'], 6)
        ellipsoid('green cabochon', (0, -.39, .16), (.09, .035, .1), m['green'], 2)
        ring('cabochon setting', (0, -.395, .16), .105, .014, m['gold'], 'Y', 16)
    else:
        raise ValueError(icon)


def finish(icon):
    objects = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    assert objects, icon
    # Bake part transforms before centring/grounding; keep transparent surfaces on a separate node.
    for obj in objects:
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method='SHORT_EDGE')
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        bm.to_mesh(obj.data)
        bm.free()
    points = [v.co for o in objects for v in o.data.vertices]
    lo = Vector(tuple(min(p[i] for p in points) for i in range(3)))
    hi = Vector(tuple(max(p[i] for p in points) for i in range(3)))
    centre = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
    turn = hi.x - lo.x > hi.y - lo.y
    for obj in objects:
        for v in obj.data.vertices:
            v.co -= centre
            if turn:
                v.co.x, v.co.y = -v.co.y, v.co.x
    for transparent in (False, True):
        objects = [o for o in bpy.context.scene.objects if o.type == 'MESH']
        group = [o for o in objects if any(m.node_tree.nodes['Principled BSDF'].inputs['Alpha'].default_value < 1
                                         for m in o.data.materials) == transparent]
        if not group:
            continue
        bpy.ops.object.select_all(action='DESELECT')
        for obj in group:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = group[0]
        bpy.ops.object.join()
        group[0].name = f'props_{icon}' + ('_glass' if transparent else '')
    objects = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    triangles = sum(len(o.data.polygons) for o in objects)
    assert 4 < triangles <= 4000, (icon, triangles)
    for obj in objects:
        assert all(math.isfinite(c) for v in obj.data.vertices for c in v.co), icon
        assert all(-.001 <= c <= 1.001 for u in obj.data.uv_layers.active.data for c in u.uv), icon
    points = [v.co for o in objects for v in o.data.vertices]
    assert abs(min(v.z for v in points)) < 1e-5, icon
    assert abs(min(v.x for v in points) + max(v.x for v in points)) < 1e-5, icon
    assert abs(min(v.y for v in points) + max(v.y for v in points)) < 1e-5, icon
    out = PROJECT / 'work' / 'exports'
    out.mkdir(parents=True, exist_ok=True)
    blend = PROJECT / 'blends'
    blend.mkdir(exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(blend / f'props_{icon}.blend'))
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.export_scene.gltf(filepath=str(out / f'props_{icon}_export.glb'), export_format='GLB',
                              use_selection=True, export_yup=True, export_animations=False,
                              export_skins=False, export_morph=False, export_tangents=False)
    print('BUILT', icon, triangles, flush=True)


def build(icon, entry):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    m = mats()
    shape = entry['shape']
    if shape == 'ore':
        ore(icon, m)
    elif shape == 'gem':
        crystal(icon, m)
    elif shape == 'sphere':
        sphere_prop(icon, m)
    elif shape == 'scroll':
        scroll(icon, m)
    elif shape == 'crate':
        crate(icon, m)
    elif shape == 'bottle':
        bottle(icon, m)
    elif shape == 'lamp':
        lamp(icon, m)
    elif shape == 'cup':
        cup(icon, m)
    elif shape == 'rope':
        rope(icon, m)
    elif shape == 'flute':
        flute(icon, m)
    elif shape == 'trumpet':
        trumpet(icon, m)
    elif shape == 'ring':
        ring_prop(icon, m)
    elif shape == 'rock':
        rock(icon, m)
    elif shape == 'mushroom':
        mushroom(icon, m)
    elif shape == 'fruit':
        fruit(icon, m)
    elif shape == 'horn':
        horn(icon, m)
    elif shape == 'food':
        food(icon, m)
    elif shape == 'mortar':
        mortar(m)
    elif shape == 'mercury':
        mercury(m)
    elif shape == 'block':
        block_prop(icon, m)
    elif shape == 'drum':
        drum(m)
    elif shape == 'keg':
        keg(m)
    elif shape == 'lighting':
        lighting_prop(icon, m)
    elif shape == 'cards':
        cards(icon, m)
    elif shape == 'book':
        book(m)
    elif shape == 'special':
        special(icon, m)
    else:
        raise ValueError((icon, shape))
    finish(icon)


def main():
    only = set(sys.argv[sys.argv.index('--') + 1:]) if '--' in sys.argv else set()
    owned = {x['icon'] for x in json.loads((PROJECT / 'ownership.json').read_text())}
    designs = json.loads((PROJECT / 'designs.json').read_text())
    assert all(name.startswith('props_') and set(d['icons']) <= owned for name, d in designs.items())
    for name, entry in designs.items():
        if entry['shape'] == 'meshy':
            continue
        icon = entry['icons'][0]
        if not only or icon in only:
            build(icon, entry)


if __name__ == '__main__':
    main()
