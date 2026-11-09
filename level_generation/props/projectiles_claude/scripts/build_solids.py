"""Solid projectile models -> work/<name>_export.glb, installed as engine/models/projectile_<name>.glb.

Sizes in world units from the restored sprites (opaque extent / 2 x frame scale); built with 1 Blender unit = 100
world units, flight along -Y, origin at the projectile's centre (the sprite's centre). Each build prints LENGTH, the
model's extent along the flight in world units, for engine/models/projectiles.yml.
- cannonball (560, spell70c, 75 across): icosphere, graded rust scan as dark iron.
- boulder (565, boulder, 59 x 45): displaced, squashed icosphere, graded rock scan, box-projected, its hollows
  darkened through COLOR_0 (pl.cavity_colour) like the painted crevices; tumbles.
- rock (4070 Rock Blast, 4090 Death Blossom, 4092 its shards; spell41, 85 across): knobbier rock, browner; tumbles.
- ice_shard (3030 Ice Bolt, 3090 Ice Blast, 3092 its shards; spell26, 61 long): a faceted hexagonal crystal with
  three small side crystals at its back, procedural ice, glossy with a faint cold glow; rolls.
- blades (4050, spell39, 110 across): four curved steel blades with a raised ridge round a hub, flat in the
  horizontal plane; whirls.
- shrapnel (9040 Shrap Metal, spell93, 52 across): nine thin steel shards in a loose cluster; tumbles.
- fire_spike (1060, spell07, 63 across): a steel caltrop, twelve spikes on a small core; spins, lies level settled.
- serpent (7030 Harm, spell70, 194 long): a tapering serpent in a gentle S, procedural gold scales.
- starburst (2100, spell22) and meteor (1080, spell09): an unlit lava core (the star's white-hot) where the painted
  ball or rock was, and
  two crossed cards with the painted flames as an additive flipbook trailing behind (make_solid_textures.py).
Usage: blender --background --python build_solids.py -- <name> [<name> ...]"""
import json
import math
import os
import random
import sys

import bmesh
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import projlib as pl  # noqa: E402

UNIT = 0.01   # Blender units per world unit
FLAME = {'blend': True, 'additive': True, 'unlit': True, 'double': True}


def length_of(obj):
    ys = [v.co.y for v in obj.data.vertices]
    print('LENGTH', obj.name, round((max(ys) - min(ys)) / UNIT, 1))


def rock_mesh(radius, amplitude, scale, seed, axes, subdivisions=3):
    bm = pl.ico(radius, subdivisions)
    pl.displace(bm, amplitude, scale, seed, axes)
    uv_layer = bm.loops.layers.uv.new('UVMap')
    bm.normal_update()
    pl.box_uv(bm, uv_layer, radius * 2.2)
    return bm


def cannonball():
    bm = pl.ico(37.5 * UNIT, 3)
    pl.sphere_uv(bm, bm.loops.layers.uv.new('UVMap'), repeat=1.0)
    obj = pl.to_object('Cannonball', bm, [pl.material('Iron', 'iron', 0.5, 0.5, normal=True)], 180)
    length_of(obj)
    pl.export(obj, 'cannonball')


def boulder():
    bm = rock_mesh(28.5 * UNIT, 0.3, 1.3, 3, (1.15, 1.0, 0.82))
    obj = pl.to_object('Boulder', bm, [pl.material('Rock', 'boulder', 0.85, normal=True)], 50)
    pl.cavity_colour(obj)
    length_of(obj)
    pl.export(obj, 'boulder')


def rock():
    bm = rock_mesh(35.5 * UNIT, 0.42, 2.1, 11, (1.0, 1.05, 0.92))
    obj = pl.to_object('Rock', bm, [pl.material('Rock', 'rock', 0.85, normal=True)], 45)
    pl.cavity_colour(obj, power=2.0, floor=0.25)
    length_of(obj)
    pl.export(obj, 'rock')


