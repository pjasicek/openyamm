#!/usr/bin/env python3
"""Paint a shared plant atlas: textures/<atlas>_basecolor.png (RGBA, alpha = cut-out), <atlas>_normal.png (OpenGL)
and <atlas>_layout.json (cell rectangles in image-space UV, v down, and per-cell outline profiles for fitting leaf
strips). Original procedural work (numpy), no external images. Atlases:
  flowers  2048²: flower heads seen face on (radial, mapped onto lathed heads), the flower plants' leaves, stems and
           the shrub sprays (plant16-27, 28-33, 42).
  leafy    2048²: leaves, fern frond, grass and sword blades, corn leaf, lily pads, the anthurium, twig tangles
           (plant01-15, 34, 37, 38, 43, 46, 48, 49, 56).
Cells sit on a 128-px grid. Each painter is seeded by its cell name, so changing one cell leaves the others intact.
Usage: make_atlas.py flowers|leafy"""
import json, math, os, sys, zlib
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paint_lib import (Canvas, shape_ellipse, shape_ovate, shape_heart, shape_sword, shape_blade, shape_petal,
                       leaf_style, petal_style, flat_style, stem_style, lin, mix, smoothstep, SS)

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX = os.path.join(HERE, 'textures')
G = 128
C = lambda *rgb: [c / 255.0 for c in rgb]          # sRGB 0-255 -> 0-1 (painted in sRGB)


def jit(rng, rgb, a=0.06):
    return [min(max(c * (1 + rng.uniform(-a, a)), 0), 1) for c in rgb]


# =============================================================== flower heads (radial: centre = flower centre)
def radial_petals(cv, n, length, shape, style, turn=0.0, jitter=0.06, width=None, bend=0.0, z=0.0, rnd_bright=0.08):
    cx, cy = cv.w / 2, cv.h / 2
    for k in range(n):
        a = turn + 2 * math.pi * k / n + cv.rng.normal(0, jitter)
        L = length * cv.rng.uniform(0.92, 1.0)
        cv.leaf((cx, cy), a, L, width or L * 0.6, shape, style, bend=bend * cv.rng.uniform(-1, 1), segs=14,
                rnd={'bright': 1 + cv.rng.uniform(-rnd_bright, rnd_bright)}, z=z)


def centre_disc(cv, radius, inner, outer, dots=None, n_dots=0, dot_r=2.0, ring=(0.0, 1.0), z=0.5, dome=0.4):
    cx, cy = cv.w / 2, cv.h / 2
    inner, outer = lin(inner), lin(outer)

    def col(r, x, y, c):
        return mix(inner, outer, smoothstep(0, 1, r)) * (1 + 0.1 * c.hi[y, x])[:, None], dome * (1 - r * r)
    cv.disc((cx, cy), radius, col, z=z)
    for k in range(n_dots):
        rr = radius * math.sqrt(cv.rng.uniform(ring[0] ** 2, ring[1] ** 2)); a = cv.rng.uniform(0, 2 * math.pi)
        d = lin(jit(cv.rng, dots, 0.1))
        cv.disc((cx + math.cos(a) * rr, cy + math.sin(a) * rr), dot_r * cv.rng.uniform(0.7, 1.2),
                lambda r, x, y, c, d=d: (np.repeat(d[None], len(r), 0) * (1.15 - 0.4 * r)[:, None], 0.3 * (1 - r)),
                z=z + 0.3)


def head_lotus(cv):      # plant16: magenta cup flower, pointed petals, yellow stamens
    R = cv.w * 0.48
    st = petal_style(C(120, 44, 83), C(190, 82, 150), C(232, 150, 205), edge=C(245, 195, 225), edge_w=0.12,
                     veins=C(150, 50, 110), vein_n=9, vein_amt=0.35, cup=0.5)
    radial_petals(cv, 6, R, shape_ovate(0.5, 0.8), st, turn=0.3, width=R * 0.62)
    st2 = petal_style(C(110, 36, 76), C(178, 72, 138), C(222, 135, 195), edge=C(240, 180, 215), edge_w=0.1,
                      veins=C(140, 45, 100), vein_n=9, vein_amt=0.35, cup=0.5)
    radial_petals(cv, 5, R * 0.82, shape_ovate(0.5, 0.8), st2, turn=0.9, width=R * 0.55, z=0.3)
    centre_disc(cv, R * 0.16, C(200, 150, 30), C(150, 90, 40), dots=C(250, 210, 60), n_dots=26, dot_r=3.0, z=0.8)


def head_tulip(cv):      # plant17: red flame, yellow-orange margins (goblet, mapped radially)
    R = cv.w * 0.48
    st = petal_style(C(110, 40, 8), C(215, 120, 18), C(235, 160, 30), edge=C(248, 210, 80), edge_w=0.32,
                     stripe=C(185, 45, 8), stripe_w=0.32, veins=C(150, 50, 8), vein_n=11, vein_amt=0.25, cup=0.6,
                     inner_t=0.3, outer_t=0.8)
    radial_petals(cv, 6, R, shape_petal(0.62, 0.45, 0.5, 0.55), st, turn=0.0, width=R * 0.85)
    st2 = petal_style(C(110, 40, 8), C(205, 105, 15), C(230, 150, 28), edge=C(248, 210, 80), edge_w=0.35,
                      stripe=C(180, 42, 8), stripe_w=0.32, cup=0.6, inner_t=0.3)
    radial_petals(cv, 3, R * 0.75, shape_petal(0.6, 0.45, 0.5, 0.5), st2, turn=0.5, width=R * 0.8, z=0.3)
    centre_disc(cv, R * 0.12, C(40, 25, 8), C(70, 45, 10), dots=C(30, 20, 10), n_dots=6, dot_r=4, z=0.6)


