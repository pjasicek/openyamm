"""MM6 dungeon mushrooms, traced from the sprites' half-widths (fractions of the content height):
`mushrm01` a tall parasol: broad flat buff cap with fine dark flecks over grey-brown gills, a slender off-white stem
with a ring two thirds up and a bulbous foot; `mushrm02` a fat orange cap with pale warts, domed almost to a sphere,
on a thick stem whose swollen foot is dark with soil; `mushrm03` a red fly agaric with white dots, a white skirt
under the cap and a bulb at the foot; `mushrm05` two flat brown parasols on thin stems that rise from one foot and
lean apart, the left cap lower and in front. Caps are bodies of revolution with a slightly wavy rim (noise), the
undersides gills (or the cap skin where the cap curls under); stems are tubes swept along gently curved paths with
a radius profile (foot bulb, ring swelling). Built per level (cap sides 32 / 16 / 10). COLOR_0: occlusion x tints to
the sprite's measured region colours (measure.py), the stems darkening toward the soil.
Writes work/<prop>_export.glb. Usage: blender --background --python build_mushrooms.py -- mushrm01|02|03|05"""
import math
import os
import sys

from mathutils import Vector, noise

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import containers_lib as cl  # noqa: E402

pl = cl.pl
PROP = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else 'mushrm01'

# Each mushroom: stem path (x, y, z) and radius profile [(t, r)], cap centre/tilt, top and underside profiles
# [(r, z)] relative to the cap's rim height, and optional ring (skirt) profile on the stem.
SPECS = {
    'mushrm01': {
        'height': 106, 'cap_texture': 'capbrown', 'under': 'gills',
        'targets': {'Cap': (144, 119, 96), 'Gills': (115, 100, 87), 'Stem': (175, 153, 128)},
        'mushrooms': [{
            'stem': [(0, 0, 0), (0.004, 0, 0.2), (0.0, 0, 0.45), (-0.006, 0, 0.62), (0.0, 0, 0.77)],
            'radius': [(0, 0.12), (0.04, 0.14), (0.1, 0.1), (0.16, 0.062), (0.25, 0.05), (0.78, 0.045),
                       (0.83, 0.058), (0.86, 0.047), (1.0, 0.044)],
            'cap': (0.0, 0.0, 0.785), 'tilt': (0.0, 0.03),
            'top': [(0.355, 0.0), (0.35, 0.018), (0.31, 0.075), (0.24, 0.125), (0.13, 0.16), (0.0, 0.172)],
            'underside': [(0.355, 0.0), (0.25, -0.012), (0.12, -0.025), (0.044, -0.035)],
            'ring': [(0.06, 0.665), (0.08, 0.64), (0.095, 0.615)],
        }],
    },
    'mushrm02': {
        'height': 87, 'cap_texture': 'caporange', 'under': None,
        'targets': {'Cap': (166, 93, 32), 'Stem': (137, 104, 80)},
        'soil': (0.0, 0.2, 0.3),
        'mushrooms': [{
            'stem': [(0, 0, 0), (0.01, 0, 0.15), (0.0, 0, 0.3), (0.0, 0, 0.44)],
            'radius': [(0, 0.2), (0.08, 0.25), (0.25, 0.27), (0.45, 0.25), (0.65, 0.2), (0.8, 0.17), (1.0, 0.18)],
            'cap': (0.0, 0.0, 0.43), 'tilt': (0.04, 0.0),
            'top': [(0.33, 0.0), (0.355, 0.08), (0.362, 0.18), (0.345, 0.3), (0.3, 0.41), (0.23, 0.49), (0.14, 0.54),
                    (0.06, 0.565), (0.0, 0.57)],
            'underside': [(0.33, 0.0), (0.29, -0.015), (0.22, -0.02), (0.17, -0.02)],
        }],
    },
    'mushrm03': {
        'height': 79, 'cap_texture': 'capred', 'under': None,
        'targets': {'Cap': (208, 101, 72), 'Stem': (154, 142, 126)},
        'soil': (0.0, 0.08, 0.6),
        'mushrooms': [{
            'stem': [(0.03, 0, 0), (0.035, 0, 0.15), (0.03, 0, 0.35), (0.03, 0, 0.62)],
            'radius': [(0, 0.15), (0.06, 0.19), (0.17, 0.17), (0.3, 0.11), (0.6, 0.095), (1.0, 0.085)],
            'cap': (0.02, 0.0, 0.61), 'tilt': (-0.03, 0.0),
            'top': [(0.38, 0.0), (0.39, 0.05), (0.375, 0.14), (0.33, 0.22), (0.25, 0.3), (0.14, 0.36), (0.05, 0.385),
                    (0.0, 0.39)],
            'underside': [(0.38, 0.0), (0.3, -0.008), (0.18, -0.012), (0.085, -0.015)],
            'ring': [(0.095, 0.575), (0.14, 0.53), (0.172, 0.47), (0.188, 0.42)],
        }],
    },
    'mushrm05': {
        'height': 88, 'cap_texture': 'capbrown', 'under': 'gills',
        'targets': {'Cap': (141, 108, 69), 'Gills': (112, 96, 80), 'Stem': (173, 151, 124)},
        'soil': (0.0, 0.08, 0.75),
        'mushrooms': [
            {'stem': [(0.0, 0.03, 0), (-0.05, 0.04, 0.2), (-0.11, 0.05, 0.4), (-0.2, 0.06, 0.55),
                      (-0.3, 0.07, 0.68)],
             'radius': [(0, 0.09), (0.06, 0.075), (0.15, 0.055), (0.5, 0.045), (0.8, 0.042), (1.0, 0.04)],
             'cap': (-0.31, 0.07, 0.675), 'tilt': (0.12, 0.05),
             'top': [(0.29, 0.0), (0.285, 0.025), (0.24, 0.065), (0.15, 0.1), (0.06, 0.12), (0.0, 0.125)],
             'underside': [(0.29, 0.0), (0.2, -0.01), (0.09, -0.02), (0.035, -0.025)]},
            {'stem': [(0.1, -0.03, 0), (0.14, -0.04, 0.3), (0.2, -0.05, 0.6), (0.27, -0.06, 0.78),
                      (0.31, -0.06, 0.87)],
             'radius': [(0, 0.09), (0.06, 0.075), (0.15, 0.055), (0.66, 0.045), (0.7, 0.058), (0.73, 0.046),
                        (1.0, 0.042)],
             'cap': (0.32, -0.06, 0.865), 'tilt': (-0.1, -0.03),
             'top': [(0.28, 0.0), (0.275, 0.025), (0.23, 0.065), (0.15, 0.1), (0.06, 0.125), (0.0, 0.13)],
             'underside': [(0.28, 0.0), (0.2, -0.01), (0.09, -0.02), (0.036, -0.025)]},
        ],
    },
}
SPEC = SPECS[PROP]
H = cl.u(SPEC['height'])
SEED = {'mushrm01': 1.0, 'mushrm02': 2.0, 'mushrm03': 3.0, 'mushrm05': 5.0}[PROP]


