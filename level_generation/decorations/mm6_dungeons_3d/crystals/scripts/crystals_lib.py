"""Shared Blender helpers for the crystal batch: textures from this batch's textures/ first (then the project's and the
outdoor props'), faceted crystal prisms and blades, native-sprite silhouettes, COLOR_0 tints toward measured native
colours and the LOD export. Sprite coordinates are logical pixels (x from the sprite's left edge, z up from its
bottom row); the sprite's horizontal centre is the model origin."""
import math
import os
import random
import sys
import zlib

import bmesh
import bpy
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, '..', 'scripts'))
import dungeon_lib as dl  # noqa: E402

pl = dl.pl
u = dl.units
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
X2 = os.path.join(REPO, 'assets_dev', 'engine', 'decorations_x2')
TEXTURES = os.path.join(HERE, 'textures')
WORK = os.path.join(HERE, 'work')


def material(name, texture, alpha=False, extras=None):
    """Material from textures/<texture>_* of this batch when present, else dungeon_lib's lookup."""
    if os.path.exists(os.path.join(TEXTURES, f'{texture}_basecolor.png')):
        pl.TEX = TEXTURES
        try:
            return pl.material(name, texture, alpha=alpha, extras=extras)
        finally:
            pl.TEX = dl.PROPS_TEXTURES
    return dl.material(name, texture, alpha=alpha, extras=extras)


def linear(srgb):
    c = np.asarray(srgb, np.float64) / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def texture_mean(mat):
    """Mean linear colour of a material's base colour texture (opaque texels)."""
    image = next(n for n in mat.node_tree.nodes if n.type == 'TEX_IMAGE').image
    pixels = np.empty(len(image.pixels), np.float32)
    image.pixels.foreach_get(pixels)
    pixels = pixels.reshape(-1, 4)
    pixels = pixels[pixels[:, 3] > 0.5]
    return linear(pixels[:, :3] * 255.0).mean(0)


def tint_for(mat, target_srgb, gain=1.0):
    """Linear COLOR_0 multiplier taking the texture mean to the native sRGB colour (times gain)."""
    return tuple(float(v) for v in linear(target_srgb) * gain / texture_mean(mat))


def apply_tints(obj, tints, factor=None, normalise=True):
    """Colour = occlusion x tints[material] x factor(co, material name) x the 'bright' attribute; with normalise the
    factors times the occlusion average one per material, so the material's mean stays at its measured native colour
    (values clamp at one)."""
    me = obj.data
    names = [m.name for m in me.materials]
    owner = {}
    for polygon in me.polygons:
        for index in polygon.vertices:
            owner[index] = names[polygon.material_index]
    bright = me.attributes['bright'].data if 'bright' in me.attributes else None
    factors = {}
    for index, name in owner.items():
        f = factor(me.vertices[index].co, name) if factor else 1.0
        factors[index] = f * (bright[index].value if bright is not None else 1.0)
    attr = me.color_attributes['Color']
    means = {}
    for name in set(owner.values()):
        members = [i for i, n in owner.items() if n == name]
        # The factors and the occlusion together average one, so the material displays its native mean colour
        # (the native mean already holds the sprite's painted crevices).
        means[name] = (sum(factors[i] * attr.data[i].color[0] for i in members) / len(members)) if normalise else 1.0
    for index, name in owner.items():
        t = tints.get(name)
        if t is None:
            continue
        f = factors[index] / means[name]
        c = attr.data[index].color
        attr.data[index].color = tuple(min(1.0, c[k] * t[k] * f) for k in range(3)) + (c[3],)


def bright(obj, value=1.0, rank=0.5):
    """Give a part the 'bright' and 'rank' attributes (every joined part needs them, or join fills zeros)."""
    for layer, v in (('bright', value), ('rank', rank)):
        if layer not in obj.data.attributes:
            attr = obj.data.attributes.new(layer, 'FLOAT', 'POINT')
            attr.data.foreach_set('value', [v] * len(obj.data.vertices))
    return obj


