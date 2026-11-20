"""Builders for the eleven props redone in real 3D. Each lies naturally on the ground in the XY plane (Blender Z up).
Usage: blender --background --python build_props.py -- <icon> [...]"""
import math
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
import propkit as k  # noqa: E402

TAU = math.tau


def offset_polyline(points, distance):
    """Mitred offset of an open polyline to its left (positive distance)."""
    points = [Vector(p) for p in points]
    result = []
    for i, p in enumerate(points):
        normals = []
        if i > 0:
            d = (p - points[i - 1]).normalized()
            normals.append(Vector((-d.y, d.x)))
        if i < len(points) - 1:
            d = (points[i + 1] - p).normalized()
            normals.append(Vector((-d.y, d.x)))
        n = sum(normals, Vector((0, 0))).normalized()
        scale = 1 / max(0.35, n.dot(normals[0]))
        result.append(p + n * distance * scale)
    return result


def band(name, points, left, right, z0, z1, mat, bevel=0.0):
    outline = offset_polyline(points, left) + list(reversed(offset_polyline(points, right)))
    return k.slab(name, [tuple(v) for v in outline], z0, z1, mat, bevel)


def loop_tube(name, points, radius, mat, sides=6, z=0.0, z_scale=1.0):
    """Closed tube following a closed XY path."""
    points = [Vector((p[0], p[1], z)) for p in points]
    count = len(points)
    vertices = []
    for i, p in enumerate(points):
        tangent = (points[(i + 1) % count] - points[i - 1]).normalized()
        normal = Vector((-tangent.y, tangent.x, 0)).normalized()
        for j in range(sides):
            b = TAU * j / sides
            vertices.append(p + normal * radius * math.cos(b) + Vector((0, 0, radius * z_scale * math.sin(b))))
    faces = [(i * sides + j, i * sides + (j + 1) % sides, ((i + 1) % count) * sides + (j + 1) % sides,
              ((i + 1) % count) * sides + j) for i in range(count) for j in range(sides)]
    return k.mesh(name, vertices, faces, mat)


def place(objects, origin=(0, 0, 0), angle=0.0):
    matrix = Matrix.Translation(origin) @ Matrix.Rotation(math.radians(angle), 4, 'Z')
    for obj in objects:
        obj.data.transform(matrix)
        obj.data.update()
    return objects


# ---------------------------------------------------------------- 7item150 Moonstone
def moonstone():
    parts = [k.slab('back', ellipse(.44, .47, 32), 0, .04, 'gold', bevel=.01)]
    parts.append(k.ring('frame', (0, 0, .055), (.43, .46), .042, 'gold', segments=40, sides=8))
    parts.append(k.ring('bezel', (0, 0, .07), (.355, .385), .022, 'gold', segments=40, sides=6))
    for i in range(16):
        a = TAU * (i + .5) / 16
        parts.append(k.uv_ball('scallop', (.49 * math.cos(a), .52 * math.sin(a), .04), (.04, .04, .032), 'gold',
                               8, 4))
    parts.append(k.cabochon('moonstone', (0, 0, .03), (.35, .38), .2, 'moonstone', 24, 6))
    return parts


def ellipse(rx, ry, count):
    return [(rx * math.cos(TAU * i / count), ry * math.sin(TAU * i / count)) for i in range(count)]


