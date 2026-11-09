"""Fruit bowl `dec28` (MM7 `7dec08`) -> work/fruitbowl_export.glb, installed as mm7_deco_fruit_bowl.glb.

A wide, shallow wooden bowl (lathe, fruitbowl_wood: CC0 fine_grained_wood graded to the sprite's grey-tan) heaped
as in the sprite: a big red apple at the back left, an orange behind it at the right, two bananas across the front
left, a bunch of pale green grapes at the right, three small red apples in front of the grapes, a small apple at the
front left and a few leaves. Fruit are the CC0 Poly Haven scans food_apple_01, bananas (bananas_a, bananas_b) and
food_lime_01 (recoloured orange, and scaled down as grapes), each decimated to its share; their own texture
coordinates and maps (make_textures.py `fruit`). Leaves use the rose atlas's leaf half (double-sided).
Usage: blender --background --python build_fruitbowl.py"""
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Euler, Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mm8lib as ml  # noqa: E402

pl = ml.pl
SOURCE = os.path.join(ml.HERE, 'source')
BOWL = [(0.0, 0.0), (0.1, 0.0), (0.14, 0.03), (0.165, 0.075), (0.172, 0.12), (0.162, 0.126), (0.15, 0.11),
        (0.12, 0.06), (0.0, 0.05)]
# (model, mesh, material, location, rotation degrees, scale, LOD triangles)
FRUIT = [
    ('food_apple_01', None, 'Apple', (-0.03, 0.045, 0.165), (0, 0, 30), 1.25, (340, 110, 60)),
    ('food_lime_01', None, 'Orange', (0.065, 0.085, 0.185), (90, 0, 0), 1.6, (260, 80, 50)),
    ('bananas', 'bananas_a', 'Banana', (-0.04, -0.045, 0.17), (14, -20, 95), 1.15, (240, 80, 45)),
    ('bananas', 'bananas_b', 'Banana', (-0.035, -0.085, 0.14), (10, -14, 100), 1.1, (240, 80, 45)),
    ('food_apple_01', None, 'Apple', (0.035, -0.095, 0.125), (0, 20, 0), 0.62, (130, 45, 30)),
    ('food_apple_01', None, 'Apple', (0.095, -0.075, 0.125), (0, -15, 60), 0.62, (130, 45, 30)),
    ('food_apple_01', None, 'Apple', (0.065, -0.03, 0.16), (10, 0, 120), 0.6, (130, 45, 30)),
    ('food_apple_01', None, 'Apple', (-0.125, -0.055, 0.12), (0, 10, 200), 0.72, (140, 45, 30)),
]
GRAPES = {'centre': (0.11, 0.01, 0.13), 'rows': [(7, 0.042, 0.0), (6, 0.034, 0.03), (5, 0.026, 0.058),
                                                  (3, 0.016, 0.083), (1, 0.0, 0.102)], 'radius': 0.0135,
          'segments': (6, 4, 0)}
LEAVES = [((-0.15, 0.03, 0.15), (0.0, 0.0, 1.0), 0.05, 40), ((0.13, 0.07, 0.23), (0.4, 0.2, 1.0), 0.045, -30)]
FILL = ('ellipsoid', (0.0, 0.01, 0.1), 0.13, (1.0, 0.85, 0.45))      # hidden heap the fruit rests on (wood)


def load_fruit(model, mesh_name):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(SOURCE, model, f'{model}_1k.gltf'))
    new = [o for o in bpy.data.objects if o not in before]
    keep = [o for o in new if o.type == 'MESH' and (mesh_name is None or o.name == mesh_name)][0]
    for o in new:
        if o is not keep:
            bpy.data.objects.remove(o)
    keep.parent = None
    ml.apply_transforms(keep)
    lo, hi = pl.bounds([keep])
    keep.data.transform(Matrix.Translation(-(lo + hi) / 2))
    keep.data.materials.clear()
    return keep


