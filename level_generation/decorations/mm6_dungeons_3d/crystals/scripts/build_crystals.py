"""MM6 dungeon crystal formations, faceted procedural geometry fitted to the native sprites (logical pixels; the
sprite's horizontal centre is the model origin, depth y is added so the cluster reads from every side):
- crystl0 (pink cluster, 113 x 92, glowing): a fan of chamfered hexagonal prisms from one root, low prisms on the
  ground; emission pulses (openyamm_pulse) with the native 33/16 s loop.
- crclstr (quartz cluster, 159 x 128): large pointed quartz prisms, smaller ones between them and pebbles at the foot.
- crys6 (blue crystal mound, 150 x 98): a faceted grey rock mound fitted to the sprite's crest, covered on its left
  and top by stubby blue crystals.
- crys5 (salmon blade rosette, 188 x 77): flat blade crystals radiating from two rosette centres below the ground.
Each level is rebuilt with fewer and simpler crystals (LOD0 chamfered prisms, LOD1 plain prisms, LOD2 the main
ones), cut at the ground plane, occluded, tinted to the measured native colours, and exported to
work/<prop>_export.glb. Usage: blender --background --python build_crystals.py -- <prop>"""
import math
import os
import random
import sys

import bmesh
import bpy
from mathutils import Vector, noise

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import crystals_lib as cl  # noqa: E402

pl = cl.pl
u = cl.u
PROP = sys.argv[sys.argv.index('--') + 1]

# Native sprite measurements (x2 frames, sRGB means of opaque texels; README.md).
NATIVE = {
    'crystl0': {'size': (113, 92), 'Crystal': (133.6, 74.7, 96.0)},
    'crclstr': {'size': (159, 128), 'Quartz': (190, 179, 160), 'Pebble': (200, 184, 160)},
    'crys6': {'size': (150, 98), 'Crystal': (163, 189, 207), 'Rock': (155, 156, 152)},
    'crys5': {'size': (188, 77), 'Blade': (222, 163.2, 142.5)},
}
# crystl0 keeps 80% of its colour as lit albedo; the rest comes back as the pulsing pink emission (finish.py).
ALBEDO_GAIN = {'crystl0': 0.8}
CRYSTL0_PULSE = [0.45, 33 / 16]
# Vertex occlusion strength (the dense blade rosette and the mound shade themselves strongly).
OCCLUSION = {'crys5': 0.3, 'crys6': 0.5}
# Facet contrast (per-facet brightness spread) and the radius scale on the traced crystal widths.
FACETS = {'crystl0': 0.95, 'crclstr': 0.8, 'crys6': 0.8, 'crys5': 0.4}
RADIUS = {'crystl0': 1.3, 'crclstr': 1.25}
# Specular scale (openyamm_specular): glossy crystal (with the low-roughness crystal texture); matte rock.
SPECULAR = {'Crystal': 1.0, 'Quartz': 1.0, 'Pebble': 0.5, 'Blade': 1.0, 'Rock': 0.4}


def P(x, y, z):
    """Sprite logical coordinates (x from the sprite's left edge) to model metres."""
    return Vector((u(x - NATIVE[PROP]['size'][0] / 2), u(y), u(z)))


def level_prism(name, base, tip, radius, mat, level, brightness=1.0, tip_fraction=1.0, flat=1.0, roll=0.0,
                main=True):
    """One crystal at a level of detail: LOD0 chamfered with a mid ring, LOD1 plain hexagonal, LOD2 pentagonal."""
    radius *= RADIUS.get(PROP, 1.0)
    if level == 0:
        return cl.prism(name, base, tip, radius, mat, sides=6, chamfer=0.22, mid=True, tip_fraction=tip_fraction,
                        flat=flat, roll=roll, brightness=brightness, facets=FACETS[PROP])
    sides = 6 if level == 1 else (5 if main else 4)
    return cl.prism(name, base, tip, radius, mat, sides=sides, tip_fraction=tip_fraction, flat=flat, roll=roll,
                    brightness=brightness, facets=FACETS[PROP] * 0.8)