def crystal(bm, uv_layer, base, direction, radius, front, back, sides, twist=0.0):
    """A faceted bipyramid crystal: a ring of `sides` at base, a long point `front` ahead along direction and a
    short one `back` behind. UVs: u along the crystal, v round it (ice streaks run along)."""
    direction = direction.normalized()
    side = direction.orthogonal().normalized()
    up = direction.cross(side)
    ring = []
    for k in range(sides):
        angle = twist + 2.0 * math.pi * k / sides
        ring.append(base + (side * math.cos(angle) + up * math.sin(angle)) * radius)
    tip = base + direction * front
    tail = base - direction * back
    for k in range(sides):
        a, b = ring[k], ring[(k + 1) % sides]
        va, vb = k / sides, (k + 1) / sides
        pl.add_face(bm, uv_layer, [(tip, (1.0, (va + vb) * 0.5)), (a, (0.3, va)), (b, (0.3, vb))])
        pl.add_face(bm, uv_layer, [(tail, (0.0, (va + vb) * 0.5)), (b, (0.3, vb)), (a, (0.3, va))])


def ice_shard():
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new('UVMap')
    forward = Vector((0.0, -1.0, 0.0))
    crystal(bm, uv_layer, Vector((0.0, -7 * UNIT, 0.0)), forward, 11 * UNIT, 38 * UNIT, 22 * UNIT, 6)
    for k in range(3):
        angle = 2.0 * math.pi * k / 3 + 0.4
        out = Vector((math.cos(angle), 0.0, math.sin(angle)))
        base = Vector((0.0, 10 * UNIT, 0.0)) + out * 5 * UNIT
        crystal(bm, uv_layer, base, (forward * 0.55 + out * 0.45), 4.5 * UNIT, 14 * UNIT, 6 * UNIT, 5, angle)
    ice = pl.material('Ice', 'ice', 0.15)
    obj = pl.to_object('IceShard', bm, [ice])
    length_of(obj)
    pl.export(obj, 'ice_shard', {'Ice': {'emissive': [0.10, 0.17, 0.24]}})


def blades():
    """Four crescent blades sweeping round a hub. Each blade is closed: its leading and trailing edges are sharp and a
    ridge runs along its middle, raised above and below, so the steel catches the light from both sides."""
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new('UVMap')
    hub, reach, ridge, steps = 12 * UNIT, 55 * UNIT, 2.6 * UNIT, 6

    def point(radius, angle, z=0.0):
        return Vector((radius * math.cos(angle), radius * math.sin(angle), z))

    def uv(co):
        return (co.x / (2 * reach) + 0.5, co.y / (2 * reach) + 0.5)

    def face(corners):
        pl.add_face(bm, uv_layer, [(c, uv(c)) for c in corners])

    for arm in range(4):
        start = arm * math.pi / 2
        leading, trailing, top, bottom = [], [], [], []
        for i in range(steps + 1):
            t = i / steps
            radius = hub * 0.8 + (reach - hub * 0.8) * t
            sweep = math.radians(75) * t ** 0.8
            width = math.radians(66) * (1.0 - t) ** 1.1 + (math.radians(6) if i == 0 else 0.0)
            height = ridge * (1.0 - t) ** 0.7
            leading.append(point(radius, start + sweep))
            trailing.append(point(radius, start + sweep - width))
            middle = start + sweep - width * 0.45
            top.append(point(radius, middle, height))
            bottom.append(point(radius, middle, -height))
        for i in range(steps):
            if i < steps - 1:
                face([trailing[i], trailing[i + 1], top[i + 1], top[i]])
                face([top[i], top[i + 1], leading[i + 1], leading[i]])
                face([trailing[i], bottom[i], bottom[i + 1], trailing[i + 1]])
                face([bottom[i], leading[i], leading[i + 1], bottom[i + 1]])
            else:
                # The tip: leading, trailing and ridge meet.
                face([trailing[i], leading[i + 1], top[i]])
                face([top[i], leading[i + 1], leading[i]])
                face([trailing[i], bottom[i], leading[i + 1]])
                face([bottom[i], leading[i], leading[i + 1]])
        # The blade's root, inside the hub.
        face([trailing[0], top[0], leading[0], bottom[0]])
    # Hub: a low octagonal boss above and below (strips, no high-valence centre), its rim closed.
    ring = [point(hub * 1.2, 2.0 * math.pi * k / 8 + math.pi / 8) for k in range(8)]
    for z, up in ((ridge * 1.3, True), (-ridge * 1.3, False)):
        loop = [r + Vector((0, 0, z)) for r in ring]
        for indices in ((0, 1, 2, 3), (0, 3, 4, 7), (4, 5, 6, 7)):
            quad = [loop[i] for i in indices]
            face(quad if up else list(reversed(quad)))
    # The rim as a band round the texture, not the top projection (which smears down its sides).
    for k in range(8):
        n = (k + 1) % 8
        low, high = Vector((0, 0, -ridge * 1.3)), Vector((0, 0, ridge * 1.3))
        pl.add_face(bm, uv_layer, [(ring[k] + low, (k / 8, 0.45)), (ring[n] + low, ((k + 1) / 8, 0.45)),
                                   (ring[n] + high, ((k + 1) / 8, 0.55)), (ring[k] + high, (k / 8, 0.55))])
    obj = pl.to_object('Blades', bm, [pl.material('Steel', 'steel', 0.25, 0.45, normal=True)])
    length_of(obj)
    pl.export(obj, 'blades')


