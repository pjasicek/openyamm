"""Parts shared by the cauldron and the campfire (2026-10-09 texture rework): split logs whose flat split face, turned
out toward the viewer, glows (unlit `fire_glow`: alligatored char with red-orange plates) while their bark side is
charred (`fire_char`, lit PBR), the ember bed, and the vertex colours of the glowing parts. The engine has only a
constant per-material emission, so the glow is an unlit material whose brightness varies through its texture and
COLOR_0 (hottest low in the fire, dimmer up the logs and at their outer feet)."""
import bmesh, math
import numpy as np
from mathutils import Vector
import props_lib as pl

GLOW_TILE = 0.95            # metres of log per glow-texture tile (pine-bark plates a few centimetres long)
CHAR_TILE = 0.45


def materials():
    return {
        'Char': pl.pbr_material('Char', 'fire_char'),
        'Glow': pl.pbr_material('Glow', 'fire_glow'),
        'Stone': pl.pbr_material('Stone', 'fire_stone'),
    }


def split_log(name, foot, tip, r_foot, r_tip, arc, mats, flat=0.25, roll=0.0, seed=0, face=None):
    """A log from foot to tip with a D cross-section: a flat split face `flat` x radius out from the axis, toward the
    horizontal outward direction (or toward `face`, e.g. up for a log lying flat; turned by `roll` radians), and a
    bark arc of `arc` segments behind it. Returns (bark object, glow object); the glow object holds the split face
    and the foot's end grain."""
    foot, tip = Vector(foot), Vector(tip)
    axis = (tip - foot); length = axis.length; axis.normalize()
    radial = Vector(face) if face is not None else Vector((foot.x + tip.x, foot.y + tip.y, 0.0)) / 2
    if radial.length < 1e-4:
        radial = Vector((1, 0, 0))
    out = (radial - axis * radial.dot(axis)).normalized()
    side = axis.cross(out).normalized()
    out, side = (out * math.cos(roll) + side * math.sin(roll)), (side * math.cos(roll) - out * math.sin(roll))
    theta0 = math.acos(flat)
    angles = [theta0 + (2 * math.pi - 2 * theta0) * i / arc for i in range(arc + 1)]

    def ring(centre, r):
        return [centre + (out * math.cos(t) + side * math.sin(t)) * r for t in angles]

    rings = [ring(foot, r_foot), ring(tip, r_tip)]
    arc_len = [0.0]
    for i in range(arc):
        arc_len.append(arc_len[-1] + (angles[i + 1] - angles[i]) * (r_foot + r_tip) / 2)
    phase = (seed * 0.371) % 1.0
    # bark: the arc
    bm = bmesh.new(); uv = bm.loops.layers.uv.verify()
    verts = [[bm.verts.new(p) for p in r] for r in rings]
    for i in range(arc):
        f = bm.faces.new((verts[0][i], verts[0][i + 1], verts[1][i + 1], verts[1][i]))
        for loop, (a, e) in zip(f.loops, ((i, 0), (i + 1, 0), (i + 1, 1), (i, 1))):
            loop[uv].uv = (arc_len[a] / CHAR_TILE + phase, e * length / CHAR_TILE)
    cap = bm.faces.new(verts[1])                            # the charred top end
    for loop in cap.loops:
        d = loop.vert.co - tip
        loop[uv].uv = (d.dot(out) / CHAR_TILE, d.dot(side) / CHAR_TILE)
    bark = pl.to_object(name + '_bark', bm, mats['Char'])
    for p in bark.data.polygons:
        p.use_smooth = p.index < arc
    # glow: the split face (u across, v along the log) and the foot's end grain
    bm = bmesh.new(); uv = bm.loops.layers.uv.verify()
    a0, a1 = rings[0][-1], rings[0][0]            # the face's edges: last and first arc points
    b0, b1 = rings[1][-1], rings[1][0]
    face = [bm.verts.new(p) for p in (a0, a1, b1, b0)]
    f = bm.faces.new(face)
    w_foot, w_tip = (a1 - a0).length, (b1 - b0).length
    for loop, (u, v) in zip(f.loops, ((0, 0), (w_foot, 0), (w_foot / 2 + w_tip / 2, length), (w_foot / 2 - w_tip / 2,
                                                                                           length))):
        loop[uv].uv = (u / GLOW_TILE + phase * 2, v / GLOW_TILE + phase)
    end = [bm.verts.new(p) for p in reversed(rings[0])]
    f = bm.faces.new(end)
    for loop in f.loops:
        d = loop.vert.co - foot
        loop[uv].uv = (d.dot(out) / GLOW_TILE * 2 + phase, d.dot(side) / GLOW_TILE * 2)
    bm.normal_update()
    glow = pl.to_object(name + '_glow', bm, mats['Glow'], smooth=False)
    return bark, glow


