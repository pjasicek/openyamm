"""Nine organic ground items rebuilt as closed 3D models (replacing flat reliefs). Run:
    blender --background --python build_designs.py -- [icon ...]      -> work/<icon>_export.glb
Each icon has its own design function; the shared kit is organic_kit.py."""
import math
import random
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import organic_kit as kit  # noqa: E402
from organic_kit import Builder  # noqa: E402

V = Vector


def rotate(vector, axis, degrees):
    return Matrix.Rotation(math.radians(degrees), 3, V(axis).normalized()) @ V(vector)


def frame(axis):
    axis = V(axis).normalized()
    side = (V((1, 0, 0)) if abs(axis.x) < 0.9 else V((0, 1, 0))).cross(axis).normalized()
    return axis, side, axis.cross(side)


def rounded(t):
    """Petal outline: narrow claw at the base, broad rounded end."""
    return max(0.0, 1 - ((t - 0.62) / 0.62) ** 2) ** 0.5 * (0.55 + 0.45 * t)


def bloom(b, key, centre, axis, scale, layers, cup=0.35, outer_bend=-1.5, seed=0, inner_bend=1.2):
    """Rose-like bloom: rings of cupped petals opening progressively from a tight centre."""
    rng = random.Random(seed)
    axis, a1, a2 = frame(axis)
    for index, (count, radius, length, width, opening) in enumerate(layers):
        offset = rng.random() * 360
        for j in range(count):
            theta = math.radians(offset + 360 * j / count + rng.uniform(-8, 8))
            radial = a1 * math.cos(theta) + a2 * math.sin(theta)
            tangent = axis.cross(radial)
            angle = math.radians(opening + rng.uniform(-6, 6))
            direction = axis * math.cos(angle) + radial * math.sin(angle)
            outermost = index == len(layers) - 1
            # Inner petals wrap towards the centre; the outermost ring turns back.
            bend = outer_bend if outermost else inner_bend * (1 - index / max(1, len(layers) - 1))
            b.blade(key, V(centre) + radial * radius * scale, direction, tangent, length * scale, width * scale,
                    0.012 * scale, rings=6, ring=6, cup=-cup, bend=bend, profile=rounded)


def leaf_at(b, key, base, direction, side, length, width, droop=0.4, cup=0.15, thickness=0.012):
    b.blade(key, base, direction, side, length, width, thickness, rings=6, ring=6, cup=cup, bend=-droop,
            profile=lambda t: math.sin(math.pi * min(1.0, 0.05 + 0.95 * t)) ** 0.8)


# ---- designs ----------------------------------------------------------------------------------------------------

def rose():
    b = Builder('rose')
    b.cell('petal', (0, 0, 2, 2), kit.petal, base=(120, 0, 10), tip=(225, 25, 30), veins=7, vein_dark=0.88)
    b.cell('leaf', (2, 0, 2, 1), kit.leaf, colour=(38, 92, 28), rib=(90, 130, 50))
    b.cell('stem', (2, 1, 1, 1), kit.stem, colour=(45, 85, 30))
    centre = V((0, 0, 0.17))
    axis = V((0, -0.35, 1))
    bloom(b, 'petal', centre, axis, 1.0, [(3, 0.0, 0.1, 0.12, 4), (4, 0.015, 0.13, 0.15, 14),
                                          (5, 0.03, 0.17, 0.19, 30), (6, 0.045, 0.21, 0.22, 50),
                                          (7, 0.06, 0.24, 0.24, 72)], cup=0.45, outer_bend=-1.6, seed=3)
    for k, angle in enumerate((200, 320, 80)):
        d = rotate(V((1, 0, -0.18)), (0, 0, 1), angle)
        leaf_at(b, 'leaf', centre + V((0, 0, -0.1)) + d * 0.05, d, rotate(d, (0, 0, 1), 90), 0.36, 0.18,
                droop=0.15)
    b.tube('stem', [centre + V((0, 0.02, -0.08)), V((0.05, 0.16, 0.05)), V((0.1, 0.32, 0.02))],
           [0.022, 0.018, 0.016])
    return b


