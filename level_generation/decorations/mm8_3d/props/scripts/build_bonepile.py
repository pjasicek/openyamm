"""Skull and bones pile `dec29` -> work/bonepile_export.glb (LOD0..2).

Real bones from the bone kit (bonekit.py: the MM6 skeleton creature's pieces): a flat, wide heap of crossed long bones
(femurs, tibias, humeri, forearm bones, clavicles, no pelvis or vertebrae, whose source pieces are dark
faceted lumps) dropped one after another onto the ground and
each other, the skull with its teeth sitting upright on top facing the viewer, the jaw lying apart in front. Each LOD
decimates every bone on its own; far levels drop the teeth and vertebrae. Texture bonepile_* (make_textures.py:
the skeleton atlas graded to dec29's greyer ivory). Usage: blender --background --python build_bonepile.py --
[--preview]"""
import os
import sys

import bpy
import numpy as np
from mathutils import Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mm8lib as ml  # noqa: E402
import bonekit as bk  # noqa: E402

pl = ml.pl
# (joint, rank, (x, y) centre, yaw, roll about the long axis) in heap order (first placed lowest)
HEAP = [   # rev 2: denser and flatter, the bones mostly lying flat and crossing under and around the skull
    ('LeftUpLeg', 0, (-0.03, 0.05), 6, 0),
    ('RightUpLeg', 0, (0.04, -0.01), -10, 90),
    ('RightLeg', 0, (0.06, 0.08), 3, 30),
    ('LeftLeg', 0, (-0.07, -0.02), 16, 0),
    ('LeftLeg', 1, (0.02, 0.12), -24, 60),
    ('LeftArm', 0, (0.11, -0.06), -14, 45),
    ('RightArm', 0, (-0.12, 0.07), -24, 0),
    ('LeftForeArm', 0, (-0.01, -0.09), 28, 0),
    ('LeftForeArm', 1, (0.16, -0.02), 64, 20),
    ('RightForeArm', 0, (0.15, 0.06), 18, 0),
    ('RightForeArm', 1, (-0.04, 0.12), -55, 0),
    ('LeftShoulder', 0, (-0.18, -0.07), 15, 0),
    ('RightShoulder', 0, (0.21, 0.02), -30, 0),
]
SKULL = {'centre': (-0.03, -0.02), 'yaw': 15, 'tilt': (-6, 3), 'sink': 0.05, 'scale': 1.4}
JAW = {'centre': (0.12, -0.15), 'yaw': -35, 'tilt': (0, 0)}
THICK = 1.35
BASE = 3                       # bones under the skull
SPREAD = 1.5                   # the heap's width about the skull (sprite 112 x 60)
LEVELS = [(2490, 10, 0.0), (1100, 8, 0.02), (480, 6, 0.06)]


def build(kit):
    """BASE bones lie on the ground, the skull rests on them, the rest of the heap is dropped round it onto the bones
    only (bones passing under the skull's rim tuck beneath it rather than climbing over the cranium)."""
    parts = []
    skull = None
    for k, (bone, rank, (x, y), yaw, roll) in enumerate(HEAP):
        if k == BASE:
            skull = kit.place(kit.ids('Head'), 'Skull', align=False)
            bk.transform(skull, scale=SKULL['scale'])
            bk.transform(skull, (SKULL['tilt'][0], SKULL['tilt'][1], SKULL['yaw']), (*SKULL['centre'], 0.5))
            bk.drop(skull, parts, sink=SKULL['sink'])
        x *= SPREAD
        b = kit.place([kit.find(bone, rank)], f'B{k}')
        b.data.transform(Matrix.Diagonal((1.0, THICK, THICK, 1.0)))     # aligned: the long axis is x
        bk.round_ends(b)
        bk.transform(b, (roll, 0, 0))
        bk.transform(b, (0, 0, yaw), (x, y, 0.3))
        bk.drop(b, parts if y > -0.04 else [], sink=0.012)      # bones in front stay low: the face shows
        parts.append(b)
    jaw = kit.place(kit.ids('Jaw'), 'Jaw', align=False)
    bk.transform(jaw, scale=SKULL['scale'])
    bk.transform(jaw, (JAW['tilt'][0], JAW['tilt'][1], JAW['yaw']), (*JAW['centre'], 0.3))
    bk.drop(jaw, parts, sink=0.004)
    return ml.pl.join('Bonepile', parts + [skull, jaw])


def long_bone(part):
    co = np.array([v.co[:] for v in part.data.vertices])
    return pl.triangles(part) <= 160 and np.ptp(co, 0).max() > 0.15


def main():
    pl.reset()
    kit = bk.Kit()
    pile = build(kit)
    ml.ground([pile]); ml.centre_xy([pile]); ml.apply_transforms(pile)
    mat = ml.material('Bone', 'bonepile', extras={'openyamm_specular': 0.35})
    pile.data.materials.clear(); pile.data.materials.append(mat)
    lo, hi = pl.bounds([pile])
    print('PILE tris', pl.triangles(pile), 'size', [round(v, 3) for v in hi - lo])
    if '--preview' in sys.argv:
        pl.setup_render((768, 512))
        out = os.path.join(ml.HERE, 'review', 'bonepile')
        for tag, view in (('front', (0, 25)), ('top', (0, 85)), ('side', (90, 10)), ('tq', (40, 30))):
            pl.render_views([pile], out, 'pose_' + tag, views=(view,))
        return
    pile.name = 'Source'
    levels = []
    for k, (target, minimum, drop) in enumerate(LEVELS):
        name = 'Bonepile' if k == 0 else f'Bonepile_LOD{k}'
        lod = ml.duplicate(pile, name)
        if drop:
            label, count = ml.loose_labels(lod)
            co = np.array([v.co[:] for v in lod.data.vertices])
            small = np.array([np.linalg.norm(np.ptp(co[label == p], 0)) < drop for p in range(count)])
            ml.delete_verts(lod, small[label])
        lod = ml.decimate_pieces(lod, target, minimum, keep=long_bone if k == 0 else None)
        lod.name = name
        ml.smooth(lod)
        ml.colour(lod, distance=0.06, strength=0.6, power=1.0)       # occlusion only in the crevices
        levels.append(lod)
    bpy.data.objects.remove(pile)
    print('LODS', [pl.triangles(o) for o in levels])
    ml.export(levels, 'bonepile')


main()
