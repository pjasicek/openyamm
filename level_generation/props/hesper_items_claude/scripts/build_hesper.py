"""Builds the Hesper ground items that need no Meshy (classification.json routes blender, flat and their variants) from
components, in world units: lying in their resting pose, longest horizontal side = the binding's length, lowest point
at 0, origin at the centre of the footprint, Blender Z up. Every face carries a material named after its surface class
(CLASSES), which the bake (hes_texture.py) turns into metallic, roughness and emission; the base colour comes from the
Codex paintings of the guide views. Writes work/<icon>.blend (object <icon>).
Usage: blender --background --python build_hesper.py -- <icon> [icon ...] | all"""
import json
import math
import os
import sys

import bmesh
import bpy
from mathutils import Euler, Matrix, Vector

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(HERE, 'work')
# Surface class: (metallic, roughness, emission strength); hes_texture.py reads the same table.
CLASSES = {'ceramic': (0, 0.42, 0), 'gold': (1, 0.32, 0), 'steel': (1, 0.5, 0), 'copper': (1, 0.38, 0),
           'resin': (0, 0.3, 0), 'bone': (0, 0.5, 0), 'glass': (0, 0.08, 0.15), 'crystal': (0, 0.08, 0.35),
           'glow': (0, 0.2, 1.0), 'screen': (0, 0.12, 0.6), 'leather': (0, 0.65, 0), 'cloth': (0, 0.8, 0),
           'paper': (0, 0.85, 0), 'food': (0, 0.9, 0), 'string': (0, 0.75, 0)}
CLASSES['auto'] = (0, 0.4, 0)    # resolved per texel from the painted colour (hes_texture.py)
CLAY = {'gold': (0.75, 0.6, 0.3), 'steel': (0.5, 0.5, 0.52), 'copper': (0.7, 0.4, 0.25), 'resin': (0.2, 0.15, 0.22),
        'glow': (0.5, 0.8, 1.0), 'glass': (0.6, 0.75, 0.85), 'crystal': (0.6, 0.75, 0.9), 'screen': (0.15, 0.2, 0.3),
        'leather': (0.4, 0.28, 0.18), 'cloth': (0.6, 0.15, 0.12), 'paper': (0.85, 0.8, 0.7), 'food': (0.4, 0.45, 0.2)}

parts = []


def material(name):
    if name not in bpy.data.materials:
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        bsdf = next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
        bsdf.inputs['Base Color'].default_value = (*CLAY.get(name, (0.85, 0.83, 0.78)), 1)
        bsdf.inputs['Metallic'].default_value = CLASSES[name][0]
        bsdf.inputs['Roughness'].default_value = CLASSES[name][1]
    return bpy.data.materials[name]


def place(bm, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1)):
    matrix = (Matrix.Translation(Vector(loc)) @ Euler([math.radians(a) for a in rot]).to_matrix().to_4x4()
              @ Matrix.Diagonal((*scale, 1)))
    bmesh.ops.transform(bm, matrix=matrix, verts=bm.verts)


def finish(bm, cls, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1), bevel=0.0, segments=1):
    if bevel:
        edges = [e for e in bm.edges if e.calc_face_angle(0) > math.radians(50)]
        bmesh.ops.bevel(bm, geom=edges, offset=bevel, segments=segments, affect='EDGES', profile=0.5,
                        clamp_overlap=True)
    place(bm, loc, rot, scale)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new(cls)
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(material(cls))
    obj = bpy.data.objects.new(cls, mesh)
    bpy.context.scene.collection.objects.link(obj)
    parts.append(obj)
    return obj


def box(size, cls, loc=(0, 0, 0), rot=(0, 0, 0), bevel=0.0, segments=1):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1)
    place(bm, scale=size)
    return finish(bm, cls, loc, rot, bevel=bevel, segments=segments)


