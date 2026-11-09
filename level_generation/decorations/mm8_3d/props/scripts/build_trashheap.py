"""Trash heap `dec23` (MM7 `7dec01`) -> work/trashheap_export.glb, installed as mm7_deco_trash_heap.glb.

A dome-shaped heap (the sprite: 128 wide, 101 tall, round top) of curled red-brown bark flakes and shards over a
mossy green-grey core showing through the gaps at the bottom. Core: a noise-lumped metaball dome (trash_core, CC0
brown_mud_leaves_01). Flakes: bent, curled cards scattered over the dome on a seeded spiral, leaning down the slope
with jittered sizes and twists (trash_bark, CC0 pine_bark; double-sided because both faces show). Far levels use
fewer, larger flakes. Usage: blender --background --python build_trashheap.py"""
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mm8lib as ml  # noqa: E402

pl = ml.pl
W, HGT = 0.64, 0.95        # dome half width and height (sprite 128 x 101 units)
LEVELS = [{'flakes': 230, 'grid': 2, 'core': 700, 'size': 1.0}, {'flakes': 110, 'grid': 1, 'core': 300, 'size': 1.35},
          {'flakes': 45, 'grid': 1, 'core': 120, 'size': 1.9}]


def dome_point(theta, phi):
    """Point and outward normal on the dome (phi 0 = top, pi/2 = ground rim)."""
    r = W * math.sin(phi) * (1.0 + 0.04 * math.sin(phi * 5))
    z = HGT * math.cos(phi) ** 0.85
    p = Vector((r * math.cos(theta), r * math.sin(theta), z))
    n = Vector((p.x / W ** 2, p.y / W ** 2, p.z / HGT ** 2)).normalized()
    return p, n


def flakes(count, grid, size, rng, tree):
    bm = bmesh.new(); uv = bm.loops.layers.uv.new('UVMap')
    golden = math.pi * (3 - math.sqrt(5))
    for k in range(count):
        t = (k + 0.5) / count
        phi = math.acos(1 - t * 1.02) if t < 0.98 else math.pi / 2
        phi = min(phi * 1.02, math.pi / 2 * 0.98)
        theta = k * golden + rng.uniform(-0.2, 0.2)
        p, n = dome_point(theta, phi)
        hit = tree.ray_cast(p + n * 0.6, -n, 2.0)            # onto the core's lumpy surface
        if hit[0] is not None:
            p, n = hit[0], hit[1]
        if p.z < 0.3 and rng.random() < 0.4 + 0.5 * (0.3 - p.z) / 0.3:                 # gaps low down: the green core shows through
            continue
        down = (Vector((0, 0, -1)) - n * -n.z).normalized() if abs(n.z) < 0.999 else Vector((1, 0, 0))
        side = n.cross(down).normalized()
        ang = rng.uniform(-0.6, 0.6)
        down, side = (down * math.cos(ang) + side * math.sin(ang)), (side * math.cos(ang) - down * math.sin(ang))
        length = rng.uniform(0.13, 0.24) * size; width = rng.uniform(0.12, 0.23) * size
        lift = rng.uniform(0.0, 0.04)                          # shingled: the upper edge lifts a little
        curl = rng.uniform(0.01, 0.04) * size
        u0, v0 = rng.uniform(0, 0.75), rng.uniform(0, 0.75)
        rows = []
        for i in range(grid + 1):
            fv = i / grid
            row = []
            for j in range(grid + 1):
                fu = j / grid - 0.5
                q = p + down * (fv - 0.3) * length + side * fu * width * (1 - 0.35 * fv)
                q += n * (0.012 + lift * (1 - fv) + curl * (1 - 4 * fu * fu))
                q.z = max(q.z, 0.004)                         # flakes at the rim rest on the ground
                row.append((bm.verts.new(q), (u0 + 0.25 * (fu + 0.5), v0 + 0.25 * fv)))
            rows.append(row)
        for i in range(grid):
            for j in range(grid):
                corners = (rows[i][j], rows[i][j + 1], rows[i + 1][j + 1], rows[i + 1][j])
                f = bm.faces.new([c[0] for c in corners])
                for loop, c in zip(f.loops, corners):
                    loop[uv].uv = c[1]
    bmesh.ops.triangulate(bm, faces=list(bm.faces))
    me = bpy.data.meshes.new('Flakes'); bm.to_mesh(me); bm.free()
    obj = bpy.data.objects.new('Flakes', me); bpy.context.scene.collection.objects.link(obj)
    for f in me.polygons:
        f.use_smooth = True
    return obj


def main():
    pl.reset()
    bark = ml.material('Bark', 'trash_bark', extras={'openyamm_specular': 0.3})
    core_mat = ml.material('Core', 'trash_core', extras={'openyamm_specular': 0.2})
    core_src = ml.metaballs('CoreSrc', [('ellipsoid', (0, 0, 0.0), 1.0, (W, W, HGT))], resolution=0.03,
                            threshold=0.5)
    lo, hi = pl.bounds([core_src])
    core_src.data.transform(Matrix.Diagonal((W / hi.x, W / hi.x, HGT / hi.z, 1.0)))
    ml.displace(core_src, 0.06, 0.16, 3)
    ml.displace(core_src, 0.025, 0.05, 4)
    ml.delete_verts(core_src, np.array([v.co.z < -0.01 for v in core_src.data.vertices]))
    from mathutils.bvhtree import BVHTree
    tree = BVHTree.FromObject(core_src, bpy.context.evaluated_depsgraph_get())
    levels = []
    for k, lv in enumerate(LEVELS):
        rng = np.random.default_rng(23)
        core = ml.duplicate(core_src, 'Core')
        pl.decimate_to(core, lv['core'])
        ml.box_uv(core, 0.5)
        core.data.materials.append(core_mat)
        fl = flakes(lv['flakes'], lv['grid'], lv['size'], rng, tree)
        fl.data.materials.append(bark)
        lod = pl.join('Trashheap' if k == 0 else f'Trashheap_LOD{k}', [core, fl])
        ml.smooth(lod)
        ml.colour(lod, distance=0.2, strength=0.85, power=1.6)
        levels.append(lod)
    bpy.data.objects.remove(core_src)
    ml.ground(levels)
    for o in levels:
        ml.apply_transforms(o)
    print('LODS', [pl.triangles(o) for o in levels])
    ml.export(levels, 'trashheap')


main()
