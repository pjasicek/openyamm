"""MM6 dungeon trash heap `trasheap` (256 x 138): a wide low mound of straw, twigs and grit (`straw`, a noise-lumped
elliptical heightfield 1.85 x the height across and 1.1 deep, peaking at half the height) heaped with the sprite's
debris, each placed where the sprite shows it (positions in fractions of the height, x right, -y toward the viewer)
and sunk into the mound: a big broken barrel tipped over at the back (staves missing, open end toward the viewer),
an orange half keg split open lying across the middle, a conical riveted iron pot, a loose barrel hoop, a grey
broken crate tipped on its side with brass corners, a bundle of red-brown boards standing behind it, a rusty iron
block on its corner and a rusty plate at the right, dark clinker rocks, a charred log, a rusty pot shell in front, a
brass bone, a hammer and a pewter spoon, plus a few rags and pottery shards. Every part carries its own COLOR_0
tint (the sprite's colour of that object) times the occlusion of the whole heap, so few materials serve many
differently coloured parts. LOD1/LOD2 use coarser parts and drop the smallest ones.
Writes work/trasheap_export.glb. Usage: blender --background --python build_trasheap.py"""
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Euler, Matrix, Vector, noise

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import containers_lib as cl  # noqa: E402

pl = cl.pl
H = cl.u(138)

pl.reset()
mats = {
    'Straw': cl.material('Straw', 'straw'),
    'Wood': cl.material('Wood', 'staves'),
    'Planks': cl.material('Planks', 'wood'),
    'Iron': cl.material('Iron', 'iron'),
    'Rust': cl.material('Rust', 'rust'),
    'Rock': cl.material('Rock', 'granite'),
    'Bark': cl.material('Bark', 'logs'),
    'Bone': cl.material('Bone', 'bone'),
    'Pewter': cl.material('Pewter', 'pewter'),
    'Crockery': cl.material('Crockery', 'crockery'),
    'Rag': cl.material('Rag', 'rag'),
}

# Sprite colours of the parts (sRGB, read off the native sprite; dark like the dungeon art).
COLOURS = {
    'straw': (92, 80, 60), 'barrel': (78, 56, 38), 'keg': (138, 72, 34), 'crate': (82, 80, 74),
    'boards': (104, 52, 32), 'iron': (78, 74, 70), 'hoop': (96, 96, 98), 'rust': (100, 52, 28), 'rock': (38, 36, 34),
    'char': (34, 31, 29), 'brass': (190, 160, 84), 'pewter': (168, 168, 170), 'crockery': (120, 80, 52),
    'rag': (92, 84, 70), 'gold': (150, 120, 50),
}
_tint_cache = {}


def tag(obj, mat_name, colour):
    """Per-vertex 'Tint' attribute (linear multiplier bringing the material's texture to the part's colour)."""
    key = (mat_name, colour)
    if key not in _tint_cache:
        _tint_cache[key] = cl.tint_for(mats[mat_name], COLOURS[colour])
    t = _tint_cache[key]
    me = obj.data
    attr = me.color_attributes.new('Tint', 'FLOAT_COLOR', 'POINT')
    attr.data.foreach_set('color', np.tile(np.array((*t, 1.0), np.float32), len(me.vertices)))
    return obj


def place(obj, location, rotation=(0, 0, 0)):
    """Rotate (Euler XYZ, radians) about the local origin, then move to location (fractions of H)."""
    obj.data.transform(Matrix.Translation(Vector(location) * H) @ Euler(rotation).to_matrix().to_4x4())
    return obj


# ---------------------------------------------------------------- the mound
def mound_height(x, y):
    """Mound surface height (fractions of H) at (x, y) in fractions of H."""
    rho2 = ((x - 0.04) / 0.93) ** 2 + (y / 0.56) ** 2
    if rho2 >= 1:
        return 0.0
    base = 0.56 * (1 - rho2) ** 0.75
    lumps = (noise.noise(Vector((x * 7, y * 7, 0.5))) * 0.035 + noise.noise(Vector((x * 19, y * 19, 3.3))) * 0.012)
    return max(0.0, base + lumps * min(1.0, (1 - rho2) * 5))