def native_ramp(file, select=None, bins=24, saturate=1.0):
    """Quantile ramp of a native sprite's colours: the opaque texels (optionally those `select(rgb, rows)` keeps, rows
    counted from the top) sorted by luminance and split into equal-count bins, as linear RGB from darkest to
    brightest. Ranks spread evenly over 0..1 then reproduce the sprite's colour distribution, not only its mean.
    saturate > 1 pushes each bin away from its grey (linear luminance), offsetting the white sheen of the gloss."""
    image = bpy.data.images.load(os.path.join(X2, file))
    w, h = image.size
    pixels = np.empty(w * h * 4, np.float32)
    image.pixels.foreach_get(pixels)
    bpy.data.images.remove(image)
    pixels = pixels.reshape(h, w, 4)[::-1]
    rows = np.repeat(np.arange(h)[:, None], w, axis=1)
    keep = pixels[..., 3] > 0.5
    rgb, rows = pixels[..., :3][keep] * 255.0, rows[keep]
    if select is not None:
        mask = select(rgb, rows)
        rgb = rgb[mask]
    lin = linear(rgb)
    order = np.argsort(lin @ np.array([0.2126, 0.7152, 0.0722]))
    ramp = []
    for chunk in np.array_split(lin[order], bins):
        colour = chunk.mean(0)
        grey = colour @ np.array([0.2126, 0.7152, 0.0722])
        ramp.append(np.clip(grey + (colour - grey) * saturate, 0.0, 1.0))
    return ramp


def ramp_colour(ramp, rank):
    x = max(0.0, min(1.0, rank)) * (len(ramp) - 1)
    i = min(int(x), len(ramp) - 2)
    f = x - i
    return ramp[i] * (1 - f) + ramp[i + 1] * f


def apply_ramps(obj, ramps, means, shift=None, normal_weight=0.3, occlusion_weight=0.8, gain=None):
    """Colour each vertex from its material's native ramp: rank = the 'rank' attribute (facet and crystal) + shift(co,
    material) + normal_weight x normal z (faces toward the light above are bright) - occlusion_weight x occlusion,
    COLOR_0 = ramp colour x gain / mean texture colour (clamped at one)."""
    me = obj.data
    names = [m.name for m in me.materials]
    owner = {}
    for polygon in me.polygons:
        for index in polygon.vertices:
            owner[index] = names[polygon.material_index]
    rank = me.attributes['rank'].data
    attr = me.color_attributes['Color']
    for index, name in owner.items():
        if name not in ramps:
            continue
        v = me.vertices[index]
        occluded = 1.0 - attr.data[index].color[0]
        r = rank[index].value + (shift(v.co, name) if shift else 0.0) + normal_weight * v.normal.z \
            - occlusion_weight * occluded
        colour = ramp_colour(ramps[name], r) * (gain or {}).get(name, 1.0) / means[name]
        attr.data[index].color = tuple(float(min(1.0, c)) for c in colour) + (attr.data[index].color[3],)


