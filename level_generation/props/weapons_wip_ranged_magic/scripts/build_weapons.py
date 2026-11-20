"""Owned ranged/magic components; run in a private background Blender scene.

blender -b -t 8 --python scripts/build_weapons.py -- [--pilots] [--render]
UV swatches deliberately overlap on identical material, with an inset of 10 texels.
"""
import argparse
import json
import math
from pathlib import Path
import subprocess
import sys

import bmesh
import bpy
from mathutils import Vector
from mathutils.geometry import closest_point_on_tri
from mathutils.bvhtree import BVHTree

HERE = Path(__file__).resolve().parents[1]
OWNED = json.loads((HERE / 'ownership.json').read_text())
PILOTS = ['7item042', '7item047', '7item064', '7item138']
SURFACE = {'wood': 0, 'elm': 1, 'leather': 2, 'redleather': 3, 'steel': 4, 'gold': 5,
           'bone': 6, 'silver': 7, 'blue': 8, 'green': 9, 'red': 10, 'black': 11,
           'lacquer': 12, 'scales': 13, 'brass': 14, 'scroll': 15}
# These are observed design matches, not family-wide substitutions.
DESIGNS = {
    '6bow6': ('bow', 'stellar', 'scales', 'gold'),
    '6bow7': ('bow', 'stellar', 'scales', 'gold'),
    '7item042': ('bow', 'simple', 'wood', 'leather'),
    '7item043': ('bow', 'recurve', 'wood', 'gold'),
    '7item044': ('bow', 'elven_red', 'elm', 'redleather'),
    '7item045': ('bow', 'compound', 'wood', 'leather'),
    '7item046': ('bow', 'griffin', 'bone', 'bone'),
    '7item047': ('crossbow', 'crude', 'elm', 'brass'),
    '7item048': ('crossbow', 'heavy', 'wood', 'steel'),
    '7item049': ('crossbow', 'dragon', 'wood', 'steel'),
    '7item228': ('bow', 'barbed', 'wood', 'gold'),
    '7item229': ('crossbow', 'ania', 'wood', 'gold'),
    '7item300': ('bow', 'compound', 'wood', 'leather'),
    '7item301': ('bow', 'compound', 'wood', 'leather'),
    'bow1': ('bow', 'long', 'elm', 'wood'),
    'bow2': ('bow', 'elven', 'gold', 'gold'),
    'bow3': ('bow', 'jewelled', 'lacquer', 'gold'),
    'bow4': ('bow', 'stars', 'lacquer', 'green'),
    'bow5': ('bow', 'stellar', 'scales', 'gold'),
    'crsbow1': ('crossbow', 'plain', 'elm', 'steel'),
    'crsbow2': ('crossbow', 'slender', 'lacquer', 'gold'),
    'crsbow3': ('crossbow', 'lever', 'elm', 'gold'),
    'item056': ('bow', 'simple', 'wood', 'black'),
    'item057': ('bow', 'recurve', 'wood', 'redleather'),
    'item058': ('bow', 'snakewood', 'wood', 'gold'),
    'item059': ('bow', 'warbow', 'wood', 'leather'),
    'item060': ('bow', 'devilbone', 'bone', 'gold'),
    'item061': ('crossbow', 'light', 'elm', 'steel'),
    'item062': ('crossbow', 'blood', 'elm', 'silver'),
    'item063': ('crossbow', 'hunting', 'wood', 'silver'),
    'item064': ('crossbow', 'caravan', 'wood', 'steel'),
    'item065': ('crossbow', 'regnan', 'wood', 'gold'),
    'item245': ('bow', 'longseeker', 'lacquer', 'silver'),
    'item246': ('crossbow', 'lightning', 'brass', 'gold'),
    'item336': ('bow', 'warbow', 'wood', 'leather'),
    'item344': ('bow', 'devilbone', 'bone', 'gold'),
    '7item064': ('blaster', 'pistol', 'steel', 'redleather'),
    '7item065': ('blaster', 'carbine', 'steel', 'redleather'),
    'blastsg': ('blaster', 'shotgun', 'silver', 'gold'),
    'raygun1': ('blaster', 'ray_pistol', 'silver', 'gold'),
    'raygun2': ('blaster', 'ray_rifle', 'silver', 'gold'),
    '7item135': ('wand', 'orb', 'blue', 'silver'),
    '7item136': ('wand', 'crystal', 'green', 'gold'),
    '7item137': ('wand', 'alacorn', 'bone', 'gold'),
    '7item138': ('wand', 'skull', 'black', 'gold'),
    '7item139': ('wand', 'winged', 'bone', 'gold'),
    'item152': ('wand', 'antler', 'wood', 'bone'),
    'item153': ('wand', 'shaman', 'wood', 'bone'),
    'item154': ('wand', 'serpent', 'wood', 'scales'),
    'item155': ('wand', 'orrery', 'bone', 'gold'),
    'item156': ('wand', 'necrotic', 'gold', 'gold'),
    'wand1': ('wand', 'crystal', 'blue', 'gold'),
    'wand2': ('wand', 'tree', 'green', 'gold'),
    'wand3': ('wand', 'horn', 'black', 'bone'),
    'wand4': ('wand', 'crystal', 'red', 'gold'),
    'wand5': ('wand', 'dragon', 'bone', 'gold'),
}
assert set(DESIGNS) == {r['icon'] for r in OWNED}
PARTS = []
MATERIAL = None