def cyl(radius, depth, cls, loc=(0, 0, 0), rot=(0, 0, 0), sides=16, radius2=None, scale=(1, 1, 1), bevel=0.0):
    """A cylinder (or cone, radius2) along Z, centred."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=sides, radius1=radius,
                          radius2=radius if radius2 is None else radius2, depth=depth)
    place(bm, scale=scale)
    return finish(bm, cls, loc, rot, bevel=bevel)


def sphere(radius, cls, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1), segments=16, rings=8):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=rings, radius=radius)
    place(bm, scale=scale)
    return finish(bm, cls, loc, rot)


def torus(major, minor, cls, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1), segments=24, sides=8, section=(1, 1),
          arc=360.0, ripple=(0, 0.0)):
    """A torus round Z (section scales the tube: radial, height); arc < 360 leaves it open with capped ends;
    ripple (count, amount) swells the tube that many times round, as ribs."""
    bm = bmesh.new()
    closed = arc >= 360
    count = segments if closed else segments + 1
    rings = []
    for i in range(count):
        a = math.radians(arc) * i / segments
        centre = Vector((major * math.cos(a), major * math.sin(a), 0))
        out = Vector((math.cos(a), math.sin(a), 0))
        tube = minor * (1 + ripple[1] * math.cos(ripple[0] * a))
        rings.append([bm.verts.new(centre + out * tube * section[0] * math.cos(b) + Vector((0, 0, 1)) * tube
                                   * section[1] * math.sin(b))
                      for b in (2 * math.pi * j / sides for j in range(sides))])
    bridge(bm, rings, closed)
    if not closed:
        bm.faces.new(rings[0][::-1])
        bm.faces.new(rings[-1])
    return finish(bm, cls, loc, rot, scale)


def bridge(bm, rings, closed):
    for i in range(len(rings) - (0 if closed else 1)):
        a, b = rings[i], rings[(i + 1) % len(rings)]
        n = len(a)
        for j in range(n):
            bm.faces.new((a[j], a[(j + 1) % n], b[(j + 1) % n], b[j]))


def lathe(profile, cls, loc=(0, 0, 0), rot=(0, 0, 0), sides=20, scale=(1, 1, 1), closed=False):
    """Revolves (radius, z) points round Z; a radius of 0 at either end closes it with a pole; closed joins the last
    point back to the first (a ring band's cross-section) instead of capping."""
    bm = bmesh.new()
    rings = []
    for r, z in profile:
        if r == 0:
            rings.append([bm.verts.new((0, 0, z))])
        else:
            rings.append([bm.verts.new((r * math.cos(a), r * math.sin(a), z))
                          for a in (2 * math.pi * j / sides for j in range(sides))])
    for a, b in zip(rings, rings[1:] + (rings[:1] if closed else [])):
        if len(a) == 1:
            for j in range(sides):
                bm.faces.new((a[0], b[(j + 1) % sides], b[j]))
        elif len(b) == 1:
            for j in range(sides):
                bm.faces.new((a[j], a[(j + 1) % sides], b[0]))
        else:
            for j in range(sides):
                bm.faces.new((a[j], a[(j + 1) % sides], b[(j + 1) % sides], b[j]))
    if len(rings[0]) > 1 and not closed:
        bm.faces.new(rings[0][::-1])
    if len(rings[-1]) > 1 and not closed:
        bm.faces.new(rings[-1])
    return finish(bm, cls, loc, rot, scale)


def sweep(points, radii, cls, sides=8, closed=False, section=(1, 1), loc=(0, 0, 0), rot=(0, 0, 0), up=(0, 0, 1)):
    """A tube along points (radius per point, or one radius); section scales it across (side, up)."""
    points = [Vector(p) for p in points]
    radii = radii if isinstance(radii, (list, tuple)) else [radii] * len(points)
    bm = bmesh.new()
    rings = []
    count = len(points)
    for i, p in enumerate(points):
        ahead = points[(i + 1) % count] if closed or i + 1 < count else p
        behind = points[i - 1] if closed or i > 0 else p
        tangent = (ahead - behind).normalized()
        side = tangent.cross(Vector(up))
        if side.length < 1e-6:
            side = tangent.cross(Vector((1, 0, 0)))
        side.normalize()
        normal = side.cross(tangent).normalized()
        rings.append([bm.verts.new(p + side * radii[i] * section[0] * math.cos(a)
                                   + normal * radii[i] * section[1] * math.sin(a))
                      for a in (2 * math.pi * j / sides for j in range(sides))])
    bridge(bm, rings, closed)
    if not closed:
        bm.faces.new(rings[0][::-1])
        bm.faces.new(rings[-1])
    return finish(bm, cls, loc, rot)


def prism(outline, depth, cls, loc=(0, 0, 0), rot=(0, 0, 0), bevel=0.0, segments=1, taper=1.0):
    """An outline [(x, y)] extruded along Z from 0 to depth; taper scales the top face."""
    bm = bmesh.new()
    bottom = [bm.verts.new((x, y, 0)) for x, y in outline]
    top = [bm.verts.new((x * taper, y * taper, depth)) for x, y in outline]
    bm.faces.new(bottom[::-1])
    bm.faces.new(top)
    for j in range(len(outline)):
        k = (j + 1) % len(outline)
        bm.faces.new((bottom[j], bottom[k], top[k], top[j]))
    return finish(bm, cls, loc, rot, bevel=bevel, segments=segments)


def crystal(length, radius, cls, sides=6, tips=(0.3, 0.2), loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1),
            twist=0.0):
    """A pointed crystal along +Z from 0: a prism of `sides` with tips (fractions of the length) at both ends."""
    bm = bmesh.new()
    low, high = length * tips[1], length * (1 - tips[0])
    rings = []
    for z, turn in ((low, 0), (high, twist)):
        rings.append([bm.verts.new((radius * math.cos(a + turn), radius * math.sin(a + turn), z))
                      for a in (2 * math.pi * j / sides for j in range(sides))])
    bottom, top = bm.verts.new((0, 0, 0)), bm.verts.new((0, 0, length))
    for j in range(sides):
        k = (j + 1) % sides
        bm.faces.new((rings[0][j], rings[0][k], rings[1][k], rings[1][j]))
        bm.faces.new((rings[1][j], rings[1][k], top))
        bm.faces.new((rings[0][k], rings[0][j], bottom))
    place(bm, scale=scale)
    return finish(bm, cls, loc, rot)


def rounded_rect(width, height, radius, steps=3):
    points = []
    for cx, cy, start in ((width / 2 - radius, height / 2 - radius, 0), (-width / 2 + radius, height / 2 - radius, 90),
                          (-width / 2 + radius, -height / 2 + radius, 180),
                          (width / 2 - radius, -height / 2 + radius, 270)):
        for i in range(steps + 1):
            a = math.radians(start + 90 * i / steps)
            points.append((cx + radius * math.cos(a), cy + radius * math.sin(a)))
    return points


def slab(width, height, depth, radius, cls, loc=(0, 0, 0), rot=(0, 0, 0), bevel=0.0):
    return prism(rounded_rect(width, height, radius), depth, cls, loc, rot, bevel=bevel)


def chain(points, link=1.8, wire=0.32, cls='gold'):
    """Links along a polyline lying on the ground, alternately flat and on edge."""
    points = [Vector(p) for p in points]
    lengths = [(b - a).length for a, b in zip(points, points[1:])]
    total, step, i, travelled = sum(lengths), link * 0.95, 0, 0.0
    position, n = 0.0, 0
    while position < total:
        while i < len(lengths) - 1 and position > travelled + lengths[i]:
            travelled += lengths[i]
            i += 1
        t = (position - travelled) / lengths[i]
        p = points[i].lerp(points[i + 1], t)
        d = (points[i + 1] - points[i]).normalized()
        yaw = math.degrees(math.atan2(d.y, d.x))
        roll = 90 if n % 2 else 0
        torus(link / 2, wire, cls, (p.x, p.y, wire + (link / 2 * 0.62 - wire if roll else 0)),
              (roll, 0, yaw), scale=(1, 0.62, 1), segments=8, sides=4)
        position += step
        n += 1


