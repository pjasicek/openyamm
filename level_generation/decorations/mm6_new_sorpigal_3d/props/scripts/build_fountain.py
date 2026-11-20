"""Fountain `sta1a`: marble plinth, urn, stem and onion-domed top (lathe profiles traced from the sprite), gold rings
and eight marble canopy panels with gold rims (the statue, unchanged since revision 1). It stands in the map's own
pool (New Sorpigal: BModel geometry with the engine's water), so the model has no basin: the streams fall into the
map's water and end just under the model's base (END_Z), as the sprite's streams do.

Water (revision 3, 2026-10-09, after the user's in-game review of revision 2):
 - eight outer streams: a sheet runs down each canopy panel from under the dome, spills over the tip and falls in a
   parabola that fans out to the sprite's full stream width (r ~0.86 m at the water; the sprite is 200 x 266 units,
   0.91 m half width at this height); eight inner streams pour from the stem collar between the panels and arc out
   over the urn. Wide, closed, flattened tubes, single-sided, so a stream shows one translucent layer;
 - material Water (textures_water/stream_*, scripts/make_water_textures.py): the dark teal of the map's rendered
   pool water, mostly transparent, glossy, with bright highlight streaks; the normal map mixes OpenMW's water_nm
   (shimmer) with the streaks. Blender v increases up each stream, so the glTF export's flipped v increases down it,
   and openyamm_uv_scroll [0, -WATER_SPEED] moves the texture toward larger glTF v: it flows down.
Primitive order Marble, Gold, Water: the static renderer draws a model's primitives in order, blended ones without
depth writes, so the solid parts come first. Each LOD is built at its own segment count.
Writes work/fountain_export.glb. Usage: blender --background --python build_fountain.py"""
import bpy, bmesh, math, os, sys
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import props_lib as pl

pl.reset()
WATER_SPEED = 1.3                   # stream texture repeats per second (STREAM_V repeats per metre: ~1.5 m/s)
STREAM_V = 0.85
WATER_TEXTURES = os.path.join(pl.PROPS, 'textures_water')


def water_material(name, stem, extras):
    """Blended water material from textures_water/ (alpha from the base colour texture)."""
    props = pl.TEX
    pl.TEX = WATER_TEXTURES
    try:
        return pl.material(name, stem, alpha=True, extras=extras)
    finally:
        pl.TEX = props


mats = {
    'Marble': pl.material('Marble', 'marble'),
    'Gold': pl.material('Gold', 'gold'),
    'Water': water_material('Water', 'stream', {'openyamm_uv_scroll': [0.0, -WATER_SPEED], 'openyamm_specular': 1.0}),
}
# (radius, z) in metres; the statue is 2.42 m tall (native 200 x 266 units), traced from the sprite
PLINTH = [(0.0, 0.0), (0.40, 0.0), (0.40, 0.06), (0.36, 0.08)]
URN = [(0.36, 0.08), (0.27, 0.12), (0.22, 0.18), (0.22, 0.24), (0.33, 0.36), (0.39, 0.56), (0.38, 0.78), (0.31, 0.98),
       (0.21, 1.12), (0.17, 1.17), (0.26, 1.22), (0.31, 1.28), (0.29, 1.31), (0.13, 1.31)]
STEM = [(0.09, 1.30), (0.09, 1.52), (0.14, 1.56), (0.17, 1.58), (0.17, 1.66), (0.11, 1.68)]
DOME = [(0.08, 1.67), (0.19, 1.72), (0.245, 1.83), (0.23, 1.94), (0.16, 2.03), (0.11, 2.07)]
FINIAL = [(0.11, 2.07), (0.135, 2.13), (0.12, 2.20), (0.065, 2.28), (0.028, 2.35), (0.0, 2.42)]
RINGS = [(0.33, 0.09, 0.028), (0.30, 1.29, 0.022), (0.17, 1.62, 0.022), (0.115, 2.07, 0.016)]   # radius, z, tube
ARM_INNER, ARM_TIP = (0.15, 1.66), (0.64, 1.56)       # canopy panels: (radius, z) at the stem and at the tip
END_Z = -0.022                                        # stream ends: just under the base (the map's water)
OUTER_LAND, INNER_LAND = 0.86, 0.62                   # radius of the outer and inner streams at END_Z
GRAVITY = 9.81


def ring(name, radius, z, thickness, segments, sides):
    profile = [(radius + thickness * math.cos(2 * math.pi * k / sides),
                z + thickness * math.sin(2 * math.pi * k / sides)) for k in range(sides + 1)]
    return pl.lathe(name, profile, segments, mats['Gold'], u_repeat=4.0, v_scale=8.0)