def mound(level):
    rings, segments = ((14, 52), (7, 24), (4, 10))[level]
    bm = bmesh.new()
    uv = bm.loops.layers.uv.verify()
    centre = bm.verts.new((0.04 * H, 0, mound_height(0.04, 0) * H))
    grid = []
    for i in range(1, rings + 1):
        f = (i / rings) ** 0.8
        row = []
        for s in range(segments):
            a = 2 * math.pi * s / segments
            x = 0.04 + 0.93 * f * math.cos(a) * (1 + 0.04 * noise.noise(Vector((math.cos(a) * 2, math.sin(a) * 2, 7))))
            y = 0.56 * f * math.sin(a)
            z = mound_height(x, y) if i < rings else 0.0
            row.append(bm.verts.new((x * H, y * H, z * H)))
        grid.append(row)
    for s in range(segments):
        t = (s + 1) % segments
        bm.faces.new((centre, grid[0][s], grid[0][t]))
        for i in range(rings - 1):
            bm.faces.new((grid[i][s], grid[i + 1][s], grid[i + 1][t], grid[i][t]))
    for face in bm.faces:
        for loop in face.loops:
            loop[uv].uv = (loop.vert.co.x / 0.7, loop.vert.co.y / 0.7)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return tag(pl.to_object('mound', bm, mats['Straw']), 'Straw', 'straw')


def ground(x, y):
    return mound_height(x, y)


# ---------------------------------------------------------------- part builders (local, then placed)
def shell(name, radius, length, sides, mat, keep=lambda s: True, bulge=0.06, thickness=0.02, rings=4, u_repeat=2):
    """Barrel shell along local z from 0 to length: outer and inner stave faces for the kept stave columns."""
    bm = bmesh.new()
    uv = bm.loops.layers.uv.verify()

    def r_at(z):
        t = (z / length - 0.5) * 2
        return radius * (1 + bulge * (1 - t * t))

    for s in range(sides):
        if not keep(s):
            continue
        a0, a1 = 2 * math.pi * s / sides, 2 * math.pi * (s + 1) / sides
        for surface, scale in ((0, 1.0), (1, 1.0 - thickness / radius)):
            for i in range(rings):
                z0, z1 = length * i / rings, length * (i + 1) / rings
                quad = [(a0, z0), (a1, z0), (a1, z1), (a0, z1)]
                if surface:
                    quad = list(reversed(quad))
                verts = [bm.verts.new((r_at(z) * scale * math.cos(a), r_at(z) * scale * math.sin(a), z))
                         for a, z in quad]
                face = bm.faces.new(verts)
                for loop, (a, z) in zip(face.loops, quad):
                    loop[uv].uv = (a / (2 * math.pi) * u_repeat, z / length)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    return pl.to_object(name, bm, mat, smooth=False)


def band(name, radius, z0, z1, sides, mat, arc=(0.0, 1.0), proud=0.012):
    """A hoop band round a shell (optionally only an arc of it)."""
    bm = bmesh.new()
    uv = bm.loops.layers.uv.verify()
    n = max(2, round(sides * (arc[1] - arc[0])))
    rings = []
    for k in range(n + 1):
        a = 2 * math.pi * (arc[0] + (arc[1] - arc[0]) * k / n)
        rings.append([bm.verts.new(((radius + d) * math.cos(a), (radius + d) * math.sin(a), z))
                      for d, z in ((0, z0), (proud, z0), (proud, z1), (0, z1))])
    for k in range(n):
        for j in range(3):
            face = bm.faces.new((rings[k][j], rings[k + 1][j], rings[k + 1][j + 1], rings[k][j + 1]))
            for loop in face.loops:
                loop[uv].uv = (loop.vert.co.x * 4, loop.vert.co.z * 4)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return pl.to_object(name, bm, mat, smooth=False)


def boxy(name, size, mat, uv_scale=3.0):
    return pl.box(name, (0, 0, 0), tuple(v * H for v in size), mat, uv_scale=uv_scale)


def lump(name, radius, mat, subdivisions, seed, squash=0.7):
    bm = bmesh.new()
    uv = bm.loops.layers.uv.verify()
    bmesh.ops.create_icosphere(bm, subdivisions=subdivisions, radius=radius * H)
    for v in bm.verts:
        d = 1 + 0.25 * noise.noise(v.co * (4 / (radius * H)) + Vector((seed, 0, 0)))
        v.co = Vector((v.co.x * d, v.co.y * d, v.co.z * d * squash))
    for face in bm.faces:
        for loop in face.loops:
            loop[uv].uv = (loop.vert.co.x / 0.3 + loop.vert.co.z / 0.3, loop.vert.co.y / 0.3)
    return pl.to_object(name, bm, mat, smooth=False)


def lathe(name, profile, sides, mat, **kw):
    return pl.lathe(name, [(r * H, z * H) for r, z in profile], sides, mat, **kw)


def tube(name, a, b, ra, rb, sides, mat, v_scale=4.0):
    return pl.tube(name, Vector(a) * H, Vector(b) * H, ra * H, rb * H, sides, mat, v_scale=v_scale)