# --- Designs ---------------------------------------------------------------------------------------------------
def bow(length, depth, recurve, limb, spines=0, spine_cls='bone', tip_cls='gold'):
    """A bow lying on its side: limbs bending back from the grip, recurved tips, a straight string."""
    points, radii = [], []
    for i in range(41):
        t = -1 + 2 * i / 40
        y = length / 2 * t
        x = -depth * (1 - t * t) + recurve * max(0, abs(t) - 0.8) ** 2 * 25
        points.append((x, y, 0))
        radii.append(limb * (1.6 if abs(t) < 0.12 else 1.0 - 0.45 * abs(t)))
    sweep(points, radii, 'resin', sides=8, section=(1.0, 0.75))
    cyl(limb * 1.9, length * 0.13, 'bone', (points[20][0], 0, 0), (90, 0, 0), sides=10, scale=(1, 0.8, 1))
    tip_x = points[0][0]
    sweep([points[1], (tip_x, -length / 2 + 0.5, 0), (tip_x, length / 2 - 0.5, 0), points[-2]], 0.22, 'string',
          sides=4)
    for sign in (-1, 1):
        # A bone horn curling forward (toward the string side, +x) from each limb tip.
        tip = Vector(points[0 if sign < 0 else 40])
        horn = [tip + Vector((curl * length * 0.07 * (1 - math.cos(a)), sign * length * 0.07 * math.sin(a), 0))
                for a, curl in ((math.radians(15 * k), 1) for k in range(7))]
        sweep([tip - Vector((0, sign * length * 0.04, 0))] + horn,
              [limb * 1.1] + [limb * (1.0 - 0.14 * k) for k in range(7)], 'bone', sides=6, section=(1, 0.8))
        crystal(length * 0.03, limb * 0.5, tip_cls, sides=5, tips=(0.6, 0.1),
                loc=(tip.x, tip.y - sign * length * 0.035, 0), rot=(-90 * sign, 0, 0))
    for k in range(spines):
        t = -0.85 + 1.7 * (k + 0.5) / spines
        if abs(t) < 0.15:
            continue
        y = length / 2 * t
        x = -depth * (1 - t * t)
        crystal(limb * 4.5, limb * 0.6, spine_cls, sides=4, tips=(0.7, 0.05), loc=(x - limb * 0.6, y, 0),
                rot=(0, -90, 0), scale=(1, 1, 1))


def build_hes_spinebow():
    bow(141, 16, 0.3, 2.5, spines=10)


def build_hes_noble_recurve():
    bow(141, 13, 0.9, 2.5, spines=4)


def build_hes_noblebone_longbow():
    bow(128, 12, 0.4, 2.3, spines=6, spine_cls='bone')


def belt_loop(a, b, height, thickness, cls):
    outline = [(a * math.cos(t), b * math.sin(t)) for t in (2 * math.pi * i / 40 for i in range(40))]
    inner = [(x * (1 - thickness / a), y * (1 - thickness / b)) for x, y in outline]
    bm = bmesh.new()
    rings = []
    for loop, z in ((outline, 0), (outline, height), (inner, height), (inner, 0)):
        rings.append([bm.verts.new((x, y, z)) for x, y in loop])
    bridge(bm, rings, True)
    return finish(bm, cls)


def on_loop(a, b, t, height, offset=0.0):
    x, y = a * math.cos(t), b * math.sin(t)
    normal = Vector((math.cos(t) / a, math.sin(t) / b, 0)).normalized()
    return Vector((x, y, height)) + normal * offset, math.degrees(math.atan2(normal.y, normal.x))


def build_hes_utility_belt():
    a, b, h = 28, 21, 9
    belt_loop(a, b, h, 1.2, 'leather')
    p, yaw = on_loop(a, b, math.pi / 2, h / 2, 0.8)
    box((10, 1.2, 10.5), 'gold', p, (0, 0, yaw - 90), bevel=0.3)
    box((6, 1.6, 6.5), 'leather', p + Vector((0, 0.4, 0)), (0, 0, yaw - 90))
    for t in (0.15, 0.95, 2.2, 2.95, 4.1):
        p, yaw = on_loop(a, b, t, h / 2, 2.6)
        box((8, 4.2, 9), 'leather' if t != 2.2 else 'ceramic', p, (0, 0, yaw - 90), bevel=0.6)


def build_hes_capacitor_belt():
    a, b, h = 28, 21, 8
    belt_loop(a, b, h, 1.1, 'resin')
    for i in range(14):
        t = 2 * math.pi * i / 14 + math.pi / 2
        p, yaw = on_loop(a, b, t, h / 2, 1.3)
        if i == 0:
            cyl(5, 2.4, 'gold', p, (90, 0, yaw - 90), sides=16)
            cyl(2.6, 2.8, 'glow', p, (90, 0, yaw - 90), sides=12)
        else:
            box((4.2, 2.4, 7.5), 'ceramic', p, (0, 0, yaw - 90), bevel=0.5)
            box((1.2, 2.7, 4.2), 'glow', p, (0, 0, yaw - 90))


def build_hes_reserve_belt():
    a, b, h = 28, 21, 9
    belt_loop(a, b, h, 1.1, 'leather')
    for i in range(8):
        t = 2 * math.pi * i / 8 + math.pi / 2
        p, yaw = on_loop(a, b, t, h / 2, 1.6)
        if i == 0:
            box((9, 2.4, 10), 'gold', p, (0, 0, yaw - 90), bevel=0.4)
            box((2, 2.8, 6), 'glow', p, (0, 0, yaw - 90))
        else:
            box((6, 3.2, 8.4), 'ceramic', p, (0, 0, yaw - 90), bevel=0.6)
            box((6.6, 2.0, 1.2), 'gold', p + Vector((0, 0, 2.8)), (0, 0, yaw - 90))
            box((6.6, 2.0, 1.2), 'gold', p - Vector((0, 0, 2.8)), (0, 0, yaw - 90))


RING_TILT = (32, 0, 0)


def ring_band(radius, width, thickness, cls, segments=32):
    lathe([(radius, -width / 2), (radius + thickness, -width / 2 + 0.3), (radius + thickness, width / 2 - 0.3),
           (radius, width / 2)], cls, sides=segments)


def ring_group(builder):
    """Builds a ring lying flat (axis vertical), its setting at +Y, then tilts it so the setting faces up."""
    start = len(parts)
    builder()
    for obj in parts[start:]:
        obj.data.transform(Euler([math.radians(a) for a in RING_TILT]).to_matrix().to_4x4())


