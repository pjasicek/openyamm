"""Sword in the stone `swrdstn` and its post-event state `swrdstx`: one boulder (props/swordboulder, a Poly Haven scan
through ../scripts/build_prop.py), with a steel sword plunged into its top in swrdstn only. The engine scales each model
to its sprite's height (174 / 83 units), so the sword reaches SWORD_RATIO x the boulder height and the boulder appears
at the same size in both states. Writes work/swordstone_export.glb (SwordStone*) and work/swordstone_empty_export.glb
(Boulder*). Usage: blender --background --python build_swordstone.py"""
import bpy, bmesh, math, os, sys
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import props_lib as pl

SWORD_RATIO = 174.0 / 83.0
pl.reset()
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=os.path.join(pl.PROPS, 'swordboulder', 'work', 'swordboulder_export.glb'))
boulders = sorted([o for o in bpy.data.objects if o not in before and o.type == 'MESH'], key=lambda o: len(o.name))
for o in boulders:
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
lo, hi = pl.bounds([boulders[0]])
height = hi.z
# boulder surface above the centre: where the sword enters
depsgraph = bpy.context.evaluated_depsgraph_get()
from mathutils.bvhtree import BVHTree
bvh = BVHTree.FromObject(boulders[0], depsgraph)
entry, *_ = bvh.ray_cast(Vector((0.05, 0.0, height + 1.0)), Vector((0, 0, -1)))
entry_z = entry.z if entry is not None else height
top = height * SWORD_RATIO
blade_mat = pl.material('Blade', 'blade'); leather = pl.material('Leather', 'leather')
bronze = pl.material('Bronze', 'bronze')
print('SWORDSTONE boulder height', round(height, 3), 'entry', round(entry_z, 3), 'sword top', round(top, 3))

X, Y = 0.05, 0.0                                   # sword axis (vertical through the boulder top)
POMMEL_H, GRIP_H, GUARD_H = 0.14, 0.42, 0.09
WIDTH, THICK = 0.17, 0.045


def make_blade(level):
    """Blade with bevelled edges and a central fuller, tapering in width towards the point (inside the stone). Both
    faces map u across the blade from edge to edge and v from the point (0) to the guard (1): the blade texture."""
    guard_z = top - POMMEL_H - GRIP_H - GUARD_H
    point_z = entry_z - 0.35
    # Half-section from one edge to the centre line: (fraction of half-width, fraction of half-thickness).
    half = {0: [(1.0, 0.0), (0.66, 0.62), (0.18, 0.78), (0.09, 0.55), (0.0, 0.5)],
            1: [(1.0, 0.0), (0.66, 0.62), (0.0, 0.8)],
            2: [(1.0, 0.0), (0.0, 1.0)], 3: [(1.0, 0.0), (0.0, 1.0)]}[level]
    across = [(-w, t) for w, t in half] + [(w, t) for w, t in reversed(half[:-1])]   # left edge -> right edge
    rings_z = {0: [guard_z, guard_z - 0.06, guard_z - 0.5, guard_z - 1.0, entry_z + 0.05, point_z + 0.25],
               1: [guard_z, guard_z - 0.06, entry_z + 0.05, point_z + 0.25], 2: [guard_z, point_z + 0.25],
               3: [guard_z, point_z + 0.25]}[level]

    def width_at(z):
        # Ricasso keeps the full width, then a gentle taper to 70 % at the point's shoulder.
        t = (guard_z - 0.06 - z) / max(guard_z - 0.06 - (point_z + 0.25), 1e-6)
        return WIDTH * (1.0 - 0.30 * min(max(t, 0.0), 1.0))

    bm = bmesh.new(); uv = bm.loops.layers.uv.verify()
    tip = bm.verts.new((X, Y, point_z))
    for side in (1, -1):                               # front (+y) and back (-y) faces
        rows = []
        for z in rings_z:
            w = width_at(z) / 2
            rows.append([bm.verts.new((X + a * w, Y + side * b * THICK / 2, z)) for a, b in across])
        for r in range(len(rows) - 1):
            lower, upper = rows[r + 1], rows[r]
            vl, vu = (rings_z[r + 1] - point_z) / (guard_z - point_z), (rings_z[r] - point_z) / (guard_z - point_z)
            for i in range(len(across) - 1):
                quad = (lower[i], lower[i + 1], upper[i + 1], upper[i]) if side > 0 else \
                    (lower[i + 1], lower[i], upper[i], upper[i + 1])
                f = bm.faces.new(quad)
                us = (i / (len(across) - 1), (i + 1) / (len(across) - 1))
                coords = ((us[0], vl), (us[1], vl), (us[1], vu), (us[0], vu)) if side > 0 else \
                    ((us[1], vl), (us[0], vl), (us[0], vu), (us[1], vu))
                for loop, c in zip(f.loops, coords):
                    loop[uv].uv = c
        last = rows[-1]
        for i in range(len(across) - 1):
            tri = (tip, last[i + 1], last[i]) if side > 0 else (tip, last[i], last[i + 1])
            f = bm.faces.new(tri)
            for loop in f.loops:
                co = loop.vert.co
                loop[uv].uv = (0.5 + (co.x - X) / WIDTH, (co.z - point_z) / (guard_z - point_z))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)   # the shared edge vertices join the two faces
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return pl.to_object('blade', bm, blade_mat, smooth=False)


