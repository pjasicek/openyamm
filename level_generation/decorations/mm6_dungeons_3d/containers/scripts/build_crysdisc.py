"""MM6 Crystal Disk `crysdisc`: a flat disc 40 units across lying on the floor: a thin rounded violet-grey metal rim
(`pewter`) with a raised lip, holding a dark violet crystal (`crystal`: faint angular facet lines) cut into a low,
flat-shaded faceted dome (the convex hull of turned facet rings) that rises a little above the lip. The sprite
(40 x 15) is a high view of this flat object, so the model is built to its true shape (6.2 units high) and bound by
width (see README.md). COLOR_0: occlusion x tints to the sprite's rim (84, 74, 100; its bright rim pixels are
reflections) and crystal (44, 36, 56; the dark pixels, nudged violet) colours. Writes work/crysdisc_export.glb.
Usage: blender --background --python build_crysdisc.py"""
import math
import os
import sys

import bmesh

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import containers_lib as cl  # noqa: E402

pl = cl.pl
u = cl.u
R = u(20)

pl.reset()
mats = {'Rim': cl.material('Rim', 'pewter'), 'Crystal': cl.material('Crystal', 'crystal')}
RIM = [(u(17.5), 0.0), (u(19.4), u(0.6)), (u(20.0), u(1.7)), (u(19.8), u(2.7)), (u(19.2), u(3.3)),
       (u(18.6), u(3.2)), (u(18.2), u(2.6))]


def crystal(level):
    """Faceted dome: the convex hull of facet rings (each turned half a facet against the one below) and an apex a
    little off centre, without its underside."""
    rings = ((u(18.4), u(2.4), 16), (u(12.5), u(4.4), 12), (u(6.0), u(5.6), 8))
    if level == 1:
        rings = ((u(18.4), u(2.4), 12), (u(10.0), u(4.9), 8))
    if level == 2:
        rings = ((u(18.4), u(2.4), 8), (u(8.0), u(5.0), 5))
    bm = bmesh.new()
    uv = bm.loops.layers.uv.verify()
    for k, (r, z, n) in enumerate(rings):
        for s in range(n):
            a = 2 * math.pi * (s + 0.5 * k) / n
            bm.verts.new((r * math.cos(a), r * math.sin(a), z))
    bm.verts.new((u(0.8), u(-0.5), u(6.2)))
    bmesh.ops.convex_hull(bm, input=bm.verts)
    bm.normal_update()
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.normal.z < -0.5], context='FACES')
    for face in bm.faces:
        for loop in face.loops:
            loop[uv].uv = (loop.vert.co.x / (2 * R) + 0.5, loop.vert.co.y / (2 * R) + 0.5)
    return pl.to_object('crystal', bm, mats['Crystal'], smooth=False)


def build(level):
    sides = (32, 16, 12)[level]
    profile = RIM if level < 2 else [RIM[i] for i in (0, 2, 4, 6)]
    parts = [pl.lathe('rim', profile, sides, mats['Rim'], u_repeat=4, v_scale=1.0 / u(6), cap_bottom=True),
             crystal(level)]
    return pl.join(f'disc{level}', parts)


lods = [build(level) for level in range(3)]
tints = {'Rim': cl.tint_for(mats['Rim'], (84, 74, 100)), 'Crystal': cl.tint_for(mats['Crystal'], (44, 36, 56))}
print('TINTS', tints, 'height units', round(max(v.co.z for v in lods[0].data.vertices) * cl.dl.UNITS_PER_METRE, 2))
cl.finish('CrystalDisk', lods, tints, {'rays': 32, 'distance': u(6), 'strength': 0.5}, prop='crysdisc')
