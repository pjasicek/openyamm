#!/usr/bin/env python3
"""Crossbow tier skins painted procedurally, without Meshy (README.md "Crossbow skins, procedural"): every map computed
per texel from the 3D position on the locked layout, by region and tier, at 4096 and downsampled once to 2048.

  python3 -I bake_crossbow.py <tier> [...]   work/crossbow/t<tier>/{basecolor,normal,mr[,emissive]}.png and
                                             work/crossbow/t<tier>/w_crossbow_t<tier>.glb

Why: the image tool refused every crossbow master (four wordings), and Meshy's paint over the rendered masters
(v3) turned their wood into dense pale ribbing and three of the four tiers into the same pale stock. Here the four
tiers follow the user's review (2026-11-14):
  1 rough weathered grey-brown wood with open cracks, rusty iron, cracked rawhide;
  2 warm polished walnut with a flowing grain, satin steel, dark leather;
  3 black lacquered ebony with framed gold filigree panels, mirror steel, gold fittings, crimson leather, rubies (no
    glow);
  4 the only glowing tier: blackened wood with a violet cast, dark star-metal with a blue-violet sheen, platinum
    fittings, luminous cyan-violet rune channels along both sides of the stock and along the prod, glowing stones.
The patterns live in the crossbow's build frame (kinds.py `mount` inverted: the stock along +X, up +Z), the grain is a
distorted ring field (irregular, a ring about every 0.6 units, never a regular stripe), the normal map is the
derivative of a height field along each texel's tangent frame (post.py's), the occlusion bake (maps/ao.png) shades
the colour gently and fills the MR map's R channel (openyamm_specular_occlusion: orm), gutter_fill.py last, and the
GLB is post.py's writer.
"""
import json
import os
import subprocess
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import post  # noqa: E402
from kinds import KINDS, weapon_from_build  # noqa: E402

KIND = 'crossbow'
BIG = 4096
WORK = os.path.join(PROJECT, 'work', KIND)
R = post.R


# -- noise ------------------------------------------------------------------------------------------------------------
def hash3(ix, iy, iz, seed):
    k = (ix * 73856093) ^ (iy * 19349663) ^ (iz * 83492791) ^ (seed * 2654435761)
    k = k & 0xFFFFFFFF
    k = ((k ^ (k >> 13)) * 1274126177) & 0xFFFFFFFF
    k = ((k ^ (k >> 16)) * 2246822519) & 0xFFFFFFFF
    return (k & 0xFFFF).astype(np.float32) / 65535.0 * 2.0 - 1.0


def noise3(p, seed=0):
    """Value noise in [-1, 1] at points (N, 3)."""
    i = np.floor(p).astype(np.int64)
    f = (p - i).astype(np.float32)
    u = f * f * (3 - 2 * f)
    out = 0.0
    for dx in (0, 1):
        wx = u[:, 0] if dx else 1 - u[:, 0]
        for dy in (0, 1):
            wy = u[:, 1] if dy else 1 - u[:, 1]
            for dz in (0, 1):
                wz = u[:, 2] if dz else 1 - u[:, 2]
                out = out + wx * wy * wz * hash3(i[:, 0] + dx, i[:, 1] + dy, i[:, 2] + dz, seed)
    return out


def fbm(p, octaves=4, seed=0):
    total, amp, norm = 0.0, 1.0, 0.0
    for k in range(octaves):
        total = total + amp * noise3(p * (2.0 ** k), seed + 17 * k)
        norm += amp
        amp *= 0.5
    return total / norm


def srgb(c):
    return post.srgb_to_linear(np.asarray(c, np.float64))


def mix(a, b, t):
    t = np.asarray(t)[..., None] if np.ndim(t) else t
    return a * (1 - t) + b * t


ss = post.smoothstep

