"""MM7 `7dec32` (208 placements in 18 dungeons): an upright wooden barrel with four iron hoops (brass rivets on the
top and bottom hoops), a fishing net draped over its front right from the top hoop down to a gathered tail at the
base, a rope wound round its left side and two ropes hanging to four iron net weights (washers). Measured on the x2
sprite (153 x 256 px = 76.5 x 128 units, seen from about 13 degrees above: the barrel is 121 units tall, the rest
of the sprite height is the lid seen from above); shared numbers in barrel_spec.json.

Every LOD is a lathe of the measured profile (hoops are steps in the profile at LOD0/LOD1, texture only below) with
one UV layout (barrel_textures.py atlas: side strip, lid disc, iron swatch, washer face), so all LODs share one
texture set. The net is an alpha-cut card (MASK, double-sided) following the barrel surface; ropes are swept tubes
on the rope texture. COLOR_0 = vertex occlusion (the atlas is graded to the sprite / EXPECTED_OCCLUSION).
Front = -y (the sprite's view). Writes work/7dec32.blend and work/7dec32_export.glb.
Usage: blender --background --python build_barrel.py"""
import json
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dlib  # noqa: E402

pl, hl, u = dlib.pl, dlib.hl, dlib.u
SIDE_V = 0.75
LID_C, LID_R = (0.125, 0.875), 0.12
DISC_C, DISC_R = (0.63, 0.875), 0.07
SPECS = json.load(open(os.path.join(dlib.HERE, 'scripts', 'barrel_spec.json')))


def configure(prop):
    """Select the barrel spec (barrel_spec.json) the module's builders use; build_cask.py reuses them."""
    global PROP, SPEC, H, R_BOT, R_TOP, R_MID, Z_MID, WOOD_V
    PROP = prop
    SPEC = SPECS[prop]
    H = SPEC['height']
    R_BOT, R_TOP = SPEC['r_end']
    R_MID = SPEC['r_mid']
    Z_MID = H / 2
    WOOD_V = SPEC.get('wood_z', 60.0) / H * SIDE_V    # a plain stave band (between hoops) for the chime's faces


configure('7dec32')
ELEV = math.radians(13.0)                       # the sprite's view elevation
SPRITE_CX = 75.5                                # barrel axis in the cropped x2 sprite


def radius(z):
    r_end = R_BOT if z < Z_MID else R_TOP
    return R_MID - (R_MID - r_end) * ((z - Z_MID) / Z_MID) ** 2


def hoop_at(z, margin=0.0):
    for hoop in SPEC['hoops']:
        if hoop['z'][0] - margin <= z <= hoop['z'][1] + margin:
            return hoop
    return None


def sprite_to_model(row, x):
    """Cropped-x2-sprite point on the front of the barrel -> (angle from the front, z) in the model."""
    s = (256 - row) / 2
    z = (s - R_BOT * math.sin(ELEV)) / math.cos(ELEV) + radius(20) * math.tan(ELEV)
    z = min(max(z, 0.0), H)
    dx = (x - SPRITE_CX) / 2
    return math.asin(max(-1.0, min(1.0, dx / radius(z)))), z


def surface(angle, z, offset):
    """Point on the barrel wall (map units) at angle from the front (-y), toward +x for positive angles."""
    r = radius(z) + offset
    return Vector((r * math.sin(angle), -r * math.cos(angle), z))


# ---------------------------------------------------------------- body
def lathe_uv(name, profile, segments, mat, smooth=True):
    """Surface of revolution [(r, z, v)] with explicit v; u = angle / 2 pi measured from the back (+y), so the
    texture seam is at the back."""
    bm = bmesh.new(); uvl = bm.loops.layers.uv.verify()
    rings = []
    for r, z, v in profile:
        ring = []
        for s in range(segments):
            a = 2 * math.pi * s / segments
            # s = 0 at the back (+y), increasing toward +x... angle from the front = a - pi
            ring.append(bm.verts.new((u(r) * math.sin(a + math.pi), -u(r) * math.cos(a + math.pi), u(z))))
        rings.append(ring)
    for i in range(len(profile) - 1):
        for s in range(segments):
            s2 = (s + 1) % segments
            f = bm.faces.new((rings[i][s], rings[i][s2], rings[i + 1][s2], rings[i + 1][s]))
            for loop, (k, j) in zip(f.loops, ((s, i), (s + 1, i), (s + 1, i + 1), (s, i + 1))):
                loop[uvl].uv = (k / segments, profile[j][2])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return pl.to_object(name, bm, mat, smooth)