def panel_top_z(r):
    """Height of a canopy panel's centre line at radius r."""
    t = (r - ARM_INNER[0]) / (ARM_TIP[0] - ARM_INNER[0])
    return ARM_INNER[1] + (ARM_TIP[1] - ARM_INNER[1]) * t


def tube_along(name, path, widths, depths, sides, side_axis, wobble=0.0, phase=0.0):
    """Closed flattened tube along path (top first): width along side_axis (horizontal, across the stream), depth
    along the path normal. u runs around, v = STREAM_V x arc length from the bottom (increasing upward). Ends capped."""
    bm = bmesh.new(); uv = bm.loops.layers.uv.verify()
    lengths = [0.0]
    for a, b in zip(path, path[1:]):
        lengths.append(lengths[-1] + (b - a).length)
    total = lengths[-1]
    rows = []
    for i, p in enumerate(path):
        tangent = (path[min(i + 1, len(path) - 1)] - path[max(i - 1, 0)]).normalized()
        across = (side_axis - tangent * side_axis.dot(tangent)).normalized()
        normal = tangent.cross(across).normalized()
        fall = lengths[i] / total
        centre = p + across * (wobble * fall * math.sin(fall * 9.0 + phase))
        ring_vs = [bm.verts.new(centre + across * math.cos(2 * math.pi * k / sides) * widths[i] / 2
                                + normal * math.sin(2 * math.pi * k / sides) * depths[i] / 2) for k in range(sides)]
        rows.append((ring_vs, (total - lengths[i]) * STREAM_V))
    for (upper, va), (lower, vb) in zip(rows, rows[1:]):
        for k in range(sides):
            k2 = (k + 1) % sides
            f = bm.faces.new((upper[k], upper[k2], lower[k2], lower[k]))
            for loop, (column, v) in zip(f.loops, ((k, va), (k + 1, va), (k + 1, vb), (k, vb))):
                loop[uv].uv = (column / sides, v)
    for ring_vs, v in (rows[0], rows[-1]):
        f = bm.faces.new(ring_vs)
        for loop in f.loops:
            loop[uv].uv = (0.5, v)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return pl.to_object(name, bm, mats['Water'])


def fall_path(start, direction, speed, land_r, samples):
    """Parabola from start leaving along direction (radial/vertical unit vector in the stream's plane) at speed,
    sampled down to the water; the horizontal speed is tuned so the stream lands at radius land_r."""
    radial = Vector((start.x, start.y, 0)).normalized()
    r0 = Vector((start.x, start.y, 0)).length
    down = -direction.z * speed
    drop = start.z - END_Z
    t_land = (-down + math.sqrt(down * down + 2 * GRAVITY * drop)) / GRAVITY
    vr = (land_r - r0) / t_land
    points = []
    for i in range(1, samples + 1):
        t = t_land * (i / samples) ** 1.6                  # dense near the lip, where the arc bends
        r = r0 + vr * t
        z = start.z - down * t - 0.5 * GRAVITY * t * t
        points.append(radial * r + Vector((0, 0, z)))
    return points


def outer_stream(k, level):
    a = 2 * math.pi * k / 8 + math.pi / 8
    radial = Vector((math.cos(a), math.sin(a), 0)); across = Vector((-radial.y, radial.x, 0))
    sheet = (5, 3, 2)[level]
    path = []
    for i in range(sheet + 1):                           # down the panel from under the dome to the tip
        r = 0.21 + (ARM_TIP[0] + 0.01 - 0.21) * i / sheet
        path.append(radial * r + Vector((0, 0, panel_top_z(r) + 0.045)))
    slope = (Vector((ARM_TIP[0], 0, ARM_TIP[1])) - Vector((ARM_INNER[0], 0, ARM_INNER[1]))).normalized()
    path += fall_path(path[-1], slope, 0.25, OUTER_LAND + 0.02 * math.sin(k * 2.3), (14, 7, 4)[level])
    width_top = 0.25 + 0.05 * (math.sin(k * 2.9) * 0.5 + 0.5)          # streams differ, as on the sprite
    widths, depths = [], []
    for i in range(len(path)):
        if i <= sheet:
            s = i / sheet
            widths.append(0.09 + (width_top - 0.09) * s); depths.append(0.022 + 0.018 * s)
        else:
            s = (i - sheet) / (len(path) - 1 - sheet)
            widths.append(width_top * (1 - 0.12 * s)); depths.append(0.04 + 0.04 * s)
    sides = (6, 4, 3)[level]
    return tube_along(f'outer{k}', path, widths, depths, sides, across, wobble=0.015, phase=k * 1.7)