# -- the stock's outline (build frame, after build.py's rear shortening) ---------------------------------------------
# build.py's stations (x before shortening, half width, half height, centre height); x < -6 was scaled by 0.79.
STATIONS = [(-34.0, 1.66, 3.25, 2.45), (-32.6, 1.74, 3.3, 2.4), (-29.0, 1.8, 3.2, 2.5), (-25.5, 1.78, 2.95, 2.75),
            (-22.0, 1.7, 2.55, 3.15), (-19.0, 1.6, 2.1, 3.6), (-16.5, 1.52, 1.82, 3.9), (-13.0, 1.45, 1.72, 4.0),
            (-9.5, 1.52, 1.75, 4.0), (-6.5, 1.72, 1.85, 3.95), (-3.0, 1.78, 1.85, 3.92), (4.0, 1.72, 1.75, 4.0),
            (12.0, 1.6, 1.55, 4.2), (17.0, 1.45, 1.35, 4.4), (20.0, 1.3, 1.15, 4.6)]
SX = np.array([s[0] if s[0] >= -6 else -6 + (s[0] + 6) * 0.79 for s in STATIONS])
SH = np.array([s[2] for s in STATIONS])
SZ = np.array([s[3] for s in STATIONS])


def stock_top_bottom(x):
    zc = np.interp(x, SX, SZ)
    h = np.interp(x, SX, SH)
    return zc + h, zc - h, zc


# -- materials --------------------------------------------------------------------------------------------------------
def wood_field(P, tier):
    """(ring band 0..1: the dark late wood, fibre streaks, pores, slow variation) of a distorted ring field."""
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    warp = fbm(P * np.array([0.035, 0.45, 0.45], np.float32), 3, 3) * 1.5
    # A log axis beside and above the stock, slowly drifting: the rings cross the sides as long flowing arcs.
    r = np.sqrt((y - 3.0 - 0.6 * np.sin(x * 0.07)) ** 2 + (z - 9.5 - 0.05 * x) ** 2)
    freq = 1.65 + 0.35 * fbm(P * np.array([0.02, 0.1, 0.1], np.float32), 2, 5)
    ring = (r * freq + warp) % 1.0
    band = ss(0.5, 0.82, ring) * (1 - ss(0.9, 1.0, ring))
    fibre = fbm(P * np.array([0.12, 7.0, 7.0], np.float32), 3, 7)
    pores = ss(0.45, 0.75, fbm(P * np.array([0.9, 22.0, 22.0], np.float32), 2, 9))
    slow = fbm(P * np.array([0.05, 0.3, 0.3], np.float32), 2, 11)
    return band.astype(np.float32), fibre, pores, slow


def rune_glyphs(s, t, seed):
    """Rune marks along a channel: s along it (units), t across it (units, 0 on the line). Each 1.6-unit cell holds a
    glyph of up to four strokes (an upright, two diagonals, a short bar) chosen by hash. Returns 0..1 coverage."""
    cell = np.floor(s / 1.6)
    local = s - cell * 1.6 - 0.8
    h = (hash3(cell.astype(np.int64), np.zeros_like(cell, np.int64), np.zeros_like(cell, np.int64), seed) + 1) / 2
    h2 = (hash3(cell.astype(np.int64), np.ones_like(cell, np.int64), np.zeros_like(cell, np.int64), seed) + 1) / 2
    w = 0.055
    inside = (np.abs(t) < 0.42) & (np.abs(local) < 0.42)
    upright = (np.abs(local - (h - 0.5) * 0.4) < w)
    diag1 = (np.abs((local - t) * 0.7071) < w) & (h2 > 0.3)
    diag2 = (np.abs((local + t + 0.2 * (h - 0.5)) * 0.7071) < w) & (h2 > 0.6)
    bar = (np.abs(t - (h2 - 0.5) * 0.5) < w) & (np.abs(local) < 0.22) & (h < 0.6)
    gap = np.abs(local) > 0.62
    return (inside & (upright | diag1 | diag2 | bar) & ~gap).astype(np.float32)