def finish(obj, surface, uv_scale=1, smooth=False):
    obj.data.materials.clear()
    obj.data.materials.append(MATERIAL)
    if not obj.data.uv_layers:
        obj.data.uv_layers.new(name='UVMap')
    uv = obj.data.uv_layers.active.data
    tile = SURFACE[surface]
    su, sv = uv_scale if isinstance(uv_scale, tuple) else (uv_scale, uv_scale)
    for loop in uv:
        u, v = loop.uv
        loop.uv = ((tile % 4 + .025 + max(0, min(.95, u * su))) / 4,
                   (3 - tile // 4 + .025 + max(0, min(.95, v * sv))) / 4)
    for p in obj.data.polygons:
        p.use_smooth = smooth
    obj['surface'] = surface
    PARTS.append(obj)
    return obj


def mesh(name, verts, faces, coords, surface, smooth=False):
    data = bpy.data.meshes.new(name)
    data.from_pydata(verts, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    layer = data.uv_layers.new(name='UVMap')
    for p in data.polygons:
        for index in p.loop_indices:
            layer.data[index].uv = coords[data.loops[index].vertex_index]
        area = sum(coords[p.vertices[j]][0] * coords[p.vertices[(j + 1) % len(p.vertices)]][1]
                   - coords[p.vertices[(j + 1) % len(p.vertices)]][0] * coords[p.vertices[j]][1]
                   for j in range(len(p.vertices)))
        if abs(area) < 1e-10:
            axes = sorted(range(3), key=lambda k: abs(p.normal[k]))[:2]
            for index in p.loop_indices:
                co = data.vertices[data.loops[index].vertex_index].co
                layer.data[index].uv = (.3 + co[axes[0]], .3 + co[axes[1]])
    # Recalculate each component before it is combined with other physical parts.
    bm = bmesh.new()
    bm.from_mesh(data)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(data)
    bm.free()
    return finish(obj, surface, smooth=smooth)


def tube(name, points, radii, surface, sides=8, depth=1):
    pts = [Vector(p) for p in points]
    if isinstance(radii, (float, int)):
        radii = [radii] * len(pts)
    assert len(pts) == len(radii) and min(radii) > 0
    verts, faces, uv = [], [], []
    distance = 0
    for i, p in enumerate(pts):
        if i:
            distance += (p - pts[i - 1]).length
        t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        n = t.cross(Vector((0, 0, 1)))
        if n.length < .01:
            n = t.cross(Vector((0, 1, 0)))
        n.normalize()
        b = t.cross(n).normalized()
        for j in range(sides):
            a = 2 * math.pi * j / sides
            verts.append(tuple(p + radii[i] * (n * math.cos(a) + b * math.sin(a) * depth)))
            uv.append((j / sides * 2 * math.pi * max(radii), distance))
        if i:
            for j in range(sides):
                k = (j + 1) % sides
                faces.append(((i - 1) * sides + j, (i - 1) * sides + k, i * sides + k, i * sides + j))
    faces += [tuple(reversed(range(sides))), tuple((len(pts) - 1) * sides + j for j in range(sides))]
    return mesh(name, verts, faces, uv, surface, True)


def rod(name, a, b, radius, surface, sides=8):
    return tube(name, [a, b], radius, surface, sides)


def bore(name, x, back, front, z, outer, inner, surface, core='black'):
    """Closed annular barrel with a recessed interior, open at the muzzle."""
    verts, uv, faces = [], [], []
    for y, radius in [(back, outer), (front, outer), (front, inner), (back, inner)]:
        for i in range(12):
            a = i * math.tau / 12
            verts.append((x + math.cos(a) * radius, y, z + math.sin(a) * radius))
            uv.append((i / 12 * math.tau * outer, abs(y - back)))
    for level in range(4):
        other = (level + 1) % 4
        for i in range(12):
            j = (i + 1) % 12
            faces.append((level * 12 + i, level * 12 + j, other * 12 + j, other * 12 + i))
    mesh(name, verts, faces, uv, surface, True)
    recess = front - min(.04, (front - back) * .6)
    rod('Recessed bore interior', (x, recess, z), (x, recess + .002, z), inner * 1.01, core, 12)


def crescent_blade(y, z, surface):
    outline = [(.008, y + .01), (.065, y + .075), (.14, y + .06), (.18, y + .005),
               (.18, y - .05), (.15, y - .01), (.1, y + .006), (.045, y - .02)]
    verts = [(x, yy, z + dz) for dz in [-.009, .009] for x, yy in outline]
    faces = [tuple(range(7, -1, -1)), tuple(range(8, 16))]
    faces += [(i, (i + 1) % 8, (i + 1) % 8 + 8, i + 8) for i in range(8)]
    mesh('Crescent grip blade', verts, faces, [(.3 + x, .5 + yy) for x, yy, zz in verts], surface)


def curve(name, controls, radii, surface, depth=1, segments=3, sides=8):
    points, rr = [], []
    for i in range(len(controls) - 1):
        a = Vector(controls[max(0, i - 1)])
        b, c = Vector(controls[i]), Vector(controls[i + 1])
        d = Vector(controls[min(len(controls) - 1, i + 2)])
        for j in range(segments):
            t = j / segments
            p = .5 * ((2 * b) + (-a + c) * t + (2 * a - 5 * b + 4 * c - d) * t * t
                      + (-a + 3 * b - 3 * c + d) * t * t * t)
            points.append(tuple(p))
            rr.append(radii[i] * (1 - t) + radii[i + 1] * t)
    points.append(controls[-1])
    rr.append(radii[-1])
    return tube(name, points, rr, surface, sides, depth)


def box(name, pos, size, surface, bevel=.008):
    bpy.ops.mesh.primitive_cube_add(size=1, location=pos)
    obj = bpy.context.object
    obj.name = name
    obj.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        mod = obj.modifiers.new('Edge bevel', 'BEVEL')
        mod.width = min(bevel, min(size) * .2)
        mod.segments = 1
        bpy.ops.object.modifier_apply(modifier=mod.name)
    # Face UVs measured in object metres preserve the same swatch density as tubes.
    for p in obj.data.polygons:
        axes = sorted(range(3), key=lambda k: abs(p.normal[k]))[:2]
        for j in p.loop_indices:
            co = obj.data.vertices[obj.data.loops[j].vertex_index].co
            obj.data.uv_layers.active.data[j].uv = (.3 + co[axes[0]], .3 + co[axes[1]])
    return finish(obj, surface)


def ball(name, pos, scale, surface, segments=12, rings=6, smooth=True):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, radius=1, location=pos)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish(obj, surface, (min(.9, 2 * math.pi * max(scale[:2])), min(.9, math.pi * max(scale))), smooth)


def ring(name, pos, radius, tube_radius, surface, plane='XY', steps=12):
    verts, faces, uv = [], [], []
    for i in range(steps):
        a = 2 * math.pi * i / steps
        for j in range(6):
            b = math.tau * j / 6
            r = radius + tube_radius * math.cos(b)
            v = (r * math.cos(a), r * math.sin(a), tube_radius * math.sin(b))
            if plane == 'XZ':
                v = (v[0], v[2], v[1])
            if plane == 'YZ':
                v = (v[2], v[0], v[1])
            verts.append(tuple(Vector(pos) + Vector(v)))
            uv.append((j / 6 * math.tau * tube_radius, i / steps * math.tau * radius))
            faces.append((i * 6 + j, i * 6 + (j + 1) % 6,
                          ((i + 1) % steps) * 6 + (j + 1) % 6, ((i + 1) % steps) * 6 + j))
    return mesh(name, verts, faces, uv, surface, True)


def band(y, radius, surface, x=0, z=.05, width=.013):
    return tube('Ferrule', [(x, y - width / 2, z), (x, y + width / 2, z)], radius, surface, 10)


def gem(pos, radius, surface, length=None):
    return ball('Set gemstone', pos, (radius, length or radius, radius * .65), surface, 8, 4, False)


def horn(controls, radius, surface='bone'):
    return curve('Curved horn', controls, [radius * (1 - i / len(controls)) for i in range(len(controls))],
                 surface, segments=3, sides=7)


def wrap(points, radius, surface, turns, thickness=.0035):
    a, b = Vector(points[0]), Vector(points[-1])
    tangent = (b - a).normalized()
    normal = tangent.cross(Vector((0, 0, 1))).normalized()
    binormal = tangent.cross(normal).normalized()
    pts = []
    for i in range(turns * 7 + 1):
        t = i / (turns * 7)
        angle = t * turns * math.tau
        pts.append(tuple(a.lerp(b, t) + radius * (normal * math.cos(angle) + binormal * math.sin(angle))))
    tube('Spiral binding', pts, thickness, surface, 5)


def skull(pos, scale, surface='bone', beast=False):
    x, y, z = pos
    obj = ball('Carved cranium', pos, (scale * .65, scale * .75, scale * .5), surface, 16, 8)
    # Actual eye recesses, not black circles painted on a solid sphere.
    for sx in [-1, 1]:
        bpy.ops.mesh.primitive_uv_sphere_add(segments=10, ring_count=6, radius=1,
                                           location=(x + sx * scale * .29, y + scale * .13, z + scale * .43))
        cut = bpy.context.object
        cut.scale = (scale * .23, scale * .29, scale * .29)
        bpy.context.view_layer.objects.active = obj
        mod = obj.modifiers.new('Recessed orbit', 'BOOLEAN')
        mod.operation = 'DIFFERENCE'
        mod.object = cut
        bpy.ops.object.modifier_apply(modifier=mod.name)
        bpy.data.objects.remove(cut, do_unlink=True)
    tile = SURFACE[surface]
    for p in obj.data.polygons:
        axes = sorted(range(3), key=lambda k: abs(p.normal[k]))[:2]
        for index in p.loop_indices:
            co = obj.data.vertices[obj.data.loops[index].vertex_index].co
            obj.data.uv_layers.active.data[index].uv = (
                (tile % 4 + .3 + co[axes[0]]) / 4, (3 - tile // 4 + .3 + co[axes[1]]) / 4)
    for sx in [-1, 1]:
        ball('Orbit interior', (x + sx * scale * .29, y + scale * .13, z + scale * .22),
             (scale * .17, scale * .21, scale * .09), 'black', 10, 6)
    ball('Nasal cavity', (x, y - scale * .19, z + scale * .45),
         (scale * .09, scale * .13, scale * .05), 'black', 8, 4)
    box('Maxilla', (x, y - scale * .45, z + scale * .12), (scale * .65, scale * .32, scale * .44), surface,
        bevel=scale * .06)
    for i in range(5):
        box('Tooth', (x + (i - 2) * scale * .115, y - scale * .62, z + scale * .17),
            (scale * .095, scale * .15, scale * .22), 'bone', bevel=scale * .02)
    if beast:
        for s in [-1, 1]:
            horn([(x + s * scale * .48, y + scale * .25, z),
                  (x + s * scale * .72, y + scale * .7, z + scale * .1),
                  (x + s * scale * .45, y + scale * 1.2, z)], scale * .18, surface)


def bow(shape, wood, trim):
    z = .05
    if shape in ('compound', 'warbow'):
        controls = [(-.1, -.49, z), (.025, -.36, z), (.14, -.19, z), (.13, -.08, z),
                    (.07, -.04, z), (.07, .04, z), (.13, .08, z), (.14, .19, z),
                    (.025, .36, z), (-.1, .49, z)]
        radii = [.006, .014, .025, .022, .017, .017, .022, .025, .014, .006]
    elif shape in ('recurve', 'snakewood', 'elven'):
        controls = [(-.1, -.5, z), (-.11, -.46, z), (.03, -.33, z), (.12, -.15, z),
                    (.105, -.08, z), (.06, -.055, z), (.06, .055, z), (.105, .08, z),
                    (.12, .15, z), (.03, .33, z), (-.11, .46, z), (-.1, .5, z)]
        radii = [.004, .006, .017, .023, .022, .015, .015, .022, .023, .017, .006, .004]
    elif shape in ('barbed', 'devilbone'):
        controls = [(-.09, -.5, z), (-.015, -.43, z), (.07, -.27, z), (.11, -.1, z),
                    (.1, .1, z), (.07, .27, z), (-.015, .43, z), (-.09, .5, z)]
        radii = [.004, .013, .017, .018, .018, .017, .013, .004]
    else:
        controls = [(-.1, -.5, z), (-.085, -.46, z), (.045, -.34, z), (.125, -.17, z),
                    (.145, 0, z), (.125, .17, z), (.045, .34, z), (-.085, .46, z), (-.1, .5, z)]
        thick = .026 if shape in ('long', 'jewelled', 'stars', 'stellar') else .016
        radii = [.0035, .005, thick * .6, thick, thick * .78, thick, thick * .6, .005, .0035]
    curve('Solid bow stave', controls, radii, wood, depth=.65, segments=4)
    rod('Taut bowstring', controls[0], controls[-1], .0016, 'blue' if shape == 'devilbone' else 'leather', 5)
    cx = .07 if shape in ('compound', 'warbow') else .06 if shape in ('recurve', 'snakewood', 'elven') else .145
    if shape in ('barbed', 'devilbone'):
        cx = .1
    rod('Grip core', (cx, -.07, z), (cx, .07, z), .019, trim, 10)
    wrap([(cx, -.065, z), (cx, .065, z)], .02, trim, 10)
    for y in [-.072, .072]:
        band(y, .022, 'gold' if trim == 'gold' else 'steel', cx, z, .009)
    if shape == 'elven_red':
        for sign in [-1, 1]:
            tube('Burgundy limb cuff', [(.14, sign * .085, z), (.113, sign * .21, z)],
                 [.026, .018], 'redleather', 8, .7)
    if shape == 'long':
        ring('Thumb aperture', (cx - .027, 0, z), .027, .006, 'wood')
    if shape in ('compound', 'warbow'):
        for sign in [-1, 1]:
            if shape == 'compound':
                ball('Tip cam', (-.1, sign * .49, z), (.026, .026, .014), 'wood', 12, 4)
            rod('Steel recurved outer limb', (-.1, sign * .49, z), (.06, sign * .29, z), .009, 'silver')
            wrap([(.12, sign * .1, z), (.045, sign * .3, z)], .023, 'leather', 10)
        if shape == 'compound':
            rod('Offset cable', (-.1, -.49, z + .01), (-.1, .49, z + .01), .0015, 'black', 5)
    if shape == 'snakewood':
        for sign in [-1, 1]:
            wrap([(.11, sign * .2, z), (.035, sign * .34, z)], .02, 'gold', 9)
    if shape in ('jewelled', 'stellar'):
        for y in ([0] if shape == 'stellar' else [-.29, -.23, 0, .23, .29]):
            x = .145 - .3 * abs(y)
            ball('Gem bezel', (x, y, z + .012), (.017, .021, .008), 'gold', 10, 4)
            gem((x, y, z + .019), .012, 'blue' if y == 0 else 'green', .017)
    if shape == 'stellar':
        for sign in [-1, 1]:
            gem((-.1, sign * .49, z + .012), .023, 'red')
            for s in [-1, 1]:
                horn([(.145 + s * .017, sign * .012, z), (.145 + s * .075, sign * .047, z),
                      (.145 + s * .07, sign * .11, z)], .014, 'gold')
        # Gold rails and fittings follow the actual limb, not the source icon's lighting.
        for sign in [-1, 1]:
            curve('Gilt limb edge', [(c[0] + .013, c[1], z + .012) for c in controls[1:-1]],
                  [.0025] * (len(controls) - 2), 'gold', segments=2, sides=5)
    if shape == 'stars':
        for y in [-.34, -.24, -.14, .14, .24, .34]:
            x = .145 - .3 * abs(y)
            verts = [(x, y, z + .012)]
            for j in range(10):
                a = j * math.pi / 5
                r = .012 if j % 2 == 0 else .005
                verts.append((x + r * math.sin(a), y + r * math.cos(a), z + .008))
            # A shallow solid emblem with a closed underside.
            verts += [(v[0], v[1], v[2] - .003) for v in verts[1:]]
            faces = [(0, 1 + j, 1 + (j + 1) % 10) for j in range(10)]
            faces += [(1 + j, 11 + j, 11 + (j + 1) % 10, 1 + (j + 1) % 10) for j in range(10)]
            faces += [tuple(range(20, 10, -1))]
            mesh('Ivory star inlay', verts, faces, [(0, 0)] * len(verts), 'bone')
    if shape in ('barbed', 'devilbone'):
        for sign in [-1, 1]:
            for yy, xx in [(.17, .105), (.27, .07), (.36, .02), (.43, -.015)]:
                y = sign * yy
                horn([(xx + .01, y, z), (xx + .065, y + sign * .012, z),
                      (xx + .08, y + sign * .04, z)], .012, 'bone')
                band(y, .019, 'gold', xx, z, .01)
        if shape == 'devilbone':
            rod('Wooden riser', (cx, -.15, z), (cx, .1, z), .02, 'wood', 10)
            band(-.065, .027, 'black', cx, z, .025)
            for s in [-1, 1]:
                ball('Bone bow tip pulley', (-.09, s * .49, z), (.025, .025, .014), 'wood', 12, 4)
            skull((cx, .1, z + .012), .056, 'bone', True)
    if shape == 'griffin':
        # An open long-snouted trophy with an actual lower jaw and separate teeth.
        skull((.17, .015, z + .012), .063, 'bone', True)
        horn([(.18, -.005, z), (.24, -.09, z), (.29, -.13, z)], .022, 'bone')
        curve('Lower jaw', [(.15, -.04, z), (.17, -.11, z), (.27, -.16, z), (.29, -.13, z)],
              [.018, .014, .012, .007], 'bone', sides=7)
        for i in range(5):
            x = .18 + i * .018
            y = -.11 - (x - .17) * .5
            horn([(x, y, z), (x + .003, y + .04, z)], .006)
    if shape == 'longseeker':
        for sign in [-1, 1]:
            band(sign * .09, .032, 'silver', .14, z, .05)
            ring('Steel nock scroll', (-.1, sign * .48, z), .027, .005, 'silver')
            horn([(.14, sign * .06, z), (.21, sign * .09, z), (.23, sign * .13, z)], .013, 'gold')


def crossbow(shape, wood, metal):
    curved = shape in ('slender', 'hunting', 'caravan', 'dragon')
    z = .065
    controls = [(0, -.49, z), (.016, -.32, z), (-.025 if curved else 0, -.1, z),
                (.032 if curved else 0, .13, z), (0, .32, z)]
    widths = [.037, .035, .028, .034, .028]
    if shape == 'dragon':
        widths = [.045, .055, .035, .062, .03]
    curve('Carved stock', controls, widths, wood, depth=.9, sides=8, segments=4)
    # Flat top deck, bolt groove and lock are distinct assembled components.
    box('Bolt rail', (0, .12, .096), (.034, .47, .018), metal, .004)
    box('Bolt groove', (0, .14, .107), (.008, .42, .004), 'black', .001)
    yroot = .28
    half = .32 if shape not in ('heavy', 'dragon') else .37
    sweep = .17 if shape not in ('crude', 'heavy', 'plain') else .09
    if shape in ('slender', 'blood', 'hunting', 'regnan', 'lever'):
        sweep = .26
    for s in [-1, 1]:
        arms = [(0, yroot, .105), (s * half * .35, yroot - .015, .11),
                (s * half * .8, yroot - sweep * .5, .105), (s * half, yroot - sweep, .09)]
        curve('Transverse prod', arms, [.022, .021, .016, .006], metal,
              depth=.65, segments=4)
        rod('Drawn string', (s * half, yroot - sweep, .09), (0, -.02, .11), .002, 'leather', 5)
    box('Lock housing', (0, -.03, .115), (.069, .065, .023), metal, .006)
    ring('Trigger guard', (0, -.07, .018), .035, .006, metal, 'YZ')
    rod('Trigger', (0, -.045, .065), (0, -.074, .025), .006, metal, 6)
    if shape in ('lever', 'caravan', 'lightning', 'blood'):
        rod('Spanning lever pivot', (.017, -.11, .055), (.074, -.08, .055), .014, metal)
        rod('Spanning lever', (.074, -.08, .055), (.17, .025, .058), .012, metal)
        ball('Lever knob', (.17, .025, .058), (.02, .02, .02), 'red' if shape == 'lever' else metal)
    if shape in ('regnan', 'ania', 'lever', 'lightning'):
        rod('Front sight tower', (0, .26, .10), (0, .43, .10), .009, metal)
        if shape == 'ania':
            horn([(0, .31, .1), (.012, .43, .1), (0, .49, .1)], .012, 'steel')
    if shape in ('light', 'blood', 'hunting', 'regnan', 'plain', 'caravan'):
        ring('Front stirrup', (0, .34, .07), .038, .007, metal)
    if shape == 'heavy':
        box('Heavy receiver', (0, .2, .088), (.09, .23, .045), 'steel')
        for s in [-1, 1]:
            box('Prod reinforcing plate', (s * .12, .25, .115), (.065, .08, .014), 'redleather')
    if shape in ('lightning', 'regnan', 'lever'):
        box('Decorated lock plate', (0, -.19, .103), (.045, .25, .009), 'brass' if shape != 'regnan' else 'gold', .002)
        for y in [-.29, -.2, -.11]:
            gem((0, y, .112), .013, 'blue' if shape != 'regnan' else 'bone')
    if shape == 'ania':
        box('Carved gilt foregrip', (0, -.22, .103), (.047, .26, .012), 'brass', .003)
        horn([(-.025, -.27, z), (-.07, -.29, z), (-.08, -.24, z)], .015, 'gold')
    if shape in ('crude', 'dragon'):
        for y in [-.35, -.26, -.17]:
            band(y, .04 if shape == 'crude' else .05, 'redleather', z=z, width=.038)
        if shape == 'crude':
            box('Carved broad fore-end', (0, .08, .07), (.086, .21, .065), 'brass')
        else:
            skull((0, .26, .13), .065, 'brass', True)
            for s in [-1, 1]:
                for i in range(4):
                    horn([(s * (.09 + .06 * i), .27 - .015 * i, .11),
                          (s * (.13 + .06 * i), .34 - .03 * i, .1)], .018, 'steel')
    for y in [-.42, -.12]:
        band(y, .038, metal, z=z, width=.012)


def blaster(shape, body, trim):
    z = .09
    if shape == 'pistol':
        box('Receiver', (0, .02, z), (.105, .54, .095), body)
        bore('Open barrel', 0, .23, .485, z, .037, .024, 'steel')
        band(.45, .045, 'black', z=z, width=.025)
        box('Upper housing', (-.025, .06, z + .05), (.085, .35, .025), trim)
        curve('Pistol grip', [(0, -.14, z), (.09, -.22, z), (.16, -.38, z)],
              [.05, .047, .04], trim, depth=.85, segments=2)
        for i in range(4):
            box('Grip rib', (.07 + i * .022, -.22 - i * .043, z + .035), (.069, .015, .012), 'steel', .003)
        ring('Trigger guard', (.09, -.15, z), .055, .009, 'steel')
        rod('Trigger', (.045, -.13, z), (.08, -.17, z), .009, 'black')
        return
    if shape == 'carbine':
        bore('Rifle barrel', 0, -.2, .505, z, .031, .022, 'steel')
        box('Rifle housing', (0, .22, z), (.095, .48, .092), trim)
        box('Fore-end rail', (-.044, -.03, z), (.026, .4, .04), 'steel')
        box('Receiver lower', (0, -.26, z), (.09, .27, .08), body)
        curve('Rear grip', [(0, -.36, z), (.04, -.42, z), (.16, -.43, z)], [.043, .043, .033], trim)
        curve('Raised carrying handle', [(.015, .37, z), (.14, .28, z), (.14, .09, z), (.02, .015, z)],
              [.009] * 4, trim, segments=4)
        band(.48, .045, 'black', z=z, width=.035)
        for y in [-.34, -.27, -.20]:
            box('Receiver panel', (0, y, z + .04), (.045, .045, .006), 'bone', .002)
        return
    # The MM6 rayguns are ornate brass/silver mechanisms, not modern gun silhouettes.
    pistol = shape == 'ray_pistol'
    rod('Energy barrel', (0, -.36, z), (0, .5, z), .016 if not pistol else .021, 'silver', 10)
    box('Receiver spine', (0, -.15, z), (.052, .34, .065), 'silver')
    box('Filigree receiver', (.035, -.11, z + .012), (.03, .3, .035), 'brass')
    for y in [-.32, -.2, -.05, .17, .38]:
        band(y, .026, 'gold', z=z, width=.021)
    if shape == 'shotgun':
        for i in range(5):
            x = (i - 2) * .044
            rod('Fan barrel', (x * .35, .21, z), (x, .48 - abs(i - 2) * .012, z), .019, 'silver', 10)
            bore('Fan muzzle', x, .48 - abs(i - 2) * .012, .515 - abs(i - 2) * .012,
                 z, .0205, .014, 'gold', 'blue')
        for y in [.2, .25, .3]:
            band(y, .046 + (y - .2) * .5, 'gold', z=z, width=.015)
        rod('Ribbed barrel grip', (0, .03, z), (0, .2, z), .029, 'black')
        for y in [.05, .085, .12, .155, .19]:
            band(y, .032, 'gold', z=z, width=.009)
    if shape in ('ray_rifle', 'shotgun'):
        rod('Rear receiver stem', (0, -.445, z), (0, -.30, z), .017, 'silver')
        # Two recurved grip blades with full elliptical cross-sections.
        for yy in [-.15, -.42]:
            crescent_blade(yy, z, 'silver')
        rod('Auxiliary barrel', (-.055, -.32, z), (-.055, .04, z), .012, 'silver')
        for y in [-.28, -.02]:
            rod('Auxiliary barrel brace', (-.02, y, z), (-.055, y, z), .007, 'silver', 6)
        rod('Green energy cell', (.034, -.2, z), (.034, -.05, z), .017, 'green')
        for yy in [-.19, -.13, -.07]:
            band(yy, .019, 'gold', x=.034, z=z, width=.01)
    else:
        curve('Curled pistol butt', [(0, -.28, z), (.065, -.34, z), (.14, -.3, z), (.14, -.26, z)],
              [.035, .036, .031, .016], 'bone', segments=3)
        ring('Circular trigger guard', (.045, -.08, z), .053, .006, 'gold')
        rod('Side energy chamber', (-.06, -.3, z), (-.06, .02, z), .021, 'silver')
        for y in [-.25, -.04]:
            rod('Chamber brace', (-.02, y, z), (-.06, y, z), .007, 'silver', 6)
        for y in [-.26, -.15, -.04]:
            band(y, .022, 'gold', x=-.06, z=z, width=.014)
        for y in [.13, .18, .23]:
            band(y, .034, 'red', z=z, width=.012)
        gem((0, .51, z), .016, 'red')
    if shape != 'shotgun':
        bore('Muzzle sleeve', 0, .495, .52, z, .023, .015, 'gold')


def wand(shape, shaft, trim):
    z = .065
    if shape == 'alacorn':
        horn([(0, .27, z), (0, .08, z), (0, -.2, z), (0, -.48, z)], .03, 'bone')
        points, radii = [], []
        for i in range(91):
            t = i / 90
            radius = .031 * (1 - t) + .001
            points.append((radius * math.cos(t * math.tau * 7), .25 - t * .73,
                           z + radius * math.sin(t * math.tau * 7)))
            radii.append(.008 * (1 - t) + .001)
        tube('Downward alacorn spiral', points, radii, 'bone', 6)
        rod('Upper sun handle', (0, .26, z), (0, .39, z), .024, 'gold', 10)
        for y in [.27, .30, .33, .36]:
            band(y, .029, 'gold', z=z)
        ball('Sun globe', (0, .43, z), (.045, .05, .045), 'gold', 12, 8)
        for i in range(8):
            a = i * math.tau / 8
            horn([(.035 * math.cos(a), .43 + .035 * math.sin(a), z),
                  (.085 * math.cos(a), .43 + .085 * math.sin(a), z)], .007, 'gold')
        return
    top = .33
    if shape in ('horn', 'necrotic'):
        top = -.23 if shape == 'horn' else -.39
    if shape in ('shaman', 'antler', 'serpent'):
        pts = [(-.018, -.47, z), (.012, -.27, z), (-.016, -.06, z), (.018, .19, z), (0, .33, z)]
        curve('Gnarled core', pts, [.013, .021, .019, .021, .018], shaft, segments=5)
    else:
        rod('Solid wand shaft', (0, -.48, z), (0, top, z), .016, shaft, 12)
    for y in [-.46, -.39, -.33, top - .025]:
        band(y, .022, 'gold' if trim in ('gold', 'bone', 'scales') else trim, z=z, width=.012)
    if shape in ('orb', 'crystal'):
        for y in [-.22, .19, .26]:
            band(y, .022, trim, z=z, width=.012)
        if shape == 'orb':
            ball('Blue crystal orb', (0, .38, z), (.034, .045, .034), 'blue', 12, 8)
            band(.33, .027, 'silver', z=z, width=.024)
            wrap([(0, -.3, z), (0, .28, z)], .0165, 'silver', 5, .002)
        else:
            color = shaft
            verts = []
            for yy, radius in [(.3, .017), (.375, .052), (.46, .001)]:
                for i in range(6):
                    a = i * math.tau / 6
                    verts.append((radius * math.cos(a), yy, z + radius * math.sin(a)))
            faces = []
            for j in range(2):
                for i in range(6):
                    faces.append((j * 6 + i, j * 6 + (i + 1) % 6, (j + 1) * 6 + (i + 1) % 6,
                                  (j + 1) * 6 + i))
            faces += [tuple(range(5, -1, -1)), tuple(range(12, 18))]
            mesh('Faceted crystal head', verts, faces, [(i % 6 / 6 * .3, i // 6 * .12) for i in range(18)], color)
            band(.3, .027, 'gold', z=z)
            for s in [-1, 1]:
                horn([(s * .015, .28, z), (s * .04, .32, z), (s * .037, .35, z)], .005, 'gold')
            if shaft == 'red':
                for y in [-.24, -.12, .04]:
                    ball('Ivory grip node', (0, y, z), (.022, .023, .022), 'bone', 10, 6)
    if shape in ('horn', 'necrotic'):
        start = -.23 if shape == 'horn' else -.42
        finish_y = .45
        if shape == 'necrotic':
            rod('Gold braid core', (0, start, z), (0, finish_y, z), .024, 'gold', 10)
        else:
            horn([(0, start, z), (0, .02, z), (0, .25, z), (0, finish_y, z)], .034, 'bone')
        # A closed spiral tapered horn with a real carved ridge around its core.
        pts = []
        for i in range(91):
            t = i / 90
            rr = .026 if shape == 'necrotic' else .036 * (1 - t) + .001
            pts.append((rr * math.cos(t * math.tau * 7), start + t * (finish_y - start),
                        z + rr * math.sin(t * math.tau * 7)))
        tube('Twisted horn ridge', pts, [.011 if shape == 'necrotic' else .009 * (1 - i / 100) for i in range(91)],
             'gold' if shape == 'necrotic' else 'bone', 5)
        if shape == 'horn':
            wrap([(0, -.43, z), (0, -.26, z)], .017, 'blue', 6, .0025)
        if shape == 'necrotic':
            for y in [-.44, .36]:
                band(y, .028, 'red', z=z, width=.025)
            skull((0, .44, z), .067, 'gold')
            for s in [-1, 1]:
                horn([(s * .025, .45, z), (s * .065, .49, z), (s * .08, .46, z)], .012, 'red')
            crescent_blade(.27, z, 'gold')
            horn([(.015, .37, z), (.10, .32, z), (.17, .29, z)], .011, 'gold')
    if shape == 'skull':
        skull((0, .36, z), .075, 'gold')
        rod('Horn mounting crossbar', (-.035, .29, z), (.035, .29, z), .011, 'gold', 8)
        for s in [-1, 1]:
            curve('Crescent skull horns', [(s * .025, .29, z), (s * .092, .3, z),
                                          (s * .11, .4, z), (s * .075, .46, z)],
                  [.016, .014, .01, .003], 'gold', segments=4)
        gem((0, .245, z + .026), .025, 'red')
        band(.235, .032, 'gold', z=z, width=.018)
        wrap([(0, -.4, z), (0, .23, z)], .018, 'gold', 2, .003)
    if shape == 'winged':
        rod('Crown support', (0, .31, z), (0, .36, z), .023, 'gold')
        wrap([(0, -.29, z), (0, .17, z)], .0165, 'gold', 3, .002)
        for y in [-.38, -.3, .17, .23]:
            band(y, .027, 'gold', z=z, width=.018)
        gem((0, .4, z), .044, 'gold', .062)
        ring('Oval crown rim', (0, .4, z), .06, .006, 'gold')
        for s in [-1, 1]:
            for i in range(8):
                a = .25 + i * .12
                base = (s * .018, .24 + i * .01, z)
                end = (s * (.1 + i * .008), .3 + i * .023, z + .003)
                curve('Feather vane', [base, (s * .08, .28 + i * .017, z + .006), end],
                      [.011, .009, .0025], 'bone', depth=.45, segments=2, sides=6)
                rod('Feather quill', base, end, .0023, 'gold', 5)
        for i in range(5):
            a = i * math.pi / 4
            horn([(.04 * math.cos(a), .4 + .05 * math.sin(a), z),
                  (.075 * math.cos(a), .4 + .09 * math.sin(a), z)], .006, 'red')
    if shape in ('antler', 'shaman'):
        wrap([(0, -.4, z), (0, .27, z)], .023, 'leather', 16, .005)
        if shape == 'shaman':
            band(.327, .025, 'bone', z=z, width=.027)
            skull((0, .38, z), .065)
            for yy in [-.12, .05, .22]:
                for s in [-1, 1]:
                    horn([(0, yy, z), (s * .07, yy + .035, z)], .012)
            rod('Tassel tie', (.027, .25, z), (.07, -.05, z), .004, 'gold', 5)
        else:
            for s in [-1, 1]:
                horn([(0, .22, z), (s * .07, .31, z), (s * .075, .46, z)], .022)
                horn([(s * .05, .3, z), (s * .13, .35, z)], .014)
                horn([(0, -.35, z), (s * .07, -.41, z), (s * .08, -.35, z)], .018)
            horn([(0, .29, z), (.015, .48, z)], .02)
            ring('Hanging charm', (.09, .12, z), .027, .006, 'gold')
            rod('Charm tether', (.075, .33, z), (.09, .145, z), .003, 'leather', 5)
    if shape == 'serpent':
        pts = []
        for i in range(80):
            t = i / 79
            pts.append((.03 * math.sin(t * math.tau * 4), -.43 + t * .79,
                        z + .03 * math.cos(t * math.tau * 4)))
        tube('Coiled serpent body', pts, [.018] * 74 + [.02, .022, .024, .025, .026, .027], 'scales', 8)
        ball('Serpent head', (0, .37, z + .025), (.035, .055, .026), 'scales', 12, 8)
        for s in [-1, 1]:
            gem((s * .023, .385, z + .045), .008, 'red')
        horn([(0, .4, z + .02), (.01, .47, z + .02)], .006, 'red')
        curve('Second serpent neck', [(.025, .22, z), (-.035, .29, z), (-.035, .37, z)],
              [.016, .017, .018], 'scales', segments=4)
        ball('Second serpent head', (-.035, .38, z + .006), (.022, .034, .02), 'scales', 10, 6)
        gem((-.043, .39, z + .025), .006, 'red')
        for y in [-.3, -.12, .08, .25]:
            gem((0, y, z + .015), .014, 'red', .022)
    if shape == 'orrery':
        rod('Armillary spindle', (0, .31, z), (0, .385, z), .005, 'gold', 6)
        wrap([(0, -.4, z), (0, .28, z)], .017, 'gold', 5, .002)
        for plane in ['XY', 'XZ', 'YZ']:
            ring('Armillary orbit', (0, .385, z), .055, .005, 'gold', plane)
        ball('Armillary core', (0, .385, z), (.023, .023, .023), 'gold')
        ring('Lower orbital collar', (0, .28, z), .039, .004, 'gold')
    if shape == 'tree':
        wrap([(0, -.41, z), (0, .24, z)], .018, 'gold', 3, .002)
        for s in [-1, 1]:
            for i in range(4):
                y = .26 + i * .055
                end = (s * (.07 + .02 * (3 - i)), y + .04, z)
                curve('Living branch', [(0, y - .05, z), (end[0] * .5, y, z), end],
                      [.007, .005, .002], 'wood', segments=3, sides=6)
                for off in [0, .018]:
                    ball('Leaf', (end[0] - s * off, end[1] + off, z + .005), (.016, .027, .005),
                         'green', 8, 4)
        rod('Living crown', (0, .28, z), (0, .48, z), .006, 'wood', 6)
    if shape == 'dragon':
        rod('Golden dragon neck', (0, .18, z), (0, .4, z), .032, 'brass')
        ball('Dragon brow', (.005, .405, z), (.035, .049, .03), 'gold', 12, 6)
        curve('Dragon upper jaw', [(.007, .42, z + .01), (.045, .46, z + .012), (.075, .49, z + .008)],
              [.026, .021, .007], 'gold', segments=3)
        curve('Dragon lower jaw', [(.005, .41, z - .012), (.035, .443, z - .017), (.072, .478, z - .01)],
              [.015, .011, .005], 'gold', segments=3)
        gem((.006, .426, z + .029), .008, 'red')
        for x in [-.025, .02]:
            horn([(x, .435, z), (x - .012, .49, z), (x + .003, .53, z)], .009, 'gold')
        for s in [-1, 1]:
            horn([(s * .018, .25, z), (s * .085, .29, z), (s * .13, .38, z),
                  (s * .09, .46, z)], .025, 'gold')
        for y in [-.32, -.22, -.12]:
            ball('Blue grip stone', (0, y, z), (.026, .031, .024), 'blue', 10, 6)
        wrap([(0, -.39, z), (0, .18, z)], .018, 'gold', 4, .003)


def material():
    m = bpy.data.materials.new('Painted surfaces with semantic PBR')
    m.use_nodes = True
    m.use_backface_culling = True
    nodes = m.node_tree.nodes
    links = m.node_tree.links
    bsdf = nodes.get('Principled BSDF')
    bsdf.inputs['Metallic'].default_value = 1
    for name in ['base', 'mr', 'normal']:
        node = nodes.new('ShaderNodeTexImage')
        node.image = bpy.data.images.load(str(HERE / 'textures' / f'weapon_{name}.png'))
        if name == 'base':
            links.new(node.outputs['Color'], bsdf.inputs['Base Color'])
        elif name == 'mr':
            node.image.colorspace_settings.name = 'Non-Color'
            sep = nodes.new('ShaderNodeSeparateColor')
            links.new(node.outputs['Color'], sep.inputs[0])
            links.new(sep.outputs['Green'], bsdf.inputs['Roughness'])
            links.new(sep.outputs['Blue'], bsdf.inputs['Metallic'])
        else:
            node.image.colorspace_settings.name = 'Non-Color'
            n = nodes.new('ShaderNodeNormalMap')
            links.new(node.outputs['Color'], n.inputs['Color'])
            links.new(n.outputs[0], bsdf.inputs['Normal'])
    return m


def normalize():
    allverts = [o.matrix_world @ v.co for o in PARTS for v in o.data.vertices]
    lo = Vector(tuple(min(p[k] for p in allverts) for k in range(3)))
    hi = Vector(tuple(max(p[k] for p in allverts) for k in range(3)))
    centre = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
    scale = 1 / max(hi.x - lo.x, hi.y - lo.y)
    for obj in PARTS:
        mat = obj.matrix_world.copy()
        for v in obj.data.vertices:
            v.co = (mat @ v.co - centre) * scale
        obj.matrix_world.identity()
    return [round((hi[k] - lo[k]) * scale, 6) for k in range(3)]


def settle():
    """Choose the nearest stable supporting hull face using the solid components' centre of mass."""
    points = []
    weighted, total = Vector((0, 0, 0)), 0
    for obj in PARTS:
        obj.data.calc_loop_triangles()
        for tri in obj.data.loop_triangles:
            a, b, c = [obj.matrix_world @ obj.data.vertices[i].co for i in tri.vertices]
            volume = a.dot(b.cross(c)) / 6
            weighted += (a + b + c) / 4 * volume
            total += volume
        points.extend(obj.matrix_world @ v.co for v in obj.data.vertices)
    centre = weighted / total
    bm = bmesh.new()
    verts = [bm.verts.new(v) for v in points]
    bmesh.ops.convex_hull(bm, input=verts, use_existing_faces=False)
    bm.normal_update()
    down = Vector((0, 0, -1))
    candidates = []
    for face in bm.faces:
        if face.normal.z >= -.65:
            continue
        a, b, c = [v.co for v in face.verts[:3]]
        projected = centre - face.normal * (centre - a).dot(face.normal)
        if (closest_point_on_tri(projected, a, b, c) - projected).length < 1e-5:
            candidates.append(face.normal.copy())
    assert candidates, 'No stable supporting face below mass centre'
    normal = min(candidates, key=lambda n: n.angle(down))
    rotation = normal.rotation_difference(down).to_matrix().to_4x4()
    for obj in PARTS:
        obj.matrix_world = rotation @ obj.matrix_world
    angle = math.degrees(normal.angle(down))
    bm.free()
    return round(angle, 3)


def check_geometry():
    triangles = 0
    for o in PARTS:
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bmesh.ops.triangulate(bm, faces=list(bm.faces), quad_method='BEAUTY', ngon_method='BEAUTY')
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        assert all(e.is_manifold for e in bm.edges), f'{o.name}: open component'
        assert bm.calc_volume(signed=True) > 1e-12, f'{o.name}: flat/inverted component'
        assert all(f.calc_area() > 1e-12 for f in bm.faces), f'{o.name}: degenerate triangle'
        triangles += len(bm.faces)
        bm.to_mesh(o.data)
        bm.free()
        assert all(0 <= x <= 1 for loop in o.data.uv_layers.active.data for x in loop.uv)
    assert triangles < 15000
    verts = [v.co for o in PARTS for v in o.data.vertices]
    assert abs(min(v.z for v in verts)) < 1e-6
    assert abs(max(v.y for v in verts) + min(v.y for v in verts)) < 1e-5
    return triangles


def assembly_groups():
    """Closed parts must intersect, contain or touch a supporting component, within 0.8 mm/model unit."""
    solids = []
    for obj in PARTS:
        verts = [obj.matrix_world @ v.co for v in obj.data.vertices]
        obj.data.calc_loop_triangles()
        triangles = [tuple(t.vertices) for t in obj.data.loop_triangles]
        low = Vector(tuple(min(v[k] for v in verts) for k in range(3)))
        high = Vector(tuple(max(v[k] for v in verts) for k in range(3)))
        solids.append((verts, BVHTree.FromPolygons(verts, triangles, all_triangles=True, epsilon=.0008), low, high))
    parent = list(range(len(solids)))

    def root(i):
        while parent[i] != i:
            i = parent[i]
        return i

    def contained(point, tree):
        nearest, normal, index, distance = tree.find_nearest(point)
        return nearest is not None and (distance < .0008 or (point - nearest).dot(normal) < -1e-7)

    for i, (av, at, al, ah) in enumerate(solids):
        for j in range(i):
            bv, bt, bl, bh = solids[j]
            if any(al[k] > bh[k] + .0008 or bl[k] > ah[k] + .0008 for k in range(3)):
                continue
            if at.overlap(bt) or contained(av[0], bt) or contained(bv[0], at):
                parent[root(i)] = root(j)
    groups = {}
    for i, obj in enumerate(PARTS):
        groups.setdefault(root(i), []).append(obj.name)
    return sorted(groups.values(), key=len, reverse=True)


def render(icon, clay=False, resolution=384, views=None):
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 12
    scene.cycles.use_denoising = True
    scene.render.resolution_x = resolution
    scene.render.resolution_y = resolution
    scene.render.resolution_percentage = 100
    scene.world.color = (.25, .25, .25)
    scene.render.image_settings.file_format = 'PNG'
    scene.view_settings.view_transform = 'Standard'
    scene.view_settings.look = 'Medium High Contrast'
    scene.render.film_transparent = False
    extras = []
    for pos, energy, size in [((1, -1, 3), 180, 3), ((-2, 1, 2), 110, 3)]:
        bpy.ops.object.light_add(type='AREA', location=pos)
        light = bpy.context.object
        light.data.energy = energy
        light.data.shape = 'DISK'
        light.data.size = size
        extras.append(light)
    neutral = bpy.data.materials.get('Neutral clay') or bpy.data.materials.new('Neutral clay')
    neutral.use_nodes = True
    neutral.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value = (.22, .22, .22, 1)
    neutral.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value = .8
    if clay:
        scene.view_layers[0].material_override = neutral
    bpy.ops.object.camera_add()
    cam = bpy.context.object
    extras.append(cam)
    cam.data.type = 'ORTHO'
    cam.data.ortho_scale = 1.2
    scene.camera = cam
    folder = HERE / 'review' / ('clay' if clay else 'textured')
    folder.mkdir(parents=True, exist_ok=True)
    for name, pos in [('top', (0, 0, 3)), ('threequarter', (1.15, -1.4, 1.5)),
                      ('low', (1.9, -.8, .35)), ('underside', (0, 0, -3))]:
        if views and name not in views:
            continue
        cam.location = pos
        target = Vector((0, 0, .035))
        cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
        scene.render.filepath = str(folder / f'{icon}_{name}.png')
        bpy.ops.render.render(write_still=True)
    scene.view_layers[0].material_override = None
    for o in extras:
        bpy.data.objects.remove(o, do_unlink=True)


def main():
    global MATERIAL
    parser = argparse.ArgumentParser()
    parser.add_argument('--pilots', action='store_true')
    parser.add_argument('--icons', nargs='+')
    parser.add_argument('--render', action='store_true')
    parser.add_argument('--audit-assembly', action='store_true')
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
    exports = HERE / 'work' / 'exports'
    exports.mkdir(parents=True, exist_ok=True)
    design_json = json.loads((HERE / 'designs.json').read_text())
    ledger = json.loads((HERE / 'ledger.json').read_text())
    selected = args.icons or (list(DESIGNS) if args.audit_assembly else
                             PILOTS if args.pilots else [k for k in DESIGNS if ledger[k]['status'] == 'pending'])
    audit = {}
    for icon in selected:
        assert icon in DESIGNS
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=False)
        PARTS.clear()
        bpy.data.orphans_purge(do_recursive=True)
        MATERIAL = material()
        kind, shape, surface, trim = DESIGNS[icon]
        {'bow': bow, 'crossbow': crossbow, 'blaster': blaster, 'wand': wand}[kind](shape, surface, trim)
        support_angle = settle()
        dimensions = normalize()
        tris = check_geometry()
        groups = assembly_groups()
        if args.audit_assembly:
            audit[icon] = groups
            print('ASSEMBLY', icon, len(groups), groups[1:], flush=True)
            continue
        assert len(groups) == 1, (icon, 'unsupported components', groups[1:])
        if args.render:
            render(icon, clay=True)
            render(icon)
        bpy.ops.object.select_all(action='DESELECT')
        for o in PARTS:
            o.select_set(True)
        bpy.context.view_layer.objects.active = PARTS[0]
        bpy.ops.object.join()
        obj = bpy.context.object
        obj.name = f'item_{icon}'
        out = exports / f'item_{icon}.glb'
        lod_counts = [tris]
        if tris > 2800:
            lod = obj.copy()
            lod.data = obj.data.copy()
            bpy.context.collection.objects.link(lod)
            lod.name = obj.name + '_LOD1'
            bpy.context.view_layer.objects.active = lod
            mod = lod.modifiers.new('Half-count distance mesh', 'DECIMATE')
            mod.ratio = .5
            bpy.ops.object.modifier_apply(modifier=mod.name)
            lod.data.calc_loop_triangles()
            lod_counts.append(len(lod.data.loop_triangles))
            assert .4 < lod_counts[1] / tris < .6
            lod.select_set(True)
        bpy.ops.export_scene.gltf(filepath=str(out), export_format='GLB', use_selection=True,
                                  export_yup=True, export_materials='EXPORT', export_animations=False,
                                  export_texcoords=True, export_normals=True, export_tangents=False)
        if len(lod_counts) > 1:
            subprocess.run(['python3', str(HERE.parents[2] / 'tools/link_static_model_lods.py'),
                            str(out), str(out)], check=True)
        design_json[icon] = {'title': ledger[icon]['name'], 'icons': [icon], 'master_icon': icon,
                             'route': 'Blender components / generated material UV atlas',
                             'construction': kind, 'design': shape, 'surface': surface, 'trim': trim,
                             'dimensions': dimensions, 'triangles': tris, 'length': ledger[icon]['binding']['length']}
        design_json[icon]['support_rotation_degrees'] = support_angle
        design_json[icon]['lod_triangles'] = lod_counts
        ledger[icon].update({'status': 'ready', 'design': shape, 'construction': kind,
                             'source_export': str(out.relative_to(HERE)), 'triangles': tris,
                             'dimensions': dimensions, 'textures': {'base': [2048, 2048], 'mr': [2048, 2048],
                                                                  'normal': [2048, 2048]},
                             'lod_triangles': lod_counts,
                             'checks': ['closed positive-volume components', 'nondegenerate triangles',
                                        'ground zero', 'centred footprint', 'UV bounds'],
                             'defects': ['Awaiting visual acceptance and native verification']})
        (HERE / 'designs.json').write_text(json.dumps(design_json, indent=2) + '\n')
        (HERE / 'ledger.json').write_text(json.dumps(ledger, indent=2) + '\n')
        print(f'READY {icon} {shape}: {tris} triangles, {dimensions}', flush=True)
    if args.audit_assembly:
        (HERE / 'receipts/assembly.json').write_text(json.dumps(audit, indent=2) + '\n')


if __name__ == '__main__':
    main()