def head_startulip(cv):  # plant19: white star tulip, yellow centre
    R = cv.w * 0.48
    st = petal_style(C(205, 170, 30), C(225, 232, 200), C(245, 248, 230), veins=C(200, 210, 175), vein_n=7,
                     vein_amt=0.4, inner_t=0.3, outer_t=0.7, cup=0.45, dark_edge=0.18)
    radial_petals(cv, 3, R, shape_ovate(0.45, 1.1), st, turn=0.0, width=R * 0.55)
    radial_petals(cv, 3, R * 0.93, shape_ovate(0.45, 1.1), st, turn=math.pi / 3, width=R * 0.55, z=0.2)
    centre_disc(cv, R * 0.3, C(150, 120, 20), C(225, 195, 40), dots=C(60, 45, 15), n_dots=10, dot_r=4,
                ring=(0.3, 0.8), z=0.6)


def head_petunia(cv):    # plant20: magenta, five fused lobes, dark throat
    R = cv.w * 0.48
    st = petal_style(C(110, 15, 55), C(190, 45, 115), C(215, 75, 140), edge=C(235, 120, 175), edge_w=0.08,
                     veins=C(130, 20, 70), vein_n=8, vein_amt=0.4, inner_t=0.35, outer_t=0.8, cup=0.35)
    radial_petals(cv, 5, R, shape_petal(0.65, 0.6, 0.4, 0.9), st, turn=0.2, width=R * 1.05)
    centre_disc(cv, R * 0.13, C(70, 10, 35), C(110, 20, 60), dots=C(240, 230, 200), n_dots=4, dot_r=2.5, z=0.5)


def head_trumpet(cv):    # plant21: salmon-cream trumpet with red-brown throat veins
    R = cv.w * 0.48
    st = petal_style(C(150, 60, 35), C(215, 140, 105), C(245, 215, 180), edge=C(252, 238, 210), edge_w=0.18,
                     veins=C(170, 75, 45), vein_n=7, vein_amt=0.55, inner_t=0.45, outer_t=0.85, cup=0.4)
    radial_petals(cv, 5, R, shape_petal(0.68, 0.6, 0.4, 0.95), st, turn=0.4, width=R * 1.05)
    centre_disc(cv, R * 0.14, C(130, 90, 30), C(160, 70, 40), dots=C(235, 210, 120), n_dots=8, dot_r=2.5, z=0.5)


def head_florets(cv):    # plant22: dome of small orange florets (butterfly weed)
    cx, cy = cv.w / 2, cv.h / 2; R = cv.w * 0.47

    def base(r, x, y, c):
        return mix(lin(C(185, 62, 8)), lin(C(140, 40, 6)), r)[...] * (1 + 0.15 * c.mid[y, x])[:, None], 0.3 * (1 - r)
    cv.disc((cx, cy), R * 0.93, base)
    for k in range(70):
        rr = R * 0.86 * math.sqrt(cv.rng.uniform()); a = cv.rng.uniform(0, 2 * math.pi)
        fx, fy = cx + math.cos(a) * rr, cy + math.sin(a) * rr
        size = cv.rng.uniform(9, 13)
        lit = cv.rng.uniform(0.85, 1.15)
        st = petal_style(C(150, 35, 5), jit(cv.rng, C(240 * lit, 105 * lit, 15), 0.05), jit(cv.rng, C(250, 145 * lit, 35)),
                         cup=0.3, inner_t=0.3, dark_edge=0.25)
        t0 = cv.rng.uniform(0, 2 * math.pi)
        for p in range(5):
            cv.leaf((fx, fy), t0 + p * 2 * math.pi / 5, size, size * 0.8, shape_petal(0.6, 0.4, 0.5, 0.8), st, segs=6,
                    z=0.5)


def head_lily(cv):       # plant23: golden six-petal lily, orange throat
    R = cv.w * 0.48
    st = petal_style(C(185, 95, 15), C(228, 168, 38), C(240, 205, 85), edge=C(250, 228, 135), edge_w=0.12,
                     veins=C(205, 130, 25), vein_n=6, vein_amt=0.3, stripe=C(215, 140, 25), stripe_w=0.1,
                     inner_t=0.35, outer_t=0.8, cup=0.45)
    radial_petals(cv, 3, R, shape_ovate(0.45, 0.9), st, turn=0.1, width=R * 0.62, bend=0.12)
    radial_petals(cv, 3, R * 0.95, shape_ovate(0.45, 0.9), st, turn=0.1 + math.pi / 3, width=R * 0.6, bend=0.12, z=0.2)
    centre_disc(cv, R * 0.1, C(160, 90, 15), C(190, 120, 20), dots=C(120, 60, 10), n_dots=6, dot_r=2.5, z=0.5)


def head_daisy(cv):      # plant24: orange gazania-like daisy
    R = cv.w * 0.48
    st = petal_style(C(190, 100, 15), C(235, 165, 35), C(248, 205, 75), veins=C(215, 135, 25), vein_n=4,
                     vein_amt=0.3, cup=0.25, inner_t=0.3)
    radial_petals(cv, 14, R, shape_petal(0.55, 0.5, 0.6, 0.7), st, turn=0.0, width=R * 0.3, jitter=0.04)
    radial_petals(cv, 12, R * 0.8, shape_petal(0.55, 0.5, 0.6, 0.7), st, turn=0.13, width=R * 0.28, z=0.2)
    centre_disc(cv, R * 0.22, C(150, 80, 15), C(210, 130, 30), dots=C(110, 55, 10), n_dots=25, dot_r=2.2, z=0.5)


def head_impatiens(cv):  # plant25: pale lilac five-petal flower, magenta eye
    R = cv.w * 0.48
    st = petal_style(C(180, 60, 140), C(215, 165, 220), C(235, 210, 238), veins=C(200, 130, 200), vein_n=6,
                     vein_amt=0.3, stripe=C(195, 85, 160), stripe_w=0.12, inner_t=0.3, outer_t=0.75, cup=0.35)
    radial_petals(cv, 5, R, shape_petal(0.65, 0.35, 0.5, 0.85), st, turn=0.3, width=R * 0.85)
    centre_disc(cv, R * 0.1, C(150, 40, 110), C(190, 70, 150), z=0.5)


