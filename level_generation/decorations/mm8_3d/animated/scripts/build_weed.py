"""Plane of Water plants: seaweed `dec58` (48 placements, ten frames weed010-019, 251 x 147 units) and the red sea
plant `dec59` (100, weed020-029, 243 x 124), both in elemw. The native frames sway the plants in a 1.25 s loop: the
seaweed's frond tips move about +-20 units, the coral spire only +-2.5 while its green strands wave.

Built from alpha-tested strips (double-sided, MASK) on painted atlases (make_textures.py `seaweed`, `coral`), each
strip a curved, twisted ribbon along its frond with texture u running from base (0) to tip (1), so the shader's
flutter wave (sin(7 t - 9 u)) travels up the fronds, and its width fitted per segment to the painted shape
(textures/<atlas>_profile.json) so little transparent area is drawn. COLOR_0 alpha (the flutter weight) rises from
0 at the base to 1 at the tip. Motion: `openyamm_wind` (a slow sway growing with height squared, in step across
neighbouring plants like a current) plus `openyamm_flutter` ripples.

seaweed: eleven pinnate fronds (four painted variants) from a tight clump, tall ones nearly upright, short ones
leaning out; wind 0.25 m (about 20 units at the top of a 251-unit plant), flutter 0.03 m.
coral: a red branching spire of three crossed fans and two lower side fans (stiff: wind 0.04 m) and fourteen green
strands round it (wind 0.15 m, flutter 0.05 m).
Writes work/<prop>_export.glb. Usage: blender --background --python build_weed.py -- seaweed|coral"""
import json
import math
import os
import sys

import bmesh
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as al  # noqa: E402

pl, u = al.pl, al.u
prop = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else 'seaweed'
pl.reset()
FOLIAGE = {'openyamm_translucency': 0.35, 'openyamm_specular': 0.15}


def strip(name, mat, base, length, yaw, lean0, lean1, twist, band, segments, width, sway=0.0, phase=0.0):
    """A ribbon of `segments` from base (units) along a frond `length` units long that leans from lean0 to lean1
    degrees out from vertical toward yaw, with an S-wave of `sway` units, twisting `twist` degrees about its length.
    band: an atlas profile entry; width: the band's full width in units."""
    bm = bmesh.new()
    uv = bm.loops.layers.uv.verify()
    d = Vector((math.cos(math.radians(yaw)), math.sin(math.radians(yaw)), 0))
    side0 = Vector((-d.y, d.x, 0))
    bins = band['bins']
    nb = len(bins)
    # The strip ends with the painted shape (its last covered bin), so the bounds stop at the visible tip.
    u_end = (max(i for i, b in enumerate(bins) if b[1] - b[0] > 0.01) + 1) / nb
    p = Vector(base)
    rows = []
    for i in range(segments + 1):
        t = i / segments
        if i > 0:
            a = math.radians(lean0 + (lean1 - lean0) * (t - 0.5 / segments))
            p = p + (d * math.sin(a) + Vector((0, 0, math.cos(a)))) * (length / segments)
        offset = side0 * sway * math.sin(math.pi * t * 1.5 + phase) * t
        lo_bin = max(0, int((t - 1.0 / segments) * u_end * nb))
        hi_bin = min(nb - 1, int((t + 1.0 / segments) * u_end * nb))
        lo = min(b[0] for b in bins[lo_bin:hi_bin + 1]) - 0.02
        hi = max(b[1] for b in bins[lo_bin:hi_bin + 1]) + 0.02
        lo, hi = max(0.0, lo), min(1.0, hi)
        tangent = d * math.sin(math.radians(lean0 + (lean1 - lean0) * t)) + Vector((0, 0, 1)) * math.cos(
            math.radians(lean0 + (lean1 - lean0) * t))
        across = Matrix.Rotation(math.radians(twist * t), 3, tangent) @ side0
        tt = min(max(t * u_end, 0.004), 0.996)
        ring = []
        for f in (lo, hi):
            co = p + offset + across * ((f - 0.5) * width)
            ring.append((bm.verts.new((u(co.x), u(co.y), u(co.z))), (tt, 1 - (band['top'] + f * band['height']))))
        rows.append(ring)
    for i in range(segments):
        (a0, ua0), (a1, ua1) = rows[i]
        (b0, ub0), (b1, ub1) = rows[i + 1]
        face = bm.faces.new((a0, a1, b1, b0))
        for loop, st in zip(face.loops, (ua0, ua1, ub1, ub0)):
            loop[uv].uv = st
    return pl.to_object(name, bm, mat, smooth=True)