def wall_profile(level):
    """(r, z, v) points of the outer wall, base to chime top."""
    zs = SPEC['profile_z'][level]
    steps = level < 2
    out = []
    for z in zs:
        v = z / H * SIDE_V
        r = radius(z)
        hoop = hoop_at(z)
        if not steps or hoop is None:
            out.append((r, z, v))
            continue
        p = hoop['proud']
        z0, z1 = hoop['z']
        if z == 0 or (abs(z - z0) < 1e-6 and z0 <= 0):
            out.append((r + p, z, v))
        elif abs(z - z0) < 1e-6:
            out += [(r, z, v), (r + p, z, v)]
        elif abs(z - z1) < 1e-6:
            if z1 >= H - 1e-6:
                out.append((r + p, z, v))
            else:
                out += [(r + p, z, v), (r, z, v)]
        else:
            out.append((r + p, z, v))
    return out


CHIME = 1.4                    # stave thickness at the rim (map units)
INNER_V = (0.48, 0.26)         # inner staves: a hoop-free band of the side strip (v at the rim, at the floor)
RIM_SHADE, FLOOR_SHADE = 0.62, 0.18    # COLOR_0 inside the open barrel, as the MM6 open barrel


def inner_radius(z):
    """The open barrel's inner wall: the staves' inside, CHIME inside the outer bulge."""
    return radius(z) - CHIME


def inner_shade(z):
    depth = min(1.0, max(0.0, (H - z) / (H - SPEC['floor_z'])))
    return RIM_SHADE + (FLOOR_SHADE - RIM_SHADE) * depth ** 0.7


def open_top(level, segments, top_r, mats):
    """Rim ring, inner stave wall (through a ring at the liquid surface) and a dark floor on the lid planks, as the
    MM6 open barrel. The inside faces carry an `inner` attribute: their COLOR_0 shade by depth."""
    zs = SPEC['inner_z'][level]
    v_top, v_bottom = INNER_V
    floor = SPEC['floor_z']
    profile = [(top_r, H, WOOD_V), (inner_radius(H), H, WOOD_V + 0.004)]
    wall = [(inner_radius(z), z, v_top + (v_bottom - v_top) * (H - z) / (H - floor)) for z in zs]
    parts = [lathe_uv('rim', profile, segments, mats['Barrel'], smooth=False),
             lathe_uv('inner', wall, segments, mats['Barrel'])]
    for obj in parts[1:]:
        for f in obj.data.polygons:                  # the wall faces inward
            f.flip()
    bm = bmesh.new(); uvl = bm.loops.layers.uv.verify()
    r = inner_radius(floor)
    ring = [bm.verts.new((u(r) * math.sin(2 * math.pi * s / segments + math.pi),
                          -u(r) * math.cos(2 * math.pi * s / segments + math.pi), u(floor))) for s in range(segments)]
    f = bm.faces.new(ring)
    for loop in f.loops:
        loop[uvl].uv = (LID_C[0] + loop.vert.co.x / u(r) * LID_R * 0.9, LID_C[1] + loop.vert.co.y / u(r) * LID_R * 0.9)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    for face in bm.faces:
        if face.normal.z < 0:
            face.normal_flip()
    parts.append(pl.to_object('floor', bm, mats['Barrel'], False))
    for obj in parts[1:]:
        attr = obj.data.attributes.new('inner', 'FLOAT', 'POINT')
        attr.data.foreach_set('value', np.array([inner_shade(v.co.z * dlib.UNITS_PER_METRE)
                                                 for v in obj.data.vertices], np.float32))
    return parts


def shade_inside(obj):
    """COLOR_0 of the open barrel's inside: its depth shade instead of the occlusion."""
    if 'inner' not in obj.data.attributes:
        return
    shade = np.empty(len(obj.data.vertices), np.float32)
    obj.data.attributes['inner'].data.foreach_get('value', shade)
    colour = obj.data.color_attributes['Color']
    c = np.empty(len(obj.data.vertices) * 4, np.float32); colour.data.foreach_get('color', c)
    c = c.reshape(-1, 4)
    inside = shade > 0
    c[inside, :3] = shade[inside, None]
    colour.data.foreach_set('color', c.ravel())
    obj.data.attributes.remove(obj.data.attributes['inner'])


def body(level, mats):
    segments = SPEC.get('segments', (24, 16, 10, 8))[level]
    parts = [lathe_uv('wall', wall_profile(level), segments, mats['Barrel'])]
    top_r = radius(H) + (SPEC['hoops'][-1]['proud'] if level < 2 else 0)
    if SPEC.get('open'):
        return parts + open_top(level, segments, top_r, mats)
    chime = CHIME
    lid_z = H - SPEC['lid_depth'] if level < 2 else H
    lid_r = top_r
    if level < 2:
        parts.append(lathe_uv('chime', [(top_r, H, WOOD_V), (top_r - chime, H, WOOD_V + 0.004),
                                        (top_r - chime, lid_z, WOOD_V + 0.012)], segments, mats['Barrel'],
                              smooth=False))
        lid_r = top_r - chime
    # lid: a fan of the disc region (planar uv)
    bm = bmesh.new(); uvl = bm.loops.layers.uv.verify()
    z = lid_z
    ring = [bm.verts.new((u(lid_r) * math.sin(2 * math.pi * s / segments), -u(lid_r) * math.cos(2 * math.pi * s / segments),
                          u(z))) for s in range(segments)]
    f = bm.faces.new(ring)
    for loop in f.loops:
        loop[uvl].uv = (LID_C[0] + loop.vert.co.x / u(lid_r) * LID_R * 0.9, LID_C[1] + loop.vert.co.y / u(lid_r) * LID_R * 0.9)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    parts.append(pl.to_object('lid', bm, mats['Barrel'], False))
    return parts