def build_hes_conductor_ring():
    def make():
        for k in range(3):
            points = []
            for i in range(49):
                t = 2 * math.pi * i / 48
                twist = t * 3 + k * 2 * math.pi / 3
                r = 6.2 + 0.9 * math.cos(twist)
                points.append((r * math.cos(t), r * math.sin(t), 0.9 * math.sin(twist)))
            sweep(points[:-1], 0.75, 'gold', sides=6, closed=True)
        box((3.8, 2.2, 3.8), 'ceramic', (0, 7.2, 0), bevel=0.5)
        box((1.0, 0.6, 2.6), 'glow', (0, 8.3, 0))
    ring_group(make)


def build_hes_induction_ring():
    def make():
        lathe([(6.0, -2.8), (7.2, -2.8), (7.6, -2.2), (7.6, 2.2), (7.2, 2.8), (6.0, 2.8)], 'gold', sides=40,
              closed=True)
        torus(7.62, 1.0, 'ceramic', segments=32, sides=4, section=(0.6, 1.9), arc=300, rot=(0, 0, 120))
        box((2.6, 1.2, 2.6), 'glow', (0, 7.9, 0), bevel=0.3)
    ring_group(make)


def build_hes_crown_band():
    def make():
        lathe([(6.0, -2.6), (7.4, -2.6), (7.8, 0), (7.4, 2.6), (6.0, 2.6)], 'resin', sides=40, closed=True)
        for z in (-2.5, 2.5):
            torus(7.0, 0.45, 'gold', (0, 0, z), segments=40, sides=6)
        box((6.5, 3.0, 4.6), 'gold', (0, 8.2, 0), bevel=0.6)
        sphere(2.2, 'glass', (0, 9.8, 0), scale=(1.4, 0.7, 0.95))
    ring_group(make)


def build_hes_stormglass_ring():
    def make():
        lathe([(6.0, -1.8), (7.2, -1.8), (7.6, 0), (7.2, 1.8), (6.0, 1.8)], 'gold', sides=40, closed=True)
        box((10, 3.4, 5.0), 'ceramic', (0, 8.1, 0), bevel=0.9, segments=2)
        for x in (-2.4, 2.4):
            sphere(2.1, 'glass', (x, 9.7, 0), scale=(1, 0.65, 1.05))
            torus(2.15, 0.4, 'gold', (x, 9.5, 0), (90, 0, 0), segments=14, sides=4)
    ring_group(make)


def build_hes_xiths_sight():
    def make():
        lathe([(6.0, -2.4), (7.6, -2.4), (8.0, 0), (7.6, 2.4), (6.0, 2.4)], 'resin', sides=40, closed=True)
        for z in (-2.3, 2.3):
            torus(7.3, 0.45, 'gold', (0, 0, z), segments=40, sides=6)
        cyl(4.2, 3.4, 'gold', (0, 8.9, 0), (90, 0, 0), sides=20, scale=(1.25, 1, 1))
        sphere(3.5, 'glass', (0, 10.6, 0), scale=(1.2, 0.5, 1))
    ring_group(make)


def pendant_chain(top, spread=13, drop=16):
    x, y = top
    chain([(x, y), (x - spread * 0.6, y + drop * 0.6), (x - spread * 0.3, y + drop), (x + spread * 0.3, y + drop),
           (x + spread * 0.6, y + drop * 0.6), (x, y)])


def build_hes_lattice_pendant():
    crystal(17, 4.2, 'crystal', sides=6, tips=(0.35, 0.3), loc=(0, -10, 3.6), rot=(-90, 0, 0), scale=(1, 0.65, 1))
    for sign in (-1, 1):
        sweep([(sign * 3, -11.5, 1.2), (sign * 5.6, -4, 2), (sign * 4.5, 3, 2), (sign * 1.5, 7, 1.6)],
              [1.0, 1.6, 1.3, 0.9], 'ceramic', sides=6, section=(1, 1.1))
    cyl(1.6, 1.8, 'gold', (0, 8.5, 1.2), (0, 0, 0), sides=10)
    torus(1.6, 0.45, 'gold', (0, 10.5, 1.0), (90, 0, 90), segments=10, sides=4)
    pendant_chain((0, 11.5))


def build_hes_surveyors_pendant():
    outline = [(0, 9), (6.5, 0), (0, -9), (-6.5, 0)]
    prism(outline, 2.4, 'ceramic', bevel=0.7)
    for p in outline:
        crystal(2.6, 1.0, 'gold', sides=4, tips=(0.6, 0.1), loc=(p[0] * 1.08, p[1] * 1.08, 1.2),
                rot=(0, 90, math.degrees(math.atan2(p[1], p[0]))))
    cyl(3.3, 1.2, 'gold', (0, 0, 2.6), sides=20)
    sphere(2.5, 'glass', (0, 0, 3.0), scale=(1, 1, 0.5))
    torus(1.4, 0.4, 'gold', (0, 10.6, 0.9), (90, 0, 90), segments=10, sides=4)
    pendant_chain((0, 11.6))


def build_hes_nightglass_amulet():
    lathe([(0, -9), (2.4, -7.5), (4.3, -3.5), (4.6, 0.5), (3.6, 4.0), (1.8, 6.0), (0, 6.6)], 'glass', sides=16,
          loc=(0, 0, 3.8), rot=(-90, 0, 0), scale=(1, 0.75, 1))
    for sign in (-1, 1):
        sweep([(sign * 2.2, -6.5, 2.4), (sign * 5.2, -1.5, 3.4), (sign * 4.0, 4.5, 3.6), (sign * 0.8, 7.2, 3.6)],
              [0.7, 1.2, 1.0, 0.7], 'ceramic', sides=6)
    cyl(1.4, 2.4, 'gold', (0, 8.2, 3.6), (90, 0, 0), sides=10)
    torus(1.8, 0.5, 'gold', (0, 10.6, 1.0), (90, 0, 90), segments=10, sides=4)
    pendant_chain((0, 11.8), spread=11, drop=12)


