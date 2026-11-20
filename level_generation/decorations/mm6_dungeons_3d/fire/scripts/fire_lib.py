"""Shared Blender helpers for the MM6 dungeon fire fixtures: the project's dungeon_lib (outdoor props_lib) with
materials from fire/textures/ first, COLOR_0 tints computed from measured native colours, flame cards, oval chain
links and the LOD build-and-export loop. Lengths are given in native map units (u() converts to metres)."""
import json
import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

SCRIPTS = os.path.dirname(os.path.abspath(__file__))
HERE = os.path.dirname(SCRIPTS)
sys.path.insert(0, os.path.join(HERE, '..', 'scripts'))
import dungeon_lib as dl  # noqa: E402

dl.TEXTURES = os.path.join(HERE, 'textures')     # this batch's textures first, then the props textures
pl = dl.pl
u = dl.units
with open(os.path.join(HERE, 'textures', 'means.json')) as handle:
    MEANS = json.load(handle)
TEXTURE_OF = {}


def material(name, texture, alpha=False, extras=None):
    TEXTURE_OF[name] = texture
    return dl.material(name, texture, alpha=alpha, extras=extras)


def glow_material(name, texture, emission, pulse=None):
    """A lit PBR material (an ember texture with normal and roughness) that also glows: a constant emission
    (glTF emissiveFactor, linear RGB from the sRGB `emission`; the engine adds it after lighting, unscaled by COLOR_0)
    and optionally openyamm_pulse [amplitude, period seconds] flickering it per placement."""
    extras = {'openyamm_pulse': list(pulse)} if pulse else None
    m = material(name, texture, extras=extras)
    bsdf = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    bsdf.inputs['Emission Color'].default_value = tuple(linear(c) for c in emission) + (1.0,)
    bsdf.inputs['Emission Strength'].default_value = 1.0
    return m


SHARED_TEXTURES = os.path.join(HERE, '..', 'textures')
# The project's shared CC0 Unity Labs flame flipbooks (../textures/, 16 x 4 frames, a seamless 64-frame loop at 30
# frames per second): per flipbook the measured texture v (0 at the cell bottom) of the flame's base and of its
# tip (the median frame's sparse top; a few frames' wisps rise higher and are cut off at the card top).
FLIPBOOKS = {'flame02': (0.023, 0.70), 'flame03': (0.055, 0.70)}


def flame_material(name, texture, billboard=True):
    """Unlit blended card on a shared flame flipbook (finish.py FLAME), camera-facing unless billboard is False."""
    TEXTURE_OF[name] = texture
    dl.TEXTURES, saved = SHARED_TEXTURES, dl.TEXTURES
    extras = {'openyamm_flipbook': [16, 4, 30], 'openyamm_specular': 0.0}
    if billboard:
        extras['openyamm_billboard'] = True
    try:
        return dl.material(name, texture, alpha=True, extras=extras)
    finally:
        dl.TEXTURES = saved


