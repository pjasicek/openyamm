"""Shared Blender helpers of the MM8 animated decorations: the MM6 outdoor props library (read only, imported via
mm6_dungeons_3d/scripts/dungeon_lib.py) with this batch's textures (textures/, make_textures.py), COLOR_0 tints toward
measured native colours, the shared CC0 flame flipbooks (mm6_dungeons_3d/textures/FLAMES.md), halo cards, chain
links, tubes along curves and the LOD build-and-export loop. Lengths are given in native map units (u() converts
to metres, 81.7 units per metre). Tint, chain and flame-card code follows the MM6 fire batch's fire_lib.py."""
import json
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

SCRIPTS = os.path.dirname(os.path.abspath(__file__))
HERE = os.path.dirname(SCRIPTS)
DECORATIONS = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(DECORATIONS, 'mm6_dungeons_3d', 'scripts'))
import dungeon_lib as dl  # noqa: E402

pl = dl.pl
u = dl.units
TEXTURES = os.path.join(HERE, 'textures')
FLAMES = os.path.join(DECORATIONS, 'mm6_dungeons_3d', 'textures')
with open(os.path.join(TEXTURES, 'means.json')) as handle:
    MEANS = json.load(handle)
TEXTURE_OF = {}
# Flame flipbooks (16 x 4 frames, 64-frame loop at 30 fps): measured texture v of the flame base and median tip.
# candleglow (make_textures.py) is Flame03 re-centred in square frames with its own baked halo: same heights.
FLIPBOOKS = {'flame02': (0.023, 0.70), 'flame03': (0.055, 0.70), 'candleglow': (0.055, 0.70)}
# Fraction of a card's width the flame spans (the rest is the frame's margin, or candleglow's halo).
FLAME_SPAN = {'flame02': 0.6, 'flame03': 0.6, 'candleglow': 0.35}


def material(name, texture, alpha=False, extras=None, roughness=None):
    """Principled material on textures/<texture>_{basecolor,normal,mr}.png (alpha mode set by finish.py)."""
    TEXTURE_OF[name] = texture
    saved = pl.TEX
    pl.TEX = TEXTURES
    try:
        m = pl.material(name, texture, alpha=alpha, extras=extras)
    finally:
        pl.TEX = saved
    return m


def set_emission(m, srgb_colour, strength=1.0):
    bsdf = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    bsdf.inputs['Emission Color'].default_value = tuple(linear(c) for c in srgb_colour) + (1.0,)
    bsdf.inputs['Emission Strength'].default_value = strength
    return m


def animated(extras, pulse=None, flicker=None):
    """Emission animation extras: a slow sine pulse (orb, runes) or a smooth random flicker (fire)."""
    if pulse:
        extras['openyamm_pulse'] = list(pulse)
    if flicker:
        extras['openyamm_flicker'] = list(flicker)
    return extras


def glow_material(name, texture, emission, pulse=None, extras=None, flicker=None):
    """Lit material that also glows: constant emissiveFactor (linear from sRGB), pulsing or flickering."""
    return set_emission(material(name, texture, extras=animated(dict(extras or {}), pulse, flicker)), emission)


def flame_material(name, texture='flame02', billboard=True, additive=False, flicker=None, emission=None,
                   flipbook=(16, 4, 30)):
    """Unlit blended card on a flipbook (finish FLAME): the shared flames (mm6_dungeons_3d/textures) or this batch's
    candleglow/sparks (textures/). billboard: True (about the model axis), 'card' (about the card's own centre: one
    primitive, so one material, per off-axis card) or False (fixed). additive: colour times alpha is added (glow)."""
    TEXTURE_OF[name] = texture
    saved = pl.TEX
    local = os.path.exists(os.path.join(TEXTURES, f'{texture}_basecolor.png'))
    pl.TEX = TEXTURES if local else FLAMES
    extras = {'openyamm_flipbook': list(flipbook), 'openyamm_specular': 0.0}
    if billboard:
        extras['openyamm_billboard'] = billboard
    if additive:
        extras['openyamm_additive'] = True
    animated(extras, None, flicker)
    try:
        m = pl.material(name, texture, alpha=True, extras=extras)
    finally:
        pl.TEX = saved
    if emission:
        set_emission(m, emission)
    return m