def crumple(name, size, mat, segments, seed):
    """A rag or shard: a small displaced sheet (two-sided by thickness: a flattened lump)."""
    bm = bmesh.new()
    uv = bm.loops.layers.uv.verify()
    n = segments
    verts = {}
    for i in range(n + 1):
        for j in range(n + 1):
            x, y = (i / n - 0.5) * size[0], (j / n - 0.5) * size[1]
            z = noise.noise(Vector((x * 9 / size[0], y * 9 / size[0], seed))) * size[2]
            verts[i, j] = bm.verts.new((x * H, y * H, z * H))
    for i in range(n):
        for j in range(n):
            face = bm.faces.new((verts[i, j], verts[i + 1, j], verts[i + 1, j + 1], verts[i, j + 1]))
            for loop in face.loops:
                loop[uv].uv = (loop.vert.co.x * 3, loop.vert.co.y * 3)
    bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=0.008 * H)
    return pl.to_object(name, bm, mat, smooth=False)


# ---------------------------------------------------------------- the heap
def rest(group, x, y, rotation, sink, spin=0.0):
    """Rotate a group of parts (local origin) by rotation (Euler XYZ or a direction for local +z), turn it about the
    vertical by spin, then set it down at (x, y) with its lowest point sink x its height below the mound surface."""
    if isinstance(rotation, Vector):
        matrix = Vector((0, 0, 1)).rotation_difference(rotation.normalized()).to_matrix().to_4x4()
    else:
        matrix = Euler(rotation).to_matrix().to_4x4()
    matrix = Matrix.Rotation(spin, 4, 'Z') @ matrix
    for obj in group:
        obj.data.transform(matrix)
    zs = [v.co.z for obj in group for v in obj.data.vertices]
    lo, hi = min(zs), max(zs)
    xs = [v.co.x for obj in group for v in obj.data.vertices]
    ys = [v.co.y for obj in group for v in obj.data.vertices]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    shift = Vector((x * H - cx, y * H - cy, (ground(x, y) - sink * (hi - lo) / H) * H - lo))
    for obj in group:
        obj.data.transform(Matrix.Translation(shift))
    return group


def barrel_group(name, radius, length, sides, rings, keep, colour, hoops, arc=(0.0, 1.0), bottom=True):
    parts = [tag(shell(name, radius * H, length * H, sides, mats['Wood'], keep=keep, rings=rings, u_repeat=2),
                 'Wood', colour)]
    for k, (z0, z1) in enumerate(hoops):
        parts.append(tag(band(f'{name}hoop{k}', radius * H * 1.05, z0 * H, z1 * H, sides, mats['Iron'], arc=arc,
                              proud=0.01 * H), 'Iron', 'hoop'))
    if bottom:
        parts.append(tag(lathe(f'{name}bottom', [(0.0, 0.004), (radius * 0.98, 0.004)], sides, mats['Wood']),
                         'Wood', colour))
    return parts