def flower_rose():
    b = Builder('7item269')
    b.cell('petal', (0, 0, 2, 2), kit.petal, base=(120, 0, 10), tip=(225, 25, 30), veins=7, vein_dark=0.88)
    b.cell('leaf', (2, 0, 2, 1), kit.leaf, colour=(36, 88, 30), rib=(85, 125, 50))
    b.cell('stem', (2, 1, 1, 1), kit.stem, colour=(40, 80, 28))
    b.cell('thorn', (3, 1, 1, 1), kit.solid, colour=(90, 70, 30), rough=0.6)
    stem = [V((-0.62, 0, 0.012)), V((-0.3, 0.01, 0.014)), V((0.0, 0.0, 0.02)), V((0.22, -0.01, 0.045)),
            V((0.36, 0.0, 0.09))]
    b.tube('stem', stem, [0.011, 0.012, 0.012, 0.013, 0.014], ring=6)
    head = V((0.4, 0.0, 0.12))
    axis = V((1, 0, 0.45))
    bloom(b, 'petal', head, axis, 0.95, [(3, 0.0, 0.1, 0.12, 4), (4, 0.015, 0.13, 0.15, 12),
                                         (5, 0.03, 0.17, 0.19, 24), (6, 0.045, 0.2, 0.21, 40)],
          cup=0.45, outer_bend=-1.0, seed=7)
    a, s1, s2 = frame(axis)
    for j in range(5):
        r = s1 * math.cos(j * 1.256) + s2 * math.sin(j * 1.256)
        b.blade('leaf', head + a * 0.01, -a * 0.6 + r, r.cross(a), 0.09, 0.03, 0.008, rings=4, ring=4)
    for x, y_sign in ((-0.12, 1), (0.1, -1)):
        base = V((x, 0, 0.016))
        rachis = V((0.35, y_sign * 1.0, 0.05)).normalized()
        b.tube('stem', [base, base + rachis * 0.1], [0.006, 0.005], ring=4)
        tip = base + rachis * 0.1
        for angle, scale in ((0, 1.0), (55, 0.8), (-55, 0.8)):
            d = rotate(rachis, (0, 0, 1), angle)
            leaf_at(b, 'leaf', tip, d + V((0, 0, 0.05)), rotate(d, (0, 0, 1), 90), 0.13 * scale, 0.075 * scale,
                    droop=0.05, cup=0.1, thickness=0.008)
    for x, angle in ((-0.45, 90), (-0.25, -90), (-0.02, 90), (0.18, -90), (0.28, 0)):
        point = V((x, 0, 0.014))
        out = rotate(V((0, 1, 0.4)), (1, 0, 0), angle) if angle else V((0, 0, 1))
        b.blade('thorn', point, out, V((1, 0, 0)), 0.03, 0.016, 0.012, rings=3, ring=4,
                profile=lambda t: 1 - t)
    return b


def crushed_petals():
    b = Builder('7item144')
    b.cell('petal', (0, 0, 2, 2), kit.petal, base=(190, 20, 100), tip=(255, 150, 200), veins=8, vein_dark=0.8)
    b.cell('loose', (2, 0, 1, 1), kit.petal, base=(170, 15, 90), tip=(250, 120, 185), veins=6, edge_dark=0.7)
    b.cell('leaf', (3, 0, 1, 1), kit.leaf, colour=(46, 120, 40), rib=(110, 160, 70))
    b.cell('stem', (2, 1, 1, 1), kit.stem, colour=(40, 90, 30))
    head = V((0.05, 0.12, 0.12))
    bloom(b, 'petal', head, V((0.4, 0.3, 1)), 0.85, [(4, 0.0, 0.1, 0.12, 8), (6, 0.025, 0.15, 0.16, 30),
                                                     (8, 0.045, 0.19, 0.19, 55), (9, 0.06, 0.2, 0.19, 78)],
          cup=0.3, outer_bend=-2.0, seed=11)
    b.tube('stem', [head + V((-0.02, -0.03, -0.07)), V((-0.08, -0.12, 0.03)), V((-0.2, -0.3, 0.012)),
                    V((-0.3, -0.42, 0.012))], [0.012, 0.011, 0.01, 0.009])
    for point, d in ((V((-0.12, -0.18, 0.02)), V((1, -0.6, 0.05))), (V((-0.2, -0.3, 0.015)), V((-0.9, 0.2, 0.08)))):
        leaf_at(b, 'leaf', point, d, rotate(d, (0, 0, 1), 90), 0.2, 0.1, droop=0.1)
    rng = random.Random(5)
    for k in range(11):
        x = rng.uniform(-0.25, 0.32)
        y = rng.uniform(-0.45, -0.12) if k < 8 else rng.uniform(0.25, 0.4)
        d = rotate(V((1, 0, 0)), (0, 0, 1), rng.uniform(0, 360))
        b.blade('loose', V((x, y, 0.008)), d + V((0, 0, rng.uniform(-0.02, 0.06))), rotate(d, (0, 0, 1), 90),
                rng.uniform(0.09, 0.14), rng.uniform(0.08, 0.11), 0.008, rings=4, ring=6, cup=0.35,
                bend=rng.uniform(-1.2, 1.2), twist=rng.uniform(-0.8, 0.8), profile=rounded)
    return b


