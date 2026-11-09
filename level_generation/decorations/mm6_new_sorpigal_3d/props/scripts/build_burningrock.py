"""Burning rock `brnrock0`: a lumpy blackened basalt mound with glowing lava veins and a flame column rising from its
top, traced from the sprite (126 x 169 units with the flame; the column rises about 0.8 x the rock's height above
it). The rock is a noise-displaced icosphere with a flat underside and a broad, rounded top at three detail levels
(displacement from one 3D noise, so the levels share the shape). Textures (2026-10-09 rework): the CC0 Poly Haven
`dark_rock` scan graded to the sprite's charcoal purple-brown (`Basalt`: lava_rock, normal and roughness) and, as a
thin shell over the upper rock (4 mm out, every LOD) with the same texture coordinates, the unlit, alpha-tested `Lava`
(lava_glow): deep red lava pooled in that scan's own hollows, so the glow sits in the rock's pores and basins.
COLOR_0 on the shell fades the glow from full on the crown to dark red at its lower edge (the engine's emission is
one constant per material, so the glow is an unlit material). The flame is a tall camera-facing card with a lower, mirrored one beside it, playing
the shared flame flipbook (pl.flame_material: openyamm_billboard, openyamm_flipbook, unlit, blended). Writes
work/burningrock_export.glb.
Usage: blender --background --python build_burningrock.py"""
import bpy, bmesh, math, os, sys
import numpy as np
from mathutils import Vector, noise
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import props_lib as pl

pl.reset()
TOTAL = 2.07                       # flame top: 169 units at 81.7 units/m
ROCK_H, ROCK_W = 1.03, 1.75
mats = {
    'Basalt': pl.pbr_material('Basalt', 'lava_rock'),
    'Lava': pl.pbr_material('Lava', 'lava_glow', alpha=True),
    'Fire': pl.flame_material(),
}
GLOW_FROM = 0.3                    # the shell covers the rock above this fraction of its height, in patches low down
UV_TILES = 1.6


def rock_mesh(level):
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=(4, 3, 2)[level], radius=1.0)
    uv = bm.loops.layers.uv.verify()
    for v in bm.verts:
        d = v.co.normalized()
        bump = 1 + 0.2 * noise.noise(d * 1.4 + Vector((3, 1, 7))) + 0.07 * noise.noise(d * 4.2 + Vector((9, 2, 4)))
        z = max(d.z, -0.15)                                    # flat underside, on the ground
        height = math.copysign(abs(z) ** 0.8, z)                # a mound with a broad, rounded top
        floor = 0.15 ** 0.8
        v.co = Vector((d.x * ROCK_W / 2 * bump, d.y * ROCK_W / 2 * 0.86 * bump,
                       (height + floor) / (1 + floor) * ROCK_H * bump))
    # about UV_TILES scan tiles per metre: cylindrical round the sides (whole tiles round, the seam mended per face),
    # planar from above on the crown, so neither pinches
    bm.normal_update()
    around = round(math.pi * ROCK_W * 0.93 * UV_TILES)
    for f in bm.faces:
        if f.normal.z > 0.75:
            for loop in f.loops:
                co = loop.vert.co
                loop[uv].uv = (co.x * UV_TILES + 0.31, co.y * UV_TILES + 0.17)
            continue
        us = [math.atan2(l.vert.co.y, l.vert.co.x) / (2 * math.pi) * around for l in f.loops]
        if max(us) - min(us) > around / 2:
            us = [u + around if u < 0 else u for u in us]
        for loop, u in zip(f.loops, us):
            loop[uv].uv = (u, loop.vert.co.z * UV_TILES + 0.5 * u)    # sheared: the scan's straight cracks
                                                                         # wind round instead of ringing it
    return bm


def rock(level):
    return pl.to_object(f'rock{level}', rock_mesh(level), mats['Basalt'])