def shard_prism(bm, uv_layer, centre, rotation, size, rng):
    """A thin closed triangular prism: an irregular steel splinter."""
    corners = [Vector((rng.uniform(0.7, 1.0) * size * math.cos(a), rng.uniform(0.4, 1.0) * size * math.sin(a), 0))
               for a in (0.0, 2.2, 4.0)]
    corners[0].x *= 1.6
    thickness = size * 0.04
    top = [centre + rotation @ (c + Vector((0, 0, thickness))) for c in corners]
    bottom = [centre + rotation @ (c - Vector((0, 0, thickness))) for c in corners]

    def uv(co):
        return (co.x * 3.0 + 0.5, co.y * 3.0 + 0.5)

    pl.add_face(bm, uv_layer, [(c, uv(c)) for c in top])
    pl.add_face(bm, uv_layer, [(c, uv(c)) for c in reversed(bottom)])
    for i in range(3):
        j = (i + 1) % 3
        quad = [bottom[i], bottom[j], top[j], top[i]]
        pl.add_face(bm, uv_layer, [(c, uv(c)) for c in quad])


def shrapnel():
    rng = random.Random(5)
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new('UVMap')
    for _ in range(12):
        direction = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1))).normalized()
        centre = direction * rng.uniform(12, 25) * UNIT
        rotation = Matrix.Rotation(rng.uniform(0, math.pi * 2), 3, 'Z') @ Matrix.Rotation(rng.uniform(0, math.pi), 3, 'X')
        shard_prism(bm, uv_layer, centre, rotation, rng.uniform(6, 10) * UNIT, rng)
    obj = pl.to_object('Shrapnel', bm, [pl.material('Steel', 'steel', 0.3, 0.6, normal=True)])
    length_of(obj)
    pl.export(obj, 'shrapnel')


def fire_spike():
    """A caltrop: twelve square spikes along the icosahedron's vertex directions round a small icosphere core."""
    bm = pl.ico(10 * UNIT, 1)
    uv_layer = bm.loops.layers.uv.new('UVMap')
    pl.sphere_uv(bm, uv_layer)
    directions = [v.co.normalized() for v in pl.ico(1.0, 0).verts]
    for direction in directions:
        side = direction.orthogonal().normalized()
        up = direction.cross(side)
        base = direction * 6 * UNIT
        ring = [base + (side * math.cos(a) + up * math.sin(a)) * 5.5 * UNIT
                for a in (0.0, math.pi / 2, math.pi, 1.5 * math.pi)]
        tip = direction * 36 * UNIT
        for k in range(4):
            a, b = ring[k], ring[(k + 1) % 4]
            pl.add_face(bm, uv_layer, [(tip, (0.5, 1.0)), (a, (k / 4, 0.0)), (b, ((k + 1) / 4, 0.0))])
    obj = pl.to_object('FireSpike', bm, [pl.material('Steel', 'steel', 0.3, 0.6, normal=True)])
    length_of(obj)
    pl.export(obj, 'fire_spike')


