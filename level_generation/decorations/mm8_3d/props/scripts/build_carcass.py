"""Half-eaten animal carcass `dec21` ("bones", Ironsand Desert) -> work/carcass_export.glb (LOD0..2).

The sprite paints a large animal (long ribcage, hoof-like leg ends, grey hide on the rump) lying on its side: the
head with its jaw at the left, the bare ribcage in the middle with meat behind the ribs, the shoulder and rump
masses with grey hide patches, one foreleg raised with its lower bone bare, a hind stump raised at the right, the
other legs lying low with bare bone ends. Bones come from the bone kit (bonekit.py: the MM6 skeleton creature's
real bones, read only): the ribcage stretched along the spine into an animal's long chest, long bones placed along
the legs, the jaw lengthened into a muzzle. Flesh is a metaball body (noise-lumped, decimated, box mapped with the
procedural `meat` texture), hide patches likewise with `hide`; bones buried in flesh are dropped.
Usage: blender --background --python build_carcass.py -- [--preview]"""
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mm8lib as ml  # noqa: E402
import bonekit as bk  # noqa: E402

pl = ml.pl
V = Vector
# Body plan (metres; x right, y away from the viewer, z up). The spine runs along x behind the ribs.
RIBCAGE = {'centre': V((0.15, 0.04, 0.34)), 'scale': (2.6, 3.5, 1.4)}   # along spine, height, depth
RIB_SHEAR = 0.5
SHOULDER = V((-0.4, 0.1, 0.27))
RUMP = V((0.7, 0.1, 0.3))
HEAD = V((-0.88, -0.05, 0.12))
# legs: (bone kit pieces, start, end, flesh radius, flesh fraction from the start)
LEGS = [
    ([('LeftArm', 0), ('LeftForeArm', 0)], SHOULDER + V((0.05, -0.08, 0.08)), V((-0.08, -0.12, 0.92)), 0.08, 0.45),
    ([('RightArm', 0), ('RightForeArm', 0)], SHOULDER + V((0.0, -0.05, -0.08)), V((-0.72, -0.28, 0.06)), 0.085, 0.4),
    ([('LeftUpLeg', 0)], RUMP + V((0.05, -0.05, 0.12)), V((0.86, -0.12, 0.62)), 0.1, 0.55),
    ([('RightUpLeg', 0), ('RightLeg', 0)], RUMP + V((-0.05, -0.08, -0.05)), V((-0.02, -0.38, 0.05)), 0.09, 0.5),
]
# the sprite's meat is an orange brown-red (red pixels 125, 59, 26); the lit texture reads pinker without this
MEAT_TINT = (1.0, 0.85, 0.3)
LEVELS = [(1800, 1300, 250), (850, 600, 110), (330, 220, 45)]     # bones, flesh, hide triangles