def halo_material(name, pulse=None, emission=None, flicker=None, additive=True, texture='halo', billboard=True):
    """Camera-facing soft glow card (finish HALO: blended, unlit, additive by default); its colour comes from
    COLOR_0, plus an optional pulsing or flickering emission where its alpha shows."""
    extras = animated({'openyamm_billboard': billboard, 'openyamm_specular': 0.0, 'openyamm_unlit_review': True},
                      pulse, flicker)
    if additive:
        extras['openyamm_additive'] = True
    m = material(name, texture, alpha=True, extras=extras)
    if emission:
        set_emission(m, emission)
    return m


def linear(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def mix(a, b, t):
    t = min(1.0, max(0.0, t))
    return tuple(x + (y - x) * t for x, y in zip(a, b))


def stops(points, z):
    """Piecewise-linear sRGB colour over a coordinate: points [(value, (r, g, b)), ...] ascending."""
    if z <= points[0][0]:
        return points[0][1]
    for (z0, c0), (z1, c1) in zip(points, points[1:]):
        if z <= z1:
            return mix(c0, c1, (z - z0) / (z1 - z0))
    return points[-1][1]


def srgb8(lin):
    lin = min(1.0, max(0.0, lin))
    return 255.0 * (lin * 12.92 if lin <= 0.0031308 else 1.055 * lin ** (1 / 2.4) - 0.055)


def scaled(texture, factor):
    """The sRGB target that tint() turns into a plain multiplier `factor` of the texture (painted textures that
    already carry the native colours: only shading through COLOR_0)."""
    return tuple(srgb8(m * factor) for m in MEANS[texture])


def tint(obj, colours):
    """Multiply each vertex's colour by linear(native sRGB) / linear(texture mean) of its material. colours:
    material name -> sRGB tuple or callable (co in units, normal) -> sRGB tuple. Clamped to one."""
    me = obj.data
    names = [m.name for m in me.materials]
    attr = me.color_attributes['Color']
    owner = {}
    for polygon in me.polygons:
        for index in polygon.vertices:
            owner[index] = names[polygon.material_index]
    clamped = set()
    for index, name in owner.items():
        target = colours.get(name)
        if target is None:
            continue
        vertex = me.vertices[index]
        if callable(target):
            target = target(vertex.co * dl.UNITS_PER_METRE, vertex.normal)
        mean = MEANS[TEXTURE_OF[name]] if TEXTURE_OF.get(name) in MEANS else (1.0, 1.0, 1.0)
        factor = []
        for channel, value in enumerate(target):
            f = linear(value) / mean[channel]
            if f > 1.0:
                clamped.add(name)
                f = 1.0
            factor.append(f)
        c = attr.data[index].color
        attr.data[index].color = (c[0] * factor[0], c[1] * factor[1], c[2] * factor[2], c[3])
    if clamped:
        print('TINT CLAMPED', obj.name, sorted(clamped))


def set_alpha(obj, weights):
    """COLOR_0 alpha per vertex (the flutter weight): weights maps material name -> callable (co units) -> 0..1."""
    me = obj.data
    names = [m.name for m in me.materials]
    attr = me.color_attributes['Color']
    for polygon in me.polygons:
        fn = weights.get(names[polygon.material_index])
        if fn is None:
            continue
        for index in polygon.vertices:
            c = attr.data[index].color
            attr.data[index].color = (c[0], c[1], c[2], float(fn(me.vertices[index].co * dl.UNITS_PER_METRE)))


def apply(objects):
    for obj in objects:
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return objects


def card(name, mat, corners, uvs, smooth=False):
    bm = bmesh.new()
    uv = bm.loops.layers.uv.verify()
    face = bm.faces.new([bm.verts.new(c) for c in corners])
    for loop, st in zip(face.loops, uvs):
        loop[uv].uv = st
    return pl.to_object(name, bm, mat, smooth=smooth)


def flame_card(name, mat, texture, base_z, tip_z, width, x=0.0, y=0.0, yaw=0.0, mirrored=False, frame_offset=0,
               v_top=None):
    """A flame card (units) whose flipbook flame base sits at base_z and whose tip reaches tip_z; the card ends at
    the tip unless v_top (texture v of the card top, above the tip: candleglow's halo) is given. Cards on the axis
    (x = y = 0) or on card-billboard materials stay in the model's x/up plane (yaw 0); fixed cards turn by yaw.
    frame_offset shifts the texture coordinates by whole frames (u by columns, v by rows of the 16 x 4 grid; the
    sampler repeats), so neighbouring flames do not play the same frame."""
    v_base, v_tip = FLIPBOOKS[texture]
    top = v_tip if v_top is None else v_top
    per_v = (tip_z - base_z) / (v_tip - v_base)
    z0 = base_z - v_base * per_v
    z1 = base_z + (top - v_base) * per_v
    du, dv = frame_offset % 16, frame_offset // 16 % 4
    a = math.radians(yaw)
    across = Vector((math.cos(a), math.sin(a), 0))
    centre = Vector((u(x), u(y), 0))
    half = u(width / 2)
    corners = [centre - across * half + Vector((0, 0, u(z0))), centre + across * half + Vector((0, 0, u(z0))),
               centre + across * half + Vector((0, 0, u(z1))), centre - across * half + Vector((0, 0, u(z1)))]
    uvs = []
    for s, t in ((0, 0), (1, 0), (1, top), (0, top)):
        uvs.append(((1 - s if mirrored else s) + du, t - dv))
    return card(name, mat, corners, uvs)


def candle_card(name, x, y, base_z, tip_z, flame_width, frame_offset, flicker=(0.3, 8.0), v_top=0.85):
    """One off-axis candle flame with its halo: an additive candleglow card turning about its own centre
    ('card' billboard), on its own material copy (the card pivot is per primitive)."""
    mat = bpy.data.materials.get(name) or flame_material(name, 'candleglow', billboard='card', additive=True,
                                                         flicker=flicker, emission=(26, 10, 2))
    return flame_card(f'{name}_card', mat, 'candleglow', base_z, tip_z, flame_width / FLAME_SPAN['candleglow'],
                      x, y, frame_offset=frame_offset, v_top=v_top)


def spark_card(name, mat, base_z, top_z, width, x=0.0, frame_offset=0):
    """Rising sparks: a camera-facing card on the 8 x 4 sparks flipbook (frame bottom at base_z, top at top_z)."""
    du, dv = frame_offset % 8, frame_offset // 8 % 4
    corners = [(u(x - width / 2), 0, u(base_z)), (u(x + width / 2), 0, u(base_z)), (u(x + width / 2), 0, u(top_z)),
               (u(x - width / 2), 0, u(top_z))]
    return card(name, mat, corners, [(0 + du, 0 - dv), (1 + du, 0 - dv), (1 + du, 1 - dv), (0 + du, 1 - dv)])


def flame_star(name, mat, texture, base_z, tip_z, width, x, y, cards=2, frame_offset=0, yaw=0.0):
    """Fixed crossed flame cards (cards planes at 180 / cards degrees) for off-axis flames (a camera-facing card
    keeps only its offset across the model)."""
    return [flame_card(f'{name}_{k}', mat, texture, base_z, tip_z, width, x, y, yaw + 180.0 * k / cards,
                       mirrored=bool(k % 2), frame_offset=frame_offset + 5 * k) for k in range(cards)]


def halo_card(name, mat, centre_z, radius, x=0.0):
    """Camera-facing soft glow card (units) centred at centre_z on the axis."""
    r = u(radius)
    corners = [(u(x) - r, 0, u(centre_z) - r), (u(x) + r, 0, u(centre_z) - r), (u(x) + r, 0, u(centre_z) + r),
               (u(x) - r, 0, u(centre_z) + r)]
    return card(name, mat, corners, [(0, 0), (1, 0), (1, 1), (0, 1)])


def link(name, mat, centre, direction, length, width, wire, segments, sides, turn):
    """One oval chain link (metres) centred at centre, long axis along direction, turned about it."""
    bm = bmesh.new()
    uv = bm.loops.layers.uv.verify()
    half_l, half_w = (length - wire) / 2, (width - wire) / 2
    rings = []
    for i in range(segments):
        t = 2 * math.pi * i / segments
        c = Vector((math.cos(t) * half_w, 0, math.sin(t) * half_l))
        tangent = Vector((-math.sin(t) * half_w, 0, math.cos(t) * half_l)).normalized()
        out = tangent.cross(Vector((0, 1, 0))).normalized()
        ring = []
        for j in range(sides):
            a = 2 * math.pi * (j + 0.5) / sides
            ring.append(bm.verts.new(c + (out * math.cos(a) + Vector((0, 1, 0)) * math.sin(a)) * wire / 2))
        rings.append(ring)
    for i in range(segments):
        following = rings[(i + 1) % segments]
        for j in range(sides):
            face = bm.faces.new((rings[i][j], following[j], following[(j + 1) % sides], rings[i][(j + 1) % sides]))
            for loop, (s, v) in zip(face.loops, ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))):
                loop[uv].uv = (s / segments * 0.5, v / sides * 0.1)
    direction = Vector(direction).normalized()
    frame = direction.to_track_quat('Z', 'X').to_matrix().to_4x4() @ Matrix.Rotation(turn, 4, 'Z')
    for v in bm.verts:
        v.co = frame @ v.co + Vector(centre)
    return pl.to_object(name, bm, mat)