def head_star(cv):       # plant26: white six pointed petals, faint pink base, yellow-brown eye
    R = cv.w * 0.48
    st = petal_style(C(200, 160, 165), C(220, 218, 218), C(244, 242, 238), veins=C(190, 185, 190), vein_n=6,
                     vein_amt=0.35, inner_t=0.3, outer_t=0.7, cup=0.4, dark_edge=0.2)
    radial_petals(cv, 6, R, shape_ovate(0.4, 1.0), st, turn=0.0, width=R * 0.45)
    centre_disc(cv, R * 0.14, C(150, 110, 50), C(200, 160, 70), dots=C(110, 70, 30), n_dots=8, dot_r=2.5, z=0.5)


def head_blossom(cv):    # plant27: broad white petals, ring of yellow stamens
    R = cv.w * 0.48
    st = petal_style(C(200, 205, 190), C(232, 235, 230), C(247, 248, 245), veins=C(205, 208, 205), vein_n=9,
                     vein_amt=0.4, inner_t=0.3, outer_t=0.8, cup=0.4, dark_edge=0.15)
    radial_petals(cv, 5, R, shape_petal(0.62, 0.35, 0.5, 0.9), st, turn=0.25, width=R * 0.95)
    centre_disc(cv, R * 0.33, C(120, 120, 60), C(180, 175, 120), dots=C(225, 170, 30), n_dots=70, dot_r=3.0,
                ring=(0.25, 1.0), z=0.6)


def head_hibiscus(cv):   # plant29/31/33: pale ruffled petals (tinted per model), warm throat
    R = cv.w * 0.48
    st = petal_style(C(170, 90, 50), C(240, 230, 210), C(252, 248, 238), edge=C(232, 225, 210), edge_w=0.06,
                     veins=C(215, 205, 185), vein_n=10, vein_amt=0.35, inner_t=0.32, outer_t=0.8, cup=0.35)
    radial_petals(cv, 5, R, shape_petal(0.68, 0.45, 0.45, 1.0), st, turn=0.1, width=R * 1.0, bend=0.1)
    centre_disc(cv, R * 0.1, C(150, 80, 40), C(190, 120, 60), dots=C(250, 220, 100), n_dots=8, dot_r=2.5, z=0.5)


def head_bud(cv):        # closed pale bud (plant15, plant38 centre) seen from the side: tip up
    st = petal_style(C(120, 140, 70), C(215, 185, 225), C(240, 225, 245), veins=C(190, 150, 205), vein_n=5,
                     vein_amt=0.35, inner_t=0.25, outer_t=0.8, cup=0.6)
    cv.leaf((cv.w / 2, cv.h * 0.98), 0.0, cv.h * 0.93, cv.w * 0.62, shape_ovate(0.4, 1.0), st, segs=16)


# =============================================================== single leaves (base at the bottom centre)
def single(cv, shape, style, width_frac=0.9, length_frac=0.97, bend=0.0, segs=24):
    cv.leaf((cv.w / 2, cv.h - 1), 0.0, cv.h * length_frac, cv.w * width_frac, shape, style, bend=bend, segs=segs)


def leaf_lance_serrate(cv):   # plant16
    single(cv, shape_ovate(0.4, 0.9), leaf_style(C(55, 125, 22), C(120, 190, 60), rib=C(150, 200, 90), rib_w=0.05,
           vein=C(110, 170, 60), veins=10, vein_amt=0.3, serr=0.18, serr_n=18, gloss=0.25), width_frac=0.6)


def leaf_tulip(cv):           # plant17: broad blue-green, glossy
    single(cv, shape_ovate(0.35, 0.8), leaf_style(C(52, 92, 40), C(110, 155, 80), rib=C(130, 170, 100), rib_w=0.04,
           vein=C(90, 140, 70), veins=12, vein_slant=0.1, vein_amt=0.2, gloss=0.35, mottle=0.05), width_frac=0.75)


def leaf_hosta(cv):           # plant20: dark green, wide cream-yellow margin
    single(cv, shape_ovate(0.4, 0.75), leaf_style(C(30, 80, 25), C(60, 120, 40), rib=C(150, 170, 70), rib_w=0.04,
           vein=C(70, 130, 45), veins=9, vein_amt=0.35, edge=C(232, 220, 120), edge_w=0.26, edge_noise=0.12,
           gloss=0.3), width_frac=0.95)


def leaf_red(cv):             # plant25: crimson-magenta with a pale midrib and darker base
    single(cv, shape_ovate(0.45, 0.85), leaf_style(C(95, 30, 40), C(195, 70, 125), rib=C(235, 190, 220),
           rib_w=0.07, vein=C(220, 120, 175), veins=8, vein_amt=0.35, gloss=0.3, centre=C(150, 45, 90),
           centre_w=0.2, serr=0.08, serr_n=14), width_frac=0.7)


def leaf_broad_lance(cv):     # plant22, plant21: dark glossy, pale midrib, strong veins
    single(cv, shape_ovate(0.4, 0.85), leaf_style(C(30, 62, 18), C(80, 125, 60), rib=C(150, 175, 120), rib_w=0.05,
           vein=C(90, 130, 70), veins=11, vein_amt=0.4, gloss=0.35), width_frac=0.62)


def leaf_lance_dark(cv):      # plant26 (whorls of long leaflets): narrow, glossy, finely serrated
    single(cv, shape_ellipse(0.7, 0.4), leaf_style(C(22, 62, 10), C(70, 140, 40), rib=C(110, 165, 70), rib_w=0.05,
           vein=C(60, 125, 35), veins=14, vein_amt=0.25, serr=0.12, serr_n=22, gloss=0.3), width_frac=0.42)