def rising(length):
    """Flutter weight: 0 at the plant's foot, 1 from `length` units up."""
    return lambda co: min(1.0, max(0.0, co.z / length)) ** 1.3


if prop == 'seaweed':
    with open(os.path.join(al.TEXTURES, 'seaweed_profile.json')) as handle:
        PROFILE = json.load(handle)
    mats = {'Frond': al.material('Frond', 'seaweed', alpha=True, extras=dict(
        FOLIAGE, openyamm_wind=0.25, openyamm_flutter=0.03))}
    # (yaw degrees, length units, lean at base, lean at tip, painted variant, sway units)
    FRONDS = [(10, 258, 4, 13, 0, 6), (105, 244, 7, 18, 1, -8), (200, 252, 5, 15, 2, 7), (290, 236, 9, 21, 3, -6),
              (55, 226, 11, 24, 1, 9), (150, 218, 12, 26, 0, -7), (245, 230, 10, 23, 3, 8), (335, 208, 14, 28, 2, -9),
              (80, 214, 15, 30, 2, 6), (190, 200, 17, 32, 3, -6), (310, 205, 16, 31, 0, 7)]

    LEAN = 1.0

    def build(level):
        keep = (11, 8, 5)[level]
        segments = (12, 6, 3)[level]
        cards = []
        for k, (yaw, length, lean0, lean1, variant, sway) in enumerate(FRONDS[:keep]):
            base = (3.5 * math.cos(math.radians(yaw + 40)), 3.5 * math.sin(math.radians(yaw + 40)), 0)
            scale = 1.0 if level == 0 else 1.06
            cards.append(strip(f'frond{k}', mats['Frond'], base, length, yaw, lean0 * LEAN, lean1 * LEAN,
                               20 + 12 * (k % 3),
                               PROFILE[variant], segments, length / 3.0 * scale, sway, k * 0.9))
        return cards, []

    COLOURS = {'Frond': lambda co, n: al.scaled('seaweed', 0.8 + 0.2 * min(1.0, co.z / 120))}
    al.build_lods('Seaweed', 'seaweed', build, COLOURS, rays=(24, 16, 8), distance=40.0, strength=0.3,
                  alpha={'Frond': rising(200)})
else:
    with open(os.path.join(al.TEXTURES, 'coral_profile.json')) as handle:
        PROFILE = json.load(handle)
    mats = {'Coral': al.material('Coral', 'coral', alpha=True, extras=dict(FOLIAGE, openyamm_wind=0.04)),
            'Tendril': al.material('Tendril', 'coral', alpha=True, extras=dict(
                FOLIAGE, openyamm_wind=0.15, openyamm_flutter=0.05))}
    # Red fans: (yaw, length, lean0, lean1, variant, twist)
    FANS = [(0, 243, 0, 2, 0, 25), (60, 238, 1, 3, 1, -20), (120, 241, 0, 2, 0, 15), (30, 150, 10, 18, 1, 30),
            (210, 140, 12, 20, 0, -30)]
    # Green strands: (yaw, length, lean0, lean1, variant)
    STRANDS = [(k * 360 / 14 + (k % 3) * 7, 135 + (k * 37) % 60, 4 + (k * 5) % 8, 14 + (k * 7) % 14, 2 + k % 4)
               for k in range(14)]

    def build(level):
        cards = []
        for k, (yaw, length, lean0, lean1, variant, twist) in enumerate(FANS[:(5, 4, 3)[level]]):
            cards.append(strip(f'fan{k}', mats['Coral'], (0, 0, 0), length, yaw, lean0, lean1, twist,
                               PROFILE[variant], (8, 4, 2)[level], length / 3.3))
        for k, (yaw, length, lean0, lean1, variant) in enumerate(STRANDS[:(14, 10, 6)[level]]):
            base = (5 * math.cos(math.radians(yaw)), 5 * math.sin(math.radians(yaw)), 0)
            cards.append(strip(f'strand{k}', mats['Tendril'], base, length, yaw, lean0, lean1, 80,
                               PROFILE[variant], (10, 5, 3)[level], length / 6.5 * (1.0 if level == 0 else 1.2)))
        return cards, []

    COLOURS = {'Coral': lambda co, n: al.scaled('coral', 0.45 + 0.4 * min(1.0, co.z / 150)),
               'Tendril': lambda co, n: al.scaled('coral', 0.85 + 0.15 * min(1.0, co.z / 120))}
    al.build_lods('Coral', 'coral', build, COLOURS, rays=(24, 16, 8), distance=40.0, strength=0.45,
                  alpha={'Tendril': rising(150), 'Coral': lambda co: 0.0})
