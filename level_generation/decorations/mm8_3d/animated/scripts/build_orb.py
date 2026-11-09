"""Plane of Air path marker orb `dec57` (428 placements in elema, one 122 x 122 native frame at DSFT scale 0.5:
61 x 61 units, light 96): a glass ball of swirling silver clouds. The sphere (radius 30.5 units) carries the
procedural `orb` cloud texture (the native ball's luminance ramp, dark grey 56 to white 249), lit and glossy (sky
reflections like glass), darkened toward its silhouette (`openyamm_edge_darkening`, the native ball's dark rim),
self-lit by a faint grey-white emission that breathes (`openyamm_pulse`), and the clouds drift round the ball
(`openyamm_uv_scroll`, one turn in 40 s). A camera-facing blended halo card (1.3 x the radius, `orbhalo`: half
opaque at the silhouette, gone at the card edge, pulsing in the same period) glows round it; the sphere hides its
inside. The halo card is the model's bounds, so the sphere's centre is at 1.3 R above the base.
Writes work/orb_export.glb. Usage: blender --background --python build_orb.py"""
import math
import os
import sys

import bmesh

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as al  # noqa: E402

pl, u = al.pl, al.u
pl.reset()
R = 30.5
HALO = 1.3
CENTRE = R * HALO
PULSE = [0.3, 3.2]
mats = {
    'Orb': al.set_emission(al.material('Orb', 'orb', extras={
        'openyamm_uv_scroll': [0.025, 0.0], 'openyamm_pulse': PULSE, 'openyamm_edge_darkening': 0.3,
        'openyamm_specular': 1.0}), (64, 64, 70)),
    # Additive (2026-10-16): the halo adds a silver glow to the sky round the ball; the slow sine pulse stays.
    'Halo': al.material('Halo', 'orbhalo', alpha=True, extras={
        'openyamm_billboard': True, 'openyamm_specular': 0.0, 'openyamm_pulse': PULSE, 'openyamm_additive': True,
        'openyamm_unlit_review': True}),
}
al.set_emission(mats['Halo'], (40, 42, 48))


def sphere(segments, rings):
    """UV sphere: u around (one texture turn), v pole to pole; pole fans keep the triangle count low."""
    bm = bmesh.new()
    uv = bm.loops.layers.uv.verify()
    grid = []
    for i in range(rings + 1):
        theta = math.pi * i / rings
        row = []
        for j in range(segments + 1):
            phi = 2 * math.pi * j / segments
            row.append(bm.verts.new((u(R * math.sin(theta) * math.cos(phi)), u(R * math.sin(theta) * math.sin(phi)),
                                     u(CENTRE + R * math.cos(theta)))))
        grid.append(row)
    for i in range(rings):
        for j in range(segments):
            corners = [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]
            if i == 0:
                corners = [(0, j), (1, j), (1, j + 1)]
            elif i == rings - 1:
                corners = [(i, j), (i + 1, j), (i, j + 1)]
            face = bm.faces.new([grid[a][b] for a, b in corners])
            for loop, (a, b) in zip(face.loops, corners):
                uu = (b + 0.5) / segments if a in (0, rings) else b / segments
                loop[uv].uv = (uu, 1 - a / rings)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-7)
    return pl.to_object('orb', bm, mats['Orb'])


def build(level):
    segments, rings = ((16, 7), (10, 5), (6, 4))[level]
    return [], [sphere(segments, rings), al.halo_card('halo', mats['Halo'], CENTRE, R * HALO)]


COLOURS = {'Halo': (176, 182, 200)}
al.build_lods('Orb', 'orb', build, COLOURS)
