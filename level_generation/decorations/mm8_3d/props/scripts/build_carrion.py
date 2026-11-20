"""Carrion `dec22` (a heap of bloody meat, Ironsand Desert) -> work/carrion_export.glb (LOD0..2).

A heap of glistening meat slabs (separate noise-lumped metaball chunks, so the slabs read apart), a rack of ribs
fanning out at the left, long bones sticking out of the heap (one up to the right, one across the top, bone ends at
the right) and a scrap of grey hide. Bones from the bone kit (bonekit.py: the MM6 skeleton creature's real bones,
read only); textures meat, hide and bonepile (make_textures.py). Usage: blender --background --python
build_carrion.py -- [--preview]"""
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Matrix, Quaternion, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mm8lib as ml  # noqa: E402
import bonekit as bk  # noqa: E402

pl = ml.pl
V = Vector


def q(axis, degrees):
    return tuple(Quaternion(axis, math.radians(degrees)))


# meat slabs: centre, radius, (sx, sy, sz), rotation
CHUNKS = [   # rev 2: fewer, flatter slabs with sliced, torn tops (centre, radius, (sx, sy, sz), rotation, cut)
    ((0.0, 0.08, 0.15), 0.40, (1.5, 1.0, 0.55), q((0, 1, 0), 4), 0.8),
    ((-0.44, -0.06, 0.15), 0.30, (1.25, 0.9, 0.6), q((0, 1, 0), 24), 0.75),
    ((0.46, 0.0, 0.14), 0.30, (1.35, 0.9, 0.55), q((0, 1, 0), -14), 0.78),
    ((-0.06, -0.02, 0.44), 0.30, (1.4, 0.8, 0.55), q((0, 1, 0), -18), 0.8),
    ((0.3, -0.14, 0.56), 0.22, (1.35, 0.75, 0.6), q((0, 1, 0), 30), 0.85),
    ((-0.32, 0.1, 0.42), 0.2, (1.2, 0.8, 0.6), q((0, 1, 0), 40), 0.82),
]
BONES = [  # kit piece, start, end, thickness
    (('LeftUpLeg', 0), (0.22, 0.02, 0.42), (0.62, 0.06, 0.88), 1.6),
    (('RightArm', 0), (-0.62, -0.1, 0.5), (-0.1, -0.12, 0.62), 1.5),
    (('RightLeg', 0), (0.2, -0.22, 0.24), (0.72, -0.14, 0.34), 1.6),
    (('LeftArm', 0), (0.35, -0.05, 0.08), (0.78, 0.0, 0.18), 1.5),
    (('RightUpLeg', 0), (-0.3, -0.24, 0.12), (-0.68, -0.3, 0.1), 1.6),
]
# dec22's meat is a deeper, more saturated red than dec21's (red pixels 129, 47, 14; median 119, 27, 2)
MEAT_TINT = (1.0, 0.78, 0.25)
LEVELS = [(1500, 2200, 120), (700, 1000, 60), (300, 340, 30)]      # bones, meat, hide triangles


def build(kit):
    parts = []
    for (bone, rank), a, b, thick in BONES:
        parts.append(bk.along(kit, [kit.find(bone, rank)], a, b, thick * 1.4))
    # half a ribcage, fanning out at the left of the heap
    cage = kit.place([kit.find('Spine2', 0)], 'Rack', align=False)
    co = np.array([v.co[:] for v in cage.data.vertices])
    ml.delete_verts(cage, co[:, 0] > 0.01)                                   # keep one side's ribs
    cage.data.transform(Matrix.Translation((-0.48, 0.04, 0.3)) @ Matrix.Rotation(math.radians(-70), 4, 'Y')
                        @ Matrix.Rotation(math.radians(90), 4, 'Z') @ Matrix.Diagonal((1.4, 1.4, 1.4, 1)))
    parts.append(cage)
    bones = pl.join('Bones', parts)
    slabs = []
    for k, (centre, radius, size, rotation, cut) in enumerate(CHUNKS):
        slab = ml.metaballs(f'Slab{k}', [('ellipsoid', centre, radius * 1.25, size, rotation)], resolution=0.016,
                            threshold=0.4)
        ml.displace(slab, 0.03, 0.14, k + 3)
        ml.displace(slab, 0.01, 0.045, k + 13)
        ml.slice_top(slab, cut, seed=k, tilt=0.25)
        slabs.append(slab)
    meat = pl.join('Meat', slabs)
    hide = ml.metaballs('Hide', [('ellipsoid', (-0.15, -0.2, 0.3), 0.15, (1.4, 0.35, 0.9), q((0, 0, 1), -10))],
                        resolution=0.014, threshold=0.4)
    ml.displace(hide, 0.01, 0.05, 9)
    print('BURIED bones dropped', ml.drop_hidden_pieces(bones, [meat, hide]))
    return bones, meat, hide


def main():
    pl.reset()
    kit = bk.Kit()
    mats = (ml.material('Bone', 'bonepile', extras={'openyamm_specular': 0.4}),
            ml.material('Meat', 'meat', extras={'openyamm_specular': 0.4}),
            ml.material('Hide', 'hide', extras={'openyamm_specular': 0.3}))
    parts = build(kit)
    ml.ground(list(parts)); ml.centre_xy(list(parts))
    for o, mat in zip(parts, mats):
        ml.apply_transforms(o)
        o.data.materials.clear(); o.data.materials.append(mat)
    lo, hi = pl.bounds(list(parts))
    print('PARTS tris', [pl.triangles(o) for o in parts], 'size', [round(v, 3) for v in hi - lo])
    if '--preview' in sys.argv:
        for o in parts[1:]:
            pl.decimate_to(o, 4000); ml.box_uv(o, 0.25)
        pl.setup_render((768, 512))
        out = os.path.join(ml.HERE, 'review', 'carrion')
        for tag, view in (('front', (0, 22)), ('top', (0, 85)), ('side', (90, 10)), ('tq', (40, 30))):
            pl.render_views(list(parts), out, 'pose_' + tag, views=(view,))
        return
    for o in parts:
        o.name = 'Src' + o.name
    levels = []
    for k, (nb, nm, ns) in enumerate(LEVELS):
        name = 'Carrion' if k == 0 else f'Carrion_LOD{k}'
        b = ml.decimate_pieces(ml.duplicate(parts[0], name + 'B'), nb, 8 if k < 2 else 5)
        m = ml.duplicate(parts[1], name + 'M'); pl.decimate_to(m, nm)
        s = ml.duplicate(parts[2], name + 'S'); pl.decimate_to(s, ns)
        ml.box_uv(m, 0.22); ml.box_uv(s, 0.2)
        for o in (b, m, s):
            ml.smooth(o)
        lod = pl.join(name, [b, m, s])
        ml.colour(lod, distance=0.15, strength=0.85, power=1.3)
        ml.tint_material(lod, 'Meat', MEAT_TINT)
        levels.append(lod)
    for o in parts:
        bpy.data.objects.remove(o)
    print('LODS', [pl.triangles(o) for o in levels])
    ml.export(levels, 'carrion')


main()