def build_hes_jammer():
    sphere(6.5, 'ceramic', (0, 0, 4.2), scale=(0.85, 1.25, 0.65), segments=20, rings=10)
    torus(6.0, 0.55, 'gold', (0, 0, 4.2), scale=(0.93, 1.36, 1), segments=28, sides=4)
    cyl(2.2, 1.2, 'gold', (0, -0.5, 8.1), sides=16)
    sphere(1.7, 'glow', (0, -0.5, 8.6), scale=(1, 1, 0.45))
    cyl(1.0, 2.2, 'gold', (0, 8.6, 4.0), (90, 0, 0), sides=8)
    torus(2.4, 0.55, 'leather', (0, 12.2, 1.0), (90, 0, 90), segments=12, sides=4)


def implant_pins(count, y, z=1.4, spacing=1.6, length=3.2):
    x0 = -spacing * (count - 1) / 2
    for i in range(count):
        cyl(0.45, length, 'gold', (x0 + spacing * i, y - length / 2, z), (90, 0, 0), sides=6)


def build_hes_dermal_1(claws=False):
    slab(20, 20, 3.4, 4.5, 'ceramic', bevel=0.6)
    slab(14, 14, 1.0, 2.0, 'steel', (0, 0, 3.0))
    for x, y in ((-8.5, 8.5), (8.5, 8.5), (-8.5, -8.5), (8.5, -8.5)):
        if claws:
            crystal(6, 1.6, 'resin', sides=4, tips=(0.6, 0.1), loc=(x, y, 1.6),
                    rot=(0, 90, math.degrees(math.atan2(y, x))))
        else:
            box((4.5, 4.5, 2.2), 'ceramic', (x * 0.95, y * 0.95, 3.5), (0, 0, 45), bevel=0.7)
    box((3, 1.3, 1.6), 'glow', (6.5, 9.6, 2.4))
    implant_pins(4, -10.2)


def build_hes_dermal_2():
    build_hes_dermal_1(claws=True)


def build_hes_capacitor_1(knobs=2):
    sphere(10, 'ceramic', (0, 0, 3.6), scale=(1.15, 0.85, 0.36), segments=24, rings=10)
    torus(5.0, 1.0, 'gold', (0, 0, 6.2), segments=24, sides=6, section=(1, 0.8))
    sphere(4.0, 'glow', (0, 0, 6.0), scale=(1, 1, 0.42), segments=16, rings=6)
    for x in ((-10.5, 10.5) if knobs == 2 else (-10.5, 10.5, 0)):
        if x:
            cyl(2.3, 3.0, 'gold', (x, 0, 3.6), (0, 90, 0), sides=12)
    implant_pins(3, -6.6, z=2.2)


def build_hes_capacitor_2():
    build_hes_capacitor_1(knobs=2)
    torus(7.4, 0.5, 'steel', (0, 0, 5.6), segments=28, sides=4)


def build_hes_damping_1(woven=3):
    frame = rounded_rect(21, 21, 3)
    prism(frame, 3.6, 'gold', bevel=0.5)
    slab(15.5, 15.5, 1.2, 1.5, 'steel' if woven > 3 else 'leather', (0, 0, 3.4))
    for x, y in ((-9, 9), (9, -9)):
        box((6, 3, 1.6), 'ceramic', (x, y, 3.8), (0, 0, 45), bevel=0.5)
    box((3, 1.2, 1.4), 'glow', (6, 10.3, 3.0))
    implant_pins(4, -10.4)


def build_hes_damping_2():
    build_hes_damping_1(woven=4)


def build_hes_regulator_1(gap=0.0):
    arc = 360 - gap
    torus(8.0, 2.8, 'ceramic', (0, 0, 1.6), (0, 0, -90 + gap / 2), segments=28, sides=8, section=(1, 0.6),
          arc=arc)
    cyl(3.4, 2.6, 'gold', (0, 0, 1.8), sides=20)
    sphere(2.5, 'glow', (0, 0, 3.0), scale=(1, 1, 0.5))
    box((1.6, 8, 1.6), 'gold', (0, -4.2, 1.6))
    box((5, 4, 3.2), 'ceramic', (0, -11, 1.6), bevel=0.6)
    implant_pins(3, -13.1, z=1.6, spacing=1.4)


def build_hes_regulator_2():
    build_hes_regulator_1(gap=70)
    for sign in (-1, 1):
        sphere(1.3, 'glow', (sign * 8.6, 2.4, 2.4), scale=(0.6, 1, 0.6))


def build_hes_resonator_1(star=False):
    outline = []
    for k in range(3):
        a = math.radians(90 + 120 * k)
        outline.append((11 * math.cos(a), 11 * math.sin(a)))
        if star:
            b = math.radians(150 + 120 * k)
            outline.append((5.2 * math.cos(b), 5.2 * math.sin(b)))
    if not star:
        inner = [(x * 0.62, y * 0.62) for x, y in outline]
        bm = bmesh.new()
        rings = [[bm.verts.new((x, y, z)) for x, y in loop]
                 for loop, z in ((outline, 0), (outline, 3.6), (inner, 3.6), (inner, 0))]
        bridge(bm, rings, True)
        finish(bm, 'ceramic', bevel=0.5)
        crystal(6.5, 6.2, 'crystal', sides=3, tips=(0.75, 0.05), loc=(0, 0, 0.4), rot=(0, 0, 90))
    else:
        prism(outline, 2.8, 'ceramic', bevel=0.5)
        for k in range(3):
            a = math.radians(90 + 120 * k)
            crystal(4, 2.6, 'crystal', sides=4, tips=(0.7, 0.1), loc=(4 * math.cos(a), 4 * math.sin(a), 2.0))
    for k in range(3):
        a = math.radians(90 + 120 * k)
        sweep([(0, 0, 3.4), (8.5 * math.cos(a), 8.5 * math.sin(a), 3.2)], 0.45, 'gold', sides=5)
    implant_pins(4, -6.2, z=1.4, spacing=1.6)


def build_hes_resonator_2():
    build_hes_resonator_1()
    rim = [(9.4 * math.cos(math.radians(90 + 120 * k)), 9.4 * math.sin(math.radians(90 + 120 * k)), 3.8)
           for k in range(3)]
    sweep(rim, 0.6, 'gold', sides=5, closed=True)


