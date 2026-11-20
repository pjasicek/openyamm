"""Standing torch `dec06` (8 placements in out02 Ravenshore; eight frames in 1 s, light 128; 29 x 119 units): a
wooden torch stuck upright in the ground, traced from dec06a (x2 pixels at 0.5 units): a club-like stick (11 wide at
the ground, 6.5 under the head, with dark carved diamonds), a wound head (44-60, up to 20 wide) and a tall fire
(from inside the head to 119, about 25 wide). The frames animate only the fire.

Surfaces: `wood` (CC0 Rough Wood) tinted to the sprite's fire-lit orange-brown stick, `rag` (CC0 Hessian 380) for the
wound head, lit and faintly glowing (`openyamm_pulse`), an ember crown (`Embers`: the ember texture through a fire
ramp, emissive, flickering) where the flame rises, and ragged tatters off the head's rim. Fire: two camera-facing
cards on the shared Flame02 flipbook (coplanar, mirrored and a third of the loop apart), an additive Flame02 `Blaze`
over the lower half (the sprite's bright, pale burning head), rising additive `sparks`, and a soft additive halo.
Every fire-lit surface flickers (`openyamm_flicker`), 2026-10-16.
Writes work/torch_export.glb. Usage: blender --background --python build_torch.py"""
import math
import os
import sys

import bmesh
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as al  # noqa: E402

pl, u = al.pl, al.u
pl.reset()
mats = {
    'Wood': al.material('Wood', 'wood', extras={'openyamm_specular': 0.3}),
    'Notch': al.material('Notch', 'wood', extras={'openyamm_specular': 0.1}),
    'Rag': al.glow_material('Rag', 'rag', (46, 16, 4), extras={'openyamm_specular': 0.2}, flicker=(0.4, 7.0)),
    'Embers': al.glow_material('Embers', 'ember', (190, 80, 20), flicker=(0.4, 9.0)),
    'Halo': al.halo_material('Halo', emission=(60, 26, 6), flicker=(0.3, 6.0)),
    'Flame': al.flame_material('Flame', 'flame02'),
    # Additive fire over the flame's lower half: the sprite's bright, pale burning head.
    'Blaze': al.flame_material('Blaze', 'flame02', additive=True, flicker=(0.25, 8.0), emission=(30, 12, 3)),
    'Sparks': al.flame_material('Sparks', 'sparks', additive=True, flipbook=(8, 4, 12)),
}
STICK = [(0.0, 0.0), (5.2, 0.0), (5.5, 4.0), (5.2, 12.0), (4.6, 22.0), (4.0, 32.0), (3.5, 40.0), (3.3, 44.0)]
HEAD = [(3.3, 43.6), (5.0, 44.6), (6.6, 46.2), (7.8, 48.2), (8.8, 50.4), (9.4, 52.6), (9.8, 54.8), (9.8, 56.8),
        (9.2, 58.6), (8.0, 60.0)]


def wrapped(obj, z0, z1, seed):
    """Rough up the head into wound strips: a spiral of raised wraps, lumps, and a ragged top edge."""
    import random
    rng = random.Random(seed)
    lumps = [rng.uniform(-1, 1) for _ in range(64)]
    for v in obj.data.vertices:
        z = v.co.z * al.dl.UNITS_PER_METRE
        r = math.hypot(v.co.x, v.co.y)
        if r < 1e-6 or z < z0 + 0.5:
            continue
        a = math.atan2(v.co.y, v.co.x)
        t = (z - z0) / (z1 - z0)
        wrap = 0.07 * math.sin(a * 1.0 + z * 1.15) ** 2 - 0.035
        lump = 0.05 * lumps[int((a + math.pi) / (2 * math.pi) * 16 + int(z / 3) * 7) % 64]
        scale = 1 + (wrap + lump) * min(1.0, t * 3)
        v.co.x *= scale
        v.co.y *= scale
        if t > 0.95:
            v.co.z += al.u(rng.uniform(-1.4, 1.0))
EMBERS = [(8.0, 60.0), (5.5, 61.4), (3.0, 62.2), (0.0, 62.4)]


def notch(name, z, angle):
    """A dark diamond cut into the stick (a flat four-sided pyramid pressed into the surface)."""
    bm = bmesh.new()
    uv = bm.loops.layers.uv.verify()
    a = math.radians(angle)
    out = Vector((math.cos(a), math.sin(a), 0))
    side = Vector((-out.y, out.x, 0))
    r = 4.6 - 0.06 * (z - 22.0)
    centre = out * u(r - 0.6) + Vector((0, 0, u(z)))
    tip = [centre + side * u(1.6), centre + Vector((0, 0, u(3.0))), centre - side * u(1.6),
           centre - Vector((0, 0, u(3.0)))]
    rim = [p + out * u(0.75) for p in tip]
    verts = [bm.verts.new(p) for p in rim] + [bm.verts.new(centre)]
    for i in range(4):
        face = bm.faces.new((verts[i], verts[(i + 1) % 4], verts[4]))
        for loop in face.loops:
            loop[uv].uv = (0.5, 0.5)
    return pl.to_object(name, bm, mats['Notch'], smooth=False)