def leaf_serrate_ovate(cv):   # plant27: dark serrated leaflets (rose-like), deep veins
    single(cv, shape_ovate(0.45, 0.9), leaf_style(C(32, 48, 10), C(85, 115, 40), rib=C(110, 130, 60), rib_w=0.05,
           vein=C(25, 38, 8), veins=9, vein_amt=0.45, serr=0.2, serr_n=14, gloss=0.25), width_frac=0.8)


def leaf_strap(cv):           # daylily / grass strap: neutral green (tinted per model)
    single(cv, shape_sword(0.8, 0.55), leaf_style(C(55, 105, 35), C(120, 165, 70), rib=C(150, 185, 100),
           rib_w=0.08, gloss=0.3, vein=None, mottle=0.1, groove=0.35), width_frac=0.85)


def stems(cv):                # two columns: green stem, brown twig
    half = cv.w // 2
    cv.strip([(half / 2, cv.h), (half / 2, 0)], [half * 0.45] * 2, stem_style(C(45, 80, 20), C(120, 160, 70)))
    cv.strip([(half * 1.5, cv.h), (half * 1.5, 0)], [half * 0.45] * 2, stem_style(C(60, 40, 22), C(140, 110, 75)))


# =============================================================== sprays (cards: base at the bottom centre)
def spray(cv, n, leaf_len, leaf_w, shape, palette, dome=(0.48, 0.55), twigs=None, lit=0.18, serr=0.0, veins=True,
          rib=True, gloss=0.2, spread=1.2, top_bias=0.0, ball=False):
    """A mound of small leaves on fine twigs radiating from the bottom centre (a clump seen from the side). palette:
    (dark, mid, light). Leaves deeper in (painted first) are darker; a fraction is sunlit."""
    rng = cv.rng
    W, H = cv.w, cv.h
    dark, mid_c, light = [lin(p) for p in palette]
    if twigs is not None:
        for k in range(int(n / 12)):
            a = rng.normal(0, 0.7)
            L = rng.uniform(0.4, 0.75) * H
            cv.leaf((W / 2 + rng.normal(0, W * 0.03), H), a, L, W * 0.012, shape_blade(0.4),
                    stem_style(twigs[0], twigs[1]), bend=rng.normal(0, 0.4), segs=10, z=-0.5)
    for k in range(n):
        depth = k / n                               # later = nearer the viewer, lighter
        while True:
            x = rng.uniform(0.04, 0.96); y = rng.uniform(0.04, 0.98)
            cy = 0.5 if ball else 0.62
            if ((x - 0.5) / dome[0]) ** 2 + ((y - cy) / dome[1]) ** 2 <= (1.0 - 0.5 * (1 - depth) if ball else 1.0):
                break
        if ball:      # a round puff: leaves point away from the centre
            ang = math.atan2(x - 0.5, 0.5 - y + 1e-3) + rng.normal(0, 0.5)
        else:
            ang = math.atan2(x - 0.5, (0.98 - y) + 0.25) * spread + rng.normal(0, 0.45)
        sun = rng.uniform() < lit * (0.5 + depth) * (1 + top_bias * (1 - y))
        base = mix(dark, mid_c, depth ** 0.8) * rng.uniform(0.85, 1.1)
        tipc = mix(mid_c, light, 0.5 + 0.5 * depth) if sun else mix(dark, mid_c, 0.4 + 0.6 * depth) * 1.15
        L = leaf_len * rng.uniform(0.75, 1.2)
        for _ in range(8):       # keep the leaf (tip and side) inside the cell
            off = 0.5 if ball else 0.0           # ball: the leaf is centred on its point
            bx, by = x * W - math.sin(ang) * L * off, y * H + math.cos(ang) * L * off
            tx, ty = bx + math.sin(ang) * L, by - math.cos(ang) * L
            m = L * leaf_w * 0.5 + 3
            if m <= tx <= W - m and m <= ty <= H - 2 and m <= bx <= W - m and by <= H - 2:
                break
            L *= 0.8
        else:
            continue
        st = leaf_style(base, tipc, rib=(tipc * 1.25 if rib else None), rib_w=0.07,
                        vein=(tipc * 1.2 if veins else None), veins=6, vein_amt=0.25, serr=serr, serr_n=10,
                        gloss=gloss * (1.5 if sun else 1.0), dark_edge=0.3)
        cv.leaf((bx, by), ang, L, L * leaf_w, shape, st, bend=rng.normal(0, 0.35), segs=8, z=depth)


def spray_ground(cv):         # mixed low foliage under flower heads
    spray(cv, 260, cv.h * 0.13, 0.55, shape_ovate(0.4, 0.9), (C(18, 32, 6), C(50, 95, 20), C(120, 170, 60)),
          dome=(0.36, 0.36), lit=0.2, gloss=0.25, ball=True)


def spray_shrub(cv):          # plant28-31: pointed ovate serrated leaves, yellow-lit
    spray(cv, 300, cv.h * 0.12, 0.62, shape_ovate(0.4, 0.95), (C(22, 28, 6), C(60, 80, 12), C(160, 200, 25)),
          dome=(0.4, 0.4), serr=0.12, lit=0.3, gloss=0.25, top_bias=0.8, ball=True)


def spray_box(cv):            # plant32/33/42: dense small leaves
    spray(cv, 650, cv.h * 0.075, 0.6, shape_ovate(0.45, 0.8), (C(18, 22, 5), C(55, 70, 16), C(170, 200, 60)),
          dome=(0.4, 0.4), lit=0.28, gloss=0.25, veins=False, top_bias=0.6, ball=True)