def scroll(u, v, half):
    """Gold rinceau in a panel (u along it from its start, v across from its middle line, half its half height, all in
    units): a vine waving along the panel with a spiral curl at every crest, tangent to it on the inner side. Returns
    0..1 coverage of lines about 0.11 units wide."""
    lam = 2.8
    k = 2 * np.pi / lam
    amp = 0.38 * half
    stem_v = amp * np.sin(k * u)
    slope = amp * k * np.cos(k * u)
    width = 0.055
    stem = 1 - ss(width, width * 1.6, np.abs(v - stem_v) / np.sqrt(1 + slope ** 2))
    j = np.floor(u / (lam / 2))
    sign = np.where(j % 2 == 0, 1.0, -1.0)
    uc = (j + 0.5) * lam / 2
    radius = np.minimum(0.42 * half, 0.75)
    vc = sign * (amp - radius)
    du, dv = (u - uc) * sign, v - vc
    r = np.sqrt(du ** 2 + dv ** 2)
    theta = np.arctan2(dv * sign, du)
    b = 0.075
    d = b * (np.pi - np.abs(((r / b - theta) % (2 * np.pi)) - np.pi))
    curl = (1 - ss(width, width * 1.6, d)) * (r < radius) * (r > 0.05)
    return np.maximum(stem, curl).astype(np.float32)