def clip_ground(obj):
    """Cut everything below the ground plane z = 0 away (crystal roots and spire feet sink into the floor)."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
    bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0, 0, 0), plane_no=(0, 0, 1), clear_inner=True)
    bm.to_mesh(obj.data)
    bm.free()
    return obj


def frame(direction):
    axis = Vector(direction).normalized()
    side = axis.cross(Vector((0, 0, 1)))
    if side.length < 1e-4:
        side = Vector((1, 0, 0))
    side.normalize()
    return axis, side, side.cross(axis).normalized()


def prism(name, base, tip, radius, mat, sides=6, tip_fraction=1.2, chamfer=0.0, mid=False, flat=1.0, taper=0.92,
          roll=0.0, brightness=1.0, cap_base=False, facets=0.0):
    """Faceted crystal from base to tip: a `sides`-gon prism (each edge optionally chamfered, flat < 1 squashes it into
    a blade) ending in a pyramid tip `tip_fraction` x radius long. u runs around the prism, v along its length.
    Writes the float vertex attributes 'bright' = brightness (per-crystal variation; facets > 0 splits the faces and
    gives every facet strip its own brightness) and 'rank' (a facet's place on the native colour ramp: chamfered edges
    near the top, dark and lit sides, as the painted translucent crystals show; shifted by the crystal's brightness)."""
    base, tip = Vector(base), Vector(tip)
    axis, side, other = frame(tip - base)
    length = (tip - base).length
    tip_length = min(radius * tip_fraction, length * 0.45)
    shoulder = tip - axis * tip_length
    # roll turns the cross-section (and its flat axis) about the crystal's axis.
    side, other = side * math.cos(roll) + other * math.sin(roll), other * math.cos(roll) - side * math.sin(roll)
    angles = []
    for s in range(sides):
        a = 2 * math.pi * s / sides
        if chamfer > 0:
            half = math.pi / sides * chamfer
            angles += [a - half, a + half]
        else:
            angles.append(a)

    def ring(centre, r):
        return [centre + (side * math.cos(a) * flat + other * math.sin(a)) * r for a in angles]

    rings = [(base, ring(base, radius), 0.0)]
    if mid:
        middle = base.lerp(shoulder, 0.55)
        rings.append((middle, ring(middle, radius * (1 + taper) / 2), (middle - base).length))
    rings.append((shoulder, ring(shoulder, radius * taper), (shoulder - base).length))
    bm = bmesh.new()
    uv = bm.loops.layers.uv.verify()
    verts = [[bm.verts.new(p) for p in points] for _, points, _ in rings]
    apex = bm.verts.new(tip)
    n = len(angles)
    scale = 1.0 / max(length, 1e-6)
    for i in range(len(rings) - 1):
        for s in range(n):
            s2 = (s + 1) % n
            f = bm.faces.new((verts[i][s], verts[i][s2], verts[i + 1][s2], verts[i + 1][s]))
            for loop, (a, b) in zip(f.loops, ((s, i), (s + 1, i), (s + 1, i + 1), (s, i + 1))):
                loop[uv].uv = (a / n, rings[b][2] * scale * 2.0)
    for s in range(n):
        s2 = (s + 1) % n
        f = bm.faces.new((verts[-1][s], verts[-1][s2], apex))
        for loop, (a, b) in zip(f.loops, ((s / n, rings[-1][2] * scale * 2), (s2 / n, rings[-1][2] * scale * 2),
                                          ((s + 0.5) / n, 2.0))):
            loop[uv].uv = (a, b)
    if cap_base:
        f = bm.faces.new(list(reversed(verts[0])))
        for loop in f.loops:
            loop[uv].uv = (0.5, 0.0)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.faces.index_update()
    rng = random.Random(zlib.crc32(name.encode()) + int(length * 1e5))
    def side_rank(s):
        if chamfer > 0 and s % 2 == 0:
            return rng.uniform(0.85, 1.0)                 # a bright edge
        if rng.random() < 0.5:
            return rng.uniform(0.0, 0.3)                  # a dark face
        return rng.uniform(0.4, 0.8)                      # a lit face

    def side_factor(s):
        if chamfer > 0 and s % 2 == 0:
            return 1 + facets * 0.9                       # a bright chamfered edge
        if rng.random() < 0.5:
            return 1 - facets * rng.uniform(0.45, 0.75)   # a dark side seen through the crystal
        return 1 + facets * rng.uniform(0.15, 0.8)        # a lit side

    strip = [side_factor(s) for s in range(n)]
    tips = [1 + facets * rng.uniform(-0.5, 1.0) for _ in range(n)]
    strip_rank = [side_rank(s) for s in range(n)]
    tip_rank = [rng.uniform(0.25, 1.0) for _ in range(n)]
    face_factor = []
    face_rank = []
    for f in bm.faces:
        if len(f.verts) == 4:
            face_factor.append(strip[(f.index % n)])
            face_rank.append(strip_rank[f.index % n])
        elif len(f.verts) == 3:
            face_factor.append(tips[(f.index - (len(rings) - 1) * n) % n])
            face_rank.append(tip_rank[(f.index - (len(rings) - 1) * n) % n])
        else:
            face_factor.append(1.0)
            face_rank.append(0.5)
    if facets > 0:
        bmesh.ops.split_edges(bm, edges=bm.edges[:])
    bm.verts.index_update()
    values = [brightness] * len(bm.verts)
    ranks = [0.5] * len(bm.verts)
    for f, factor, r in zip(bm.faces, face_factor, face_rank):
        for v in f.verts:
            values[v.index] = brightness * max(0.15, factor)
            # An inner glint along the lit faces, brightest at mid length (the sprite's light streaks).
            along = (v.co - base).dot(axis) / max(length, 1e-6)
            glint = 0.3 * max(0.0, 1 - abs(along - 0.5) / 0.3) if r > 0.35 else 0.0
            ranks[v.index] = r + glint + 0.6 * (brightness - 1.0)
    obj = pl.to_object(name, bm, mat, smooth=False)
    attr = obj.data.attributes.new('bright', 'FLOAT', 'POINT')
    attr.data.foreach_set('value', values)
    attr = obj.data.attributes.new('rank', 'FLOAT', 'POINT')
    attr.data.foreach_set('value', ranks)
    return obj


def apply_transforms(objects):
    for obj in objects:
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)