def interpolate(table, x):
    if x <= table[0][0]:
        return table[0][1]
    for (x0, y0), (x1, y1) in zip(table, table[1:]):
        if x <= x1:
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return table[-1][1]


def smooth_path(points, count):
    """Catmull-Rom through the control points, count + 1 samples."""
    pts = [Vector(p) for p in points]
    pts = [pts[0] * 2 - pts[1]] + pts + [pts[-1] * 2 - pts[-2]]
    result = []
    spans = len(points) - 1
    for k in range(count + 1):
        f = k / count * spans
        i = min(int(f), spans - 1)
        t = f - i
        p0, p1, p2, p3 = pts[i:i + 4]
        result.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                             + (-p0 + 3 * p1 - 3 * p2 + p3) * t * t * t))
    return result


def cap_surface(name, mushroom, profile, mat, sides, rings, k):
    """Body of revolution of profile [(r, dz)] (rim first) about the cap centre, tilted, rim waved by noise."""
    cx, cy, cz = mushroom['cap']
    tx, ty = mushroom['tilt']
    samples = []
    for i in range(rings + 1):                    # resample the profile at even parameter steps
        f = i / rings * (len(profile) - 1)
        j = min(int(f), len(profile) - 2)
        t = f - j
        (r0, z0), (r1, z1) = profile[j], profile[j + 1]
        samples.append((r0 + (r1 - r0) * t, z0 + (z1 - z0) * t))
    rim = max(r for r, _ in profile)

    def point(t, theta):
        r, dz = samples[round(t * rings)]
        weight = (r / rim) ** 2
        wave = noise.noise(Vector((math.cos(theta) * 1.6, math.sin(theta) * 1.6, SEED + k * 3.7)))
        rr = r * (1 + 0.05 * wave * weight)
        dz += 0.025 * wave * weight * rim
        x, y = rr * math.cos(theta), rr * math.sin(theta)
        z = dz + x * tx + y * ty
        return Vector(((cx + x) * H, (cy + y) * H, (cz + z) * H))

    return cl.soft_body(name, rings, sides, point, mat, u_repeat=2.0, v_scale=3.0, recalc=False)