def box_uv(bm, uv, tiles_per_metre, seed):
    """Box projection per face (the two axes across its dominant normal axis) so the rock scan is not stretched."""
    bm.normal_update()
    for f in bm.faces:
        n = f.normal
        axis = max(range(3), key=lambda i: abs(n[i]))
        a, b = [(1, 2), (0, 2), (0, 1)][axis]
        for loop in f.loops:
            co = loop.vert.co
            loop[uv].uv = (co[a] * tiles_per_metre + seed * 0.37, co[b] * tiles_per_metre + seed * 0.21)


def ember_bed(name, radius, height, segments, mats, coals=0, seed=0):
    """A low glowing dome with optional heaped coals (icospheres), all `Glow`."""
    parts = [pl.lathe(name, [(0.0, height), (radius * 0.47, height * 0.82), (radius * 0.82, height * 0.36),
                             (radius, 0.0)], segments, mats['Glow'], u_repeat=3.0, v_scale=1 / GLOW_TILE)]
    for k in range(coals):
        a = 2 * math.pi * k / coals + 0.4 + seed
        cb = bmesh.new(); bmesh.ops.create_icosphere(cb, subdivisions=1, radius=1.0)
        cuv = cb.loops.layers.uv.verify()
        r = radius * 0.5
        for v in cb.verts:
            v.co = Vector((v.co.x * radius * 0.22, v.co.y * radius * 0.18, v.co.z * radius * 0.13)) \
                + Vector((math.cos(a) * r, math.sin(a) * r, height * 0.75 - height * 0.18 * (k % 2)))
        for f in cb.faces:
            for loop in f.loops:
                loop[cuv].uv = (loop.vert.co.x / GLOW_TILE * 3 + k * 0.3, loop.vert.co.y / GLOW_TILE * 3)
        parts.append(pl.to_object(f'{name}_coal{k}', cb, mats['Glow']))
    return parts


def glow_colour(obj, top, ring):
    """COLOR_0 of the glowing parts: full at the fire's heart (low, near the axis), down to about a third up the logs
    and at their outer feet, so the split faces read hot at the bottom and cooling to char above."""
    me = obj.data
    colours = []
    for v in me.vertices:
        h = max(0.0, v.co.z) / top
        r = math.hypot(v.co.x, v.co.y) / ring
        heat = 1.0 - 0.45 * min(1.0, h) ** 1.2 - 0.2 * max(0.0, r - 0.55) / 0.45
        heat = min(1.0, max(0.3, heat))
        colours.append((heat, heat * (0.75 + 0.25 * heat), heat * (0.7 + 0.3 * heat), 1.0))
    attr = me.color_attributes.new('Color', 'FLOAT_COLOR', 'POINT')
    attr.data.foreach_set('color', np.array(colours, np.float32).ravel())
    me.color_attributes.active_color = attr


def fire_lit(obj, centre, strength=0.75, stone_low=0.25):
    """Redden the vertex colours where faces look at the fire (and the stones' lower parts: the sprite's red,
    fire-lit undersides) on top of the occlusion already in 'Color'."""
    me = obj.data
    names = [m.name for m in me.materials]
    lit = {i: names[p.material_index] for p in me.polygons for i in p.vertices}
    attr = me.color_attributes['Color']
    for i, name in lit.items():
        v = me.vertices[i]
        f = max(0.0, v.normal.dot((centre - v.co).normalized())) * strength
        if name == 'Stone' and stone_low:
            f = min(1.0, f + 0.55 * max(0.0, 1 - v.co.z / stone_low))
        c = attr.data[i].color
        attr.data[i].color = (c[0], c[1] * (1 - 0.6 * f), c[2] * (1 - 0.8 * f), c[3])