def build_hes_resonator_3():
    build_hes_resonator_1(star=True)


def zigzag(points, width, height, cls_body='ceramic', cls_channel='glow', offset=(0, 0)):
    path = [(x + offset[0], y + offset[1], height / 2 + 0.2) for x, y in points]
    sweep(path, width / 2, cls_body, sides=6, section=(1, height / width))
    sweep([(x, y, z + height / 2) for x, y, z in path], 0.55, cls_channel, sides=4, section=(1.4, 0.4))


def build_hes_coupler_1(double=False):
    points = [(-13, -5), (-6, -5), (-1, 4), (3, -4), (7, 5), (13, 5)]
    zigzag(points, 5.0, 3.8)
    if double:
        zigzag([(x, y - 4.6) for x, y in points[1:-1]], 2.6, 2.4, 'gold', 'glow')
    for (x, y), sign in ((points[0], -1), (points[-1], 1)):
        cyl(3.2, 8, 'ceramic', (x + sign * 2.5, y, 3.2), (0, 90 * sign, 0), sides=8, radius2=2.3, bevel=0.3)
        for k in (-0.9, 0.9):
            cyl(0.4, 2.8, 'gold', (x + sign * 7.6, y + k, 3.2), (0, 90, 0), sides=5)


def build_hes_coupler_2():
    build_hes_coupler_1(double=True)


def build_hes_coupler_3():
    build_hes_coupler_1(double=False)
    for x, y in ((-1, 4), (3, -4)):
        box((4.4, 4.4, 1.2), 'gold', (x, y, 4.2), (0, 0, 45), bevel=0.3)


def build_hes_striking_lattice():
    outline = [(0, 11), (8.5, 0), (0, -11), (-8.5, 0)]
    for (x0, y0), (x1, y1) in zip(outline, outline[1:] + outline[:1]):
        sweep([(x0, y0, 1.6), (x1, y1, 1.6)], 1.3, 'gold', sides=6)
    for t in (-0.5, 0.0, 0.5):
        sweep([(-8.5 * (1 - abs(t)) * 0.9, 11 * t, 1.6), (8.5 * (1 - abs(t)) * 0.9, 11 * t, 1.6)], 0.6, 'gold',
              sides=5)
        sweep([(8.5 * t, -11 * (1 - abs(t)) * 0.9, 1.9), (8.5 * t, 11 * (1 - abs(t)) * 0.9, 1.9)], 0.6, 'gold',
              sides=5)
    for x, y in outline:
        sphere(2.0, 'ceramic', (x, y, 1.9), scale=(1.2, 1.2, 0.8), segments=10, rings=6)
    box((3.4, 3.4, 2.2), 'glass', (0, 0, 2.6), (0, 0, 45), bevel=0.6)
    implant_pins(2, -12.3, z=1.6, spacing=1.4)


def canister(radius, height, ribs, rib_cls, core_cls, loc=(0, 0, 0)):
    x, y, z = loc
    lathe([(0, 0), (radius * 0.92, 0), (radius, height * 0.05), (radius, height * 0.2), (radius * 0.95, height * 0.24),
           (radius * 0.95, height * 0.76), (radius, height * 0.8), (radius, height * 0.95), (radius * 0.9, height),
           (0, height)], 'ceramic', loc=loc, sides=20)
    cyl(radius * 0.97, height * 0.5, core_cls, (x, y, z + height * 0.5), sides=16)
    for k in range(ribs):
        a = 2 * math.pi * k / ribs
        box((radius * 0.32, radius * 0.22, height * 0.62), rib_cls,
            (x + radius * 1.0 * math.cos(a), y + radius * 1.0 * math.sin(a), z + height * 0.5),
            (0, 0, math.degrees(a)), bevel=0.2)
    for z_band in (0.21, 0.79):
        torus(radius * 1.0, radius * 0.08, rib_cls, (x, y, z + height * z_band), segments=20, sides=4)


def build_hes_shield_cell():
    canister(9, 28, 4, 'gold', 'glow')
    for x in (-3.2, 3.2):
        cyl(1.6, 3, 'gold', (x, 0, 29.5), sides=10)


def build_hes_ion_cell():
    canister(9, 28, 6, 'resin', 'glow')
    cyl(3.5, 2, 'gold', (0, 0, 29), sides=14)


def build_hes_shield_burst_cell():
    for x, y in ((-6, 4), (6, 4), (0, -5.5)):
        canister(6.2, 26, 3, 'gold', 'glow', (x, y, 0))
    box((18, 15, 3.5), 'ceramic', (0, 0, 26.5), bevel=1.0)
    cyl(2.2, 2.4, 'gold', (0, 0, 29), sides=12)


def build_hes_stim():
    profile = [(0, 0), (1.2, 0), (2.6, 3.5), (3.2, 4.5), (3.4, 6.5), (3.4, 21), (2.2, 22), (1.2, 22), (1.2, 25),
               (3.6, 25), (3.6, 27), (0, 27.5)]
    lathe(profile, 'ceramic', loc=(0, -13.75, 3.4), rot=(-90, 0, 0), sides=14)
    cyl(3.5, 9, 'glow', (0, -2, 3.4), (90, 0, 0), sides=12)
    cyl(3.5, 2.4, 'gold', (0, -12, 3.4), (90, 0, 0), sides=12, radius2=2.4)
    for y in (2.6, -6.6):
        torus(3.45, 0.4, 'gold', (0, y, 3.4), (90, 0, 0), segments=14, sides=4)


def build_hes_emp_grenade():
    sphere(10, 'ceramic', (0, 0, 10), segments=24, rings=12)
    torus(10.05, 1.0, 'gold', (0, 0, 10), segments=28, sides=4, section=(0.6, 1.6))
    cyl(3.6, 3, 'gold', (0, 0, 20.4), sides=16)
    sweep([(2.6, 0, 21.4), (6, 0, 21.6), (9.5, 0, 18), (10.8, 0, 12)], 0.7, 'gold', sides=4, section=(2.2, 0.6))
    for a, b in ((0, 30), (120, 20), (240, 25)):
        direction = Euler((0, math.radians(90 - b), math.radians(a))).to_matrix() @ Vector((0, 0, 1))
        cyl(2.8, 1.2, 'gold', Vector((0, 0, 10)) + direction * 9.7, (0, 90 - b, a), sides=14)
        sphere(2.0, 'glow', Vector((0, 0, 10)) + direction * 10.3, (0, 90 - b, a), scale=(1, 1, 0.45))