def inner_stream(k, level):
    b = 2 * math.pi * k / 8 + math.pi / 4                # between the panels
    radial = Vector((math.cos(b), math.sin(b), 0)); across = Vector((-radial.y, radial.x, 0))
    start = radial * 0.18 + Vector((0, 0, 1.60))
    path = [start] + fall_path(start, Vector((1, 0, 0)), 0.0, INNER_LAND + 0.02 * math.sin(k * 1.9),
                               (12, 6)[level])
    widths = [0.07] + [0.13 * (1 - 0.15 * i / (len(path) - 1)) for i in range(1, len(path))]
    depths = [0.03] + [0.045 + 0.02 * i / (len(path) - 1) for i in range(1, len(path))]
    return tube_along(f'inner{k}', path, widths, depths, (5, 3)[level], across, wobble=0.01, phase=k * 2.3 + 1.0)


def build(level):
    seg = (32, 16, 8)[level]
    parts = [pl.lathe('plinth', PLINTH, seg, mats['Marble'], u_repeat=3, cap_top=False),
             pl.lathe('urn', URN if level < 2 else URN[::2] + [URN[-1]], seg, mats['Marble'], u_repeat=3, v_scale=1.5),
             pl.lathe('stem', STEM, max(seg // 2, 6), mats['Marble'], u_repeat=2, v_scale=2),
             pl.lathe('dome', DOME, seg, mats['Marble'], u_repeat=3, v_scale=2),
             pl.lathe('finial', FINIAL, max(seg // 2, 6), mats['Marble'], u_repeat=2, v_scale=3)]
    if level < 2:
        for k, (r, z, t) in enumerate(RINGS):
            parts.append(ring(f'ring{k}', r, z, t, seg, (6, 4)[level]))
    for k in range(8):                                       # canopy: marble panels with gold rims, drooping out
        a = 2 * math.pi * k / 8 + math.pi / 8
        radial = Vector((math.cos(a), math.sin(a), 0)); side = Vector((-radial.y, radial.x, 0))
        inner = radial * ARM_INNER[0] + Vector((0, 0, ARM_INNER[1]))
        tip = radial * ARM_TIP[0] + Vector((0, 0, ARM_TIP[1]))
        bm = bmesh.new(); uvs = bm.loops.layers.uv.verify()
        w_in, w_out, thick = 0.05, 0.13, 0.035
        corners = [inner - side * w_in, inner + side * w_in, tip + side * w_out, tip - side * w_out]
        top = [bm.verts.new(c + Vector((0, 0, thick / 2))) for c in corners]
        bottom = [bm.verts.new(c - Vector((0, 0, thick / 2))) for c in corners]
        faces = [top, list(reversed(bottom))] + [[top[i], bottom[i], bottom[(i + 1) % 4], top[(i + 1) % 4]][::-1]
                                                  for i in range(4)]
        for face in faces:
            f = bm.faces.new(face)
            for loop in f.loops:
                loop[uvs].uv = (loop.vert.co.dot(side) * 3 + 0.5, loop.vert.co.dot(radial) * 3)
        parts.append(pl.to_object(f'panel{k}', bm, mats['Marble'], smooth=False))
        if level < 2:
            parts.append(pl.tube(f'rim{k}', tip - side * w_out + Vector((0, 0, 0.02)),
                                 tip + side * w_out + Vector((0, 0, 0.02)), 0.014, 0.014, 4, mats['Gold'], v_scale=4))
            parts.append(pl.tube(f'rib{k}', inner + Vector((0, 0, 0.022)), tip + Vector((0, 0, 0.022)), 0.012, 0.012,
                                 4, mats['Gold'], v_scale=4))
    solid = pl.join(f'solid{level}', parts)
    streams = [outer_stream(k, level) for k in range(8)]
    if level < 2:
        streams += [inner_stream(k, level) for k in range(8)]
    water = pl.join(f'water{level}', streams)
    return solid, water


lods = []
for level in range(3):
    solid, water = build(level)
    occl = pl.vertex_occlusion(solid, rays=(40, 24, 12)[level], distance=0.4, strength=0.6)
    pl.white_colour(water)
    name = 'Fountain' if level == 0 else f'Fountain_LOD{level}'
    obj = pl.join(name, [solid, water])
    print('LEVEL', level, name, 'tris', pl.triangles(obj), 'mean occlusion', round(occl, 3),
          'materials', [m.name for m in obj.data.materials])
    lods.append(obj)
work = os.path.join(pl.PROPS, 'work')
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(work, 'fountain.blend'))
pl.export(lods, os.path.join(work, 'fountain_export.glb'))