def dragons_eye():
    b = Builder('7item147')
    b.cell('eye', (0, 0, 2, 2), kit.eye)
    b.cell('bronze', (2, 0, 1, 1), kit.solid, colour=(150, 110, 60), rough=0.38, metal=1.0, grain=0.22)
    b.cell('enamel', (3, 0, 1, 1), kit.solid, colour=(120, 10, 8), rough=0.3, grain=0.1)
    b.cell('dark', (2, 1, 1, 1), kit.solid, colour=(70, 50, 30), rough=0.45, metal=1.0, grain=0.3)
    b.ellipsoid('dark', (0, 0, 0.03), (0.42, 0.42, 0.03), segments=24, rings=6)
    b.torus('bronze', (0, 0, 0.05), (0, 0, 1), 0.4, 0.05, segments=32, ring=8)
    b.torus('enamel', (0, 0, 0.055), (0, 0, 1), 0.315, 0.04, segments=32, ring=6)
    b.ellipsoid('eye', (0, 0, 0.05), (0.29, 0.29, 0.11), segments=24, rings=8, planar=True)
    for k in range(8):
        a = math.radians(22.5 + 45 * k)
        p = V((math.cos(a) * 0.36, math.sin(a) * 0.36, 0.085))
        b.ellipsoid('bronze', p, (0.045, 0.03, 0.03), axes=(V((math.cos(a), math.sin(a), 0)),
                                                             V((-math.sin(a), math.cos(a), 0)), V((0, 0, 1))),
                    segments=8, rings=4)
    b.torus('bronze', (0, 0.5, 0.025), (0, 0, 1), 0.07, 0.02, segments=16, ring=6)
    b.ellipsoid('bronze', (0, 0.44, 0.04), (0.04, 0.035, 0.03), segments=8, rings=4)
    return b


def datura():
    b = Builder('item167')
    b.cell('trumpet', (0, 0, 2, 2), kit.petal, base=(150, 175, 95), tip=(246, 244, 232), veins=5,
           vein_dark=0.9, edge_dark=0.95)
    b.cell('leaf', (2, 0, 2, 1), kit.leaf, colour=(34, 85, 30), rib=(120, 150, 80), veins=6)
    b.cell('calyx', (2, 1, 1, 1), kit.stem, colour=(70, 105, 45))

    def radius(t, theta):
        r = 0.03 + 0.045 * t + 0.2 * t ** 3.2
        if t > 0.72:
            lobe = max(0.0, math.cos(5 * theta)) ** 3
            r *= 1 + 0.32 * lobe * (t - 0.72) / 0.28
        return r

    axis = [V((-0.32 + 0.6 * t, 0.0, 0.13 + 0.06 * t * t)) for t in [i / 11 for i in range(12)]]
    b.shell('trumpet', axis, radius, 0.012, segments=30)
    b.tube('calyx', [axis[0] - V((0.02, 0, 0)), axis[3]], [0.045, 0.05], ring=8)
    b.tube('calyx', [axis[0] - V((0.0, 0, 0.0)), V((-0.42, 0.06, 0.07)), V((-0.5, 0.12, 0.02))],
           [0.016, 0.013, 0.011], ring=6)
    leaf_at(b, 'leaf', V((-0.42, 0.08, 0.04)), V((0.5, 1.0, -0.05)), V((-1, 0.5, 0)), 0.5, 0.26, droop=0.2,
            cup=0.12, thickness=0.014)
    return b


def heart(size, points=24):
    """Heart outline with its notch at +x, resampled evenly by arc length and centred on its area centre."""
    dense = []
    for k in range(480):
        t = 2 * math.pi * k / 480
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        dense.append(((y + 2) * size / 32, x * size / 32))
    lengths = [0.0]
    for k in range(1, len(dense) + 1):
        p, q = dense[k - 1], dense[k % len(dense)]
        lengths.append(lengths[-1] + math.hypot(q[0] - p[0], q[1] - p[1]))
    outline, j = [], 0
    for k in range(points):
        target = lengths[-1] * k / points
        while lengths[j + 1] < target:
            j += 1
        f = (target - lengths[j]) / max(lengths[j + 1] - lengths[j], 1e-12)
        p, q = dense[j], dense[(j + 1) % len(dense)]
        outline.append((p[0] + (q[0] - p[0]) * f, p[1] + (q[1] - p[1]) * f))
    # Fan from the area centre, away from the notch, so no slender triangles reach into it.
    cx = sum(p[0] for p in outline) / points
    return [(x - cx, y) for x, y in outline]