def build_hes_breach_charge():
    box((24, 20, 10), 'steel', (0, 0, 5), bevel=0.8)
    box((16, 14, 1.2), 'ceramic', (-2, 0, 10.4), bevel=0.3)
    box((5, 21, 10.6), 'leather', (2, 0, 5.1))
    box((2.4, 4.4, 1.2), 'steel', (2, 0, 10.9))
    cyl(2.0, 5, 'steel', (11.5, 4, 8), (0, 90, 0), sides=10)
    cyl(1.0, 2, 'gold', (11.5, 4, 11), sides=8)
    sweep([(10, 4, 9.6), (7, 6, 11.2), (2, 7.6, 10.8)], 0.4, 'copper', sides=4)


def build_hes_hesper_ration():
    box((24, 18, 8), 'paper', (0, 0, 4), bevel=1.2, segments=2)
    box((20, 14, 3.2), 'food', (0, 0, 8.6), bevel=0.8)
    for y in (-4.5, 4.5):
        torus(1.0, 0.3, 'string', (0, y, 4.1), (0, 90, 0), scale=(4.3, 1, 12.6), segments=16, sides=4)


def build_hes_engram_shard():
    crystal(24, 3.4, 'crystal', sides=6, tips=(0.3, 0.12), loc=(0, -8, 3.2), rot=(-90, 0, 0), scale=(1, 0.75, 1))
    lathe([(0, 0), (1.0, 0), (2.4, 2.5), (3.2, 5.5), (3.0, 7)], 'gold', loc=(0, -14.5, 3.2), rot=(-90, 0, 0), sides=10,
          scale=(1, 0.8, 1))
    box((2.4, 4, 1.6), 'ceramic', (0, -11, 5.6), bevel=0.4)


def build_hes_aster_shard_2():
    crystal(22, 3.0, 'crystal', sides=5, tips=(0.35, 0.1), loc=(-1, -6, 3), rot=(-90, 0, 18), scale=(1, 0.7, 1))
    crystal(18, 2.6, 'crystal', sides=5, tips=(0.35, 0.1), loc=(1, -6, 3), rot=(-90, 0, -25), scale=(1, 0.7, 1))
    lathe([(0, 0), (1.0, 0), (2.4, 2.5), (2.6, 4.5), (0, 5)], 'ceramic', loc=(0, -11, 3), rot=(-90, 0, 0),
          sides=10)


def build_hes_aster_shard_3():
    outer, inner = [], []
    for i in range(17):
        a = math.radians(-60 + 230 * i / 16)
        w = math.sin(math.pi * i / 16)
        outer.append((12 * math.cos(a), 12 * math.sin(a)))
        inner.append(((12 - 1 - 6 * w) * math.cos(a), (12 - 1 - 6 * w) * math.sin(a)))
    prism(outer + inner[::-1], 4.0, 'crystal', bevel=0.6)
    sweep([(x * 0.98, y * 0.98, 0.9) for x, y in inner], 0.9, 'gold', sides=5)


def build_hes_aster_shard_4():
    crystal(20, 6.2, 'crystal', sides=4, tips=(0.45, 0.35), loc=(0, -6, 4.6), rot=(-90, 0, 45),
            scale=(1, 0.55, 1))
    lathe([(0, 0), (1.0, 0), (2.6, 2.4), (3.0, 4.2), (0, 4.6)], 'ceramic', loc=(0, -10.8, 3.2), rot=(-90, 0, 0),
          sides=12, scale=(1, 0.7, 1))


