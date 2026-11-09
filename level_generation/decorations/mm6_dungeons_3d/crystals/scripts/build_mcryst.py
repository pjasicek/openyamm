"""MM6 Memory Crystal `mcryst01` (44 x 65, six frames over 24/16 s), revision 2: a glass ball with a ghostly face,
floating over a flat stand disc. The disc (40 across, 6 high) is what the sprite shows: a thin ellipse with a dark
flat top, a bright rolled rim at the back and front edge and a slightly rounded underside (seen from about 16 degrees
above); it is not a bowl. Scratched dark metal from CC0 Poly Haven `blue_metal_plate` (projected from above),
coloured from the sprite's disc texels through COLOR_0.
The ball is a camera-facing card (openyamm_billboard) with a 3 x 2 flipbook (textures/memorb_basecolor.png, from
make_memory_crystal.py): one still ball (the median of the restored frames, so the upscaled frames do not flicker)
with the native sparkles and eye glints drawn crisply where the six native frames have them, 4 frames per second (the
native 4/16 s per frame), cut out by MASK, with a lavender emission pulsing over the native loop (1.5 s). The face is
the Memory Crystal's identity, so it stays on the card: a ball looks the same from every side, and a 3D sphere with a
projected face would smear it at the sides. The ball floats as in the sprite (43 across, 20 to 63 up).
Writes work/mcryst01_export.glb.
Usage: blender --background --python build_mcryst.py -- mcryst01"""
import math
import os
import sys

import bmesh

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import crystals_lib as cl  # noqa: E402

pl = cl.pl
u = cl.u
BALL_COLUMNS, BALL_ROWS, BALL_FPS = 3, 2, 4.0
BALL_PULSE = [0.5, 24 / 16]
# Disc profile (radius, height) in logical pixels from the centre of the underside out to the rolled rim and back
# over the flat top to the centre.
PROFILE = [(0, 0), (8, 0), (12, 0.3), (15.5, 1.2), (18.2, 2.6), (19.6, 3.8), (20.1, 4.7), (19.9, 5.4), (19.3, 5.85),
           (18.5, 5.9), (17.9, 5.6), (17.4, 5.15), (16.4, 4.95), (12, 4.85), (6, 4.8), (0, 4.8)]
DISC_TILE = 0.8                  # metres of the Poly Haven plate per texture repeat (planar, from above)
BALL_LEFT, BALL_RIGHT, BALL_BOTTOM, BALL_TOP = -21.5, 21.5, 20, 63     # MEMBALL_BOX in logical pixels


def dish_rank(co, name):
    """Rank shift on the disc: the rolled rim catches the light, the flat top is dark, the underside mid."""
    radius, height = math.hypot(co.x, co.y) / u(1), co.z / u(1)
    if height > 5.2 and radius > 17.6:
        return 0.35
    if height > 4.6 and radius < 17.3:
        return -0.25
    return 0.1 * height / 5 - 0.05


def planar_uv(obj):
    """Texture coordinates projected from above (scratches lie across the top as on a real plate)."""
    me = obj.data
    layer = me.uv_layers[0]
    for loop in me.loops:
        co = me.vertices[loop.vertex_index].co
        layer.data[loop.index].uv = (co.x / DISC_TILE + 0.5, co.y / DISC_TILE + 0.5)


def card(mat):
    bm = bmesh.new()
    uv = bm.loops.layers.uv.verify()
    corners = ((u(BALL_LEFT), 0, u(BALL_BOTTOM)), (u(BALL_RIGHT), 0, u(BALL_BOTTOM)),
               (u(BALL_RIGHT), 0, u(BALL_TOP)), (u(BALL_LEFT), 0, u(BALL_TOP)))
    face = bm.faces.new([bm.verts.new(c) for c in corners])
    for loop, (s, t) in zip(face.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
        loop[uv].uv = (s, t)
    return pl.to_object('ball', bm, mat, smooth=False)


def main():
    pl.reset()
    dish_mat = cl.material('Disc', 'memdisc', extras={'openyamm_specular': 1.0})
    ball_mat = cl.material('Ball', 'memorb', alpha=True,
                           extras={'openyamm_billboard': True,
                                   'openyamm_flipbook': [BALL_COLUMNS, BALL_ROWS, BALL_FPS],
                                   'openyamm_pulse': BALL_PULSE, 'openyamm_specular': 0.0})
    # The disc's colours from its own native texels (rows 98-130 of the x2 frame): near-black top, bright rim.
    ramps = {'Disc': cl.native_ramp('mcryst01_p549.png', lambda rgb, rows: rows >= 98)}
    means = {'Disc': cl.texture_mean(dish_mat)}
    lods = []
    for level in range(3):
        profile = PROFILE if level == 0 else [PROFILE[i] for i in (0, 2, 4, 6, 8, 10, 12, 14, 15)] if level == 1 \
            else [PROFILE[i] for i in (0, 3, 6, 8, 11, 15)]
        dish = pl.lathe('disc', [(u(r), u(z)) for r, z in profile], (48, 24, 12)[level], dish_mat)
        planar_uv(dish)
        cl.bright(dish, 1.0, 0.3)
        cl.finish_lod(dish, f'disc{level}', (40, 24, 12)[level], u(10), 0.5, None, dish_rank, floor=True,
                      ramps=ramps, means=means, normal_weight=0.15, occlusion_weight=0.6)
        ball = card(ball_mat)
        pl.white_colour(ball)
        name = 'Mcryst01' if level == 0 else f'Mcryst01_LOD{level}'
        obj = pl.join(name, [dish, ball])
        print('LEVEL', name, 'tris', pl.triangles(obj))
        lods.append(obj)
    cl.save_and_export('mcryst01', lods)


main()