# ---------------------------------------------------------------- crystl0
def crystl0(level, mats):
    m = mats['Crystal']
    # (base, tip) in sprite logical pixels, radius, brightness; traced from the native frame (README.md).
    main = [
        ((52, 0, 16), (68, -4, 89), 6.5, 1.15), ((56, 4, 16), (87, 14, 74), 7.0, 1.05),
        ((60, -3, 15), (107, -14, 52), 7.0, 1.0), ((52, 8, 17), (53, 22, 69), 5.5, 0.75),
        ((49, -4, 17), (24, -14, 64), 6.0, 0.9), ((47, 6, 17), (3, 16, 62), 5.5, 0.8),
        ((62, 10, 18), (69, 24, 90), 4.5, 0.55), ((57, -6, 14), (55, -40, 52), 6.0, 1.1),
        ((58, 8, 14), (66, 46, 56), 6.0, 0.8), ((57, -3, -4), (57, 1, 24), 9.0, 0.6),
    ]
    minor = [
        ((55, 2, 14), (30, 30, 42), 5.0, 0.8), ((58, -4, 14), (85, -35, 38), 5.0, 0.95),
        ((46, -2, 9), (16, -4, 7), 5.0, 0.8), ((63, 2, 9), (101, -6, 11), 5.0, 0.9),
        ((50, -8, 8), (38, -24, 4), 5.0, 0.7), ((66, -6, 8), (80, -22, 6), 4.5, 0.85),
        ((60, 14, 8), (70, 40, 5), 4.5, 0.7), ((50, 14, 8), (30, 34, 6), 4.5, 0.7),
    ]
    items = main + (minor if level < 2 else [])
    parts = []
    for i, (base, tip, radius, b) in enumerate(items):
        parts.append(level_prism(f'c{i}', P(*base), P(*tip), u(radius), m, level, b, tip_fraction=0.75,
                                 roll=i * 0.7, main=i < len(main)))
    if level == 0:
        rng = random.Random(17)
        for i in range(10):
            a = rng.uniform(0, 2 * math.pi); e = rng.uniform(0.35, 1.2); length = rng.uniform(10, 20)
            d = Vector((math.cos(a) * math.cos(e), math.sin(a) * math.cos(e), math.sin(e)))
            base = P(57, 0, 10) + Vector((math.cos(a), math.sin(a), 0)) * u(6)
            parts.append(cl.prism(f's{i}', base, base + d * u(length), u(rng.uniform(2, 3.5)), m, sides=6,
                                  tip_fraction=1.0, roll=a, brightness=rng.uniform(0.7, 1.1),
                                  facets=FACETS[PROP]))
    return parts


def crystl0_factor(co, name):
    """Rank shift: dark wine-red roots and tips, the bright glowing middle (the sprite's quarters 108/146/113)."""
    t = max(0.0, min(1.0, co.z / u(92)))
    return 0.45 * math.sin(math.pi * t) - 0.3


