"""Red glass goblet `dec35` (MM7 `7dec48`) -> work/goblet_export.glb, installed as mm7_deco_goblet.glb.

A cut-glass goblet traced from the sprite (13 x 30 units): a tall straight-sided faceted cup, a short stem with a
knob, a wide flat foot. One faceted lathe per level (10 / 8 / 6 facets, flat shaded, so the cut faces catch light
like the sprite's glass), with an open cup (inner wall and floor). Material Glass: the `goblet` texture (deep red with
pale streaks across the facets), glossy and opaque (no blending, so no sorting issues).
Usage: blender --background --python build_goblet.py"""
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mm8lib as ml  # noqa: E402

pl = ml.pl
H = 0.3                       # model height (the binding scales it to 30 units)
FULL = [(0.0, 0.0), (0.215, 0.0), (0.215, 0.035), (0.12, 0.07), (0.06, 0.12), (0.055, 0.24), (0.085, 0.28),
        (0.06, 0.33), (0.09, 0.38), (0.19, 0.44), (0.215, 0.62), (0.22, 1.0), (0.19, 1.0), (0.175, 0.62),
        (0.15, 0.48), (0.0, 0.47)]
MID = [(0.0, 0.0), (0.2, 0.0), (0.1, 0.06), (0.045, 0.11), (0.045, 0.33), (0.19, 0.44), (0.22, 1.0), (0.19, 1.0),
       (0.15, 0.48), (0.0, 0.47)]
FAR = [(0.0, 0.0), (0.2, 0.0), (0.05, 0.1), (0.05, 0.35), (0.2, 0.45), (0.22, 1.0), (0.0, 0.85)]
LEVELS = [(FULL, 10), (MID, 8), (FAR, 6)]


def main():
    pl.reset()
    glass = ml.material('Glass', 'goblet', extras={'openyamm_specular': 0.5})
    for node in glass.node_tree.nodes:
        if node.type == 'BSDF_PRINCIPLED':
            node.inputs['Roughness'].default_value = 0.15
    levels = []
    for k, (profile, segments) in enumerate(LEVELS):
        obj = pl.lathe('Goblet' if k == 0 else f'Goblet_LOD{k}', [(r * H, z * H) for r, z in profile], segments,
                       glass, u_repeat=1.0, v_scale=1.0 / H, smooth=False)
        ml.triangulate(obj)
        ml.colour(obj, rays=16, distance=0.05, strength=0.5)
        levels.append(obj)
    print('LODS', [pl.triangles(o) for o in levels])
    ml.export(levels, 'goblet')


main()