def clover():
    b = Builder('clover')
    b.cell('leaf', (0, 0, 2, 2), kit.leaf, colour=(28, 135, 40), rib=(60, 165, 60), veins=5, chevron=(150, 215, 120))
    b.cell('stem', (2, 0, 1, 1), kit.stem, colour=(45, 110, 35))
    centre = V((0, 0, 0.05))
    for k in range(4):
        d = rotate(V((1, 0, 0)), (0, 0, 1), 45 + 90 * k + (6 if k % 2 else -4))
        b.slab('leaf', centre + d * 0.2 + V((0, 0, 0.012 * k)), V((0, 0, 1)) - d * 0.12, d, heart(0.44), 0.016,
               cup=0.06)
    b.tube('stem', [centre + V((0, 0, -0.01)), V((0.05, -0.12, 0.03)), V((0.08, -0.32, 0.012)),
                    V((0.06, -0.46, 0.01))], [0.018, 0.016, 0.014, 0.012])
    return b


def poppysnaps_bush():
    b = Builder('7item143')
    b.cell('flower', (0, 0, 2, 2), kit.radial, centre=(215, 120, 15), petal_colour=(255, 212, 35),
           tip=(255, 236, 110), centre_radius=0.16, rays=5)
    b.cell('leaf', (2, 0, 2, 1), kit.leaf, colour=(30, 100, 30), rib=(80, 140, 50), veins=6)
    b.cell('stem', (2, 1, 1, 1), kit.stem, colour=(50, 100, 30))
    rng = random.Random(21)
    base = V((-0.42, 0.0, 0.03))
    heads = []
    for k in range(10):
        angle = math.radians(-42 + 84 * k / 9 + rng.uniform(-5, 5))
        reach = rng.uniform(0.45, 0.7)
        head = base + V((math.cos(angle) * reach, math.sin(angle) * reach, rng.uniform(0.06, 0.2)))
        heads.append(head)
        middle = base.lerp(head, 0.55) + V((0, 0, 0.04))
        end = head - V((0, 0, 0.02))
        b.tube('stem', [base, base.lerp(middle, 0.5), middle, middle.lerp(end, 0.5), end],
               [0.011, 0.01, 0.009, 0.0085, 0.008], ring=5)
        facing = (V((0.6, head.y * 0.6, 1.0)) + V((rng.uniform(-0.3, 0.3), rng.uniform(-0.3, 0.3), 0))).normalized()
        b.star('flower', head, facing, 5, rng.uniform(0.085, 0.1), 0.05, 0.012, cup=0.12,
               phase=rng.uniform(0, 1.2), round_tips=3)
    for k in range(11):
        angle = math.radians(-70 + 140 * k / 10 + rng.uniform(-6, 6))
        d = V((math.cos(angle), math.sin(angle), rng.uniform(0.05, 0.35)))
        start = base + d.normalized() * rng.uniform(0.05, 0.25)
        leaf_at(b, 'leaf', start, d, rotate(d, (0, 0, 1), 90), rng.uniform(0.25, 0.36), rng.uniform(0.06, 0.08),
                droop=0.6, cup=0.2, thickness=0.01)
    return b


def poppysnaps_sprig():
    b = Builder('herb01')
    b.cell('flower', (0, 0, 2, 2), kit.radial, centre=(200, 150, 40), petal_colour=(248, 230, 130),
           tip=(255, 246, 190), centre_radius=0.16, rays=6)
    b.cell('leaf', (2, 0, 2, 1), kit.leaf, colour=(100, 140, 45), rib=(170, 190, 90), veins=7)
    b.cell('stem', (2, 1, 1, 1), kit.stem, colour=(110, 130, 50))
    rng = random.Random(9)
    base = V((-0.48, -0.02, 0.025))
    tips = []
    for k in range(3):
        angle = math.radians(-14 + 14 * k)
        end = base + V((math.cos(angle) * 0.62, math.sin(angle) * 0.62, 0.05 + 0.03 * k))
        b.tube('stem', [base, base.lerp(end, 0.5) + V((0, 0, 0.02)), end], [0.012, 0.011, 0.009], ring=5)
        tips.append(end)
    for k in range(9):
        stem_tip = tips[k % 3]
        anchor = base.lerp(stem_tip, rng.uniform(0.25, 0.8))
        side = 1 if k % 2 else -1
        d = V((0.75, side * rng.uniform(0.5, 0.9), rng.uniform(0.1, 0.4)))
        leaf_at(b, 'leaf', anchor, d, rotate(d, (0, 0, 1), 90), rng.uniform(0.3, 0.42), rng.uniform(0.08, 0.1),
                droop=0.7, cup=0.25, thickness=0.01)
    for k in range(7):
        stem_tip = tips[k % 3]
        head = stem_tip + V((rng.uniform(0.04, 0.12), rng.uniform(-0.12, 0.12), rng.uniform(0.02, 0.08)))
        b.tube('stem', [stem_tip, head], [0.007, 0.006], ring=4)
        facing = V((0.5 + rng.uniform(-0.3, 0.3), rng.uniform(-0.4, 0.4), 1.0)).normalized()
        b.star('flower', head, facing, 6, rng.uniform(0.075, 0.09), 0.035, 0.01, cup=0.18,
               phase=rng.uniform(0, 1), round_tips=1)
    return b