def sweep(name, points, radii, sides, mat, u_repeat=1.0, v_scale=1.0):
    """Tube along a polyline with a radius per point (closed rings, capped ends)."""
    bm = bmesh.new(); uv = bm.loops.layers.uv.verify()
    rings, travelled = [], [0.0]
    for k in range(1, len(points)):
        travelled.append(travelled[-1] + (Vector(points[k]) - Vector(points[k - 1])).length)
    for k, (p, r) in enumerate(zip(points, radii)):
        a = Vector(points[max(k - 1, 0)]); b = Vector(points[min(k + 1, len(points) - 1)])
        axis = (b - a).normalized(); side = Vector((0, 1, 0)); other = axis.cross(side).normalized()
        side = other.cross(axis).normalized()
        rings.append([bm.verts.new(Vector(p) + (side * math.cos(2 * math.pi * s / sides)
                                                + other * math.sin(2 * math.pi * s / sides)) * r)
                      for s in range(sides)])
    for k in range(len(rings) - 1):
        for s in range(sides):
            s2 = (s + 1) % sides
            f = bm.faces.new((rings[k][s], rings[k][s2], rings[k + 1][s2], rings[k + 1][s]))
            for loop, (uu, vv) in zip(f.loops, ((s, k), (s + 1, k), (s + 1, k + 1), (s, k + 1))):
                loop[uv].uv = (uu / sides * u_repeat, travelled[vv] * v_scale)
    for ring, flip in ((rings[0], True), (rings[-1], False)):
        f = bm.faces.new(list(reversed(ring)) if flip else ring)
        for loop in f.loops:
            loop[uv].uv = (0.5, 0.5)
    return pl.to_object(name, bm, mat, True)


def crossguard(level):
    """Quillons that taper outwards and curve slightly towards the blade, ending in round knobs; a raised centre
    block where the blade passes through."""
    guard_z = top - POMMEL_H - GRIP_H - GUARD_H
    z0 = guard_z + GUARD_H / 2
    steps = (6, 3, 1, 1)[level]
    sides = (8, 6, 4, 4)[level]
    parts = []
    for direction in (1, -1):
        points, radii = [], []
        for k in range(steps + 1):
            t = k / steps
            points.append((X + direction * (0.04 + 0.25 * t), Y, z0 - 0.035 * t * t))
            radii.append(0.04 - 0.014 * t)
        parts.append(sweep('quillon', points, radii, sides, bronze, 1.0, 3.0))
        if level < 2:
            bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=(2, 1)[level], radius=0.042)
            uv = bm.loops.layers.uv.verify()
            for vert in bm.verts:
                vert.co += Vector((X + direction * 0.30, Y, z0 - 0.04))
            for f in bm.faces:
                for loop in f.loops:
                    loop[uv].uv = (loop.vert.co.x * 4, loop.vert.co.z * 4)
            parts.append(pl.to_object('knob', bm, bronze))
    parts.append(pl.box('centre', (X, Y, z0), (0.11, 0.075, GUARD_H * 1.1), bronze, 2.0))
    return parts