def spray_strap(cv):          # plant23 foliage: arching strap leaves from the base (tuft)
    rng = cv.rng
    for k in range(34):
        side = rng.uniform(-1, 1); depth = k / 34
        L = cv.h * rng.uniform(0.55, 0.95) * (1 - 0.3 * abs(side))
        st = leaf_style(mix(lin(C(30, 34, 6)), lin(C(70, 80, 18)), depth), mix(lin(C(80, 85, 20)),
                        lin(C(140, 140, 40)), depth), rib=C(150, 150, 60), rib_w=0.1, gloss=0.25, dark_edge=0.2)
        cv.leaf((cv.w / 2 + rng.normal(0, cv.w * 0.05), cv.h), side * 0.8 + rng.normal(0, 0.1), L,
                cv.w * rng.uniform(0.045, 0.06), shape_sword(0.8, 0.5), st, bend=side * 0.9 + rng.normal(0, 0.2),
                segs=16, z=depth)


# =============================================================== leafy atlas
def leafy_schefflera(cv):     # plant02/08: glossy dark leaflets with pale speckled highlights
    single(cv, shape_ellipse(0.75, 0.3), leaf_style(C(32, 80, 22), C(95, 155, 60), rib=C(150, 190, 110), rib_w=0.04,
           vein=C(70, 130, 45), veins=10, vein_amt=0.2, spots=C(150, 190, 110), spot_amt=0.35, spot_scale='hi',
           spot_thr=1.6, gloss=0.4, mottle=0.08), width_frac=0.5)


def leafy_broad(cv):          # plant10 and fillers: broad ovate, glossy, yellow-green
    single(cv, shape_ovate(0.4, 0.8), leaf_style(C(45, 100, 20), C(130, 185, 60), rib=C(170, 205, 110), rib_w=0.04,
           vein=C(100, 160, 50), veins=9, vein_amt=0.3, spots=C(160, 200, 90), spot_amt=0.25, spot_scale='hi',
           spot_thr=1.7, gloss=0.4, mottle=0.08), width_frac=0.72)


def leafy_spot(cv):           # plant03 / plant01: aglaonema, dark green with pale speckles
    single(cv, shape_ovate(0.42, 0.85), leaf_style(C(28, 60, 18), C(70, 115, 40), rib=C(150, 175, 90), rib_w=0.05,
           vein=C(60, 100, 35), veins=10, vein_amt=0.25, spots=C(170, 185, 100), spot_amt=0.85, spot_scale='mid',
           spot_thr=0.9, gloss=0.3, mottle=0.06), width_frac=0.6)


def leafy_dieff(cv):          # plant01: big leaf, cream-yellow feathered centre, green margin
    single(cv, shape_ovate(0.4, 0.8), leaf_style(C(55, 95, 30), C(120, 160, 60), rib=C(220, 220, 150), rib_w=0.05,
           vein=C(210, 210, 140), veins=12, vein_amt=0.35, centre=C(205, 205, 120), centre_w=0.42,
           spots=C(215, 215, 150), spot_amt=0.5, spot_thr=1.0, gloss=0.3, mottle=0.06), width_frac=0.75)


def leafy_heart(cv):          # plant09: pothos heart leaf, yellow-green marbled
    single(cv, shape_heart(0.25), leaf_style(C(55, 110, 20), C(140, 195, 60), rib=C(180, 215, 110), rib_w=0.04,
           vein=C(120, 180, 60), veins=7, vein_amt=0.3, spots=C(205, 225, 120), spot_amt=0.6, spot_scale='mid',
           spot_thr=1.1, gloss=0.4, mottle=0.06), width_frac=0.88)


def leafy_sword(cv):          # plant11 / plant56: snake plant, banded, yellow margin
    single(cv, shape_sword(0.7, 0.7), leaf_style(C(60, 100, 35), C(110, 150, 60), bands=C(25, 50, 15), band_freq=16,
           band_amt=0.8, edge=C(215, 200, 70), edge_w=0.13, edge_noise=0.1, gloss=0.25, groove=0.15, mottle=0.05),
           width_frac=0.8)


def leafy_blade(cv):          # plant13 / plant04: grass blade with a pale midline
    single(cv, shape_blade(0.9), leaf_style(C(25, 75, 20), C(80, 160, 60), rib=C(140, 200, 110), rib_w=0.08,
           gloss=0.3, mottle=0.08, groove=0.3), width_frac=0.85)


def leafy_corn(cv):           # plant34: corn leaf, yellow-green with a pale midrib
    single(cv, shape_sword(0.55, 0.45), leaf_style(C(95, 140, 20), C(190, 210, 60), rib=C(225, 230, 140), rib_w=0.07,
           vein=C(160, 190, 50), veins=30, vein_slant=0.05, vein_amt=0.15, tip_dry=C(210, 190, 90), gloss=0.3,
           mottle=0.06, groove=0.3), width_frac=0.8)


def leafy_lance(cv):          # plant15: long narrow lance, dark, speckled
    single(cv, shape_ellipse(0.7, 0.45), leaf_style(C(40, 75, 30), C(100, 130, 70), rib=C(150, 170, 110), rib_w=0.05,
           spots=C(140, 160, 100), spot_amt=0.35, spot_scale='hi', spot_thr=1.5, gloss=0.25), width_frac=0.75)


def leafy_fern(cv):           # plant05: pinnate frond, base at the bottom centre
    rng = cv.rng
    W, H = cv.w, cv.h
    x0, y0 = W / 2, H - 2
    L = H * 0.97
    rach = stem_style(C(50, 85, 20), C(110, 150, 50))
    pairs = 30
    for k in range(pairs):
        t = 0.06 + 0.92 * k / pairs
        outline = math.sin(math.pi * min(t * 1.05, 1.0)) ** 0.7 * (1 - 0.5 * t) + 0.08
        plen = W * 0.47 * outline
        for side in (-1, 1):
            py = y0 - L * (t + side * 0.006)
            st = leaf_style(C(35, 85, 18), C(105, 165, 55), rib=C(130, 180, 70), rib_w=0.08, serr=0.35, serr_n=9,
                            gloss=0.2, dark_edge=0.35, mottle=0.1)
            cv.leaf((x0, py), side * (1.05 - 0.35 * t) + rng.normal(0, 0.04), plen, plen * 0.32,
                    shape_ellipse(0.6, 0.5), st, bend=-side * 0.25, segs=10, rnd={'bright': rng.uniform(0.9, 1.1)},
                    z=0.2)
    cv.leaf((x0, y0), 0.0, L, W * 0.035, shape_blade(0.4), rach, segs=16, z=0.5)


