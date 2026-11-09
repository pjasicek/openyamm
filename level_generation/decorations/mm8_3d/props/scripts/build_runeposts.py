"""Shadowspire rune posts `dec13` .. `dec17` -> work/runepost<NN>_export.glb (LOD0..2).

Tall weathered stone spikes (a faceted lathe with seeded per-facet radii, a flared foot and noise relief, mapped
round with the graded CC0 lichen_rock scan) carrying a column of carved red runes: an alpha-tested strip projected
onto the spike's front (ray cast, a few millimetres out) with the `runes` atlas (Elder Futhark glyphs as on each
sprite), its own `Rune` material faintly emissive with a slow `openyamm_pulse`. dec15/dec16 add a second, lower spike
behind to the right; dec13, dec15 and dec17 stand in a skirt of dark bramble cards (`roots`, alpha tested), dec13
with a white rose at its foot. Usage: blender --background --python build_runeposts.py -- <13|14|15|16|17> [...]"""
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mm8lib as ml  # noqa: E402

pl = ml.pl
u = ml.units
# height / base radius in map units (from the sprites' opaque sizes and the spike's share of the width)
POSTS = {
    '13': {'height': 255, 'radius': 52, 'spikes': [], 'column': 0, 'runes': (0.28, 0.83), 'strip': 0.34,
           'roots': 1.45, 'rose': True, 'seed': 13, 'power': 1.2},
    '14': {'height': 255, 'radius': 50, 'spikes': [], 'column': 0, 'runes': (0.38, 0.84), 'strip': 0.34,
           'roots': 0, 'rose': False, 'seed': 14, 'power': 0.95},
    '15': {'height': 124, 'radius': 31, 'spikes': [(0.78, 0.62, (0.55, 0.45))], 'column': 1, 'runes': (0.30, 0.84),
           'strip': 0.36, 'roots': 1.55, 'rose': False, 'seed': 15, 'power': 0.75},
    '16': {'height': 124, 'radius': 26, 'spikes': [(0.8, 0.6, (0.55, 0.4))], 'column': 1, 'runes': (0.30, 0.84),
           'strip': 0.36, 'roots': 0, 'rose': False, 'seed': 16, 'power': 0.75},
    '17': {'height': 61, 'radius': 17, 'spikes': [], 'column': 2, 'runes': (0.12, 0.72), 'strip': 0.62,
           'roots': 1.5, 'rose': False, 'seed': 17, 'power': 0.8},
}
LEVELS = [{'segments': 16, 'rings': 16, 'rows': 4, 'cards': 16, 'rose': 2},
          {'segments': 10, 'rings': 9, 'rows': 2, 'cards': 8, 'rose': 1},
          {'segments': 7, 'rings': 5, 'rows': 1, 'cards': 4, 'rose': 0}]
GLYPHS = [7, 3, 2]
TILE = 1.2                        # metres of rock per texture repeat


def spike(name, height, radius, segments, rings, seed, power, offset=(0, 0)):
    rng = np.random.default_rng(seed)
    facets = rng.uniform(0.82, 1.12, segments)
    twist = rng.uniform(-0.25, 0.25)
    bm = bmesh.new(); uv = bm.loops.layers.uv.new('UVMap')
    zs = np.linspace(0, height, rings + 1)[:-1]
    rows = []
    for i, z in enumerate(zs):
        t = z / height
        r = radius * (1 - t) ** power * (1 + 0.15 * math.exp(-t / 0.05))
        row = []
        for s in range(segments):
            a = 2 * math.pi * s / segments + twist * t
            f = facets[s] * (1 + 0.06 * rng.normal()) if i else facets[s]
            row.append(bm.verts.new((offset[0] + math.cos(a) * r * f, offset[1] + math.sin(a) * r * f, z)))
        rows.append(row)
    apex = bm.verts.new((offset[0] + rng.uniform(-0.02, 0.02) * radius, offset[1], height))
    circumference = 2 * math.pi * radius
    for i in range(len(rows) - 1):
        for s in range(segments):
            t = (s + 1) % segments
            f = bm.faces.new((rows[i][s], rows[i][t], rows[i + 1][t], rows[i + 1][s]))
            for loop, (uu, vv) in zip(f.loops, ((s, zs[i]), (s + 1, zs[i]), (s + 1, zs[i + 1]), (s, zs[i + 1]))):
                loop[uv].uv = (uu / segments * circumference / TILE + seed * 0.37, vv / TILE)
    for s in range(segments):
        t = (s + 1) % segments
        f = bm.faces.new((rows[-1][s], rows[-1][t], apex))
        for loop, (uu, vv) in zip(f.loops, ((s, zs[-1]), (s + 1, zs[-1]), (s + 0.5, height))):
            loop[uv].uv = (uu / segments * circumference / TILE + seed * 0.37, vv / TILE)
    bmesh.ops.triangulate(bm, faces=list(bm.faces), quad_method='SHORT_EDGE')
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    obj = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(obj)
    from mathutils import noise
    for v in obj.data.vertices:
        if 0.005 < v.co.z < height * 0.97:
            v.co += v.normal * radius * 0.045 * noise.noise(v.co / (radius * 0.5) + Vector((seed, 0, 0)))
    obj.data.update()
    return obj