def build(level):
    seg = (12, 8, 6)[level]
    step = (1, 2, 2)[level]
    stick = STICK[::step] + ([STICK[-1]] if (len(STICK) - 1) % step else [])
    head = HEAD[::step] + ([HEAD[-1]] if (len(HEAD) - 1) % step else [])
    solids = [pl.lathe('stick', [(u(r), u(z)) for r, z in stick], seg, mats['Wood'], u_repeat=1.0, v_scale=3.0),
              pl.lathe('head', [(u(r), u(z)) for r, z in head], (16, 10, 6)[level], mats['Rag'], u_repeat=2.0,
                       v_scale=6.0)]
    wrapped(solids[1], 43.6, 60.0, 6)
    if level < 2:
        # Wound strips round the head: flat tilted rings, like the sprite's ragged wrapping.
        for k, (z, tilt, turn) in enumerate(((46.6, 14.0, 20.0), (50.0, -11.0, 140.0), (53.4, 13.0, 250.0),
                                             (56.6, -9.0, 40.0), (59.0, 10.0, 300.0))):
            radius = {0: 7.2, 1: 9.0, 2: 9.9, 3: 10.0, 4: 8.9}[k]
            n = (14, 9)[level]
            path = []
            for i in range(n + 1):
                a = 2 * math.pi * i / n
                p = Vector((math.cos(a) * radius, math.sin(a) * radius, 0.0))
                p.z = math.sin(a) * radius * math.tan(math.radians(tilt))
                c, si = math.cos(math.radians(turn)), math.sin(math.radians(turn))
                p = Vector((p.x * c - p.y * si, p.x * si + p.y * c, p.z + z))
                path.append(Vector((u(p.x), u(p.y), u(p.z))))
            solids.append(al.sweep(f'wrap{k}', path, u(1.2), 4, mats['Rag'], u_repeat=1.0, v_scale=8.0, caps=False,
                                   flat=(0.6, 1.6)))
    if level == 0:
        for k, (z, angle) in enumerate(((19.0, -90.0), (31.0, -80.0), (25.0, 90.0), (36.0, 100.0))):
            solids.append(notch(f'notch{k}', z, angle))
    if level < 2:
        # Ragged burning tatters standing off the head's top rim (the sprite's crumpled, flaming wrapping).
        n = (15, 7)[level]
        for k in range(n):
            a = 2 * math.pi * k / n + 0.35 * ((k * 5) % 3)
            out = Vector((math.cos(a), math.sin(a), 0))
            side = Vector((-out.y, out.x, 0))
            z = 52.0 + 2.6 * ((k * 3) % 4)
            r = 9.6 - 0.4 * ((k * 3) % 4)
            foot = out * u(r - 0.8) + Vector((0, 0, u(z)))
            tip = out * u(r + 3.5 + 1.5 * (k % 2)) + side * u(1.5 * ((k % 3) - 1)) \
                + Vector((0, 0, u(z + 3.5 + 1.5 * ((k * 7) % 3))))
            solids.append(pl.tube(f'tatter{k}', foot, tip, u(1.8), u(0.25), 4, mats['Rag']))
    al.apply(solids)
    whites = [pl.lathe('embers', [(u(r), u(z)) for r, z in EMBERS], seg, mats['Embers'], u_repeat=2.0, v_scale=6.0),
              al.halo_card('halo', mats['Halo'], 80.0, 30.0)]
    whites.append(al.flame_card('flame', mats['Flame'], 'flame02', 50.0, 119.0, 42.0))
    whites.append(al.flame_card('blaze', mats['Blaze'], 'flame02', 47.0, 92.0, 38.0, x=-1.0, frame_offset=37))
    if level < 2:
        whites.append(al.flame_card('flame2', mats['Flame'], 'flame02', 55.0, 112.0, 34.0, x=1.5, mirrored=True,
                                    frame_offset=21))
        whites.append(al.spark_card('sparks', mats['Sparks'], 62.0, 119.0, 28.0))
    return solids, whites


COLOURS = {
    # dec06a: the stick's orange-brown (131-175, 74-103, 36-51; darker in its middle band), near-black notches, the
    # head dark at its foot (89, 33, 9) and fire-lit orange above (145-178, 67-90, 23-38).
    'Wood': lambda co, n: al.stops([(0, (160, 94, 48)), (10, (148, 86, 43)), (28, (110, 64, 32)), (34, (138, 80, 40)),
                                    (44, (100, 52, 24))], co.z),
    'Notch': (20, 10, 6),
    'Rag': lambda co, n: al.stops([(44, (60, 24, 8)), (50, (96, 42, 14)), (56, (136, 62, 22)), (61, (166, 80, 32))],
                                  co.z),
    'Embers': (230, 120, 40),
    'Halo': (255, 160, 70)}
al.build_lods('Torch', 'torch', build, COLOURS, rays=(24, 16, 10), distance=10.0, strength=0.45,
              last=('Halo', 'Flame', 'Blaze', 'Sparks'))