def lily_pad(cv, base, mid, edge, vein, mottle_c, notch=0.28):
    cx, cy = cv.w / 2, cv.h / 2
    R = cv.w * 0.47
    base, mid, edge, vein, mottle_c = [lin(x) for x in (base, mid, edge, vein, mottle_c)]

    def col(r, x, y, c):
        a = np.arctan2(y / SS - cy, x / SS - cx)
        v = np.abs(np.mod(a * 8 / math.pi + 0.15 * c.lo[y, x], 1.0) - 0.5)
        rgb = mix(mid, base, smoothstep(0.0, 1.0, r))
        rgb = mix(rgb, mottle_c, smoothstep(0.4, 1.4, c.lo[y, x]) * 0.7)
        rgb = mix(rgb, vein, smoothstep(0.06, 0.0, v) * smoothstep(0.1, 0.3, r) * 0.5)
        rgb = mix(rgb, edge, smoothstep(0.9, 0.98, r))
        return rgb * (1 + 0.08 * c.hi[y, x])[:, None], 0.3 * (1 - r * r) + 0.05 * c.hi[y, x]
    cv.disc((cx, cy), R, col)
    ys, xs = np.mgrid[0:cv.H, 0:cv.W]
    ang = np.abs(np.angle(np.exp(1j * (np.arctan2(ys + 0.5 - cy * SS, xs + 0.5 - cx * SS) - math.pi / 2))))
    cut = (ang < notch * 0.5 + 0.02 * np.hypot(ys - cy * SS, xs - cx * SS) / (R * SS)) & \
        (np.hypot(ys - cy * SS, xs - cx * SS) > R * SS * 0.04)
    cv.alpha[cut] = 0


def leafy_pad_green(cv):      # plant37: olive lily pad with dark mottling
    lily_pad(cv, C(95, 110, 30), C(120, 130, 40), C(150, 120, 40), C(70, 85, 25), C(55, 70, 20))


def leafy_pad_pink(cv):       # plant38: pink-lilac pad with pale veins
    lily_pad(cv, C(150, 110, 140), C(190, 150, 180), C(120, 70, 100), C(230, 210, 225), C(130, 90, 120), notch=0.4)


def head_waterlily(cv):       # plant56: white pointed petals, yellow centre
    R = cv.w * 0.48
    st = petal_style(C(205, 210, 185), C(238, 240, 230), C(250, 250, 245), veins=C(210, 215, 200), vein_n=6,
                     vein_amt=0.3, cup=0.4, dark_edge=0.15)
    radial_petals(cv, 10, R, shape_ovate(0.4, 0.9), st, width=R * 0.32)
    radial_petals(cv, 8, R * 0.75, shape_ovate(0.4, 0.9), st, turn=0.3, width=R * 0.32, z=0.3)
    centre_disc(cv, R * 0.2, C(200, 150, 20), C(240, 200, 50), dots=C(250, 220, 80), n_dots=20, dot_r=2.5, z=0.6)


def head_violets(cv):         # plant01: cluster of small purple flowers
    cx, cy = cv.w / 2, cv.h / 2; R = cv.w * 0.46
    cv.disc((cx, cy), R * 0.9, lambda r, x, y, c: (np.repeat(lin(C(40, 25, 45))[None], len(r), 0), 0.2 * (1 - r)))
    for k in range(26):
        rr = R * 0.78 * math.sqrt(cv.rng.uniform()); a = cv.rng.uniform(0, 2 * math.pi)
        fx, fy = cx + math.cos(a) * rr, cy + math.sin(a) * rr
        size = cv.rng.uniform(18, 26); lit = cv.rng.uniform(0.85, 1.15)
        st = petal_style(C(70, 25, 90), jit(cv.rng, C(120 * lit, 50 * lit, 140 * lit)), C(150, 80, 170), cup=0.3)
        t0 = cv.rng.uniform(0, 2 * math.pi)
        for p in range(5):
            cv.leaf((fx, fy), t0 + p * 2 * math.pi / 5, size, size * 0.8, shape_petal(0.6, 0.4, 0.5, 0.8), st,
                    segs=6, z=0.5)
        cv.disc((fx, fy), 2.5, lambda r, x, y, c: (np.repeat(lin(C(240, 220, 90))[None], len(r), 0), 0.1 * r),
                z=0.8)


def head_anthurium(cv):       # plant43: glossy red heart spathe with a pale spadix (side card, base at the bottom)
    st = leaf_style(C(120, 15, 35), C(200, 40, 70), rib=C(230, 90, 110), rib_w=0.03, vein=C(160, 25, 50), veins=8,
                    vein_amt=0.3, gloss=0.6, dark_edge=0.3)
    cv.leaf((cv.w / 2, cv.h * 0.98), 0.0, cv.h * 0.9, cv.w * 0.95, shape_heart(0.3), st, segs=20)
    cv.leaf((cv.w / 2, cv.h * 0.75), 0.35, cv.h * 0.45, cv.w * 0.09, shape_blade(0.3),
            stem_style(C(170, 150, 60), C(240, 225, 140)), segs=8, z=1.0)


