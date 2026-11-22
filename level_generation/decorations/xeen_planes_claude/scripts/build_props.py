"""Stage 1 (Blender) for the built props: the return daises (a 12-sided carved disc), the test pedestals (a fluted
column with an emblem on its top) and the Drowned Bell. Writes work/<id>/high.blend with collections High (detailed
sources for the normal bake: carved emblem tops, flutes, bands) and Low (LOD0 pieces, custom property part).
Model units: metres = game units / 100; origin at the bottom centre (the bell: its floor contact centre); front
toward Blender -Y (glTF +Z). Usage: blender -b --python build_props.py -- <id>"""
import json
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import shapes  # noqa: E402

pid = sys.argv[sys.argv.index('--') + 1]
cfg = json.load(open(os.path.join(HERE, 'props.json')))[pid]
work = os.path.join(PROJECT, 'work', pid)
os.makedirs(work, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
high_col = bpy.data.collections.new('High')
low_col = bpy.data.collections.new('Low')
scene.collection.children.link(high_col)
scene.collection.children.link(low_col)
plain = bpy.data.materials.new('Plain')


def add(bm, name, col, part=0):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = shapes.to_object(bm, name, plain, col)
    ob['part'] = part
    return ob


def load_mask(path):
    img = bpy.data.images.load(path)
    w, h = img.size
    a = np.array(img.pixels[:], np.float32).reshape(h, w, 4)[..., 0]     # row 0 = bottom (+Y low)
    return a


def sample(a, u, v):
    h, w = a.shape
    x = min(max(u * (w - 1), 0), w - 1.001)
    y = min(max(v * (h - 1), 0), h - 1.001)
    x0, y0 = int(x), int(y)
    fx, fy = x - x0, y - y0
    return (a[y0, x0] * (1 - fx) * (1 - fy) + a[y0, x0 + 1] * fx * (1 - fy) + a[y0 + 1, x0] * (1 - fx) * fy
            + a[y0 + 1, x0 + 1] * fx * fy)


def carved_top(mask, radius, z, depth, n, sides=None):
    """A grid patch over the disc (or polygon) of `radius` at height z, pushed down by depth x mask."""
    bm = bmesh.new()
    verts = {}
    step = 2 * radius / n
    for j in range(n + 1):
        for i in range(n + 1):
            x, y = -radius + i * step, -radius + j * step
            verts[i, j] = bm.verts.new((x, y, z - depth * sample(mask, (x + radius) / (2 * radius),
                                                                 (y + radius) / (2 * radius))))
    for j in range(n):
        for i in range(n):
            q = [verts[i, j], verts[i + 1, j], verts[i + 1, j + 1], verts[i, j + 1]]
            cx = sum(v.co.x for v in q) / 4
            cy = sum(v.co.y for v in q) / 4
            if inside(cx, cy, radius * 0.995, sides):
                bm.faces.new(q)
    for v in [v for v in bm.verts if not v.link_faces]:
        bm.verts.remove(v)
    return bm


def inside(x, y, r, sides):
    if sides is None:
        return x * x + y * y <= r * r
    a = math.atan2(y, x)
    seg = 2 * math.pi / sides
    a0 = math.floor(a / seg) * seg
    # distance to the polygon edge along the direction a
    apo = r * math.cos(seg / 2)
    return math.hypot(x, y) * math.cos(a - a0 - seg / 2) <= apo


if cfg['kind'] == 'dais':
    R, H, ch = cfg['radius'], cfg['height'], cfg['chamfer']
    sides = 12
    # LOD0: a 12-sided prism with a chamfered top edge and a centre fan on top (open bottom)
    bm = bmesh.new()
    prof = [(R, 0.0), (R, H - ch), (R - ch, H), (R * 0.62, H), (R * 0.30, H), (0.0, H)]
    shapes.lathe(bm, prof, segments=sides, cap_bottom=False, cap_top=False)
    low = add(bm, 'LowDais', low_col, 0)
    # high: the sides (no top) and the carved top
    bm = bmesh.new()
    shapes.lathe(bm, prof[:3], segments=sides, cap_bottom=False, cap_top=False)
    add(bm, 'HighSides', high_col)
    mask = load_mask(os.path.join(PROJECT, 'work', 'emblems', cfg['emblem_image']))
    add(carved_top(mask, R - ch, H, cfg['depth'], 520, sides), 'HighTop', high_col)

if cfg['kind'] == 'pedestal':
    H = cfg['height']
    r = cfg['radius']
    prof = [(r, 0.0), (r, 0.10), (r * 0.93, 0.13), (r * 0.74, 0.15), (r * 0.72, 0.20), (r * 0.66, 0.26),
            (r * 0.64, H - 0.26), (r * 0.70, H - 0.21), (r * 0.80, H - 0.17), (r * 0.98, H - 0.13), (r, H - 0.11),
            (r, H - 0.02), (r * 0.98, H)]
    bm = bmesh.new()
    shapes.lathe(bm, prof + [(r * 0.5, H), (0.0, H)], segments=16, cap_bottom=False, cap_top=False)
    add(bm, 'LowPedestal', low_col, 0)
    # high: fluted shaft (24 flutes), the profile at 96 segments, no top; the carved top
    bm = bmesh.new()
    segs = 96
    rings = []
    for rr, z in prof:
        ring = []
        fl = 0.0
        if 0.26 <= z <= H - 0.26:
            fl = 1.0
        for k in range(segs):
            a = 2 * math.pi * k / segs
            d = rr * (1 - 0.06 * fl * (0.5 + 0.5 * math.cos(24 * a)) ** 2)
            ring.append(Vector((d * math.cos(a), d * math.sin(a), z)))
        rings.append(ring)
    shapes.loft(bm, rings, cap_bottom=False, cap_top=False)
    add(bm, 'HighColumn', high_col)
    mask = load_mask(os.path.join(PROJECT, 'work', 'emblems', cfg['emblem_image']))
    add(carved_top(mask, r * 0.98, H, cfg['depth'], 260), 'HighTop', high_col)

if cfg['kind'] == 'bell':
    bc = cfg['bell']
    outer = [tuple(p) for p in bc['outer']]          # (r, z) from the lip up to the crown pole
    inner = [tuple(p) for p in bc['inner']]          # (r, z) from the lip up to the inner pole
    prof = outer[::-1] + inner                        # crown pole -> outer -> lip -> inner -> inner pole

    def bell_body(bm, segs):
        shapes.lathe(bm, prof, segments=segs, cap_bottom=False, cap_top=False)

    def loop(bm, segs, rr):
        top = outer[-1][1]
        cz = top + bc['loop_r'] + 0.02
        pts = [Vector((math.cos(2 * math.pi * k / segs) * bc['loop_r'], 0, cz + math.sin(2 * math.pi * k / segs)
                       * bc['loop_r'])) for k in range(segs + 1)]
        shapes.tube(bm, pts, [rr] * len(pts), sides=10, cap_start=False, cap_end=False)
        shapes.lathe(bm, [(0.0, top - 0.04), (0.12, top - 0.04), (0.10, top + 0.06), (0.0, top + 0.07)], segments=12,
                     cap_bottom=False, cap_top=False)

    lo = bmesh.new()
    bell_body(lo, bc['segments'])
    loop(lo, 16, bc['loop_t'])
    hi = bmesh.new()
    bell_body(hi, 96)
    loop(hi, 48, bc['loop_t'])
    # raised bands round the outer surface (normal detail only)
    for zb in bc['bands']:
        rb = np.interp(zb, [p[1] for p in outer], [p[0] for p in outer])
        pts = [Vector((math.cos(2 * math.pi * k / 96) * rb, math.sin(2 * math.pi * k / 96) * rb, zb)) for k in range(97)]
        shapes.tube(hi, pts, [bc['band_t']] * len(pts), sides=8, cap_start=False, cap_end=False)
    # lie it down: the axis along X (crown +X, mouth -X), then tilt so the lip and the shoulder rest on the floor
    tilt = math.radians(bc['tilt_deg'])
    M = Matrix.Rotation(tilt, 4, 'Y') @ Matrix.Rotation(math.radians(-90), 4, 'Y')
    for bm_ in (lo, hi):
        bmesh.ops.transform(bm_, matrix=M, verts=bm_.verts)
    lob = add(lo, 'LowBell', low_col, 0)
    hib = add(hi, 'HighBell', high_col)
    pts = [v.co for v in lob.data.vertices]
    zmin = min(p.z for p in pts)
    floor = [p for p in pts if p.z < zmin + 0.03]
    # the footprint's centre (the bell's plan bounds), on the floor
    cx = (min(p.x for p in pts) + max(p.x for p in pts)) / 2
    cy = (min(p.y for p in pts) + max(p.y for p in pts)) / 2
    T = Matrix.Translation((-cx, -cy, -zmin - bc['sink']))
    for o in (lob, hib):
        o.data.transform(T)
    print('BELL contacts', len(floor), 'x span %.2f..%.2f' % (min(p.x for p in floor) - cx, max(p.x for p in floor) - cx))

allv = [v.co for o in low_col.objects for v in o.data.vertices]
lo_ = Vector([min(p[i] for p in allv) for i in range(3)])
hi_ = Vector([max(p[i] for p in allv) for i in range(3)])
print('BOUNDS', tuple(round(x, 3) for x in lo_), tuple(round(x, 3) for x in hi_))
for o in low_col.objects:
    print('LOW', o.name, 'tris', sum(len(p.vertices) - 2 for p in o.data.polygons))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(work, 'high.blend'))
print('HIGH_DONE')