# ---------------------------------------------------------------- 7item159 Philosopher's Stone
def philosophers_stone():
    parts = [k.faceted_stone('stone', (0, 0, 0), (.9, .9, .46), 'smoky_violet', sides=4, rotation=0)]
    # Bevel the four-sided cushion's long facets into an eight-sided read without losing its diamond outline.
    parts[0].modifiers.new('bevel', 'BEVEL').width = .05
    k.apply_modifier(parts[0], parts[0].modifiers[0])
    for a in range(4):
        angle = TAU * a / 4
        tip = Vector((math.cos(angle) * .45, math.sin(angle) * .45, .17))
        parts.append(k.uv_ball('corner cap', tip, (.055, .055, .06), 'gold', 10, 5))
    for sign in (1, -1):
        # Crossed wires over the crown, from edge middle to edge middle.
        points = []
        for i in range(13):
            t = i / 12
            x = (-.26 + .52 * t)
            y = sign * (.26 - .52 * t)
            r = math.hypot(x, y)
            z = .5 - .25 * (r / .37) ** 2
            points.append((x, y, z))
        parts.append(k.tube('wire', points, .024, 'gold', 6))
    parts.append(k.uv_ball('crossing cap', (0, 0, .5), (.06, .06, .035), 'gold', 10, 5))
    parts.append(k.faceted_stone('centre diamond', (0, 0, .5), (.08, .08, .07), 'diamond', sides=8))
    return parts


# ---------------------------------------------------------------- 7item363 / 7item364 Altar Pieces
def altar(mirror, wide_arms):
    points = [(.2, .42), (-.02, .42), (-.21, 0.0), (-.02, -.42), (.2, -.42)]
    if wide_arms:
        points = [(.22, .43), (-.04, .43), (-.21, 0.0), (-.04, -.43), (.22, -.43)]
    if mirror:
        points = [(-x, y) for x, y in points]
    # With the polyline running from the top arm downwards, its left side is the inside of the bracket unless
    # mirrored.
    inner = -1 if mirror else 1
    w = .11
    parts = [band('block', points, -w, w, 0, .13, 'violet_stone', bevel=.012)]
    parts.append(band('outer rim', points, -w * inner, -.03 * inner, .12, .19, 'violet_stone', bevel=.012))
    parts.append(band('inner lip', points, .075 * inner, w * inner, .12, .15, 'violet_stone', bevel=.008))
    return parts


# ---------------------------------------------------------------- ankh
def ankh():
    t0, t1 = 0.0, .1
    stem = [(-.05, .02), (.05, .02), (.07, -.3), (.12, -.62), (-.12, -.62), (-.07, -.3)]
    bar = [(-.4, -.05), (-.24, -.0), (-.06, .01), (.06, .01), (.24, -.0), (.4, -.05), (.4, .17), (.24, .12),
           (.06, .1), (-.06, .1), (-.24, .12), (-.4, .17)]
    parts = [k.slab('stem', stem, t0, t1, 'gold', bevel=.025, segments=2, smooth=True),
             k.slab('crossbar', bar, t0, t1, 'gold', bevel=.025, segments=2, smooth=True)]
    loop = k.ring('loop', (0, .31, .05), (.15, .2), .055, 'gold', segments=32, sides=10, z_scale=.9)
    parts.append(loop)
    return parts


# ---------------------------------------------------------------- item263 Telelocator
def telelocator():
    profile = [(0.0, .0), (0.0, .024), (.012, .03), (.03, .03), (.04, .022)]
    y = .04
    while y < .8:
        profile += [(y + .015, .02), (y + .07, .02), (y + .078, .027), (y + .092, .027), (y + .1, .02)]
        y += .1
    profile += [(.82, .022), (.84, .032), (.86, .032), (.87, .026), (.89, .036), (.9, .036), (.91, .024),
                (.93, .02)]
    rod = k.lathe('rod', profile, 'gold', segments=12)
    parts = [rod]
    helix = []
    for i in range(110):
        t = i / 109
        yy = .06 + .74 * t
        a = TAU * 6 * t
        helix.append((.021 * math.cos(a), yy, .021 * math.sin(a)))
    parts.append(k.tube('carved spiral', helix, .0055, 'gold', 5))
    skull_z = 0.0
    parts.append(k.uv_ball('cranium', (0, .985, skull_z + .008), (.052, .058, .055), 'gold', 14, 8))
    parts.append(k.box('jaw', (0, .935, skull_z - .02), (.06, .05, .04), 'gold', bevel=.012, segments=2))
    for side in (-1, 1):
        parts.append(k.uv_ball('eye socket', (side * .022, .97, skull_z - .04), (.016, .016, .014), 'dark', 8, 4))
    parts.append(k.uv_ball('nose', (0, .945, skull_z - .045), (.008, .01, .008), 'dark', 6, 4))
    # Lie on the ground: tilt so the skull and the butt cap both touch.
    tilt = math.atan2(.06 - .03, .95)
    for obj in parts:
        obj.data.transform(Matrix.Rotation(math.pi, 4, 'Y'))  # face of the skull upward
        obj.data.transform(Matrix.Rotation(tilt, 4, 'X'))
        obj.data.update()
    return parts