def spray_tuft(cv):           # plant04/13: grass tuft
    rng = cv.rng
    for k in range(70):
        side = rng.uniform(-1, 1); depth = k / 70
        L = cv.h * rng.uniform(0.45, 0.95) * (1 - 0.35 * abs(side))
        st = leaf_style(mix(lin(C(20, 45, 12)), lin(C(45, 95, 30)), depth),
                        mix(lin(C(70, 120, 40)), lin(C(130, 185, 80)), depth), rib=C(150, 200, 110), rib_w=0.1,
                        gloss=0.2, dark_edge=0.2)
        cv.leaf((cv.w / 2 + rng.normal(0, cv.w * 0.06), cv.h), side * 0.85 + rng.normal(0, 0.1), L,
                cv.w * rng.uniform(0.018, 0.03), shape_blade(0.9), st, bend=side * 0.8 + rng.normal(0, 0.25),
                segs=14, z=depth)


def palmate(cv, x, y, ang, size, style, lobes=5):
    for j in range(lobes):
        a = ang + (j - (lobes - 1) / 2) * 0.45
        L = size * (1 - 0.18 * abs(j - (lobes - 1) / 2))
        cv.leaf((x, y), a, L, L * 0.45, shape_ovate(0.45, 0.9), style, segs=8)


def spray_ivy(cv):            # plant46: jagged palmate leaves on a vine spray
    rng = cv.rng
    for k in range(90):
        x = rng.uniform(0.15, 0.85) * cv.w; y = rng.uniform(0.2, 0.85) * cv.h
        if ((x / cv.w - 0.5) / 0.36) ** 2 + ((y / cv.h - 0.52) / 0.34) ** 2 > 1:
            continue
        lit = rng.uniform(0.75, 1.2)
        st = leaf_style(C(25 * lit, 70 * lit, 20 * lit), C(80 * lit, 150 * lit, 55 * lit), rib=C(140, 190, 100),
                        rib_w=0.05, serr=0.25, serr_n=8, gloss=0.25)
        palmate(cv, x, y, math.atan2(x / cv.w - 0.5, 0.6 - y / cv.h) + rng.normal(0, 0.4), cv.w * 0.13, st)
    for k in range(10):          # fill the middle of the spray
        x = (0.5 + rng.normal(0, 0.07)) * cv.w; y = (0.55 + rng.normal(0, 0.07)) * cv.h
        lit = rng.uniform(0.9, 1.25)
        st = leaf_style(C(25 * lit, 70 * lit, 20 * lit), C(80 * lit, 150 * lit, 55 * lit), rib=C(140, 190, 100),
                        rib_w=0.05, serr=0.25, serr_n=8, gloss=0.25)
        palmate(cv, x, y, rng.uniform(-1.5, 1.5), cv.w * 0.12, st)


def spray_pothos(cv):         # plant09: ball of heart leaves
    rng = cv.rng
    for k in range(120):
        depth = k / 120
        while True:
            x = rng.uniform(0.05, 0.95); y = rng.uniform(0.05, 0.95)
            if ((x - 0.5) / 0.38) ** 2 + ((y - 0.5) / 0.38) ** 2 <= 1 - 0.4 * (1 - depth):
                break
        lit = 0.75 + 0.45 * depth
        st = leaf_style(C(50 * lit, 100 * lit, 18 * lit), C(130 * lit, 190 * lit, 60 * lit), rib=C(180, 215, 110),
                        rib_w=0.04, spots=C(200, 225, 120), spot_amt=0.5, spot_thr=1.2, gloss=0.4)
        L = cv.h * rng.uniform(0.11, 0.16)
        cv.leaf((x * cv.w, y * cv.h), math.atan2(x - 0.5, 0.5 - y) + rng.normal(0, 0.5), L, L * 0.8, shape_heart(0.25),
                st, segs=8, z=depth)


def spray_twigs(cv):          # plant49 tumbleweed / plant48: tangle of pale dry twigs
    rng = cv.rng
    cx, cy = cv.w / 2, cv.h / 2
    for k in range(110):
        a = rng.uniform(0, 2 * math.pi); r = rng.uniform(0.0, 0.4) * cv.w
        x, y = cx + math.cos(a) * r, cy + math.sin(a) * r
        tan = a + math.pi / 2 + rng.normal(0, 0.6)
        L = cv.w * rng.uniform(0.15, 0.4)
        lit = rng.uniform(0.6, 1.2)
        st = stem_style(C(70 * lit, 58 * lit, 36 * lit), C(185 * lit, 165 * lit, 115 * lit))
        cv.leaf((x, y), tan, L, cv.w * rng.uniform(0.008, 0.016), shape_blade(0.2), st, bend=rng.normal(0, 1.2),
                segs=12, z=k / 110)