def shade(P, N, reg, ao, tier, height_only=False):
    """Per texel: base colour (linear), roughness, metallic, emission (linear) and height (units)."""
    n = len(P)
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    base = np.zeros((n, 3), np.float32)
    rough = np.full(n, 0.6, np.float32)
    metal = np.zeros(n, np.float32)
    emit = np.zeros((n, 3), np.float32)
    height = np.zeros(n, np.float32)
    wood = reg == R['wood']
    steel = reg == R['metal']
    trim = reg == R['brass']
    hide = reg == R['leather']
    cord = reg == R['string']
    gem = reg == R['gem']
    side = np.abs(N[:, 1]) > 0.55
    # The stock's sides (wood or the lock plates; the cheek piece reaches |y| 2.35), between nose and butt.
    top, bottom, centre = stock_top_bottom(x)
    on_stock = (np.abs(y) < 2.45) & (x > -28.4) & (x < 19.8) & (z < top + 0.05) & (z > bottom - 0.05)
    # The prod: metal out across the stock (|y| beyond its side), at the front.
    prod = steel & (np.abs(y) > 2.05) & (x > 10.5) & (x < 18.5) & (np.abs(z - 4.6) < 1.0)

    # Wood.
    if wood.any():
        Pw = P[wood]
        band, fibre, pores, slow = wood_field(Pw, tier)
        if tier == 1:
            light, dark = srgb((0.56, 0.5, 0.42)), srgb((0.3, 0.26, 0.21))
            c = mix(light, dark, np.clip(0.55 * band + 0.25 * (fibre * 0.5 + 0.5) + 0.25 * pores, 0, 1))
            # Weathered: grey bleaching, cracks along the grain, grime.
            grey = (0.5 + 0.5 * fbm(Pw * np.array([0.08, 0.6, 0.6], np.float32), 3, 21)) * 0.45
            c = mix(c, c.mean(1, keepdims=True) * np.array([1.02, 1.0, 0.97]), grey)
            crack = ss(0.82, 0.93, np.abs(fbm(Pw * np.array([0.06, 2.2, 2.2], np.float32), 3, 23))
                       + 0.25 * fbm(Pw * np.array([0.5, 6.0, 6.0], np.float32), 2, 24))
            c = c * (1 - 0.6 * crack[:, None])
            scuff = ss(0.55, 0.8, fbm(Pw * np.array([0.35, 1.2, 1.2], np.float32), 3, 25))
            c = c * (1 + 0.18 * scuff[:, None])
            base[wood] = c
            rough[wood] = 0.82 + 0.1 * crack
            height[wood] = -0.035 * crack - 0.008 * band + 0.004 * fibre
        elif tier == 2:
            light, dark = srgb((0.52, 0.3, 0.16)), srgb((0.24, 0.11, 0.05))
            figure = 0.5 + 0.5 * fbm(Pw * np.array([0.25, 1.8, 1.8], np.float32), 3, 31)
            t = np.clip(0.62 * band + 0.18 * (fibre * 0.5 + 0.5) + 0.12 * pores + 0.15 * (figure - 0.5), 0, 1)
            c = mix(light, dark, t) * (0.9 + 0.2 * (slow[:, None] * 0.5 + 0.5))
            base[wood] = c
            rough[wood] = 0.3 + 0.12 * band + 0.08 * pores
            height[wood] = -0.006 * band - 0.006 * pores
        elif tier == 3:
            light, dark = srgb((0.075, 0.06, 0.05)), srgb((0.028, 0.022, 0.02))
            c = mix(light, dark, np.clip(0.7 * band + 0.3 * (fibre * 0.5 + 0.5), 0, 1))
            gold = np.zeros(len(Pw), np.float32)
            # Framed filigree panels on the sides of the butt and the fore-end: a border line 0.32 inside the top and
            # bottom edges, a cross line closing each panel, and contour tracery of a smooth field inside.
            xs, zs = Pw[:, 0], Pw[:, 2]
            tw, bw, _ = stock_top_bottom(xs)
            sd = side[wood] & on_stock[wood]
            panels = [(-27.6, -15.2), (1.6, 13.8)]
            in_panel = np.zeros(len(Pw), bool)
            frame = np.zeros(len(Pw), np.float32)
            vine = np.zeros(len(Pw), np.float32)
            for x0, x1 in panels:
                inside = sd & (xs > x0) & (xs < x1) & (zs < tw - 0.32) & (zs > bw + 0.32)
                in_panel |= inside
                band_x = sd & (zs < tw - 0.25) & (zs > bw + 0.25) & (
                    (np.abs(xs - x0) < 0.07) | (np.abs(xs - x1) < 0.07))
                band_z = sd & (xs > x0 - 0.07) & (xs < x1 + 0.07) & (
                    (np.abs(zs - (tw - 0.32)) < 0.07) | (np.abs(zs - (bw + 0.32)) < 0.07))
                frame = np.maximum(frame, (band_x | band_z).astype(np.float32))
                vine = np.maximum(vine, inside * scroll(xs - x0 - 0.4, zs - (tw + bw) / 2,
                                                        ((tw - bw) / 2 - 0.32)))
            gold = np.maximum(frame, vine)
            gc = srgb((1.0, 0.78, 0.38)) * (0.85 + 0.15 * (fibre[:, None] * 0.5 + 0.5))
            base[wood] = mix(c, gc, gold)
            rough[wood] = 0.16 + 0.06 * band
            rough[wood] = rough[wood] * (1 - gold) + 0.22 * gold
            metal[wood] = gold
            height[wood] = 0.025 * gold - 0.003 * band
        else:
            light, dark = srgb((0.07, 0.06, 0.085)), srgb((0.022, 0.02, 0.03))
            c = mix(light, dark, np.clip(0.7 * band + 0.3 * (fibre * 0.5 + 0.5), 0, 1))
            sheen = 0.5 + 0.5 * fbm(Pw * np.array([0.08, 0.5, 0.5], np.float32), 2, 51)
            c = c * (1 + np.array([0.0, -0.05, 0.25]) * sheen[:, None])
            base[wood] = c
            rough[wood] = 0.3 + 0.08 * band
            height[wood] = -0.004 * band

    # Fittings: steel (the prod, plates, stirrup, lever, nut, bolt head) and trim (prod clamps, butt plate).
    for mask, kind in ((steel, 'steel'), (trim, 'trim')):
        if not mask.any():
            continue
        Pm = P[mask]
        brush = fbm(Pm * np.array([0.25, 14.0, 14.0], np.float32), 2, 61)
        blot = fbm(Pm * np.array([0.6, 0.6, 0.6], np.float32), 3, 63)
        if tier == 1:
            iron = srgb((0.27, 0.26, 0.25)) * (0.85 + 0.25 * blot[:, None])
            rust_t = ss(-0.05, 0.3, fbm(Pm * 0.45, 4, 65) + 0.25 * fbm(Pm * 3.0, 2, 66))
            rust_c = mix(srgb((0.42, 0.2, 0.08)), srgb((0.6, 0.33, 0.14)),
                         0.5 + 0.5 * fbm(Pm * 2.5, 2, 67))
            base[mask] = mix(iron, rust_c, rust_t)
            rough[mask] = 0.62 + 0.3 * rust_t
            metal[mask] = 1.0 - 0.95 * rust_t
            height[mask] = 0.02 * rust_t * (fbm(Pm * 6.0, 2, 68) * 0.5 + 0.5) + 0.006 * blot
        elif tier == 2:
            colour = srgb((0.66, 0.67, 0.69)) * (0.95 + 0.06 * brush[:, None])
            base[mask] = colour
            rough[mask] = 0.28 + 0.06 * brush + 0.05 * blot
            metal[mask] = 1.0
            height[mask] = 0.0015 * brush
        elif tier == 3:
            if kind == 'trim':
                engraving = fbm(Pm * 1.4 + 7.0, 3, 71) * 4.0
                engraved = 1 - ss(0.04, 0.09, np.abs((engraving % 1.0) - 0.5) - 0.4)
                base[mask] = srgb((1.0, 0.77, 0.36)) * (1 - 0.45 * engraved[:, None])
                rough[mask] = 0.16 + 0.2 * engraved
                height[mask] = -0.012 * engraved
            else:
                # Mirror steel: without an environment map a very low roughness renders nearly black away from the
                # highlight (the first bake's prod and plates read dark), so a polish of 0.2.
                base[mask] = srgb((0.93, 0.94, 0.96)) * (0.97 + 0.03 * brush[:, None])
                rough[mask] = 0.2 + 0.04 * blot
                height[mask] = 0.0
            metal[mask] = 1.0
        else:
            if kind == 'trim':
                base[mask] = srgb((0.86, 0.88, 0.92))
                rough[mask] = 0.22 + 0.04 * blot
            else:
                hue = 0.5 + 0.5 * fbm(Pm * np.array([0.15, 0.8, 0.8], np.float32), 3, 75)
                base[mask] = mix(srgb((0.3, 0.3, 0.45)), srgb((0.4, 0.3, 0.52)), hue) * (
                    0.9 + 0.12 * brush[:, None])
                rough[mask] = 0.26 + 0.06 * blot
            metal[mask] = 1.0
            height[mask] = 0.001 * brush

    # Leather: the laced grip sleeve over the wrist (criss-cross lacing raised over a pebbled hide).
    if hide.any():
        Pl = P[hide]
        ang = np.arctan2(Pl[:, 1] / 1.72, (Pl[:, 2] - 3.95) / 1.95)
        s1 = (Pl[:, 0] * 0.9 + ang * 0.9) % 1.0
        s2 = (Pl[:, 0] * 0.9 - ang * 0.9) % 1.0
        lace = np.maximum(1 - ss(0.07, 0.12, np.abs(s1 - 0.5)), 1 - ss(0.07, 0.12, np.abs(s2 - 0.5)))
        pebble = fbm(Pl * 7.0, 2, 81)
        hide_c, lace_c = {1: ((0.44, 0.31, 0.2), (0.62, 0.55, 0.42)), 2: ((0.2, 0.12, 0.07), (0.1, 0.06, 0.035)),
                          3: ((0.48, 0.035, 0.05), (1.0, 0.78, 0.38)), 4: ((0.13, 0.07, 0.2), (0.86, 0.88, 0.92))}[tier]
        c = mix(srgb(hide_c) * (0.9 + 0.12 * pebble[:, None]), srgb(lace_c), lace)
        if tier == 1:
            c = c * (1 - 0.35 * ss(0.6, 0.85, fbm(Pl * 2.0, 3, 83))[:, None])
        base[hide] = c
        laced_metal = 1.0 if tier in (3, 4) else 0.0
        metal[hide] = lace * laced_metal
        rough[hide] = (0.55 + 0.1 * pebble) * (1 - lace) + lace * (0.3 if laced_metal else 0.7)
        height[hide] = 0.03 * lace + 0.004 * pebble

    # Cord and fletching.
    if cord.any():
        Pc = P[cord]
        twist = np.sin(Pc[:, 0] * 9.0 + np.arctan2(Pc[:, 2] - 5.0, Pc[:, 1]) * 2.0) * 0.5 + 0.5
        cc = {1: (0.52, 0.45, 0.33), 2: (0.84, 0.79, 0.67), 3: (0.9, 0.72, 0.36), 4: (0.82, 0.84, 0.9)}[tier]
        base[cord] = srgb(cc) * (0.82 + 0.18 * twist[:, None])
        metal[cord] = {1: 0.0, 2: 0.0, 3: 0.6, 4: 0.6}[tier]
        rough[cord] = {1: 0.9, 2: 0.7, 3: 0.35, 4: 0.3}[tier]
        height[cord] = 0.004 * twist

    # Stones: iron bosses (low), steel bosses (mid), rubies (high), glowing crystals (legendary).
    if gem.any():
        Pg = P[gem]
        facet = 0.5 + 0.5 * fbm(Pg * 5.0, 2, 91)
        if tier == 1:
            base[gem] = srgb((0.2, 0.19, 0.18)) * (0.8 + 0.3 * facet[:, None])
            metal[gem], rough[gem] = 0.9, 0.6
        elif tier == 2:
            base[gem] = srgb((0.72, 0.73, 0.75))
            metal[gem], rough[gem] = 1.0, 0.18
        elif tier == 3:
            base[gem] = mix(srgb((0.42, 0.01, 0.025)), srgb((0.75, 0.05, 0.08)), facet)
            metal[gem], rough[gem] = 0.0, 0.05
        else:
            base[gem] = mix(srgb((0.25, 0.55, 0.9)), srgb((0.55, 0.35, 0.95)), facet)
            metal[gem], rough[gem] = 0.0, 0.08
            emit[gem] = mix(np.array([0.25, 0.8, 1.0]), np.array([0.6, 0.35, 1.0]), facet) * (
                0.65 + 0.35 * facet[:, None])

    # Legendary rune channels: along both sides of the stock at its centre line (over wood and the lock plates), and
    # along the prod's front and back faces at mid height.
    if tier == 4:
        chan = side & on_stock & (wood | steel) & (x > -27.6) & (x < 19.2)
        if chan.any():
            xc = x[chan]
            _, _, zc = stock_top_bottom(xc)
            t = z[chan] - zc
            line = 1 - ss(0.05, 0.09, np.abs(t))
            glyph = rune_glyphs(xc + 0.0 * y[chan], t, 101 + (y[chan] > 0))
            # The line breaks around each glyph so the marks stand in the channel.
            mark = np.maximum(line * (np.abs(t) < 0.09), glyph)
            colour = mix(np.array([0.2, 0.85, 1.0]), np.array([0.62, 0.32, 1.0]),
                         0.5 + 0.5 * np.sin(xc * 0.35))
            emit[chan] = np.maximum(emit[chan], colour * mark[:, None])
            base[chan] = mix(base[chan], colour * 0.6, mark)
            metal[chan] = metal[chan] * (1 - mark)
            rough[chan] = rough[chan] * (1 - mark) + 0.35 * mark
            height[chan] = height[chan] - 0.02 * mark
        pr = prod & (np.abs(N[:, 2]) < 0.55)
        if pr.any():
            # Along the prod: s the distance across the stock (|y|), the line at mid height.
            t = z[pr] - 4.6
            s = np.abs(y[pr])
            line = 1 - ss(0.04, 0.075, np.abs(t))
            glyph = rune_glyphs(s * 1.0, t * 1.4, 111 + (y[pr] > 0))
            mark = np.maximum(line, glyph * (s > 3.0))
            colour = mix(np.array([0.2, 0.85, 1.0]), np.array([0.62, 0.32, 1.0]), np.clip(s / 18.0, 0, 1))
            emit[pr] = np.maximum(emit[pr], colour * mark[:, None])
            base[pr] = mix(base[pr], colour * 0.6, mark)
            metal[pr] = metal[pr] * (1 - mark)
            rough[pr] = rough[pr] * (1 - mark) + 0.35 * mark
            height[pr] = height[pr] - 0.015 * mark
    if height_only:
        return height
    # Occlusion: a gentle darkening of the colour in the crevices (the Meshy route's grade used 0.5).
    base = base * (0.55 + 0.45 * ao)[:, None]
    return base, rough, metal, emit, height