def sprite_alpha(file):
    """Native x2 sprite alpha as a boolean array, row 0 at the top."""
    image = bpy.data.images.load(os.path.join(X2, file))
    w, h = image.size
    pixels = np.empty(w * h * 4, np.float32)
    image.pixels.foreach_get(pixels)
    alpha = pixels.reshape(h, w, 4)[::-1, :, 3] > 0.5     # Blender stores rows bottom-up
    bpy.data.images.remove(image)
    return alpha


def silhouette(alpha, window, h0, h1, step):
    """[(height, centre x, half width)] in logical pixels, sprite x measured from the sprite centre, sampled every
    `step` logical rows from h0 to h1 within the x2 column window [x0, x1)."""
    rows, cols = alpha.shape
    x0, x1 = window
    out = []
    h = h0
    while h <= h1:
        row = rows - 1 - min(rows - 1, int(round(h * 2)))
        xs = np.nonzero(alpha[row, x0:x1])[0]
        if len(xs):
            left, right = xs[0] + x0, xs[-1] + x0 + 1
            out.append((h, ((left + right) / 2 - cols / 2) / 2, (right - left) / 4))
        h += step
    return out


def finish_lod(obj, name, rays, distance, strength, tints, factor=None, floor=True, normalise=True, ramps=None,
               means=None, gain=None, normal_weight=0.3, occlusion_weight=0.8):
    """Occlusion, then COLOR_0 from the native ramps (factor = rank shift) when given, else from the tints."""
    occlusion = pl.vertex_occlusion(obj, rays=rays, distance=distance, strength=strength, floor=floor)
    if ramps:
        apply_ramps(obj, ramps, means, factor, normal_weight, occlusion_weight, gain)
    else:
        apply_tints(obj, tints, factor, normalise)
    obj.name = name
    obj.data.name = name
    print('LEVEL', name, 'tris', pl.triangles(obj), 'mean occlusion', round(occlusion, 3))
    return obj


def save_and_export(prop, lods):
    os.makedirs(WORK, exist_ok=True)
    for obj in lods:
        for layer in ('bright', 'rank'):
            if layer in obj.data.attributes:
                obj.data.attributes.remove(obj.data.attributes[layer])
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, f'{prop}.blend'))
    pl.export(lods, os.path.join(WORK, f'{prop}_export.glb'))