def icon_outline(icon, points=40):
    """The convex outline of an icon's 1254 px painting (its selected master), centred, y up, longest side 1."""
    image = bpy.data.images.load(os.path.join(HERE, 'codex_tex', icon, 'design_reference.png'), check_existing=False)
    width, height = image.size
    alpha = image.pixels[3::4]
    step = max(1, max(width, height) // 200)
    inside = [(x, y) for y in range(0, height, step) for x in range(0, width, step) if alpha[y * width + x] > 0.5]
    bpy.data.images.remove(image)
    inside.sort()
    hull = []
    for sequence in (inside, inside[::-1]):
        chain = []
        for point in sequence:
            while len(chain) >= 2 and ((chain[-1][0] - chain[-2][0]) * (point[1] - chain[-2][1])
                                       - (chain[-1][1] - chain[-2][1]) * (point[0] - chain[-2][0])) <= 0:
                chain.pop()
            chain.append(point)
        hull += chain[:-1]
    xs, ys = [p[0] for p in hull], [p[1] for p in hull]
    size = max(max(xs) - min(xs), max(ys) - min(ys))
    cx, cy = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
    keep = hull[::max(1, len(hull) // points)]
    return [((x - cx) / size, (y - cy) / size) for x, y in keep]


def build_hes_aster_shard_1():
    # Meshy made a block with the crystal on its narrow sides; the shard is a slab in its icon's outline, the icon
    # painting projected from above (codex_tex/hes_aster_shard_1/NOTE.md).
    outline = [(x * 27, y * 27) for x, y in icon_outline('hes_aster_shard_1')]
    prism(outline, 6.5, 'auto', bevel=0.8, taper=0.94)


def build_hes_ion_coil():
    torus(8, 3.0, 'gold', (0, 0, 4.4), segments=72, sides=10, ripple=(24, 0.1))
    cyl(10, 1.4, 'ceramic', (0, 0, 0.7), sides=24)
    cyl(4.2, 1.6, 'glow', (0, 0, 2.0), sides=16)
    cyl(3.4, 6, 'ceramic', (0, -12, 4.0), (90, 0, 0), sides=12, bevel=0.3)
    torus(2.4, 0.45, 'glow', (0, -15.1, 4.0), (90, 0, 0), segments=12, sides=4)
    box((5, 3, 1.2), 'ceramic', (9.6, 7, 0.6), (0, 0, 40), bevel=0.4)


def build_hes_nav_matrix():
    slab(26, 26, 8, 3.5, 'ceramic', bevel=0.8)
    slab(15, 15, 1.4, 1.5, 'gold', (0, 0, 7.6))
    slab(12, 12, 1.0, 1.0, 'crystal', (0, 0, 8.5))
    for x in (-3, 0, 3):
        box((0.4, 11, 0.6), 'gold', (x, 0, 9.4))
        box((11, 0.4, 0.6), 'gold', (0, x, 9.4))
    for x in range(-8, 9, 2):
        box((0.8, 1.2, 3.2), 'steel', (x, -13.1, 3.4))


def build_hes_lander_log_core():
    for y in (-11, 11):
        cyl(9, 6, 'ceramic', (0, y, 8.3), (90, 0, 0), sides=8, bevel=0.6)
        torus(8.6, 0.6, 'gold', (0, y * 0.72, 8.3), (90, 0, 22.5), segments=8, sides=4)
    cyl(7.6, 16, 'steel', (0, 0, 8.3), (90, 0, 0), sides=8)
    box((6, 10, 1.2), 'glow', (0, 0, 15.4))
    cyl(3.6, 1.2, 'gold', (0, -14.4, 8.3), (90, 0, 0), sides=14)
    cyl(2.2, 1.4, 'steel', (0, -14.8, 8.3), (90, 0, 0), sides=12)


def build_hes_pilots_core():
    profile = [(0, 0), (4.4, 0), (5.2, 1), (5.2, 18), (5.6, 19), (5.6, 21), (5.2, 22), (5.2, 25), (5.8, 26), (5.8, 28),
               (5.2, 29), (5.2, 32), (5.6, 33), (5.6, 35), (5.2, 36), (5.2, 51), (4.2, 53), (0, 53)]
    lathe(profile, 'ceramic', loc=(0, -26.5, 5.8), rot=(-90, 0, 0), sides=16)
    for y in (-5.5, 1.5, 8.5):
        torus(5.6, 0.7, 'gold', (0, y, 5.8), (90, 0, 0), segments=16, sides=4)
    torus(5.7, 0.9, 'glow', (0, 2.0, 5.8), (90, 0, 0), segments=16, sides=4)
    for x in (-2, 0, 2):
        cyl(0.5, 3, 'gold', (x, -28, 3.6), (90, 0, 0), sides=6)


def build_hes_court_seal():
    cyl(13, 2.8, 'resin', (0, 0, 1.4), sides=32, bevel=0.4)
    torus(12.6, 0.9, 'gold', (0, 0, 2.2), segments=32, sides=6)
    for i in range(3):
        torus(1.6, 0.45, 'gold', (0, 14.6 + 2.6 * i, 0.5 + (0.9 if i % 2 else 0)), (90 if i % 2 else 0, 0, 90),
              scale=(1, 0.65, 1), segments=8, sides=4)


def build_hes_archive_armoury_key():
    slab(20, 28, 1.8, 2.2, 'ceramic', bevel=0.3)
    for x in (-10.1, 10.1):
        box((1.0, 24, 2.0), 'gold', (x, 0, 1.0))
    box((1.0, 5, 0.6), 'glow', (8.4, -4, 1.9))


def build_hes_militia_warrant():
    box((30, 19, 2.6), 'paper', (0, 0, 1.3), bevel=0.6)
    box((6, 19.6, 3.2), 'cloth', (1, 0, 1.4), (0, 0, -8))
    box((4.6, 9, 0.4), 'cloth', (3, -9, 0.2), (0, 0, 20))
    cyl(4.2, 1.4, 'gold', (1, 1, 3.4), sides=24, bevel=0.3)


def build_hes_colony_log_tablet():
    slab(30, 28, 4.5, 4.0, 'ceramic', bevel=0.8)
    slab(21, 19, 1.0, 2.0, 'screen', (0, 0.5, 4.0))
    box((4, 1.4, 1.2), 'gold', (9, -12.6, 3.6))


def build_hes_data_slate():
    slab(24, 30, 3.0, 3.0, 'ceramic', bevel=0.5)
    slab(25, 31, 1.2, 3.3, 'gold', (0, 0, 2.2))
    slab(20, 26, 1.0, 1.6, 'screen', (-0.5, 0.5, 2.9))
    cyl(0.9, 22, 'gold', (13.4, 0, 1.2), (90, 0, 0), sides=8)


def build(icon):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    parts.clear()
    globals()['build_' + icon]()
    for obj in bpy.context.scene.objects:
        obj.select_set(obj in parts)
    with bpy.context.temp_override(active_object=parts[0], selected_editable_objects=parts, object=parts[0]):
        bpy.ops.object.join()
    obj = parts[0]
    obj.name = obj.data.name = icon
    points = [v.co for v in obj.data.vertices]
    lo = Vector([min(p[i] for p in points) for i in range(3)])
    hi = Vector([max(p[i] for p in points) for i in range(3)])
    shift = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
    for v in obj.data.vertices:
        v.co -= shift
    with bpy.context.temp_override(active_object=obj, selected_objects=[obj], object=obj):
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(35))
    obj.data.calc_loop_triangles()
    size = hi - lo
    os.makedirs(WORK, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, f'{icon}.blend'))
    report = {'triangles': len(obj.data.loop_triangles), 'size': [round(v, 1) for v in size],
              'length': round(max(size.x, size.y), 1)}
    print('BUILT', icon, json.dumps(report))
    return report


def main():
    args = sys.argv[sys.argv.index('--') + 1:]
    if args == ['all']:
        args = sorted(name[6:] for name in globals() if name.startswith('build_hes_'))
    reports = {}
    path = os.path.join(WORK, 'built.json')
    if os.path.exists(path):
        reports = json.load(open(path))
    for icon in args:
        reports[icon] = build(icon)
    with open(path, 'w') as handle:
        json.dump(reports, handle, indent=1, sort_keys=True)


main()