# -- the texel set ------------------------------------------------------------------------------------------------------
def texels():
    """4096 rasters of the locked layout (cached): triangle id, barycentrics."""
    cache = os.path.join(WORK, 'maps', 'raster4k.npz')
    mesh = np.load(os.path.join(WORK, 'maps', 'mesh.npz'))
    if os.path.exists(cache) and os.path.getmtime(cache) > os.path.getmtime(os.path.join(WORK, 'maps', 'mesh.npz')):
        d = np.load(cache)
        return mesh, d['tid'], d['bary']
    tid, bary = post.rasterize(mesh['uv'], BIG)
    np.savez(cache, tid=tid.astype(np.int32), bary=bary.astype(np.float32))
    return mesh, tid.astype(np.int32), bary.astype(np.float32)


def to_build(mount):
    """glTF runtime coordinates -> the build frame (Blender: the stock along +X, up +Z)."""
    place = weapon_from_build(mount)
    gltf = np.array([[1.0, 0.0, 0.0], [0.0, 0.0, 1.0], [0.0, -1.0, 0.0]])
    turn = gltf.T @ place[:3, :3] @ gltf
    offset = gltf.T @ place[:3, 3]
    from_gltf = np.array([[1.0, 0.0, 0.0], [0.0, 0.0, -1.0], [0.0, 1.0, 0.0]])

    def points(v):
        b = v @ from_gltf.T
        return (b - offset) @ turn

    def dirs(v):
        return (v @ from_gltf.T) @ turn
    return points, dirs