def debris(level):
    parts = []
    sides = (16, 10, 7)[level]
    small = level < 2

    # Big broken barrel tipped back at the rear, its open end toward the viewer and up; staves missing.
    missing = (1, 2, sides // 2 + 2) if level < 2 else ()
    group = barrel_group('barrel', 0.21, 0.46, sides, (4, 2, 1)[level], lambda s: s not in missing, 'barrel',
                         ((0.05, 0.09), (0.36, 0.40)))
    parts += rest(group, 0.14, 0.2, Vector((-0.25, -0.75, 0.62)), 0.12)

    # Orange half keg split open, lying across the middle.
    group = barrel_group('keg', 0.16, 0.42, sides, (3, 2, 1)[level], lambda s: s < sides * 0.62, 'keg',
                         ((0.06, 0.1), (0.31, 0.35)) if small else (), arc=(0.0, 0.62), bottom=False)
    parts += rest(group, -0.22, -0.12, (math.radians(90), 0, 0), 0.25, spin=math.radians(-75))

    # Conical riveted iron pot (or helm), a little tilted.
    pot = lathe('pot', [(0.0, 0.0), (0.15, 0.0), (0.16, 0.035), (0.14, 0.14), (0.095, 0.27), (0.04, 0.37),
                        (0.0, 0.40)], sides, mats['Iron'], u_repeat=2, v_scale=4.0)
    group = [tag(pot, 'Iron', 'iron')]
    if small:
        clasp = boxy('clasp', (0.035, 0.025, 0.12), mats['Rust'])
        clasp.data.transform(Matrix.Translation(Vector((0.13, 0, 0.12)) * H) @ Euler((0, -0.35, 0)).to_matrix()
                             .to_4x4())
        group.append(tag(clasp, 'Rust', 'gold'))
    parts += rest(group, 0.22, -0.02, (math.radians(10), math.radians(-12), 0), 0.15)

    # Loose barrel hoop standing tilted.
    if small:
        count = (24, 12)[level]
        ring = [Vector((0.1 * math.cos(a), 0, 0.1 * math.sin(a))) * H for a in
                (2 * math.pi * k / count for k in range(count))]
        hoop = cl.sweep('hoop', ring, 0.012 * H, (5, 4)[level], mats['Iron'], closed=True)
        parts += rest([tag(hoop, 'Iron', 'hoop')], -0.34, 0.06, (0, math.radians(20), 0), 0.15,
                      spin=math.radians(20))

    # Broken crate tipped on its side (open toward the front right), brass corners.
    crate = []
    w, d, h, t = 0.62, 0.42, 0.36, 0.028
    for name, centre, size in (('cbase', (0, 0, t / 2), (w, d, t)), ('cback', (0, d / 2 - t / 2, h / 2), (w, t, h)),
                               ('cleft', (-w / 2 + t / 2, 0, h / 2), (t, d, h)),
                               ('cright', (w / 2 - t / 2, 0, h / 2), (t, d, h)),
                               ('cfront', (0.1, -d / 2 + t / 2, h * 0.3), (w * 0.55, t, h * 0.6)),
                               ('cslat', (-0.05, 0.0, h - t / 2), (t * 1.6, d, t))):
        if level == 2 and name in ('cfront', 'cslat'):
            continue
        board = boxy(name, size, mats['Planks'])
        board.data.transform(Matrix.Translation(Vector(centre) * H))
        crate.append(tag(board, 'Planks', 'crate'))
    if level == 0:
        for k, (cx, cy) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1))):
            corner = boxy(f'corner{k}', (0.04, 0.04, 0.05), mats['Rust'])
            corner.data.transform(Matrix.Translation(Vector((cx * w / 2, cy * d / 2, h - 0.025)) * H))
            crate.append(tag(corner, 'Rust', 'gold'))
    parts += rest(crate, -0.6, -0.1, (math.radians(62), 0, 0), 0.08, spin=math.radians(22))

    # A bundle of red-brown boards standing behind the crate.
    boards = []
    for k in range((5, 3, 2)[level]):
        board = boxy(f'board{k}', (0.07, 0.022, 0.36 + 0.04 * (k % 2)), mats['Planks'])
        board.data.transform(Matrix.Translation(Vector((0.072 * k, 0.01 * k, 0.18)) * H)
                             @ Euler((0, math.radians(4 - 2 * k), 0)).to_matrix().to_4x4())
        boards.append(tag(board, 'Planks', 'boards'))
    parts += rest(boards, -0.5, 0.22, (math.radians(-8), math.radians(12), 0), 0.25, spin=math.radians(-10))

    # Rusty iron block on its corner (front left), rusty plate leaning at the right.
    block = boxy('block', (0.2, 0.2, 0.2), mats['Rust'], uv_scale=4.0)
    parts += rest([tag(block, 'Rust', 'rust')], -0.44, -0.34, (math.radians(45), math.radians(35), 0), 0.1)
    plate = boxy('plate', (0.36, 0.26, 0.055), mats['Rust'], uv_scale=4.0)
    parts += rest([tag(plate, 'Rust', 'rust')], 0.72, -0.14, (math.radians(-35), math.radians(8), 0), 0.15,
                  spin=math.radians(-12))

    # Dark clinker rocks and a charred log.
    for k, (x, y, r) in enumerate(((0.44, 0.14, 0.095), (0.5, -0.02, 0.08), (0.64, 0.18, 0.07), (0.1, -0.5, 0.05),
                                   (-0.04, -0.46, 0.045), (0.78, 0.02, 0.05))):
        if level == 2 and k > 1:
            continue
        rock = lump(f'rock{k}', r, mats['Rock'], (2, 1, 1)[level], seed=k * 3.1)
        parts += rest([tag(rock, 'Rock', 'rock')], x, y, (0, 0, k), 0.3)
    log = tube('log', (-0.24, 0, 0), (0.24, 0, 0), 0.085, 0.07, (9, 6, 5)[level], mats['Bark'], v_scale=3.0)
    parts += rest([tag(log, 'Bark', 'char')], 0.04, -0.33, (0, math.radians(-14), 0), 0.3, spin=math.radians(-28))

    # Rusty pot shell in front, half buried.
    shellpot = shell('potshell', 0.13 * H, 0.18 * H, sides, mats['Rust'], keep=lambda s: s < sides * 0.55, rings=1,
                     bulge=0.1, u_repeat=2)
    parts += rest([tag(shellpot, 'Rust', 'rust')], -0.16, -0.5, (math.radians(90), 0, 0), 0.3,
                  spin=math.radians(200))

    if small:
        # Brass bone, hammer, pewter spoon.
        bone = [tube('bone', (-0.06, 0, 0), (0.06, 0, 0), 0.015, 0.015, (6, 4)[level], mats['Bone'])]
        for k, x in enumerate((-0.07, 0.07)):
            knob = lump(f'knob{k}', 0.024, mats['Bone'], 1, seed=k, squash=1.0)
            knob.data.transform(Matrix.Translation(Vector((x, 0, 0)) * H))
            bone.append(knob)
        parts += rest([tag(p, 'Bone', 'brass') for p in bone], 0.3, -0.26, (0, 0, 0), 0.2, spin=math.radians(20))
        handle = tube('handle', (0, 0, 0), (0.17, 0, 0.0), 0.013, 0.013, (6, 4)[level], mats['Planks'])
        head = boxy('head', (0.04, 0.04, 0.08), mats['Iron'])
        head.data.transform(Matrix.Translation(Vector((0.17, 0, 0)) * H))
        parts += rest([tag(handle, 'Planks', 'char'), tag(head, 'Iron', 'iron')], 0.32, -0.42,
                      (0, math.radians(-25), 0), 0.25, spin=math.radians(-10))
        spoon = lump('spoon', 0.05, mats['Pewter'], 1, seed=4.0, squash=0.3)
        spoon.data.transform(Matrix.Diagonal((1.4, 1.0, 1.0, 1.0)))
        stick = tube('spoonhandle', (0.06, 0, 0), (0.18, 0, 0.02), 0.009, 0.007, 4, mats['Pewter'])
        parts += rest([tag(spoon, 'Pewter', 'pewter'), tag(stick, 'Pewter', 'pewter')], 0.54, -0.4,
                      (math.radians(-20), math.radians(-10), 0), 0.2, spin=math.radians(160))
        # Rags and pottery shards on the straw.
        for k, (x, y, rz) in enumerate(((0.6, -0.28, 0.4), (-0.72, 0.12, -0.3))):
            rag = crumple(f'rag{k}', (0.22, 0.15, 0.035), mats['Rag'], (5, 3)[level], seed=k + 0.5)
            parts += rest([tag(rag, 'Rag', 'rag')], x, y, (0.15, -0.1, rz), 0.4)
        for k, (x, y, rz) in enumerate(((-0.62, -0.38, 0.3), (0.2, -0.56, 1.2), (0.82, 0.12, 2.0))):
            shard = crumple(f'shard{k}', (0.09, 0.07, 0.014), mats['Crockery'], 2, seed=k + 7.0)
            parts += rest([tag(shard, 'Crockery', 'crockery')], x, y, (0.4, 0.3, rz), 0.4)
    return parts