# ---------------------------------------------------------------- crclstr
def crclstr(level, mats):
    q, p = mats['Quartz'], mats['Pebble']
    main = [
        ((62, 0, 12), (64, 4, 128), 11.0, 1.0), ((70, -10, 18), (68, -14, 96), 9.5, 1.05),
        ((86, -4, 8), (150, -10, 84), 9.5, 1.1), ((95, 12, 40), (10, 8, 84), 7.0, 0.9),
        ((40, -2, 26), (2, -8, 50), 6.0, 0.85), ((36, -6, 20), (28, -10, 66), 7.0, 1.0),
        ((75, 14, 18), (85, 30, 72), 6.0, 0.85),
    ]
    minor = [
        ((30, -8, 18), (22, -16, 46), 5.0, 0.95), ((45, -10, 12), (40, -18, 55), 5.5, 1.0),
        ((50, -14, 10), (60, -24, 50), 5.0, 1.05), ((70, -8, 18), (92, -18, 45), 5.0, 0.9),
        ((50, 10, 18), (30, 20, 60), 5.0, 0.85), ((60, -16, 6), (60, -40, 30), 5.0, 0.95),
        ((80, -14, 6), (105, -30, 22), 4.5, 0.9), ((40, -14, 4), (20, -28, 18), 4.0, 0.9),
        ((100, 8, 6), (118, 26, 30), 4.5, 0.85), ((20, 6, 6), (8, 22, 28), 4.0, 0.9),
    ]
    items = main + (minor if level < 2 else minor[:3])
    parts = []
    for i, (base, tip, radius, b) in enumerate(items):
        parts.append(level_prism(f'q{i}', P(*base), P(*tip), u(radius), q, level, b, tip_fraction=1.0,
                                 roll=i * 0.9, main=i < len(main)))
    if level == 0:
        rng = random.Random(29)
        for i in range(8):
            a = rng.uniform(0, 2 * math.pi); e = rng.uniform(0.4, 1.1); length = rng.uniform(9, 18)
            d = Vector((math.cos(a) * math.cos(e), math.sin(a) * math.cos(e), math.sin(e)))
            base = P(rng.uniform(30, 100), rng.uniform(-18, 18), 4)
            parts.append(cl.prism(f's{i}', base, base + d * u(length), u(rng.uniform(2.5, 4)), q, sides=6,
                                  tip_fraction=1.0, roll=a, brightness=rng.uniform(0.85, 1.1),
                                  facets=FACETS[PROP]))
    # Pebbles along the foot (the sprite's rounded tan stones), icosahedra smoothed by shading.
    rng = random.Random(41)
    count = (24, 14, 7)[level]
    for i in range(count):
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=1 if level == 0 else 0, radius=1.0)
        uv = bm.loops.layers.uv.verify()
        r = rng.uniform(5, 9)
        x = 10 + 115 * i / max(1, count - 1) + rng.uniform(-3, 3)
        y = rng.uniform(-14, 10)
        centre = P(x, y, r * 0.3)
        for v in bm.verts:
            v.co = centre + Vector((v.co.x * u(r), v.co.y * u(r) * 0.9, v.co.z * u(r) * 0.7))
        for f in bm.faces:
            for loop in f.loops:
                loop[uv].uv = (loop.vert.co.x * 4, loop.vert.co.y * 4 + loop.vert.co.z * 4)
        parts.append(cl.bright(pl.to_object(f'pebble{i}', bm, p, smooth=True), 1.0, rng.uniform(0.45, 0.8)))
    return parts


def crclstr_factor(co, name):
    return 0.05 - 0.12 * max(0.0, min(1.0, co.z / u(128)))


# ---------------------------------------------------------------- crys6
def crest(alpha):
    """Highest opaque row per logical x of the sprite (heights in logical pixels)."""
    rows, cols = alpha.shape
    heights = []
    for x in range(0, cols, 2):
        ys = [r for r in range(rows) if alpha[r, x:x + 2].any()]
        heights.append((rows - min(ys)) / 2 if ys else 0.0)
    return heights