def rune_strip(name, rock, spec, rows_per_glyph, height, radius):
    """Alpha-tested strip of the post's rune column projected onto the rock's front (-y)."""
    tree = BVHTree.FromObject(rock, bpy.context.evaluated_depsgraph_get())
    z0, z1 = spec['runes'][0] * height, spec['runes'][1] * height
    glyphs = GLYPHS[spec['column']]
    width = (z1 - z0) * spec['strip']
    rows = glyphs * rows_per_glyph + 1
    cols = {4: 6, 2: 4}.get(rows_per_glyph, 3)
    bm = bmesh.new(); uv = bm.loops.layers.uv.new('UVMap')
    grid = []
    for i in range(rows):
        z = z1 - (z1 - z0) * i / (rows - 1)
        row = []
        for j in range(cols):
            x = -width / 2 + width * j / (cols - 1)
            hit = tree.ray_cast(Vector((x, -5.0, z)), Vector((0, 1, 0)), 10.0)
            p = hit[0] - Vector((0, 1, 0)) * radius * 0.06 if hit[0] is not None else Vector((x, 0, z))
            row.append((bm.verts.new(p), (spec['column'] * 0.25 + j / (cols - 1) * 0.25, 1 - i / (rows - 1))))
        grid.append(row)
    for i in range(rows - 1):
        for j in range(cols - 1):
            corners = (grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1], grid[i][j])
            f = bm.faces.new([c[0] for c in corners])
            for loop, c in zip(f.loops, corners):
                loop[uv].uv = c[1]
    bmesh.ops.triangulate(bm, faces=list(bm.faces), quad_method='SHORT_EDGE')
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons:
        if p.normal.y > 0:
            p.flip()
    obj = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(obj)
    return obj


def root_cards(name, radius, spread, cards, seed):
    """A skirt of bramble cards round the foot: half lean far out (a mat), half stand more upright."""
    rng = np.random.default_rng(seed)
    bm = bmesh.new(); uv = bm.loops.layers.uv.new('UVMap')
    for k in range(cards):
        a = 2 * math.pi * (k + rng.uniform(-0.3, 0.3)) / cards
        lean = math.radians(rng.uniform(55, 72) if k % 2 == 0 else rng.uniform(20, 40))
        length = radius * spread * rng.uniform(0.8, 1.1)
        w = radius * rng.uniform(1.4, 2.0)
        radial = Vector((math.cos(a), math.sin(a), 0)); tangent = Vector((-math.sin(a), math.cos(a), 0))
        base = radial * radius * 0.55
        up = (radial * math.sin(lean) + Vector((0, 0, 1)) * math.cos(lean)) * length
        u0 = rng.choice([0.0, 0.5])
        quad = [base - tangent * w / 2, base + tangent * w / 2, base + tangent * w / 2 + up, base - tangent * w / 2 + up]
        f = bm.faces.new([bm.verts.new(p) for p in quad])
        for loop, t in zip(f.loops, ((u0, 0.0), (u0 + 0.5, 0.0), (u0 + 0.5, 1.0), (u0, 1.0))):
            loop[uv].uv = t
    bmesh.ops.triangulate(bm, faces=list(bm.faces))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    obj = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(obj)
    return obj