# ---------------------------------------------------------------- keys
def key(name, length, mat, bow='ring', bit='simple', bow_size=.06, shaft=.013, gem=None):
    """A key with its bow at the origin and its shaft running down -Y, lying flat (axis at z = shaft)."""
    z = shaft
    parts = []
    if bow == 'ring':
        parts.append(k.ring(name + ' bow', (0, bow_size * .9, z), (bow_size, bow_size * 1.1), .013, mat, 18, 6))
    elif bow == 'trefoil':
        for dx, dy in ((-.04, .045), (.04, .045), (0, .085)):
            parts.append(k.ring(name + ' lobe', (dx, dy, z), (.032, .032), .011, mat, 14, 6))
    elif bow == 'gem':
        parts.append(k.ring(name + ' bow', (0, bow_size * .9, z), (bow_size, bow_size), .016, mat, 18, 6))
    elif bow == 'fleur':
        outline = [(0, .0), (.03, .02), (.07, .03), (.1, .08), (.075, .09), (.06, .065), (.045, .085),
                   (.06, .13), (.03, .16), (.02, .12), (0, .15), (-.02, .12), (-.03, .16), (-.06, .13),
                   (-.045, .085), (-.06, .065), (-.075, .09), (-.1, .08), (-.07, .03), (-.03, .02)]
        parts.append(k.slab(name + ' bow', outline, z - .012, z + .012, mat, bevel=.006))
    if gem:
        colour, shape = gem
        centre = (0, bow_size * .9, z + .004)
        if shape == 'crystal':
            parts.append(k.faceted_stone(name + ' gem', (0, bow_size * .9, z - .01), (.07, .1, .06), colour, 6,
                                         rotation=math.pi / 2))
        elif shape == 'rough':
            parts.append(k.ball(name + ' gem', (0, bow_size * .9, z + .01), (.05, .055, .035), colour, 1))
        else:
            parts.append(k.cabochon(name + ' gem', (0, bow_size * .9, z - .012), (.048, .052), .05, colour, 14, 4))
    parts.append(k.tube(name + ' shaft', [(0, 0, z), (0, -length, z)], shaft, mat, 8))
    parts.append(k.ring(name + ' collar', (0, -.02, z), (shaft * 1.6, shaft * 1.6), shaft * .5, mat, 10, 5))
    end = -length
    if bit == 'simple':
        parts.append(k.box(name + ' bit', (.035, end + .035, z), (.045, .045, .022), mat, .004))
        parts.append(k.box(name + ' tooth', (.06, end + .02, z), (.018, .025, .022), mat, .004))
    elif bit == 'double':
        parts.append(k.box(name + ' bit', (0, end + .04, z), (.11, .04, .022), mat, .004))
        parts.append(k.box(name + ' ward', (-.045, end + .075, z), (.022, .03, .022), mat, .004))
        parts.append(k.box(name + ' ward', (.045, end + .01, z), (.022, .03, .022), mat, .004))
    elif bit == 'ornate':
        outline = [(-.01, 0), (.03, .0), (.04, -.02), (.08, -.01), (.1, .03), (.07, .02), (.06, .05), (.09, .08),
                   (.05, .075), (.03, .095), (-.01, .09)]
        bit_part = k.slab(name + ' bit', [(x, y + end) for x, y in outline], z - .011, z + .011, mat, .004)
        parts.append(bit_part)
    return parts