# ---------------------------------------------------------------- net
# Edges of the draped net on the sprite: (row, left x, right x) in the cropped x2 sprite.
NET_EDGES = [(24, 61, 131), (60, 70, 130), (100, 78, 127), (140, 90, 121), (170, 97, 117), (200, 99, 113),
             (225, 100, 111), (252, 98, 108)]
NET_CELL = 46.0                                  # map units per texture repeat (eight diamonds)
NET_SAG = 1.25                                   # cells drawn out vertically: the net hangs


def net_offset(z):
    """The net lies over the hoops and sags a little toward the staves between them."""
    best = 0.6
    for hoop in SPEC['hoops']:
        z0, z1 = hoop['z']
        d = max(z0 - z, 0.0, z - z1)
        best = max(best, hoop['proud'] + 0.6 - 0.06 * d)
    return best


def net(level):
    if level >= 3:
        return []
    rows = (13, 6, 3)[level]
    cols = (6, 3, 2)[level]
    rng = np.random.default_rng(9)
    edges = [(sprite_to_model(r, xl), sprite_to_model(r, xr)) for r, xl, xr in NET_EDGES]
    zs = [e[0][1] for e in edges]
    bm = bmesh.new(); uvl = bm.loops.layers.uv.verify()
    grid = []
    z_top, z_bot = zs[0], zs[-1]
    for i in range(rows + 1):
        z = z_top + (z_bot - z_top) * i / rows
        # interpolate the edge angles at z
        for k in range(len(edges) - 1):
            if zs[k] >= z >= zs[k + 1]:
                t = (zs[k] - z) / max(zs[k] - zs[k + 1], 1e-6)
                a_l = edges[k][0][0] * (1 - t) + edges[k + 1][0][0] * t
                a_r = edges[k][1][0] * (1 - t) + edges[k + 1][1][0] * t
                break
        n = cols
        row = []
        for j in range(n + 1):
            f = j / n
            a = a_l + (a_r - a_l) * f
            if 0 < j < n:
                a += (a_r - a_l) / n * rng.uniform(-0.2, 0.2)
            elif i not in (0, rows):
                a += rng.uniform(-0.03, 0.03)                 # ragged side edges
            # loose drape: vertical folds standing off the staves between the hoops, a sag toward the tail
            fold = 0.5 + 0.5 * math.sin(f * math.pi * 3.0 + i * 0.35)
            loose = (0.4 + 1.2 * fold) * min(1.0, i / 3) + rng.uniform(0.0, 0.4)
            p = surface(a, z, net_offset(z) + (loose if level == 0 else loose * 0.6))
            arc = a * radius(z)
            row.append((bm.verts.new(p * (1 / dlib.UNITS_PER_METRE)), (arc / NET_CELL, z / (NET_CELL * NET_SAG))))
        grid.append(row)
    for a_row, b_row in zip(grid, grid[1:]):
        for j in range(len(a_row) - 1):
            quad = (a_row[j], a_row[j + 1], b_row[j + 1], b_row[j])
            f = bm.faces.new([q[0] for q in quad])
            for loop, q in zip(f.loops, quad):
                loop[uvl].uv = q[1]
    bmesh.ops.triangulate(bm, faces=bm.faces)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for face in bm.faces:                         # face outward (double-sided anyway; normals for light)
        c = face.calc_center_median()
        if face.normal.dot(Vector((c.x, c.y, 0))) < 0:
            face.normal_flip()
    return [pl.to_object('net', bm, mats_cache['Net'], True)]


# ---------------------------------------------------------------- ropes and weights
# The rope wound round the left side (sprite points), and the two hanging ropes to the washers.
WOUND = [(26, 64), (50, 50), (75, 36), (100, 22), (125, 9)]
HANGING = [((28, 58), (170, 51)), ((28, 63), (204, 62))]
WASHERS = [(172, 51), (193, 53), (207, 63), (218, 54)]    # centres (row, x)
WASHER_R = 5.8
WASHER_T = 1.6


def rope(name, pts, radius_u, sides, mat):
    return hl.sweep(name, pts, radius_u, sides, mat, caps=False, v_scale=12.0)