def chain(name, mat, start, end, pitch, width, wire, segments, sides, phase=0):
    """Links from start to end (metres) about `pitch` apart, alternately turned."""
    start, end = Vector(start), Vector(end)
    span = (end - start).length
    count = max(1, round(span / pitch))
    step = span / count
    direction = (end - start).normalized()
    return [link(f'{name}{i}', mat, start + direction * (step * (i + 0.5)), direction, step + wire * 2, width, wire,
                 segments, sides, (i + phase) % 2 * math.pi / 2) for i in range(count)]


def bezier(points, samples):
    """Points along a Catmull-Rom spline through points (any coordinates), samples in total."""
    pts = [Vector(p) for p in points]
    pts = [pts[0] * 2 - pts[1]] + pts + [pts[-1] * 2 - pts[-2]]
    out = []
    for k in range(samples):
        t = k / (samples - 1) * (len(points) - 1)
        i = min(int(t), len(points) - 2)
        f = t - i
        p0, p1, p2, p3 = pts[i], pts[i + 1], pts[i + 2], pts[i + 3]
        out.append(0.5 * (2 * p1 + (-p0 + p2) * f + (2 * p0 - 5 * p1 + 4 * p2 - p3) * f * f
                          + (-p0 + 3 * p1 - 3 * p2 + p3) * f * f * f))
    return out