def linear(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def mix(a, b, t):
    t = min(1.0, max(0.0, t))
    return tuple(x + (y - x) * t for x, y in zip(a, b))


def stops(points, z):
    """Piecewise-linear sRGB colour over height: points [(z units, (r, g, b)), ...] bottom to top."""
    if z <= points[0][0]:
        return points[0][1]
    for (z0, c0), (z1, c1) in zip(points, points[1:]):
        if z <= z1:
            return mix(c0, c1, (z - z0) / (z1 - z0))
    return points[-1][1]


def tint(obj, colours):
    """Multiply each vertex's occlusion colour by linear(native sRGB) / linear(texture mean) of its material.
    colours: material name -> sRGB tuple, or callable (co in units, normal) -> sRGB tuple. Clamped to one."""
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
        mean = MEANS[TEXTURE_OF[name]]
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


def apply(objects):
    for obj in objects:
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return objects


def flame_card(name, mat, texture, base_z, tip_z, width, x=0.0, mirrored=False):
    """A flame card whose flipbook flame base sits at base_z (inside the fixture) and whose tip reaches tip_z (the
    native flame's top); the card ends at the tip (texture v from 0 to the tip's v), so the model's bounds do not
    rise above the sprite. width: the card width in units (the flame fills about two thirds of it)."""
    v_base, v_tip = FLIPBOOKS[texture]
    per_v = (tip_z - base_z) / (v_tip - v_base)
    z0 = base_z - v_base * per_v
    bm = bmesh.new()
    uv = bm.loops.layers.uv.verify()
    corners = ((u(x - width / 2), 0, u(z0)), (u(x + width / 2), 0, u(z0)), (u(x + width / 2), 0, u(tip_z)),
               (u(x - width / 2), 0, u(tip_z)))
    face = bm.faces.new([bm.verts.new(c) for c in corners])
    for loop, (s, t) in zip(face.loops, ((0, 0), (1, 0), (1, v_tip), (0, v_tip))):
        loop[uv].uv = (1 - s if mirrored else s, t)
    return pl.to_object(name, bm, mat, smooth=False)


def link(name, mat, centre, direction, length, width, wire, segments, sides, turn):
    """One oval chain link (outer length x width, wire thickness) centred at centre, its long axis along direction,
    turned `turn` radians about it (alternate links: 0 and pi / 2)."""
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
            face = bm.faces.new((rings[i][j], rings[i][(j + 1) % sides], following[(j + 1) % sides], following[j]))
            for loop, (s, v) in zip(face.loops, ((i, j), (i, j + 1), (i + 1, j + 1), (i + 1, j))):
                loop[uv].uv = (s / segments * 0.5, v / sides * 0.1)
    direction = Vector(direction).normalized()
    frame = direction.to_track_quat('Z', 'X').to_matrix().to_4x4() @ Matrix.Rotation(turn, 4, 'Z')
    for v in bm.verts:
        v.co = frame @ v.co + Vector(centre)
    return pl.to_object(name, bm, mat)


def chain(name, mat, start, end, pitch, width, wire, segments, sides, phase=0):
    """Links from start to end (metres), about `pitch` apart, alternately turned; returns (objects, count)."""
    start, end = Vector(start), Vector(end)
    span = (end - start).length
    count = max(1, round(span / pitch))
    step = span / count
    direction = (end - start).normalized()
    links = []
    for i in range(count):
        centre = start + direction * (step * (i + 0.5))
        links.append(link(f'{name}{i}', mat, centre, direction, step + wire * 2, width, wire, segments, sides,
                          (i + phase) % 2 * math.pi / 2))
    return links


def merge_materials(obj, merge):
    """Move the faces of each material in merge (name -> target name) onto the target's slot and drop the slot:
    parts tinted apart (chain and bowl) share one material and one draw."""
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


def build_lods(base_name, prop, build, colours, rays=(32, 20, 12), distance=20.0, strength=0.5, levels=3,
               merge=None):
    """build(level) -> (solid objects, white objects (flame cards, unlit embers: no occlusion, tinted only when
    colours names their material)); occlusion on the solids, tints
    from colours, materials merged (merge: name -> name), LOD join, then saves work/<prop>.blend and exports
    work/<prop>_export.glb."""
    lods = []
    for level in range(levels):
        solids, whites = build(level)
        solid = pl.join(f'solid{level}', solids)
        occlusion = pl.vertex_occlusion(solid, rays=rays[level], distance=u(distance), strength=strength,
                                        floor=False)
        tint(solid, colours)
        merge_materials(solid, merge or {})
        parts = [solid]
        for obj in whites:
            pl.white_colour(obj)
            tint(obj, colours)
            parts.append(obj)
        name = base_name if level == 0 else f'{base_name}_LOD{level}'
        obj = pl.join(name, parts)
        print('LEVEL', level, name, 'tris', pl.triangles(obj), 'mean occlusion', round(occlusion, 3))
        lods.append(obj)
    work = os.path.join(HERE, 'work')
    os.makedirs(work, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(work, f'{prop}.blend'))
    pl.export(lods, os.path.join(work, f'{prop}_export.glb'))
    return lods