def keys2():
    parts = key('key', .5, 'copper', bow='fleur', bit='ornate', shaft=.017)
    for y in (-.05, -.09):
        parts.append(k.ring('collar', (0, y, .017), (.026, .026), .008, 'copper', 12, 5))
    parts.append(k.box('bit plate', (.07, -.47, .017), (.14, .05, .022), 'copper', .005))
    parts.append(k.box('bit wing', (.13, -.44, .017), (.03, .08, .022), 'copper', .005))
    return place(parts, angle=-25)


def ring_of_keys():
    parts = [k.ring('ring', (0, .3, .016), (.09, .09), .016, 'old_brass', 28, 6)]
    gems = [('pearl', 'pearl'), ('amethyst', 'crystal'), ('emerald', 'cabochon'), ('amber', 'rough')]
    angles = [-24, -8, 8, 24]
    for i, (angle, gem) in enumerate(zip(angles, gems)):
        piece = key(f'key{i}', .38, 'old_brass', bow='gem', bit='double' if i % 2 else 'simple', bow_size=.05,
                    gem=gem)
        # Bows hang side by side from the bottom of the ring, keys fanning slightly downwards.
        place(piece, origin=(-.15 + .1 * i, .1 + .015 * (1 - abs(i - 1.5)), .004 * (i % 2)), angle=angle)
        parts += piece
    for i in range(3):
        parts.append(k.uv_ball('bead', (-.1 + .1 * i, .215, .02), (.022, .022, .02), 'old_brass', 8, 4))
        parts.append(k.tube('link', [(-.1 + .1 * i, .23, .016), ((-.1 + .1 * i) * .4, .3, .016)], .008, 'old_brass',
                            5))
    return parts


def dragon_tower_keys():
    parts = [k.ring('ring', (0, .25, .02), (.2, .2), .02, 'copper', 30, 6)]
    parts.append(k.uv_ball('bead', (0, .45, .025), (.032, .028, .03), 'iron', 10, 5))
    specs = [('copper', 'ring', 'simple', -30, .36), ('rust', 'ring', 'double', -15, .42),
             ('iron', 'ring', 'simple', 0, .36), ('old_brass', 'ring', 'double', 13, .44),
             ('iron', 'trefoil', 'ornate', 28, .38)]
    for i, (mat, bow, bit, angle, length) in enumerate(specs):
        piece = key(f'key{i}', length, mat, bow=bow, bit=bit, bow_size=.05)
        place(piece, origin=(-.1 + .05 * i, .06 + .02 * (1 - abs(i - 2) / 2), .003 * (i % 2)), angle=angle * .6)
        parts += piece
    return parts


# ---------------------------------------------------------------- item327 Enchanted Amulet
def shield_outline(scale=1.0, count=40):
    """Rounded top, pointed bottom; closed outline starting at the top centre, clockwise."""
    half = count // 2
    right = []
    for i in range(1, half + 1):
        s = i / half
        if s < .45:
            a = math.radians(90 - 100 * s / .45)
            p = (.31 * math.cos(a), .2 + .26 * math.sin(a))
        else:
            u = (s - .45) / .55
            p0, c, p1 = Vector((.306, .155)), Vector((.3, -.2)), Vector((0, -.5))
            p = tuple((1 - u) ** 2 * p0 + 2 * (1 - u) * u * c + u * u * p1)
        right.append(p)
    left = [(-x, y) for x, y in reversed(right[:-1])]
    return [(x * scale, y * scale) for x, y in [(0, .46)] + right + left]