def crys6(level, mats):
    c, rock = mats['Crystal'], mats['Rock']
    heights = crest(cl.sprite_alpha('crys6_p142.png'))
    width = NATIVE['crys6']['size'][0]

    def crest_at(x):
        i = max(0, min(len(heights) - 1, int(round(x))))
        window = heights[max(0, i - 3):i + 4]
        return sum(window) / len(window)

    cx, rx, ry0 = width / 2, width / 2 - 2, 42.0
    rings, segments = ((9, 28), (6, 18), (4, 12))[level]
    bm = bmesh.new()
    uv = bm.loops.layers.uv.verify()
    grid = []
    mound = []          # (x, y, z, normal) samples for crystal placement
    for i in range(rings + 1):
        r = i / rings
        ring = []
        for s in range(segments):
            a = 2 * math.pi * s / segments
            x = cx + r * rx * math.cos(a)
            ry = ry0 * max(0.35, math.sqrt(max(0.0, 1 - ((x - cx) / rx) ** 2)))
            y = r * ry0 * math.sin(a)
            crest_height = max(6.0, crest_at(x) - 11.0)
            z = crest_height * math.sqrt(max(0.0, 1 - (y / ry) ** 2)) if abs(y) < ry else 0.0
            lump = noise.noise(Vector((x * 0.14, y * 0.14, 3.3))) * 6.0
            z = max(0.0, z + lump * (0.3 + 0.7 * min(1.0, z / 10)))
            ring.append(bm.verts.new(P(x, y, z)))
        grid.append(ring)
    skirt = [bm.verts.new((v.co.x, v.co.y, 0.0)) for v in grid[-1]]
    centre = bm.verts.new(P(cx, 0, max(6.0, crest_at(cx) - 11.0)))
    # Ring 0 is the centre point repeated: a fan from one centre vertex to ring 1 replaces it.
    for s in range(segments):
        s2 = (s + 1) % segments
        bm.faces.new((centre, grid[1][s], grid[1][s2]))
        for i in range(1, rings):
            bm.faces.new((grid[i][s], grid[i + 1][s], grid[i + 1][s2], grid[i][s2]))
        bm.faces.new((grid[rings][s], skirt[s], skirt[s2], grid[rings][s2]))
    for v in grid[0]:
        bm.verts.remove(v)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        for loop in f.loops:
            co = loop.vert.co
            loop[uv].uv = (co.x * 2.0 + co.y * 0.7, co.z * 2.0 + co.y * 1.3)
    bm.normal_update()
    for f in bm.faces:
        mound.append((f.calc_center_median().copy(), f.normal.copy(), f.calc_area(), [v.co.copy() for v in f.verts]))
    parts = [cl.bright(pl.to_object('mound', bm, rock, smooth=False), 1.0, 0.3)]
    # Chunks cover the whole mound: blue crystals on the left and top, grey rock chunks on the right and here and
    # there among the crystals (the sprite's dark grey patches).
    rng = random.Random(53)
    faces = [f for f in mound if f[0].z >= u(2) and f[1].z >= -0.3]
    # Area-weighted samples over the mound (the polar grid's faces grow toward its foot).
    candidates = []
    for centre, normal, _, corners in rng.choices(faces, weights=[f[2] for f in faces], k=120):
        candidates.append((rng.random(), centre.lerp(rng.choice(corners), rng.uniform(0.0, 0.7)), normal))
    candidates.sort(key=lambda c: c[0])
    count = (84, 44, 14)[level]
    rng = random.Random(59)
    # The sprite's spike at the crest (x 48, up to 98) leads the list, so every level keeps it.
    peak = P(48, 0, crest_at(48) - 14)
    candidates.insert(0, (0.0, peak, Vector((0.05, 0, 1)).normalized()))
    for i, (_, position, normal) in enumerate(candidates[:count]):
        sx = position.x / u(1) + width / 2
        blue = sx + rng.uniform(-18, 18) < 100 and rng.random() > 0.12
        radius = (rng.uniform(10, 16) if blue else rng.uniform(9, 14)) * ((1.0, 1.2, 1.5)[level])
        if i == 0:
            radius, normal = 8.0, Vector((0.05, 0, 1))
        d = (normal + Vector((0, 0, 0.35)) + Vector((rng.uniform(-.5, .5), rng.uniform(-.5, .5), 0))).normalized()
        length = radius * (rng.uniform(1.3, 1.8) if blue else rng.uniform(0.9, 1.3)) * (2.2 if i == 0 else 1.0)
        base = position - d * u(length * 0.4)
        sides = (5 if i % 3 == 0 else 4) if level < 2 else 4
        # Chunky broken crystals: four- and five-sided, chamfered at LOD0, without the mid ring; rock chunks blunt.
        parts.append(cl.prism(f'b{i}', base, base + d * u(length), u(radius), c if blue else rock, sides=sides,
                              chamfer=0.25 if level == 0 else 0.0, tip_fraction=1.2 if blue else 0.6,
                              flat=rng.uniform(0.7, 1.0), roll=rng.uniform(0, 3), brightness=rng.uniform(0.8, 1.15),
                              facets=FACETS[PROP] * (1.0 if level < 2 else 0.8)))
    return parts


# ---------------------------------------------------------------- crys5
LOBES = ((-36.0, 0.0, -12.0), (30.0, 0.0, -12.0))
LOBE_AXES = (62.0, 42.0, 94.0)