def face_tangents(mesh):
    """Per triangle, the surface directions of +u and of up the image (post.py tangent_frames, per face)."""
    uv = mesh['uv'].astype(np.float64)
    p = mesh['pos'].astype(np.float64)
    du1, du2 = uv[:, 1] - uv[:, 0], uv[:, 2] - uv[:, 0]
    det = du1[:, 0] * du2[:, 1] - du1[:, 1] * du2[:, 0]
    det = np.where(np.abs(det) < 1e-12, 1e-12, det)
    e1, e2 = p[:, 1] - p[:, 0], p[:, 2] - p[:, 0]
    dpdx = (e1 * du2[:, 1:2] - e2 * du1[:, 1:2]) / det[:, None]
    dpdy = -(e2 * du1[:, 0:1] - e1 * du2[:, 0:1]) / det[:, None]
    return dpdx, dpdy


def bake(tier):
    out = os.path.join(WORK, f't{tier}')
    os.makedirs(out, exist_ok=True)
    mesh, tid, bary = texels()
    inside = tid >= 0
    idx = np.nonzero(inside.ravel())[0]
    tall = tid.ravel()[idx]
    ball = bary.reshape(-1, 3)[idx]
    dpdx, dpdy = face_tangents(mesh)
    points, dirs = to_build(KINDS[KIND]['mount'])
    ao_img = Image.open(os.path.join(WORK, 'maps', 'ao.png')).convert('L').resize((BIG, BIG), Image.BILINEAR)
    ao = (np.asarray(ao_img, np.float32) / 255).ravel()[idx]
    region = mesh['region'][tall]
    n = len(idx)
    base = np.zeros((n, 3), np.float32)
    rough = np.zeros(n, np.float32)
    metal = np.zeros(n, np.float32)
    emit = np.zeros((n, 3), np.float32)
    normal = np.zeros((n, 3), np.float32)
    eps = 0.012
    step = 500000
    for a in range(0, n, step):
        s = slice(a, min(a + step, n))
        t, b = tall[s], ball[s].astype(np.float64)
        pos = np.einsum('nc,nck->nk', b, mesh['pos'][t])
        nrm = np.einsum('nc,nck->nk', b, mesh['nrm'][t])
        nrm /= np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-9)
        tx, ty = dpdx[t], dpdy[t]
        tx = tx - nrm * np.sum(tx * nrm, 1, keepdims=True)
        tx /= np.maximum(np.linalg.norm(tx, axis=1, keepdims=True), 1e-12)
        ty = ty - nrm * np.sum(ty * nrm, 1, keepdims=True) - tx * np.sum(ty * tx, 1, keepdims=True)
        ty /= np.maximum(np.linalg.norm(ty, axis=1, keepdims=True), 1e-12)
        P, N = points(pos).astype(np.float32), dirs(nrm).astype(np.float32)
        TX, TY = dirs(tx).astype(np.float32), dirs(ty).astype(np.float32)
        reg, occ = region[s], ao[s]
        bc, r, m, e, _ = shade(P, N, reg, occ, tier)
        base[s], rough[s], metal[s], emit[s] = bc, r, m, e
        hx = (shade(P + eps * TX, N, reg, occ, tier, True) - shade(P - eps * TX, N, reg, occ, tier, True)) / (2 * eps)
        hy = (shade(P + eps * TY, N, reg, occ, tier, True) - shade(P - eps * TY, N, reg, occ, tier, True)) / (2 * eps)
        v = np.stack([-hx, -hy, np.ones_like(hx)], 1)
        normal[s] = v / np.linalg.norm(v, axis=1, keepdims=True)
        print(f'  tier {tier}: {min(a + step, n)} / {n}', flush=True)

    def image(values, fill):
        full = np.tile(np.asarray(fill, np.float32), (BIG * BIG, 1)) if np.ndim(fill) else np.full(BIG * BIG, fill,
                                                                                                    np.float32)
        full[idx] = values
        return full.reshape((BIG, BIG) + values.shape[1:])
    files = {'basecolor': os.path.join(out, 'basecolor.png'), 'normal': os.path.join(out, 'normal.png'),
             'mr': os.path.join(out, 'mr.png')}
    size = post.SIZE

    def save(array, path, target):
        Image.fromarray(np.clip(array * 255 + 0.5, 0, 255).astype(np.uint8)).resize((target, target),
                                                                                    Image.LANCZOS).save(path)
    save(post.linear_to_srgb(image(base, (0.0, 0.0, 0.0))), files['basecolor'], size)
    save(image(normal * 0.5 + 0.5, (0.5, 0.5, 1.0)), files['normal'], size)
    ao_full = image(ao, 1.0)
    mr = np.stack([np.clip(0.35 + 0.65 * ao_full, 0, 1), np.clip(image(rough, 0.6), 0.05, 1),
                   np.clip(image(metal, 0.0), 0, 1)], -1)
    save(mr, files['mr'], size // 2)
    if emit.max() > 0.02:
        files['emissive'] = os.path.join(out, 'emissive.png')
        save(post.linear_to_srgb(np.clip(image(emit, (0.0, 0.0, 0.0)), 0, 1)), files['emissive'], size)
    np.savez(os.path.join(WORK, 'maps', 'uv_tris.npz'), uv=mesh['uv'])
    subprocess.run([sys.executable, os.path.join(post.SHARED, 'gutter_fill.py'), os.path.join(WORK, 'maps', 'uv_tris.npz')]
                   + list(files.values()) + ['--in-place'], check=True, stdout=subprocess.DEVNULL)
    glb = os.path.join(out, f'w_{KIND}_t{tier}.glb')
    tris, verts = post.write_glb(glb, KIND, tier, mesh, files)
    stats = {'source': 'bake_crossbow.py (procedural, no Meshy)', 'tris': tris, 'verts': verts,
             'emissive': 'emissive' in files, 'glb_mb': round(os.path.getsize(glb) / 1e6, 2),
             'by_region': {k: {'base_srgb': post.linear_to_srgb(np.median(base[region == v], 0)).round(3).tolist(),
                               'rough': round(float(np.median(rough[region == v])), 2),
                               'metal': round(float(np.median(metal[region == v])), 2)}
                           for k, v in R.items() if (region == v).any()}}
    json.dump(stats, open(os.path.join(out, 'post.json'), 'w'), indent=1)
    print('BAKE', KIND, tier, json.dumps(stats)[:300])


if __name__ == '__main__':
    for tier_arg in sys.argv[1:]:
        bake(int(tier_arg))