def leaf(name, at, normal, size, spin, mat):
    n = Vector(normal).normalized()
    t = n.orthogonal().normalized()
    t = Matrix.Rotation(math.radians(spin), 3, n) @ t
    b = n.cross(t)
    base = Vector(at)
    pts = [base - b * size * 0.3, base + t * size * 0.5, base + b * size * 0.7 + t * size * 0.1,
           base - t * size * 0.1 + b * size * 1.1, base - t * size * 0.5]
    bm = bmesh.new(); uv = bm.loops.layers.uv.new('UVMap')
    f = bm.faces.new([bm.verts.new(p) for p in pts])
    for loop, c in zip(f.loops, ((0.75, 0.05), (0.95, 0.4), (0.8, 0.95), (0.75, 0.95), (0.55, 0.4))):
        loop[uv].uv = c
    bmesh.ops.triangulate(bm, faces=list(bm.faces))
    return pl.to_object(name, bm, mat)


def main():
    pl.reset()
    mats = {name: ml.material(name, tex, extras={'openyamm_specular': spec}) for name, tex, spec in (
        ('Wood', 'fruitbowl_wood', 0.4), ('Apple', 'fruit_apple', 0.7), ('Banana', 'fruit_banana', 0.4),
        ('Orange', 'fruit_orange', 0.5), ('Grape', 'fruit_grape', 0.7), ('Leaves', 'rose', 0.3))}
    sources = {}
    levels = []
    for k in range(3):
        parts = [pl.lathe('Bowl', BOWL, (28, 18, 10)[k], mats['Wood'], u_repeat=3.0, v_scale=4.0)]
        ml.smooth(parts[0], 50)
        for i, (model, mesh, mat, loc, rot, scale, tris) in enumerate(FRUIT):
            key = (model, mesh)
            if key not in sources:
                sources[key] = load_fruit(model, mesh)
                sources[key].hide_render = True
            f = ml.duplicate(sources[key], f'F{i}')
            f.data.transform(Matrix.LocRotScale(Vector(loc), Euler([math.radians(a) for a in rot]),
                                                Vector((scale,) * 3)))
            pl.decimate_to(f, tris[k])
            f.data.materials.append(mats[mat])
            parts.append(f)
        if GRAPES['segments'][k]:
            rng = np.random.default_rng(28)
            cx, cy, cz = GRAPES['centre']
            for row, (n, r, dz) in enumerate(GRAPES['rows']):
                for j in range(n):
                    a = 2 * math.pi * j / max(n, 1) + row * 0.5
                    seg = GRAPES['segments'][k]
                    bm = bmesh.new()
                    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=4, radius=GRAPES['radius'] *
                                              rng.uniform(0.9, 1.1), calc_uvs=True)
                    bmesh.ops.translate(bm, verts=bm.verts, vec=Vector((cx + r * math.cos(a),
                                                                        cy + r * math.sin(a) * 0.8, cz + dz)))
                    g = pl.to_object(f'G{row}_{j}', bm, mats['Grape'])
                    parts.append(g)
        else:
            blob = ml.metaballs('Grapes', [('ellipsoid', (GRAPES['centre'][0], GRAPES['centre'][1],
                                                          GRAPES['centre'][2] + 0.05), 0.07, (1.0, 0.8, 1.1))],
                                resolution=0.03)
            pl.decimate_to(blob, 40); ml.box_uv(blob, 0.1)
            blob.data.materials.append(mats['Grape']); parts.append(blob)
        fill = ml.metaballs('Fill', [FILL], resolution=0.02)
        pl.decimate_to(fill, (60, 30, 0)[k] or 20); ml.box_uv(fill, 0.2)
        fill.data.materials.append(mats['Wood']); parts.append(fill)
        if k < 2:
            for i, (at, normal, size, spin) in enumerate(LEAVES):
                parts.append(leaf(f'L{i}', at, normal, size, spin, mats['Leaves']))
        lod = pl.join('Fruitbowl' if k == 0 else f'Fruitbowl_LOD{k}', parts)
        ml.smooth(lod)
        ml.colour(lod, distance=0.06, strength=0.7, power=1.2)
        levels.append(lod)
    for o in sources.values():
        bpy.data.objects.remove(o)
    ml.ground(levels)
    for o in levels:
        ml.apply_transforms(o)
    print('LODS', [pl.triangles(o) for o in levels])
    ml.export(levels, 'fruitbowl')


main()
