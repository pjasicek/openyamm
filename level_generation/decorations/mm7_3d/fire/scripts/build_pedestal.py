"""Magic pedestals dec64-dec75: one golden pedestal (a flared skirt ringed with curled claws, a notched plinth band,
a plain shaft, a capital with hanging tabs and a notched cup) holding a glowing glass orb, traced from the restored
native frames (x2 pixels at 0.8 units). The orb is neutral here (pale clouded glass with swirls, a placeholder
emission); finish.py writes one GLB per orb colour by setting the Orb material's baseColorFactor and emissiveFactor,
so all twelve share geometry and textures. Orb: openyamm_uv_scroll turns its swirls slowly, openyamm_pulse breathes
its glow. A faint additive halo card behind the orb, centred a little below it (its top at the orb's top, so the bounds
stay 201), takes the orb colour from finish.py too. Writes work/pedestal_export.glb.
Usage: blender --background --python build_pedestal.py"""
import math
import os
import sys

import bmesh
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import firelib as fl  # noqa: E402

pl = fl.pl
pl.reset()
gold = fl.material('Gold', 'gold', extras={'openyamm_specular': 0.8})
orb = fl.glow_material('Orb', 'orb', (110, 110, 110), pulse=(0.3, 2.0),
                       extras={'openyamm_uv_scroll': [0.02, 0.0]})
halo = fl.halo_material('Halo')

PROFILE = [
    (0, 0), (30, 0), (36, 2), (40, 5.5), (41, 8.5), (39.5, 11.5), (36, 14.5), (32, 17), (29.5, 19.5), (28.5, 21),
    (28.5, 22.5), (26.5, 23.2), (24.5, 24.5), (24.5, 27), (25.5, 27.5), (25.5, 36.5), (24, 37.5), (20.5, 38.5),
    (17.5, 40), (16.3, 42), (15.8, 45), (15.5, 80), (15.2, 120), (15.5, 127.5), (17.5, 129.5), (18.5, 131),
    (18.5, 135), (21, 136), (22.5, 138.5), (22.5, 141.5), (25, 143), (26, 145.5), (25.3, 147.5), (22, 148.5),
    (20, 149.5), (19.5, 151), (21, 152.5), (21, 156.5), (19, 157), (17, 155.5)]
ORB_CENTRE, ORB_RADIUS = 176.5, 24.5


def block(name, radius, angle, z0, z1, width, depth):
    """A small box on a ring (notched bands, tabs), turned to face out."""
    obj = pl.box(name, (fl.u(radius), 0, fl.u((z0 + z1) / 2)), (fl.u(depth), fl.u(width), fl.u(z1 - z0)), gold,
                 uv_scale=4)
    obj.rotation_euler = (0, 0, angle)
    return fl.apply([obj])[0]


def claw(k, count, sides):
    """A curled claw on the skirt: out from the flare, then hooking down to a point."""
    a = 2 * math.pi * (k + 0.5) / count
    d = Vector((math.cos(a), math.sin(a), 0))
    p = [tuple(d * r + Vector((0, 0, z))) for r, z in ((32, 17.5), (42, 15.5), (46.5, 9), (46, 2.5))]
    return [fl.tube(f'claw{k}a', p[0], p[1], 3.6, 3.0, sides, gold, caps=False),
            fl.tube(f'claw{k}b', p[1], p[2], 3.0, 2.0, sides, gold, caps=False),
            fl.tube(f'claw{k}c', p[2], p[3], 2.0, 0.5, sides, gold, caps=False)]


def sphere(segments, rings):
    """UV sphere of the orb: u once round (the swirls scroll along it), v pole to pole; shared seam vertices (the
    texture seam is per loop), single pole vertices."""
    bm = bmesh.new()
    uv = bm.loops.layers.uv.verify()

    def at(t, a):
        return (fl.u(ORB_RADIUS * math.sin(t) * math.cos(a)), fl.u(ORB_RADIUS * math.sin(t) * math.sin(a)),
                fl.u(ORB_CENTRE - ORB_RADIUS * math.cos(t)))
    bottom = bm.verts.new(at(0, 0))
    top = bm.verts.new(at(math.pi, 0))
    rows = [[bm.verts.new(at(math.pi * j / rings, 2 * math.pi * i / segments)) for i in range(segments)]
            for j in range(1, rings)]
    for i in range(segments):
        i2 = (i + 1) % segments
        face = bm.faces.new((bottom, rows[0][i2], rows[0][i]))
        for loop, c in zip(face.loops, ((i + 0.5, 0), (i + 1, 1), (i, 1))):
            loop[uv].uv = (c[0] / segments, c[1] / rings)
        for j in range(rings - 2):
            face = bm.faces.new((rows[j][i], rows[j][i2], rows[j + 1][i2], rows[j + 1][i]))
            for loop, c in zip(face.loops, ((i, j + 1), (i + 1, j + 1), (i + 1, j + 2), (i, j + 2))):
                loop[uv].uv = (c[0] / segments, c[1] / rings)
        face = bm.faces.new((rows[-1][i], rows[-1][i2], top))
        for loop, c in zip(face.loops, ((i, rings - 1), (i + 1, rings - 1), (i + 0.5, rings))):
            loop[uv].uv = (c[0] / segments, c[1] / rings)
    return pl.to_object('orb', bm, orb)


def build(level):
    seg = (16, 12, 8)[level]
    step = (1, 2, 3)[level]
    profile = [p for i, p in enumerate(PROFILE) if i % step == 0 or i == len(PROFILE) - 1]
    solids = [fl.lathe('body', profile, seg, gold, u_repeat=2, v_scale=1.5)]
    if level < 2:
        sides = (4, 3)[level]
        for k in range(12):
            solids += claw(k, 12, sides)
        notches = (14, 10)[level]
        for k in range(notches):
            solids.append(block(f'band{k}', 26.0, 2 * math.pi * k / notches, 28.5, 35.5, 5.5, 2.5))
        if level == 0:
            for k in range(12):
                solids.append(block(f'tab{k}', 19.3, 2 * math.pi * (k + 0.5) / 12, 130.5, 136.5, 3.6, 2.2))
            for k in range(10):
                solids.append(block(f'crown{k}', 21.3, 2 * math.pi * k / 10, 154.5, 158.5, 4.5, 2.0))
    whites = [sphere(*((20, 12), (14, 8), (9, 5))[level]),
              # The halo sits a little low (its top at the orb's top keeps the bounds): the orb's light on the cup.
              fl.glow_card('halo', halo, 168.0, 84.0, 66.0)]
    return solids, whites


# Native gold (dec64a by height, all twelve share it): bright skirt and claws, mid shaft, bright capital.
STOPS = [(0, (185, 150, 88)), (22, (170, 132, 80)), (40, (160, 120, 70)), (60, (168, 127, 76)),
         (125, (162, 123, 73)), (140, (150, 116, 70)), (148, (180, 142, 80)), (158, (170, 130, 76))]
colours = {'Gold': lambda co, n: tuple(c * w for c, w in zip(fl.stops(STOPS, co.z), (1.12, 1.07, 0.86)))}
fl.build_lods('Pedestal', 'pedestal', build, colours, rays=(32, 20, 12), distance=14.0, strength=0.55, sharp=35,
              last=('Halo',))