def ring_skirt(name, mushroom, mat, sides, k):
    """The annulus round the stem: a thin flared skirt (outer and inner faces)."""
    path = smooth_path(mushroom['stem'], 40)
    profile = mushroom['ring']
    outer = [(r, z) for r, z in profile]
    inner = [(r * 0.85, z + 0.012) for r, z in reversed(profile)]
    full = list(reversed(outer + inner))           # inner face down and out, then the outer face up and in

    def point(t, theta):
        f = t * (len(full) - 1)
        j = min(int(f), len(full) - 2)
        s = f - j
        r = full[j][0] + (full[j + 1][0] - full[j][0]) * s
        z = full[j][1] + (full[j + 1][1] - full[j][1]) * s
        centre = min(path, key=lambda p: abs(p.z - z))
        rr = r * (1 + 0.12 * noise.noise(Vector((math.cos(theta) * 2.5, math.sin(theta) * 2.5, SEED + 9 + k))))
        return Vector(((centre.x + rr * math.cos(theta)) * H, (centre.y + rr * math.sin(theta)) * H, z * H))

    return cl.soft_body(name, (len(full) - 1) * 2, sides, point, mat, u_repeat=2.0, v_scale=3.0, recalc=False)


def stem(name, mushroom, sides, steps, mat):
    path = [p * H for p in smooth_path(mushroom['stem'], steps)]
    wobble = lambda t: 1 + 0.06 * noise.noise(Vector((t * 6, SEED, 1.0)))  # noqa: E731
    return cl.sweep(name, path, lambda t: interpolate(mushroom['radius'], t) * H * wobble(t), sides, mat,
                    u_repeat=1.0, v_scale=2.0)


def build(level):
    cap_sides = (32, 16, 10)[level]
    stem_sides = (14, 8, 6)[level]
    if len(SPEC['mushrooms']) > 1:
        cap_sides = (22, 12, 8)[level]
        stem_sides = (9, 6, 4)[level]
    parts = []
    for k, mushroom in enumerate(SPEC['mushrooms']):
        parts.append(stem(f'stem{k}', mushroom, stem_sides, (16, 8, 4)[level], mats['Stem']))
        parts.append(cap_surface(f'cap{k}', mushroom, mushroom['top'], mats['Cap'], cap_sides, (6, 4, 2)[level], k))
        under = mats.get('Gills', mats['Cap'])
        # the underside runs stem to rim so that its faces look down
        parts.append(cap_surface(f'under{k}', mushroom, list(reversed(mushroom['underside'])), under, cap_sides,
                                 (3, 2, 1)[level], k))
        if 'ring' in mushroom and level < 2:
            parts.append(ring_skirt(f'ring{k}', mushroom, mats.get('Ring', mats['Stem']), stem_sides + 2, k))
    return pl.join(f'mushroom{level}', parts)


pl.reset()
mats = {'Cap': cl.material('Cap', SPEC['cap_texture']), 'Stem': cl.material('Stem', 'stem')}
if SPEC['under']:
    mats['Gills'] = cl.material('Gills', SPEC['under'])
if 'Ring' in SPEC['targets']:
    mats['Ring'] = cl.material('Ring', 'stem')
lods = [build(level) for level in range(3)]
cl.drop_to_ground(lods)
tints = {name: cl.tint_for(mats[name], target) for name, target in SPEC['targets'].items()}
print('TINTS', tints)


def shade(name, co):
    """Stems darken toward the soil; brown parasol caps darken toward their centre (the sprites' dark crowns)."""
    soil = SPEC.get('soil')
    if name == 'Cap' and SPEC['cap_texture'] == 'capbrown':
        caps = [(Vector(m['cap']) * H, m['top'][0][0] * H) for m in SPEC['mushrooms']]
        centre, rim = min(caps, key=lambda c: (Vector((co.x, co.y)) - c[0].xy).length)
        distance = (Vector((co.x, co.y)) - centre.xy).length / rim
        crown = 0.5 if len(SPEC['mushrooms']) > 1 else 0.6
        return crown + (1 - crown) * cl.smoothstep(0.1, 0.8, distance)
    if name != 'Stem' or soil is None:
        return 1.0
    lo, hi, dark = soil
    return dark + (1 - dark) * cl.smoothstep(lo * H, hi * H, co.z)


cl.finish(PROP.capitalize(), lods, tints, {'rays': 40, 'distance': H * 0.3, 'strength': 0.6, 'floor': True},
          shade=shade, prop=PROP)