def sweep(name, path, radii, sides, mat, u_repeat=1.0, v_scale=1.0, caps=True, flat=None, smooth=True):
    """Tube along a path (metres) with per-point radii (parallel transport frame). flat: (width, thickness) scale of
    the section's two axes (a flat strap when thickness < width), the width axis kept horizontal where possible."""
    path = [Vector(p) for p in path]
    radii = list(radii) if hasattr(radii, '__len__') else [radii] * len(path)
    bm = bmesh.new()
    uv = bm.loops.layers.uv.verify()
    tangent = (path[1] - path[0]).normalized()
    ref = Vector((0, 0, 1)) if abs(tangent.z) < 0.9 else Vector((1, 0, 0))
    side = tangent.cross(ref).normalized()
    rings = []
    length = [0.0]
    for i, p in enumerate(path):
        if i > 0:
            length.append(length[-1] + (p - path[i - 1]).length)
        t = (path[min(i + 1, len(path) - 1)] - path[max(i - 1, 0)]).normalized()
        side = (side - t * side.dot(t)).normalized()
        other = t.cross(side)
        sx, sy = flat if flat else (1.0, 1.0)
        rings.append([bm.verts.new(p + (side * math.cos(2 * math.pi * s / sides) * sx
                                        + other * math.sin(2 * math.pi * s / sides) * sy) * radii[i])
                      for s in range(sides)])
    for i in range(len(path) - 1):
        for s in range(sides):
            s2 = (s + 1) % sides
            f = bm.faces.new((rings[i][s], rings[i][s2], rings[i + 1][s2], rings[i + 1][s]))
            for loop, (a, b) in zip(f.loops, ((s, i), (s + 1, i), (s + 1, i + 1), (s, i + 1))):
                loop[uv].uv = (a / sides * u_repeat, length[b] * v_scale)
    if caps:
        bm.faces.new(list(reversed(rings[0])))
        bm.faces.new(rings[-1])
    return pl.to_object(name, bm, mat, smooth)