def ropes(level):
    if level >= 2:
        return []
    sides = (4, 3)[level]
    parts = []
    # wound rope: across the left side and on round the back, slightly below the sprite's last visible point
    pts = []
    for row, x in WOUND:
        a, z = sprite_to_model(row, x)
        pts.append(surface(a, z, net_offset(z) + 0.2))
    a_last, z_last = sprite_to_model(*WOUND[-1])
    for k in range(1, 4 if level == 0 else 2):
        a = a_last - 0.35 * k
        z = z_last - 7 * k
        pts.append(surface(a, z, net_offset(z) + 0.2))
    if level == 1:
        pts = pts[::2] + [pts[-1]]
    parts.append(rope('ropeW', pts, 0.75, sides, mats_cache['Rope']))
    for k, ((r0, x0), (r1, x1)) in enumerate(HANGING):
        a0, z0 = sprite_to_model(r0, x0)
        a1, z1 = sprite_to_model(r1, x1)
        steps = (6, 3)[level]
        pts = []
        for s in range(steps + 1):
            t = s / steps
            a = a0 + (a1 - a0) * t
            z = z0 + (z1 - z0) * t
            pts.append(surface(a, z, net_offset(z) + 0.6 + 1.2 * t))
        parts.append(rope(f'ropeH{k}', pts, 0.7, sides, mats_cache['Rope']))
    return parts


def washer(name, centre, normal, sides):
    """A short iron cylinder (net weight) facing along normal; front cap on the painted washer face."""
    n = normal.normalized()
    side = Vector((0, 0, 1)).cross(n).normalized()
    up = n.cross(side)
    bm = bmesh.new(); uvl = bm.loops.layers.uv.verify()
    rings = []
    for d in (-WASHER_T / 2, WASHER_T / 2):
        rings.append([bm.verts.new((centre + n * d + (side * math.cos(2 * math.pi * s / sides) +
                                                       up * math.sin(2 * math.pi * s / sides)) * WASHER_R)
                                   * (1 / dlib.UNITS_PER_METRE)) for s in range(sides)])
    for s in range(sides):
        s2 = (s + 1) % sides
        f = bm.faces.new((rings[0][s], rings[0][s2], rings[1][s2], rings[1][s]))
        for loop in f.loops:
            loop[uvl].uv = (0.4 + 0.08 * (s / sides), 0.8)
    front = bm.faces.new(rings[1])
    for loop, s in zip(front.loops, range(sides)):
        a = 2 * math.pi * s / sides
        loop[uvl].uv = (DISC_C[0] + math.cos(a) * DISC_R, DISC_C[1] + math.sin(a) * DISC_R)
    back = bm.faces.new(list(reversed(rings[0])))
    for loop in back.loops:
        loop[uvl].uv = (0.4, 0.88)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return pl.to_object(name, bm, mats_cache['Barrel'], False)


def washers(level):
    if level >= 2:
        return []
    parts = []
    for k, (row, x) in enumerate(WASHERS):
        a, z = sprite_to_model(row, x)
        lift = 2.2 + (0.9 if k == 2 else 0.0)               # the third overlaps the others
        c = surface(a, z, net_offset(z) + lift)
        n = (surface(a, z + 0.5, 1) - surface(a, z - 0.5, 1)).cross(surface(a + 0.01, z, 1) - surface(a - 0.01, z, 1))
        n = -n if n.dot(Vector((c.x, c.y, 0))) < 0 else n
        n = (n.normalized() + Vector((0, 0, -0.15))).normalized()    # hanging: tipped slightly down
        parts.append(washer(f'washer{k}', c, n, (8, 6)[level]))
    return parts


if __name__ == '__main__':
    pl.reset()
    mats_cache = {
        'Barrel': dlib.material('Barrel', PROP, extras={'openyamm_specular': 0.6, 'openyamm_specular_mask': True}),
        'Net': dlib.material('Net', 'net', alpha=True, extras={'openyamm_specular': 0.2}),
        'Rope': dlib.material('Rope', 'rope', extras={'openyamm_specular': 0.2}),
    }
    mats = mats_cache
    lods = []
    for level in range(4):
        parts = body(level, mats) + net(level) + ropes(level) + washers(level)
        for obj in parts:
            dlib.apply(obj)
        name = 'Barrel' if level == 0 else f'Barrel_LOD{level}'
        solid = pl.join(name, parts)
        bpy.context.view_layer.objects.active = solid
        solid.select_set(True)
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(40))
        occ = pl.vertex_occlusion(solid, rays=(48, 32, 16, 12)[level], distance=u(20), strength=0.45, floor=True)
        shade_inside(solid)
        print('LEVEL', level, name, 'tris', pl.triangles(solid), 'occlusion', round(occ, 3))
        lods.append(solid)
    dlib.save(PROP, lods)