def bones_and_flesh(kit):
    parts = []
    # ribcage in side view: rest up (z) -> -x (head to the left), rest left (x) -> -y (toward the viewer), rest
    # back (+y) -> +z (spine on top, ribs hanging down to the belly on the ground)
    cage = kit.place([kit.find('Spine2', 0)], 'Cage', align=False)
    cage.data.transform(Matrix(((0, 0, -1, 0), (-1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 0, 1))))
    sx, sz, sy = RIBCAGE['scale']
    cage.data.transform(Matrix.Diagonal((sx, sy, sz, 1.0)))
    # human ribs slope down from the spine toward the head's side; the sprite's animal ribs hang straight
    for v in cage.data.vertices:
        v.co.x += RIB_SHEAR * v.co.z
    cage.data.transform(Matrix.Translation(RIBCAGE['centre']))
    parts.append(cage)
    co = np.array([v.co[:] for v in cage.data.vertices])
    lo, hi = co.min(0), co.max(0)
    # vertebrae along the back, behind the ribs
    for k, (bone, rank) in enumerate((('Spine', 0), ('Spine', 1), ('Spine1', 0), ('Spine1', 1), ('Neck', 0))):
        x = lo[0] - 0.08 + k * (hi[0] - lo[0] + 0.16) / 4
        v = kit.place([kit.find(bone, rank)], f'V{k}', align=False)
        v.data.transform(Matrix.Translation((x, RIBCAGE['centre'].y, hi[2] - 0.03)) @ Matrix.Diagonal((1.4, 1.4, 1.4, 1)))
        parts.append(v)
    for k, (pieces, a, b, _, _) in enumerate(LEGS):
        n = len(pieces)
        for i, (bone, rank) in enumerate(pieces):
            pa, pb = a.lerp(b, i / n), a.lerp(b, (i + 1) / n)
            parts.append(bk.along(kit, [kit.find(bone, rank)], pa, pb, 2.2, f'L{k}{i}'))
    jaw = kit.place(kit.ids('Jaw'), 'Jaw', align=False)        # rest: opening backward (+y), teeth up
    jaw.data.transform(Matrix.Diagonal((1.2, 2.2, 1.0, 1.0)))   # lengthened into a muzzle
    jaw.data.transform(Matrix.Translation(HEAD + V((0.02, -0.08, -0.04))) @ Matrix.Rotation(math.radians(-80), 4, 'Z'))
    parts.append(jaw)
    bones = pl.join('Bones', parts)
    centre = (V(lo) + V(hi)) / 2
    flesh = [
        ('ellipsoid', V((centre.x, centre.y + 0.06, centre.z + 0.02)), 0.3, (1.5, 0.55, 1.15)),   # meat inside the ribs
        ('ellipsoid', SHOULDER, 0.34, (1.05, 0.8, 0.9)),
        ('ellipsoid', RUMP, 0.38, (0.95, 0.85, 0.9)),
        ('capsule', SHOULDER, HEAD + V((0.12, 0.02, 0.05)), 0.17),                               # neck
        ('ellipsoid', HEAD + V((0.08, 0.02, 0.06)), 0.18, (1.3, 0.75, 0.75)),
    ]
    for pieces, a, b, radius, share in LEGS:
        flesh.append(('capsule', a, a.lerp(b, share), radius * 1.4))
    hide = [
        ('ellipsoid', RUMP + V((0.08, -0.12, 0.06)), 0.24, (1.0, 0.6, 0.8)),
        ('ellipsoid', SHOULDER + V((0.02, -0.1, 0.12)), 0.17, (1.0, 0.6, 0.7)),
        ('ellipsoid', HEAD + V((-0.02, 0.0, 0.08)), 0.15, (1.2, 0.8, 0.7)),
    ]
    meat = ml.metaballs('Flesh', flesh, resolution=0.014, threshold=0.4)
    skin = ml.metaballs('Hide', hide, resolution=0.014, threshold=0.4)
    ml.displace(meat, 0.035, 0.16, 1)             # torn, uneven masses (rev 2)
    ml.displace(meat, 0.012, 0.05, 4)
    ml.slice_top(meat, 0.86, seed=5)
    ml.displace(skin, 0.01, 0.06, 2)
    print('BURIED bones dropped', ml.drop_hidden_pieces(bones, [meat, skin]))
    return bones, meat, skin


def main():
    pl.reset()
    kit = bk.Kit()
    bone_mat = ml.material('Bone', 'bonepile', extras={'openyamm_specular': 0.4})
    meat_mat = ml.material('Meat', 'meat', extras={'openyamm_specular': 0.4})
    skin_mat = ml.material('Hide', 'hide', extras={'openyamm_specular': 0.3})
    bones, meat, skin = bones_and_flesh(kit)
    parts = (bones, meat, skin)
    lo, hi = pl.bounds(list(parts))
    offset = V((-(lo.x + hi.x) / 2, -(lo.y + hi.y) / 2, -lo.z))
    for o, mat in zip(parts, (bone_mat, meat_mat, skin_mat)):
        o.data.transform(Matrix.Translation(offset))
        o.data.materials.clear(); o.data.materials.append(mat)
    print('PARTS tris', [pl.triangles(o) for o in parts], 'size', [round(v, 3) for v in hi - lo])
    if '--preview' in sys.argv:
        for o in (meat, skin):
            pl.decimate_to(o, 3000); ml.box_uv(o, 0.25)
        pl.setup_render((768, 512))
        out = os.path.join(ml.HERE, 'review', 'carcass')
        for tag, view in (('front', (0, 22)), ('top', (0, 85)), ('side', (90, 10)), ('tq', (40, 30))):
            pl.render_views(list(parts), out, 'pose_' + tag, views=(view,))
        return
    for o in parts:
        o.name = 'Src' + o.name
    levels = []
    for k, (nb, nm, ns) in enumerate(LEVELS):
        name = 'Carcass' if k == 0 else f'Carcass_LOD{k}'
        b = ml.decimate_pieces(ml.duplicate(bones, name + 'B'), nb, 8 if k < 2 else 5)
        m = ml.duplicate(meat, name + 'M'); pl.decimate_to(m, nm)
        s = ml.duplicate(skin, name + 'S'); pl.decimate_to(s, ns)
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
    ml.export(levels, 'carcass')


main()