def merge_materials(obj, merge):
    """Move the faces of each material in merge (name -> target) onto the target's slot and drop the slot."""
    for source, target in merge.items():
        names = [m.name for m in obj.data.materials]
        if source not in names or target not in names:
            continue
        s, t = names.index(source), names.index(target)
        for polygon in obj.data.polygons:
            if polygon.material_index == s:
                polygon.material_index = t
        obj.active_material_index = s
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.material_slot_remove()


def order_materials(obj, last):
    """Put the material slots whose names start with each entry of `last` at the end, in that order (blended and
    additive cards draw after the opaque parts, in slot order: glTF primitive order is draw order)."""
    me = obj.data
    mats = list(me.materials)
    rank = [next((k + 1 for k, prefix in enumerate(last) if m.name.startswith(prefix)), 0) for m in mats]
    order = sorted(range(len(mats)), key=lambda i: (rank[i], i))
    if order == list(range(len(mats))):
        return
    new_index = {old: new for new, old in enumerate(order)}
    indices = [new_index[p.material_index] for p in me.polygons]
    me.materials.clear()
    for i in order:
        me.materials.append(mats[i])
    for p, index in zip(me.polygons, indices):
        p.material_index = index


def build_lods(base_name, prop, build, colours, rays=(32, 20, 12), distance=20.0, strength=0.5, levels=3,
               merge=None, alpha=None, last=()):
    """build(level) -> (solid objects (vertex occlusion), white objects (cards, glow: no occlusion)); tints from
    colours, flutter weights from alpha (material -> fn), materials merged, blended slots last, LOD join; saves
    work/<prop>.blend and exports work/<prop>_export.glb."""
    lods = []
    for level in range(levels):
        solids, whites = build(level)
        parts = []
        if solids:
            solid = pl.join(f'solid{level}', solids)
            occlusion = pl.vertex_occlusion(solid, rays=rays[min(level, len(rays) - 1)], distance=u(distance),
                                            strength=strength, floor=False)
            tint(solid, colours)
            parts.append(solid)
        else:
            occlusion = 1.0
        for obj in whites:
            pl.white_colour(obj)
            tint(obj, colours)
            parts.append(obj)
        name = base_name if level == 0 else f'{base_name}_LOD{level}'
        obj = pl.join(name, parts)
        if alpha:
            set_alpha(obj, alpha)
        merge_materials(obj, merge or {})
        order_materials(obj, last)
        print('LEVEL', level, name, 'tris', pl.triangles(obj), 'mean occlusion', round(occlusion, 3))
        lods.append(obj)
    work = os.path.join(HERE, 'work')
    os.makedirs(work, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(work, f'{prop}.blend'))
    pl.export(lods, os.path.join(work, f'{prop}_export.glb'))
    return lods