def veins(level):
    """The upper rock's faces again, 4 mm out, with the crack texture tiled twice as densely."""
    bm = rock_mesh(level)
    bm.normal_update()
    for v in bm.verts:
        v.co += v.normal * 0.004
    def keep(f):
        c = f.calc_center_median()
        t = (c.z / ROCK_H - GLOW_FROM) / (1 - GLOW_FROM)
        return t > 0 and t + 0.45 * noise.noise(c * 2.2 + Vector((5, 3, 1))) > 0.3
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if not keep(f)], context='FACES')
    return pl.to_object(f'veins{level}', bm, mats['Lava'])


def rock_glow_tint(obj):
    """Redden the rock's COLOR_0 (occlusion) toward its crown, where the sprite's rock is lit red by its lava."""
    me = obj.data
    attr = me.color_attributes['Color']
    for v in me.vertices:
        t = max(0.0, min(1.0, (v.co.z / ROCK_H - 0.35) / 0.55))
        t = t * t * (3 - 2 * t)
        c = attr.data[v.index].color
        attr.data[v.index].color = (c[0], c[1] * (1 - 0.5 * t), c[2] * (1 - 0.55 * t), c[3])


def lava_colour(obj):
    """COLOR_0 of the lava shell: full glow on the crown, fading to dark red toward the shell's lower edge."""
    me = obj.data
    top = max(v.co.z for v in me.vertices)
    colours = []
    for v in me.vertices:
        t = max(0.0, min(1.0, (v.co.z - ROCK_H * GLOW_FROM) / (top - ROCK_H * GLOW_FROM)))
        heat = 0.22 + 0.78 * t * t * (3 - 2 * t)
        colours.append((heat, heat ** 1.6, heat ** 1.6, 1.0))
    attr = me.color_attributes.new('Color', 'FLOAT_COLOR', 'POINT')
    attr.data.foreach_set('color', np.array(colours, np.float32).ravel())
    me.color_attributes.active_color = attr


def flame(level):
    """(centre x, width, top, mirrored) cards rising from just under the rock's crown, so the flame's dense part
    stands above the rock as a column. They show the shared flame's lower 80 % (pl.flame_material; the flame spans
    60 % of a card's width). Blender v runs up; the glTF export flips it."""
    bm = bmesh.new(); uv = bm.loops.layers.uv.verify()
    bottom = ROCK_H * 0.9
    cards = [(0.0, 0.75, TOTAL, False), (0.1, 0.57, bottom + (TOTAL - bottom) * 0.6, True)]
    for cx, w, top, mirrored in cards[:(2, 2, 1)[level]]:
        verts = [bm.verts.new(c) for c in ((cx - w / 2, 0, bottom), (cx + w / 2, 0, bottom), (cx + w / 2, 0, top),
                                           (cx - w / 2, 0, top))]
        f = bm.faces.new(verts)
        for loop, (u, v) in zip(f.loops, ((0, 1), (1, 1), (1, 0), (0, 0))):
            loop[uv].uv = (1 - u if mirrored else u, pl.FLAME_FRAME_TOP * (1 - v))
    return pl.to_object(f'flame{level}', bm, mats['Fire'], smooth=False)


lods = []
for level in range(3):
    solid = rock(level)
    if level == 0:
        print('ROCK TOP', round(max(v.co.z for v in solid.data.vertices), 3), 'of', TOTAL)
    occl = pl.vertex_occlusion(solid, rays=(32, 20, 12)[level], distance=0.4, strength=0.5)
    rock_glow_tint(solid)
    fire = flame(level); pl.white_colour(fire)
    parts = [solid, fire]
    shell = veins(level); lava_colour(shell); parts.append(shell)
    name = 'BurningRock' if level == 0 else f'BurningRock_LOD{level}'
    obj = pl.join(name, parts)
    print('LEVEL', level, name, 'tris', pl.triangles(obj), 'mean occlusion', round(occl, 3))
    lods.append(obj)
work = os.path.join(pl.PROPS, 'work'); os.makedirs(work, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(work, 'burningrock.blend'))
pl.export(lods, os.path.join(work, 'burningrock_export.glb'))