def crys5(level, mats):
    m = mats['Blade']
    rng = random.Random(71)
    blades = []
    for lobe in LOBES:
        for i in range(46):
            a = rng.uniform(0, 2 * math.pi)
            e = math.asin(rng.uniform(0.08, 1.0))
            d = Vector((math.cos(a) * math.cos(e) * LOBE_AXES[0], math.sin(a) * math.cos(e) * LOBE_AXES[1],
                        math.sin(e) * LOBE_AXES[2]))
            reach = rng.uniform(0.8, 1.0)
            blades.append((rng.random(), lobe, d, reach, rng.uniform(13.0, 19.0), rng.uniform(0.13, 0.2),
                           rng.uniform(0, math.pi)))
    blades.sort(key=lambda b: b[0])
    count = (90, 46, 20)[level]
    parts = []
    for i, (_, lobe, d, reach, width, flat, roll) in enumerate(blades[:count]):
        c = Vector(lobe)
        tip = c + d * reach
        base = c + d * 0.35
        # Wide petal-like blades, each turned at random about its length.
        parts.append(cl.prism(f'blade{i}', P(base.x + 94, base.y, base.z), P(tip.x + 94, tip.y, tip.z), u(width),
                              m, sides=6 if level < 2 else 4, tip_fraction=0.9, flat=flat, roll=roll,
                              mid=level == 0, brightness=rng.uniform(0.85, 1.12),
                              facets=FACETS[PROP]))
    # A low central boss under the two lobes, so the roots never show the ground between them.
    boss = pl.lathe('boss', [(u(40), 0), (u(28), u(6)), (u(10), u(9)), (u(2), u(10))], (16, 10, 8)[level], m,
                    u_repeat=2, v_scale=3)
    boss.scale = (1, 0.55, 1)
    cl.apply_transforms([boss])
    parts.append(cl.bright(boss, 0.6, 0.1))
    return parts


def crys5_factor(co, name):
    best = 2.0
    for lobe in LOBES:
        d = (Vector((co.x / u(1), co.y / u(1), co.z / u(1))) - Vector(lobe))
        t = math.sqrt((d.x / LOBE_AXES[0]) ** 2 + (d.y / LOBE_AXES[1]) ** 2 + (d.z / LOBE_AXES[2]) ** 2)
        best = min(best, t)
    return 0.55 * (min(1.0, best) ** 1.3 - 0.5)          # rank shift: dark heart, bright blade tips


def _blue(rgb, rows):
    return (rgb[:, 2] - rgb[:, 0]) > 18


# Which native texels each material's ramp is built from (default: all opaque texels).
RAMP_SELECT = {('crys6', 'Crystal'): _blue, ('crys6', 'Rock'): lambda rgb, rows: ~_blue(rgb, rows),
               ('crclstr', 'Pebble'): lambda rgb, rows: rows >= 256 - 40}


# Ramp saturation boost against the gloss's white sheen (the quartz is natively near grey and keeps its own).
SATURATE = {('crystl0', 'Crystal'): 1.4, ('crys5', 'Blade'): 1.1, ('crys6', 'Crystal'): 1.3}


BUILD = {'crystl0': (crystl0, crystl0_factor), 'crclstr': (crclstr, crclstr_factor), 'crys6': (crys6, None),
         'crys5': (crys5, crys5_factor)}


def main():
    pl.reset()
    names = [k for k in NATIVE[PROP] if k != 'size']
    texture = {'Crystal': 'crystal', 'Quartz': 'crystal', 'Pebble': 'crystal', 'Blade': 'crystal', 'Rock': 'greyrock'}
    mats = {}
    for name in names:
        extras = {'openyamm_specular': SPECULAR[name]}
        if PROP == 'crystl0' and name == 'Crystal':
            extras['openyamm_pulse'] = CRYSTL0_PULSE
        mats[name] = cl.material(name, texture[name], extras=extras)
    gain = ALBEDO_GAIN.get(PROP, 1.0)
    file = {'crystl0': 'crystl0_p549.png', 'crclstr': 'crclstr_p142.png', 'crys6': 'crys6_p142.png',
            'crys5': 'crys5_p142.png'}[PROP]
    ramps = {name: cl.native_ramp(file, RAMP_SELECT.get((PROP, name)), saturate=SATURATE.get((PROP, name), 1.0))
             for name in names}
    means = {name: cl.texture_mean(mats[name]) for name in names}
    print('RAMPS', {n: [tuple(round(float(c), 3) for c in r[k]) for k in (0, len(r) // 2, -1)] for n, r in ramps.items()})
    build, factor = BUILD[PROP]
    lods = []
    base_name = PROP.capitalize()
    for level in range(3):
        parts = build(level, mats)
        cl.apply_transforms(parts)
        solid = pl.join(f'{PROP}{level}', parts)
        cl.clip_ground(solid)
        name = base_name if level == 0 else f'{base_name}_LOD{level}'
        lods.append(cl.finish_lod(solid, name, (40, 24, 12)[level], u(16), OCCLUSION.get(PROP, 0.6), None,
                                  factor, ramps=ramps, means=means, gain={n: gain for n in names}))
    cl.save_and_export(PROP, lods)


main()