def enchanted_amulet():
    outline = shield_outline()
    parts = [k.slab('back', outline, 0, .05, 'gold', bevel=.01)]
    parts.append(loop_tube('rim', outline, .03, 'gold', 6, z=.055))
    parts.append(k.cabochon('heart stone', (0, .0, .05), (.12, .16), .1, 'aquamarine', 24, 5))
    parts.append(k.ring('heart bezel', (0, .0, .058), (.125, .165), .016, 'gold', 28, 6))
    for row, (scale, count, size) in enumerate(((.8, 18, .05), (.58, 12, .042))):
        stones = shield_outline(scale, count)
        for i, (x, y) in enumerate(stones):
            colour = 'sapphire' if (i + row) % 2 else 'turquoise'
            parts.append(k.cabochon('stone', (x, y - .02, .045), (size, size), size, colour, 8, 2))
            if row == 0:
                nx, ny = stones[(i + 1) % len(stones)]
                parts.append(k.uv_ball('bead', ((x + nx) / 2, (y + ny) / 2 - .02, .06), (.013, .013, .013), 'gold',
                                       6, 3))
    parts.append(k.ring('bail', (0, .5, .03), (.05, .05), .016, 'gold', 16, 6))
    return parts


# ---------------------------------------------------------------- shovel
def shovel():
    r = .024
    parts = [k.tube('shaft', [(0, .27 + .73 * i / 8, r) for i in range(9)], r, 'wood', 10,
                    radii=[r * (1.0 - .12 * i / 8) for i in range(9)])]
    parts.append(k.lathe('grip cap', [(0, 0), (0, .022), (.02, .026), (.04, .02), (.045, 0)], 'wood', segments=10))
    parts[-1].data.transform(Matrix.Translation((0, .995, r)))
    socket = k.lathe('socket', [(0, .0), (0, .03), (.03, .034), (.12, .028), (.13, .024), (.13, 0)], 'steel',
                     segments=10)
    socket.data.transform(Matrix.Translation((0, .17, r)))
    parts.append(socket)
    # Spade blade dished across its width, pointed at the bottom, lying with its underside on the ground.
    vertices, faces = [], []
    rows, cols = 9, 9
    for i in range(rows):
        v = i / (rows - 1)
        y = .19 - .3 * v
        half = .13 * (1 - max(0.0, (v - .45) / .55) ** 1.6) + .004
        for j in range(cols):
            u = j / (cols - 1) * 2 - 1
            x = u * half
            z = .006 + .045 * u * u
            vertices.append((x, y, z))
    top = len(vertices)
    for i in range(rows):
        for j in range(cols):
            x, y, z = vertices[i * cols + j]
            vertices.append((x, y, z + .012))
    for i in range(rows - 1):
        for j in range(cols - 1):
            a = i * cols + j
            faces.append((a, a + cols, a + cols + 1, a + 1))
            faces.append((top + a, top + a + 1, top + a + cols + 1, top + a + cols))
    border = [i * cols for i in range(rows)] + [(rows - 1) * cols + j for j in range(1, cols)] + \
        [i * cols + cols - 1 for i in range(rows - 2, -1, -1)] + [j for j in range(cols - 2, 0, -1)]
    for a, b in zip(border, border[1:] + border[:1]):
        faces.append((a, b, top + b, top + a))
    blade = k.mesh('blade', vertices, faces, 'steel')
    parts.append(blade)
    return parts


BUILDERS = {
    '7item150': moonstone, '7item159': philosophers_stone,
    '7item363': lambda: altar(mirror=True, wide_arms=False), '7item364': lambda: altar(mirror=False, wide_arms=True),
    'ankh': ankh, 'item263': telelocator, 'item295': ring_of_keys, 'item327': enchanted_amulet,
    'keyring': dragon_tower_keys, 'keys2': keys2, 'shovel': shovel,
}


def main():
    icons = sys.argv[sys.argv.index('--') + 1:] or list(BUILDERS)
    for icon in icons:
        k.reset()
        parts = BUILDERS[icon]()
        obj = k.join(parts, icon)
        k.bake_and_export(obj, icon)


if __name__ == '__main__':
    main()