def grip(level):
    """Leather wound in a spiral (raised turns) between two bronze collars."""
    guard_z = top - POMMEL_H - GRIP_H - GUARD_H
    z0, z1 = guard_z + GUARD_H + 0.03, top - POMMEL_H - 0.02
    parts = []
    if level == 0:
        sides, rings, turns = 12, 36, 9
        bm = bmesh.new(); uv = bm.loops.layers.uv.verify()
        verts = []
        for r in range(rings + 1):
            t = r / rings
            z = z0 + (z1 - z0) * t
            ring = []
            for s in range(sides):
                a = 2 * math.pi * s / sides
                wrap = (0.5 + 0.5 * math.cos(2 * math.pi * turns * t - a)) ** 3
                radius = (0.034 - 0.003 * t) * (1.0 + 0.09 * wrap)
                ring.append(bm.verts.new((X + math.cos(a) * radius, Y + math.sin(a) * radius, z)))
            verts.append(ring)
        for r in range(rings):
            for s in range(sides):
                s2 = (s + 1) % sides
                f = bm.faces.new((verts[r][s], verts[r][s2], verts[r + 1][s2], verts[r + 1][s]))
                for loop, (uu, vv) in zip(f.loops, ((s, r), (s + 1, r), (s + 1, r + 1), (s, r + 1))):
                    loop[uv].uv = (uu / sides, vv / rings * 3)
        parts.append(pl.to_object('grip', bm, leather))
    else:
        parts.append(pl.tube('grip', (X, Y, z0), (X, Y, z1), 0.035, 0.032, (8, 6, 4)[level - 1] if level < 3 else 4,
                             leather, v_scale=3))
    if level < 3:
        for z, length in ((z0 - 0.03, 0.035), (z1, 0.025)):
            parts.append(pl.tube('collar', (X, Y, z), (X, Y, z + length), 0.041, 0.039, (12, 8, 6)[level], bronze,
                                 v_scale=4))
    return parts


def pommel(level):
    """Wheel pommel: a bevelled disc facing front and back, a central boss on each face, and the peened tang end."""
    centre = Vector((X, Y, top - POMMEL_H * 0.5))
    if level >= 3:
        return [pl.box('pommel', tuple(centre), (0.13, 0.05, 0.12), bronze, 2.0)]
    segments = (20, 12, 8)[level]
    profile = [(0.0, -0.032), (0.045, -0.032), (0.062, -0.022), (0.068, 0.0), (0.062, 0.022), (0.045, 0.032),
               (0.0, 0.032)] if level == 0 else [(0.0, -0.03), (0.066, -0.025), (0.066, 0.025), (0.0, 0.03)]
    disc = pl.lathe('pommel', profile, segments, bronze, u_repeat=2.0, v_scale=4.0)
    disc.rotation_euler = (math.pi / 2, 0, 0); disc.location = centre
    bpy.context.view_layer.update()
    bpy.ops.object.select_all(action='DESELECT'); disc.select_set(True); bpy.context.view_layer.objects.active = disc
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    parts = [disc]
    if level == 0:
        for direction in (1, -1):
            parts.append(pl.tube('boss', tuple(centre), tuple(centre + Vector((0, direction * 0.045, 0))), 0.026,
                                 0.018, 10, bronze, v_scale=4))
        # The peened tang end finishes exactly at the sword top, which sets the model height (and so its scale).
        parts.append(pl.tube('tang', tuple(centre + Vector((0, 0, 0.05))), (X, Y, top), 0.016, 0.012, 8, bronze,
                             v_scale=4))
    return parts


def sword(level):
    return pl.join(f'sword{level}', [make_blade(level)] + crossguard(level) + grip(level) + pommel(level))


work = os.path.join(pl.PROPS, 'work')
empty, full = [], []
for level, boulder in enumerate(boulders):
    pl.white_colour(boulder)                 # the scan's ambient occlusion is in its base colour
    copy = boulder.copy(); copy.data = boulder.data.copy(); bpy.context.scene.collection.objects.link(copy)
    blade = sword(level); pl.white_colour(blade)
    name = 'SwordStone' if level == 0 else f'SwordStone_LOD{level}'
    full.append(pl.join(name, [copy, blade]))
    boulder.name = 'Boulder' if level == 0 else f'Boulder_LOD{level}'
    empty.append(boulder)
    print('LEVEL', level, 'sword stone tris', pl.triangles(full[-1]), 'boulder tris', pl.triangles(boulder))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(work, 'swordstone.blend'))
pl.export(full, os.path.join(work, 'swordstone_export.glb'))
pl.export(empty, os.path.join(work, 'swordstone_empty_export.glb'))