def colour(obj):
    """COLOR_0 = occlusion x the per-part tint; drop the helper attribute."""
    me = obj.data
    occ = me.color_attributes['Color']
    tint = me.color_attributes['Tint']
    n = len(me.vertices)
    a = np.empty(n * 4, np.float32)
    b = np.empty(n * 4, np.float32)
    occ.data.foreach_get('color', a)
    tint.data.foreach_get('color', b)
    a = a.reshape(-1, 4)
    b = b.reshape(-1, 4)
    a[:, :3] *= b[:, :3]
    occ.data.foreach_set('color', a.ravel())
    me.color_attributes.remove(tint)
    me.color_attributes.active_color = me.color_attributes['Color']
    me.color_attributes.render_color_index = me.color_attributes.active_color_index   # what the exporter writes


lods = []
for level in range(3):
    obj = pl.join(f'heap{level}', [mound(level)] + debris(level))
    cl.clamp_ground(obj)
    lods.append(obj)
done = []
for level, obj in enumerate(lods):
    mean = pl.vertex_occlusion(obj, rays=(40, 24, 12)[level], distance=0.25 * H, strength=0.7, floor=True)
    colour(obj)
    name = 'TrashHeap' if level == 0 else f'TrashHeap_LOD{level}'
    obj.name = name
    obj.data.name = name
    print('LEVEL', level, name, 'tris', pl.triangles(obj), 'mean occlusion', round(mean, 3))
    done.append(obj)
os.makedirs(cl.WORK, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(cl.WORK, 'trasheap.blend'))
pl.export(done, os.path.join(cl.WORK, 'trasheap_export.glb'))