def rose(name, centre, size, detail):
    """White rose: rings of cupped petals (2 x 2 grids, flat quads far away) and three leaves."""
    bm = bmesh.new(); uv = bm.loops.layers.uv.new('UVMap')
    rings = [(3, 0.25, 70), (5, 0.45, 50), (6, 0.62, 30)] if detail > 1 else [(4, 0.35, 60), (5, 0.6, 35)]
    rng = np.random.default_rng(7)
    c = Vector(centre)
    for n, r, tilt in rings:
        for k in range(n):
            a = 2 * math.pi * (k / n + rng.uniform(-0.05, 0.05)) + r * 3
            radial = Vector((math.cos(a), math.sin(a), 0)); tangent = Vector((-math.sin(a), math.cos(a), 0))
            t = math.radians(tilt)
            out = radial * math.sin(t) + Vector((0, 0, math.cos(t)))
            base = c + radial * size * r * 0.35
            w = size * (0.35 + r * 0.4); h = size * (0.45 + r * 0.25)
            steps = 2 if detail > 1 else 1
            grid = []
            for i in range(steps + 1):
                row = []
                for j in range(steps + 1):
                    fu, fv = j / steps - 0.5, i / steps
                    cup = (fu * fu) * 0.6 * w
                    p = base + tangent * fu * w * (1 - 0.3 * fv) + out * fv * h - radial * cup
                    row.append((bm.verts.new(p), (0.05 + 0.4 * (fu + 0.5), 0.05 + 0.9 * fv)))
                grid.append(row)
            for i in range(steps):
                for j in range(steps):
                    corners = (grid[i][j], grid[i][j + 1], grid[i + 1][j + 1], grid[i + 1][j])
                    f = bm.faces.new([q[0] for q in corners])
                    for loop, q in zip(f.loops, corners):
                        loop[uv].uv = q[1]
    for k in range(3):
        a = 2 * math.pi * k / 3 + 0.4
        radial = Vector((math.cos(a), math.sin(a), 0)); tangent = Vector((-math.sin(a), math.cos(a), 0))
        base = c + radial * size * 0.3 - Vector((0, 0, size * 0.25))
        tip = base + radial * size * 0.9 - Vector((0, 0, size * 0.15))
        quad = [base - tangent * size * 0.18, base + tangent * size * 0.18, tip + tangent * 0.02, tip - tangent * 0.02]
        f = bm.faces.new([bm.verts.new(p) for p in quad])
        for loop, t in zip(f.loops, ((0.55, 0.1), (0.95, 0.1), (0.95, 0.9), (0.55, 0.9))):
            loop[uv].uv = t
    bmesh.ops.triangulate(bm, faces=list(bm.faces))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    obj = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(obj)
    return obj


def build(post):
    spec = POSTS[post]
    height, radius = u(spec['height']), u(spec['radius'])
    mats = {'Rock': ml.material('Rock', 'runerock', extras={'openyamm_specular': 0.4}),
            'Rune': ml.material('Rune', 'runes', alpha=True, extras={'openyamm_specular': 0.6}),
            'Roots': ml.material('Roots', 'roots', alpha=True, extras={'openyamm_specular': 0.1}),
            'Rose': ml.material('Rose', 'rose', extras={'openyamm_specular': 0.3})}
    levels = []
    for k, lv in enumerate(LEVELS):
        name = f'Runepost{post}' if k == 0 else f'Runepost{post}_LOD{k}'
        rocks = [spike(name + 'R', height, radius, lv['segments'], lv['rings'], spec['seed'], spec['power'])]
        for i, (hf, rf, (ox, oy)) in enumerate(spec['spikes']):
            rocks.append(spike(name + f'R{i}', height * hf, radius * rf, lv['segments'], max(4, lv['rings'] * 3 // 4),
                               spec['seed'] + 10 + i, spec['power'], (radius * ox, radius * oy)))
        rock = pl.join(name + 'Rock', rocks)
        ml.smooth(rock, 50)
        ml.colour(rock, distance=radius * 1.2, strength=0.6, power=1.2)
        ml.set_colour(rock, lambda i, co, c: (c[0] * (0.72 + 0.28 * co.z / height),) * 3 + (1.0,))
        rock.data.materials.append(mats['Rock'])
        parts = [rock]
        strip = rune_strip(name + 'Runes', rock, spec, lv['rows'], height, radius)
        ml.colour(strip, rays=8, distance=0.01, strength=0.0)
        strip.data.materials.append(mats['Rune']); parts.append(strip)
        if spec['roots']:
            cards = root_cards(name + 'Roots', radius, spec['roots'], lv['cards'], spec['seed'])
            ml.colour(cards, rays=8, distance=0.01, strength=0.0)
            ml.set_colour(cards, lambda i, co, c: (0.85, 0.85, 0.85, 1.0))
            cards.data.materials.append(mats['Roots']); parts.append(cards)
        if spec['rose'] and lv['rose']:
            flower = rose(name + 'Rose', (radius * 0.45, -radius * 1.05, radius * 0.35), radius * 0.45, lv['rose'])
            ml.colour(flower, distance=0.1, strength=0.4)
            flower.data.materials.append(mats['Rose']); parts.append(flower)
        lod = pl.join(name, parts)
        levels.append(lod)
    ml.ground(levels); ml.centre_xy(levels)
    for lod in levels:
        ml.apply_transforms(lod)
    print('LODS', post, [pl.triangles(o) for o in levels])
    ml.export(levels, f'runepost{post}')


for post in sys.argv[sys.argv.index('--') + 1:]:
    pl.reset()
    pl._images.clear()          # the reset freed the images props_lib's cache still points at
    build(post)