def serpent():
    """Harm (7030, spell70): a serpent 194 long and 8.5 thick at most, head forward, in a gentle S (sideways and a
    little up and down, as the painted one slithers), tapering to its tail; the head is a flattened, rounded wedge.
    Rings of six sides; u runs along the body (tail 0, head 1), v round it with the back at 0.5."""
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new('UVMap')
    length, thickest, sides, stations = 194 * UNIT, 4.4 * UNIT, 6, 30
    rings = []
    for i in range(stations + 1):
        t = i / stations                       # 0 tail .. 1 head
        y = (0.5 - t) * length                 # the head leads toward -Y
        sway = math.sin(t * math.pi * 3.0) * 8.0 * UNIT * (0.35 + 0.65 * (1.0 - t))
        rise = math.sin(t * math.pi * 2.0 + 0.8) * 3.0 * UNIT
        # Thickest a little behind the head, a neck, the head's bulge, then the snout.
        radius = thickest * (min(1.0, 0.08 + t * 1.3) if t < 0.86 else 0.8 if t < 0.9 else 1.2 if t < 0.97 else 0.8)
        ring = []
        for k in range(sides + 1):
            angle = 2.0 * math.pi * k / sides - math.pi / 2     # k = 0 at the belly
            flat = 0.7 if t > 0.9 else 1.0                        # the head is flatter
            co = Vector((sway + radius * math.cos(angle), y, rise + radius * math.sin(angle) * flat))
            ring.append((co, (t, k / sides)))
        rings.append(ring)
    for a, b in zip(rings, rings[1:]):
        for k in range(sides):
            pl.add_face(bm, uv_layer, [a[k], a[k + 1], b[k + 1], b[k]])
    # The tail closes on a point behind its last ring, the snout on one ahead of its first.
    for ring, step, outward in ((rings[0], -1.5 * UNIT, False), (rings[-1], 6.0 * UNIT, True)):
        centre = sum((c for c, _ in ring[:-1]), Vector()) / sides
        tip = (centre + Vector((0.0, -step, 0.0)), (1.0 if outward else 0.0, 0.5))
        for k in range(sides):
            tri = [tip, ring[k + 1], ring[k]] if outward else [tip, ring[k], ring[k + 1]]
            pl.add_face(bm, uv_layer, tri)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    obj = pl.to_object('Serpent', bm, [pl.material('Serpent', 'serpent', 0.45)], 70)
    length_of(obj)
    pl.export(obj, 'serpent')


def burning(name, flame, core_radius, core_rough, card_scale, core_u, lava):
    """A lava core and crossed flame cards. The card spans the flame window (sprite pixels at x2: world units = px / 2);
    the origin is the sprite frame's centre, at u = (128 - x0) / w along the window."""
    window = json.load(open(os.path.join(pl.TEXTURES, 'flames.json')))[flame]['window']
    x0, _, w, h = window
    length = w / 2 * UNIT * card_scale
    half = h / 4 * UNIT * card_scale
    centre_u = (128 - x0) / w
    front = -centre_u * length
    back = front + length
    core_y = front + core_u * length
    bm = rock_mesh(core_radius * UNIT, core_rough, 1.8, 7, (1.0, 1.0, 1.0), 2 if core_radius < 25 else 3)
    bmesh.ops.translate(bm, verts=bm.verts, vec=Vector((0.0, core_y, 0.0)))
    uv_layer = bm.loops.layers.uv['UVMap']
    pl.crossed_cards(bm, uv_layer, back, front, half, 1)
    obj = pl.to_object(name.capitalize(), bm, [pl.material('Lava', lava, 0.8), pl.material('Fire', flame, alpha=True)],
                       60)
    length_of(obj)
    pl.export(obj, name, {'Lava': {'unlit': True}, 'Fire': dict(FLAME, flipbook=[2, 4, 10])})


def starburst():
    # The painted ball is about 100 px across with its centre a third of the way along the window.
    burning('starburst', 'starburst_flame', 13, 0.2, 1.0, 0.33, 'lava_hot')


def meteor():
    # The painted rock is about 33 px across at the window's front.
    burning('meteor', 'meteor_flame', 8.5, 0.4, 1.0, 0.08, 'lava')


BUILDERS = {f.__name__: f for f in (cannonball, boulder, rock, ice_shard, blades, shrapnel, fire_spike, starburst,
                                    meteor, serpent)}


def main():
    for name in sys.argv[sys.argv.index('--') + 1:]:
        pl.reset()
        BUILDERS[name]()


main()