def dragonbane():
    b = Builder('item304')
    b.cell('petal', (0, 0, 2, 2), kit.petal, base=(235, 120, 20), tip=(215, 25, 18), veins=10, vein_dark=0.82,
           streak=(250, 200, 40))
    b.cell('leaf', (2, 0, 2, 1), kit.leaf, colour=(60, 100, 35), rib=(130, 150, 70))
    b.cell('stem', (2, 1, 1, 1), kit.stem, colour=(70, 90, 35))
    b.cell('stamen', (3, 1, 1, 1), kit.solid, colour=(245, 200, 60), rough=0.5)
    head = V((0.12, 0.0, 0.13))
    axis = V((0.45, 0.0, 1.0)).normalized()
    a, s1, s2 = frame(axis)
    for j in range(5):
        theta = math.radians(72 * j + 10)
        radial = s1 * math.cos(theta) + s2 * math.sin(theta)
        direction = (radial * math.cos(math.radians(18)) + a * math.sin(math.radians(18))).normalized()
        b.blade('petal', head + radial * 0.02, direction, a.cross(radial), 0.34, 0.32, 0.014, rings=7, ring=8,
                cup=-0.22, bend=0.7, twist=0.25 * (1 if j % 2 else -1), profile=rounded)
    for j in range(6):
        theta = math.radians(60 * j)
        radial = s1 * math.cos(theta) + s2 * math.sin(theta)
        tip = head + a * 0.13 + radial * 0.04
        b.tube('stamen', [head + a * 0.01, tip], [0.006, 0.005], ring=4)
        b.ellipsoid('stamen', tip, (0.016, 0.016, 0.012), segments=6, rings=4)
    b.tube('stem', [head - a * 0.03, V((-0.08, 0.0, 0.05)), V((-0.35, 0.04, 0.02)), V((-0.6, 0.05, 0.016))],
           [0.016, 0.014, 0.012, 0.011])
    for point, d in ((V((-0.2, 0.02, 0.03)), V((0.4, 1.0, 0.1))), (V((-0.36, 0.04, 0.02)), V((0.3, -1.0, 0.1))),
                     (V((-0.5, 0.05, 0.018)), V((-0.2, 1.0, 0.12)))):
        leaf_at(b, 'leaf', point, d, rotate(d, (0, 0, 1), 90), 0.2, 0.08, droop=0.2)
    for point, tilt in ((V((-0.02, 0.1, 0.06)), V((0.5, 1.0, 0.6))), (V((-0.05, -0.1, 0.05)), V((0.6, -1.0, 0.5)))):
        b.tube('stem', [V((-0.12, 0.0, 0.04)), point], [0.008, 0.007], ring=4)
        b.blade('petal', point, tilt, V((0, 0, 1)).cross(V(tilt)), 0.09, 0.05, 0.04, rings=4, ring=6)
    return b


DESIGNS = {'rose': rose, '7item269': flower_rose, '7item144': crushed_petals, '7item147': dragons_eye,
           'item167': datura, 'clover': clover, '7item143': poppysnaps_bush, 'herb01': poppysnaps_sprig,
           'item304': dragonbane}


def main():
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    for icon in args or list(DESIGNS):
        builder = DESIGNS[icon]()
        obj = builder.build()
        obj.data.calc_loop_triangles()
        (HERE / 'work').mkdir(exist_ok=True)
        kit.export(obj, HERE / 'work' / f'{icon}_export.glb')
        dims = obj.dimensions
        print('BUILT', icon, len(obj.data.loop_triangles), 'triangles', [round(x, 3) for x in dims], flush=True)


if __name__ == '__main__':
    main()