# =============================================================== layouts
FLOWERS = {
    # name: (x, y, w, h in grid units, painter, kind)
    'h_lotus': (0, 0, 2, 2, head_lotus, 'head'), 'h_tulip': (2, 0, 2, 2, head_tulip, 'head'),
    'h_startulip': (4, 0, 2, 2, head_startulip, 'head'), 'h_petunia': (6, 0, 2, 2, head_petunia, 'head'),
    'h_trumpet': (8, 0, 2, 2, head_trumpet, 'head'), 'h_florets': (10, 0, 2, 2, head_florets, 'head'),
    'h_lily': (12, 0, 2, 2, head_lily, 'head'), 'h_daisy': (14, 0, 2, 2, head_daisy, 'head'),
    'h_impatiens': (0, 2, 2, 2, head_impatiens, 'head'), 'h_star': (2, 2, 2, 2, head_star, 'head'),
    'h_blossom': (4, 2, 2, 2, head_blossom, 'head'), 'h_hibiscus': (6, 2, 2, 2, head_hibiscus, 'head'),
    'h_bud': (8, 2, 1, 2, head_bud, 'leaf'),
    'l_lance_serrate': (0, 4, 2, 4, leaf_lance_serrate, 'leaf'), 'l_tulip': (2, 4, 2, 4, leaf_tulip, 'leaf'),
    'l_hosta': (4, 4, 2, 4, leaf_hosta, 'leaf'), 'l_red': (6, 4, 2, 4, leaf_red, 'leaf'),
    'l_broad_lance': (8, 4, 2, 4, leaf_broad_lance, 'leaf'), 'l_lance_dark': (10, 4, 2, 4, leaf_lance_dark, 'leaf'),
    'l_serrate_ovate': (12, 4, 2, 4, leaf_serrate_ovate, 'leaf'), 'l_strap': (14, 4, 1, 4, leaf_strap, 'leaf'),
    'stems': (15, 4, 1, 4, stems, 'strip'),
    's_ground': (0, 8, 4, 4, spray_ground, 'card'), 's_shrub': (4, 8, 4, 4, spray_shrub, 'card'),
    's_box': (8, 8, 4, 4, spray_box, 'card'), 's_strap': (12, 8, 4, 4, spray_strap, 'card'),
}
LEAFY = {
    'l_schefflera': (0, 0, 2, 4, leafy_schefflera, 'leaf'), 'l_broad': (2, 0, 2, 4, leafy_broad, 'leaf'),
    'l_spot': (4, 0, 2, 4, leafy_spot, 'leaf'), 'l_dieff': (6, 0, 2, 4, leafy_dieff, 'leaf'),
    'l_heart': (8, 0, 2, 3, leafy_heart, 'leaf'), 'h_waterlily': (10, 0, 2, 2, head_waterlily, 'head'),
    'h_violets': (12, 0, 2, 2, head_violets, 'head'), 'h_anthurium': (14, 0, 2, 2, head_anthurium, 'leaf'),
    'h_bud': (10, 2, 1, 2, head_bud, 'leaf'), 'l_lance': (13, 4, 1, 4, leafy_lance, 'leaf'),
    'stems': (14, 4, 1, 4, stems, 'strip'),
    'l_sword': (0, 4, 1, 8, leafy_sword, 'leaf'), 'l_blade': (1, 4, 1, 8, leafy_blade, 'leaf'),
    'l_corn': (2, 4, 1, 8, leafy_corn, 'leaf'), 'l_fern': (3, 4, 2, 8, leafy_fern, 'leaf'),
    's_tuft': (5, 4, 4, 4, spray_tuft, 'card'), 's_ivy': (9, 4, 4, 4, spray_ivy, 'card'),
    's_twigs': (5, 8, 4, 4, spray_twigs, 'card'), 's_pothos': (9, 8, 4, 4, spray_pothos, 'card'),
    'p_green': (0, 12, 4, 4, leafy_pad_green, 'head'), 'p_pink': (4, 12, 4, 4, leafy_pad_pink, 'head'),
    's_ground': (8, 12, 4, 4, spray_ground, 'card'),
}
ATLASES = {'flowers': (2048, FLOWERS), 'leafy': (2048, LEAFY)}


def profile(alpha, kind, rows=32):
    """Leaf cells: per row band (v from the bottom up) the half width of the opaque texels about the centre column,
    relative to the cell half width, and the opaque v range. Heads: the opaque radius relative to the half size."""
    a = alpha >= 128
    h, w = a.shape
    if kind == 'head':
        ys, xs = np.nonzero(a)
        r = np.hypot(xs + 0.5 - w / 2, ys + 0.5 - h / 2).max() / (w / 2) if len(xs) else 1.0
        return {'radius': round(float(r), 3)}
    out = []
    for k in range(rows):
        y1 = h - int(round(k * h / rows)); y0 = h - int(round((k + 1) * h / rows))
        band = a[y0:y1]
        cols = np.nonzero(band.any(0))[0]
        if len(cols) == 0:
            out.append(0.0); continue
        out.append(round(float(max(abs(cols.min() - w / 2), abs(cols.max() + 1 - w / 2)) / (w / 2)), 3))
    rows_any = np.nonzero(a.any(1))[0]
    t0 = 1 - (rows_any.max() + 1) / h if len(rows_any) else 0.0
    t1 = 1 - rows_any.min() / h if len(rows_any) else 1.0
    return {'half': out, 't0': round(float(t0), 3), 't1': round(float(t1), 3)}


def build(name):
    size, layout = ATLASES[name]
    rgba = np.zeros((size, size, 4), np.uint8); nrm = np.zeros((size, size, 3), np.uint8)
    nrm[..., 2] = 255; nrm[..., :2] = 128
    meta = {'size': size, 'cells': {}}
    used = np.zeros((size // G, size // G), bool)       # cells must not overlap
    for cell, (x, y, w, h, painter, kind) in layout.items():
        assert not used[y:y + h, x:x + w].any(), f'{name}: cell {cell} overlaps another cell'
        used[y:y + h, x:x + w] = True
    for cell, (x, y, w, h, painter, kind) in layout.items():
        cv = Canvas(w * G, h * G, seed=zlib.crc32(cell.encode()))
        painter(cv)
        c_rgba, c_nrm = cv.finish()
        rgba[y * G:(y + h) * G, x * G:(x + w) * G] = c_rgba
        nrm[y * G:(y + h) * G, x * G:(x + w) * G] = c_nrm
        info = {'rect': [x * G / size, y * G / size, (x + w) * G / size, (y + h) * G / size], 'kind': kind,
                'aspect': w / h, 'coverage': round(float((c_rgba[..., 3] >= 128).mean()), 3)}
        info.update(profile(c_rgba[..., 3], kind))
        meta['cells'][cell] = info
        print('CELL', cell, kind, 'coverage', info['coverage'])
    os.makedirs(TEX, exist_ok=True)
    Image.fromarray(rgba, 'RGBA').save(os.path.join(TEX, f'{name}_basecolor.png'), optimize=True)
    Image.fromarray(nrm, 'RGB').resize((size // 2, size // 2), Image.LANCZOS).save(
        os.path.join(TEX, f'{name}_normal.png'), optimize=True)
    with open(os.path.join(TEX, f'{name}_layout.json'), 'w') as fh:
        json.dump(meta, fh, indent=1)
    print('ATLAS', name, 'written')


if __name__ == '__main__':
    build(sys.argv[1])
