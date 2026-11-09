"""`dec96`: a gold art-deco eagle (outdoor, 7out13, 1 placement): wings spread level in five stepped feather rows
whose outer ends step inward row by row, a shield-shaped breast, the head in profile with a hooked beak to the
viewer's right, a splayed tail fan and two legs gripping a ball, on a two-step square plinth. Measured on the x2
sprite (52 high, 64.6 wide; map units). The wings sweep back 12 degrees and every row is a bevelled slab, so the side
view keeps some depth. One gold material (Poly Haven rusty_metal_02 luminance in gold, small_textures.py `gold`);
COLOR_0 = vertex occlusion x the outdoor grade. LOD1/LOD2 drop bevels, rows and segments.
Usage: blender --background --python small_eagle.py -- [grade_r grade_g grade_b]"""
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dlib  # noqa: E402

pl, hl, u = dlib.pl, dlib.hl, dlib.u
PROP = 'dec96'
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
GRADE = [float(a) for a in args[:3]] if len(args) >= 3 else [1.0, 1.0, 1.0]


def slab(name, x0, x1, z0, z1, y0, y1, mat, bevel, level, sweep=0.0, taper=0.0):
    """A box from x0..x1, z0..z1, y0..y1 (map units); sweep: degrees the outer (|x| large) end turns back (+y);
    taper: the outer end's height shrinks by this fraction (feather tips)."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        fx = v.co.x + 0.5
        x = x0 + (x1 - x0) * fx
        zc = (z0 + z1) / 2; hz = (z1 - z0) / 2
        outer = abs(x) / 33.0
        z = zc + v.co.z * 2 * hz * (1 - taper * outer)
        y = y0 + (y1 - y0) * (v.co.y + 0.5) + abs(x) * math.tan(math.radians(sweep))
        v.co = Vector((u(x), u(y), u(z)))
    if bevel and level == 0:
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=u(bevel), segments=1, affect='EDGES', profile=0.5)
    uv = bm.loops.layers.uv.verify()
    for f in bm.faces:
        n = f.normal
        for loop in f.loops:
            co = loop.vert.co
            if abs(n.z) > 0.6:
                loop[uv].uv = (co.x * 2.5, co.y * 2.5)
            elif abs(n.x) > 0.6:
                loop[uv].uv = (co.y * 2.5, co.z * 2.5)
            else:
                loop[uv].uv = (co.x * 2.5, co.z * 2.5)
    return pl.to_object(name, bm, mat, False)


def ellipsoid(name, centre, radii, segments, rings, mat, squash=None):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=rings, radius=1.0, calc_uvs=True)
    for v in bm.verts:
        p = v.co.copy()
        if squash:
            p = squash(p)
        v.co = Vector((u(centre[0] + p.x * radii[0]), u(centre[1] + p.y * radii[1]), u(centre[2] + p.z * radii[2])))
    return pl.to_object(name, bm, mat, True)


def shield(p):
    """Breast: a heart/shield shape, full at the top, narrowing to a rounded point below."""
    if p.z < 0:
        k = 1 + p.z * 0.55
        return Vector((p.x * k, p.y * (0.6 + 0.4 * k), p.z * 1.15))
    return Vector((p.x * (1 + 0.25 * p.z), p.y, p.z * 0.85))


def head_shape(p):
    return Vector((p.x * (1.0 + 0.15 * max(p.x, 0)), p.y, p.z))


def beak(name, level, mat):
    """Hooked beak to +x: a tapering four- or six-sided tube along a curve, ending down-turned."""
    pts = [(3.0, -0.5, 48.6), (6.2, -0.5, 48.9), (8.4, -0.5, 47.9), (9.2, -0.5, 46.2)]
    radii = [2.2, 1.6, 1.0, 0.35]
    return hl.sweep(name, pts if level == 0 else [pts[0], pts[2], pts[3]], radii if level == 0 else
                    [radii[0], radii[2], radii[3]], (6, 4, 4)[level], mat, flat=0.75)


def build(level, mat):
    parts = []
    bev = 0.5
    # plinth: base block and a thinner slab
    parts.append(slab('base', -10.7, 10.7, 0, 5.2, -10.7, 10.7, mat, bev, level))
    parts.append(slab('step', -9.5, 9.5, 5.2, 9.2, -9.5, 9.5, mat, bev, level))
    # ball
    parts.append(ellipsoid('ball', (0, 0, 16.0), (7.7, 7.7, 7.7), (24, 12, 8)[level], (12, 7, 5)[level], mat))
    # legs: two square blocks from the ball top into the body
    for side in (-1, 1):
        parts.append(slab(f'leg{side}', side * 4.6 - 1.7, side * 4.6 + 1.7 if side > 0 else side * 0.6,
                          22.0, 31.5, -2.2, 2.2, mat, 0.3, level) if False else
                     slab(f'leg{side}', side * 2.4 - 1.9, side * 2.4 + 1.9, 21.5, 32.5, -2.6, 1.6, mat, 0.3,
                          level))
        if level < 2:
            for toe in (-1, 0, 1):          # talons over the ball's crown
                parts.append(slab(f'toe{side}{toe}', side * 2.6 + toe * 1.3 - 0.5, side * 2.6 + toe * 1.3 + 0.5,
                                  21.6, 23.2, -3.6 + abs(toe) * 0.8, 1.0, mat, 0, level))
    # tail fan: feathers radiating down and out from under the breast
    fan = ((-52, 12.5), (-34, 11.5), (34, 11.5), (52, 12.5)) if level < 2 else ((-45, 12.0), (45, 12.0))
    for k, (angle, length) in enumerate(fan):
        feather = slab(f'tail{k}', -1.6, 1.6, -length, 0, -1.6, 0.6, mat, 0.3, level)
        feather.rotation_euler = (0, math.radians(angle), 0)
        feather.location = (0, 0, u(34.5))
        dlib.apply(feather)
        parts.append(feather)
    # breast and head
    parts.append(ellipsoid('breast', (0, -1.6, 38.8), (6.6, 4.6, 7.4), (16, 10, 7)[level], (10, 7, 5)[level], mat,
                           shield))
    if level < 2:
        parts.append(ellipsoid('neck', (0.6, -0.5, 44.0), (4.0, 3.4, 3.4), (10, 8)[level], (7, 5)[level], mat))
    parts.append(ellipsoid('head', (1.0, -0.5, 48.4), (4.6, 3.8, 3.9), (14, 10, 6)[level], (9, 7, 4)[level], mat,
                           head_shape))
    parts.append(beak('beak', level, mat))
    # wings: five stepped rows per side, the top row the longest; each row a little behind the one above
    rows = [(47.3, 43.9, 32.3), (44.3, 41.0, 30.6), (41.4, 38.4, 27.6), (38.8, 36.0, 24.6), (36.4, 33.9, 22.2)]
    if level == 2:
        rows = [(47.3, 41.0, 32.0), (41.4, 33.9, 26.0)]
    for k, (top, bottom, reach) in enumerate(rows):
        for side in (-1, 1):
            x_in, x_out = side * 3.5, side * reach
            parts.append(slab(f'wing{k}{side}', min(x_in, x_out), max(x_in, x_out), bottom, top,
                              -0.6 + k * 0.5, 2.8 + k * 0.3, mat, 0.45, level, sweep=12.0, taper=0.12))
    return parts


pl.reset()
mat = dlib.material('Gold', 'misc_eagle_metal', extras={'openyamm_specular': 1.0})
lods = []
for level in range(3):
    parts = build(level, mat)
    for p in parts:
        dlib.apply(p)
    obj = pl.join('Base' if level == 0 else f'Base_LOD{level}', parts)
    pl.vertex_occlusion(obj, rays=(48, 24, 12)[level], distance=u(14), strength=0.8, floor=True)   # crevice grime
    me = obj.data
    c = np.empty(len(me.vertices) * 4, np.float32); me.color_attributes['Color'].data.foreach_get('color', c)
    c = c.reshape(-1, 4); c[:, :3] *= np.array(GRADE, np.float32); c[:, :3] = np.clip(c[:, :3], 0, 1)
    me.color_attributes['Color'].data.foreach_set('color', c.ravel())
    lods.append(obj)
dlib.save(PROP, lods)
