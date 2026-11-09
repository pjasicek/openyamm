#!/usr/bin/env python3
"""Procedural textures for the MM7 plants batch (ferns, cacti, the Joshua tree, the broad-leaved plant and the potted
plants), painted with numpy/PIL at supersampling. No external images. The paint surface (Canvas, rib_base,
radial_spines, the prickly-pear pad painter) is imported from the MM6 succulents pipeline
(../../mm6_new_sorpigal_3d/succulents/scripts/make_textures.py), with its output folder pointed at plants/textures.
Colours are sRGB values measured from the native MM7 sprites.

Each texture writes textures/<name>_basecolor.png (RGB, or RGBA for cut-out atlases) and <name>_normal.png (OpenGL
tangent space; tools/link_static_model_lods.py converts it to the glTF convention). Every texture has its own seed.
Atlas cell rectangles are listed in common.CELLS. Usage: make_textures.py [name ...] (default: all)."""
import math, os, sys
import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, 'scripts'))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'mm6_new_sorpigal_3d', 'succulents', 'scripts'))
import make_textures as mm6          # noqa: E402  (MM6 succulents painter)
from common import CELLS            # noqa: E402

mm6.OUT = os.path.join(HERE, 'textures')
os.makedirs(mm6.OUT, exist_ok=True)
Canvas, mix, rib_base, radial_spines = mm6.Canvas, mm6.mix, mm6.rib_base, mm6.radial_spines


def c255(*rgb):
    return tuple(c / 255.0 for c in rgb)


def clamp(c):
    return [min(max(float(x), 0.0), 1.0) for x in c]


def scale(c, f):
    return clamp([x * f for x in c])


class Cell:
    """A rectangle of an atlas with isotropic local coordinates: x 0..1 across, y 0..aspect down (aspect = cell height
    / cell width), so shapes keep their proportions in non-square cells."""

    def __init__(self, cv, rect):
        self.cv = cv
        self.u0, self.v0, self.u1, self.v1 = rect
        self.aspect = ((self.v1 - self.v0) * cv.H) / ((self.u1 - self.u0) * cv.W)

    def p(self, x, y):
        return (self.u0 + x * (self.u1 - self.u0), self.v0 + (y / self.aspect) * (self.v1 - self.v0))

    def width(self, w):
        """A width in local units as the Canvas.stroke width (x units of the whole image)."""
        return w * (self.u1 - self.u0)


def leaf(cell, x, y, angle, length, width, light, dark, rib=None, h=0.6, lobes=0, lobe_depth=0.3, skew=0.8,
         tip=1.0, curl=0.0, steps=10):
    """A leaf from (x, y) in direction `angle` (0 = up, positive = clockwise toward +x): a lens (half-width
    width/2 * (4 t (1 - t))^0.6 over t^skew), the left half `light` and the right half `dark` as a leaf folded along
    its midrib, an optional midrib stroke and `lobes` saw-teeth along each edge. `curl` bends the axis."""
    cv = cell.cv
    axis = []
    px, py, a = x, y, angle
    for i in range(steps + 1):
        axis.append((px, py, a))
        a += curl / steps
        px += math.sin(a) * length / steps; py -= math.cos(a) * length / steps
    halves = ([], [])
    for i, (ax, ay, aa) in enumerate(axis):
        t = i / steps
        tt = t ** skew
        w = width * 0.5 * (4 * tt * (1 - tt)) ** 0.6 * (1 - (1 - tip) * t)
        if lobes:
            w *= 1 - lobe_depth * abs(math.sin(math.pi * lobes * t))
        nx, ny = math.cos(aa), math.sin(aa)
        halves[0].append((ax - nx * w, ay - ny * w))
        halves[1].append((ax + nx * w, ay + ny * w))
    mid = [(ax, ay) for ax, ay, _ in axis]
    for side, col in ((0, light), (1, dark)):
        pts = mid + halves[side][::-1]
        cv.poly([cell.p(*q) for q in pts], cv.jitter(col, 0.05), h, hmode='max')
    if rib is not None:
        cv.stroke([cell.p(*q) for q in mid[:-2]], cell.width(width * 0.09), cell.width(width * 0.02), rib, rib,
                  h + 0.15, h + 0.1)


# =================================================================== fronds atlas (four 256 x 1024 strips)
def frond(cell, rng, pinnae, length_max, angle, rachis, light, dark, light_tip, dark_tip, lobes=0, pinna_width=0.28,
          droop=0.0, rachis_w=0.035, rib=None, length_profile=(0.15, 0.85), x0=0.5, curve=0.0, skip=0.0, tint=None,
          spray=False, taper=0.4):
    """A pinnate frond along the strip: rachis from the bottom centre to the top, `pinnae` leaflets per side, longest
    a third of the way up, angled `angle` toward the tip (`droop` turns the outer ones down)."""
    top = 0.04
    bottom = cell.aspect - 0.01
    n = 24
    pts = []
    for i in range(n + 1):
        t = i / n
        pts.append((x0 + curve * math.sin(math.pi * t) * 0.5, bottom - (bottom - top) * t))
    cell.cv.stroke([cell.p(*q) for q in pts], cell.width(rachis_w), cell.width(rachis_w * 0.3), rachis,
                   scale(rachis, 1.15), 0.7, 0.6)
    for k in range(pinnae):
        t = (k + 0.5) / pinnae
        i = min(int(t * n), n - 1); f = t * n - i
        px = pts[i][0] + (pts[i + 1][0] - pts[i][0]) * f; py = pts[i][1] + (pts[i + 1][1] - pts[i][1]) * f
        a0, a1 = length_profile
        L = length_max * math.sin(math.pi * (a0 + a1 * t) ** 0.9) * (1 - 0.55 * t)
        if spray:                                       # leafy to the tip (sprays, palm fronds)
            L = length_max * (0.8 + 0.2 * math.sin(math.pi * t)) * (1 - taper * t * t)
        L = max(L, length_max * 0.12)
        for side in (-1, 1):
            if rng.uniform() < skip:
                continue
            jitter = rng.normal(0, 0.08)
            ang = side * (angle + droop * t + jitter)
            ll = L * rng.uniform(0.85, 1.05)
            lc = mix(light, light_tip, t * rng.uniform(0.6, 1.0)).tolist()
            dc = mix(dark, dark_tip, t * rng.uniform(0.6, 1.0)).tolist()
            if tint is not None and rng.uniform() < tint[1]:
                lc = mix(lc, tint[0], rng.uniform(0.3, 0.7)).tolist(); dc = mix(dc, tint[0], 0.3).tolist()
            if side < 0:
                lc, dc = dc, lc
            leaf(cell, px, py + 0.004, ang, ll, ll * pinna_width, lc, dc, rib=rib, lobes=lobes, lobe_depth=0.45,
                 curl=side * rng.normal(0.15, 0.1), h=0.5 + 0.2 * rng.uniform())


def tex_fronds():
    """Four frond strips: the bush03 fern, the plant01a leafy spray, the plant02a / plant01a palm frond, and a
    withered tan frond for plant01b / plant03b (painted upright; the build hangs it)."""
    cv = Canvas(1024, 1024, 2, False, 7301)
    cv.a[:] = 0
    rng = cv.rng
    # fern (bush03): bright yellow-green lobed pinnae with dark undersides; the sprite's mid (45,93,20), light
    # (121,183,65), dark (13,33,9)
    frond(Cell(cv, CELLS['fern_a']), rng, 36, 0.66, 0.95, c255(60, 90, 28), c255(110, 172, 55), c255(38, 82, 18),
          c255(150, 200, 80), c255(60, 120, 28), lobes=5, pinna_width=0.42, droop=0.25, spray=True,
          taper=0.7)
    # leafy spray (plant01a): few broad lance leaves close to the stem, yellow-green, to the tip
    frond(Cell(cv, CELLS['spray']), rng, 13, 0.62, 0.42, c255(70, 90, 30), c255(150, 170, 60), c255(50, 80, 24),
          c255(190, 196, 90), c255(70, 104, 30), pinna_width=0.30, droop=0.1, rib=c255(170, 180, 90), spray=True)
    leaf(Cell(cv, CELLS['spray']), 0.5, 0.20, 0.0, 0.18, 0.06, c255(170, 180, 70), c255(80, 110, 34))
    # palm frond (plant02a): long narrow pinnae, light green with pale midribs and a few pinkish tips
    frond(Cell(cv, CELLS['palm']), rng, 30, 0.80, 0.70, c255(70, 96, 40), c255(132, 170, 80), c255(54, 92, 34),
          c255(170, 200, 110), c255(80, 124, 52), pinna_width=0.18, droop=0.2, rib=c255(190, 210, 150),
          tint=(c255(190, 130, 140), 0.12), spray=True)
    # withered frond (plant01b / plant03b): tan and brown lobed pinnae, a little sparse
    frond(Cell(cv, CELLS['dry']), rng, 24, 0.74, 0.85, c255(90, 70, 40), c255(172, 140, 80), c255(96, 72, 38),
          c255(140, 112, 64), c255(70, 52, 30), lobes=5, pinna_width=0.30, droop=0.3, skip=0.08,
          tint=(c255(140, 90, 110), 0.10))
    mott = cv.noise(2.0)
    cv.col *= (0.9 + 0.2 * mott)[..., None]
    cv.save('fronds', strength=4.0, cutout=True)


# =================================================================== leaves atlas
def broad_leaf(cell, rng, light, dark, variegate=None, rib=None, wilt=None, brown_edge=None):
    """One broad ovate leaf filling its cell (base at the bottom centre, tip at the top), with lateral veins, optional
    cream variegation (dieffenbachia), browned margins (wilting)."""
    cv = cell.cv
    L = cell.aspect * 0.96
    x, y = 0.5, cell.aspect - 0.01
    leaf(cell, x, y, 0.0, L, 0.94, light, dark, rib=None, skew=0.75, h=0.5, steps=18)
    # variegation: cream patches between the veins, kept off the margin
    u0, v0, u1, v1 = cell.u0, cell.v0, cell.u1, cell.v1
    sl = (slice(int(v0 * cv.H), int(v1 * cv.H)), slice(int(u0 * cv.W), int(u1 * cv.W)))
    hh, ww = cv.a[sl].shape
    yy, xx = np.mgrid[0:hh, 0:ww].astype(np.float32)
    lx = (xx + 0.5) / ww; ly = (yy + 0.5) / hh * cell.aspect
    t = np.clip((y - ly) / L, 0, 1)
    tt = t ** 0.75
    half = 0.47 * (4 * tt * (1 - tt)) ** 0.6 + 1e-4
    across = np.abs(lx - x) / half                          # 0 midrib .. 1 margin
    inside = cv.a[sl] > 0.5
    if variegate is not None:
        n = cv.noise(1.6, (1.0, 1.0), size=(hh, ww))
        streak = 0.5 + 0.5 * np.sin(across * 9.0 + t * 3.0 + n * 3.0)
        m = np.clip((n * 0.7 + streak * 0.5 - 0.30) * 4, 0, 1) * np.clip((0.86 - across) * 4, 0, 1) * inside
        cv.col[sl] = mix(cv.col[sl], variegate, m * 0.95)
    if brown_edge is not None:
        n = cv.noise(2.0, (1.0, 1.0), size=(hh, ww))
        m = np.clip((across + t * 0.6 + n * 0.5 - brown_edge[1]) * 3, 0, 1) * inside
        cv.col[sl] = mix(cv.col[sl], brown_edge[0], m)
    # lateral veins: darker grooves curving to the margin
    vein = np.abs(np.sin((t * 11.0 - across * 1.6) * math.pi))
    cv.col[sl] *= (1 - 0.12 * np.clip(1 - vein * 4, 0, 1) * inside)[..., None]
    cv.hgt[sl] -= 0.12 * np.clip(1 - vein * 4, 0, 1) * inside
    if rib is not None:
        cv.stroke([cell.p(x, y - L * f) for f in np.linspace(0, 0.92, 8)], cell.width(0.05), cell.width(0.01), rib,
                  rib, 0.8, 0.6)


def leaf_clump(cell, rng, count, light, dark, highlight, twig):
    """plant11a: twigs from the bottom centre with many small pointed ovate leaves, bright on top."""
    cv = cell.cv
    for k in range(7):
        a = rng.uniform(-0.9, 0.9)
        pts = [(0.5, cell.aspect)]
        x, y = 0.5, cell.aspect
        for s in range(6):
            x += math.sin(a) * 0.12; y -= math.cos(a) * 0.12; a += rng.normal(0, 0.1)
            pts.append((x, y))
        cv.stroke([cell.p(*q) for q in pts], cell.width(0.02), cell.width(0.006), twig, scale(twig, 1.2), 0.3, 0.4)
    for k in range(count):
        r = math.sqrt(rng.uniform(0, 1)) * 0.42
        th = rng.uniform(0, 2 * math.pi)
        cx, cy = 0.5 + math.cos(th) * r, 0.5 * cell.aspect + math.sin(th) * r * 0.95
        up = (0.5 * cell.aspect - cy) / 0.42                 # +1 top .. -1 bottom
        lc = mix(dark, light, np.clip(0.55 + 0.45 * up + rng.normal(0, 0.25), 0, 1)).tolist()
        if rng.uniform() < 0.18:
            lc = mix(lc, highlight, 0.7).tolist()
        size = rng.uniform(0.08, 0.13)
        leaf(cell, cx, cy, rng.uniform(-2.2, 2.2), size, size * 0.62, lc, scale(lc, 0.72), skew=0.7,
             h=0.5 + 0.4 * rng.uniform(), steps=6)


def grass_strands(cell, rng, count, colours, spread=1.2):
    """plant07b: long thin arching dry blades from the bottom centre, brown, rust and lilac."""
    cv = cell.cv
    for k in range(count):
        a = rng.normal(0, 0.45) * spread
        L = rng.uniform(0.45, 0.95) * cell.aspect
        bend = math.copysign(rng.uniform(0.6, 2.4), a + rng.normal(0, 0.2))
        x, y = 0.5 + rng.normal(0, 0.02), cell.aspect - 0.005
        pts = [(x, y)]
        for s in range(10):
            aa = a + bend * (s / 10) ** 1.6
            x += math.sin(aa) * L / 10; y -= math.cos(aa) * L / 10
            pts.append((min(max(x, 0.02), 0.98), max(y, 0.02)))
        c = colours[int(rng.integers(len(colours)))]
        c = cv.jitter(c, 0.12)
        cv.stroke([cell.p(*q) for q in pts], cell.width(rng.uniform(0.018, 0.03)), cell.width(0.004), scale(c, 0.7),
                  scale(c, 1.15), 0.4, 0.8)


def stem_strip(cell, colour, dark):
    cv = cell.cv
    pts = [cell.p(0.0, 0), cell.p(1.0, 0), cell.p(1.0, cell.aspect), cell.p(0.0, cell.aspect)]

    def fill(X, Y):
        lx = (X - cell.u0) / (cell.u1 - cell.u0)
        return mix(dark, colour, np.clip(np.sin(np.clip(lx, 0, 1) * math.pi), 0, 1) ** 0.7)
    cv.poly(pts, fill, 0.4)


def tex_leaves():
    """Leaves atlas: four broad leaves (bush02 variegated and dark; plant04b green and wilted brown), the plant11a
    leaf clump, the plant07b dry grass and two opaque stem strips (green, woody)."""
    cv = Canvas(1024, 1024, 2, False, 7302)
    cv.a[:] = 0
    rng = cv.rng
    # bush02 pale leaves (revision 2): cream variegation over most of the blade, green margins and veins (the
    # sprite's light quartile is 188, 201, 148)
    broad_leaf(Cell(cv, CELLS['leaf_var']), rng, c255(178, 188, 120), c255(118, 136, 76),
               variegate=c255(232, 230, 182), rib=c255(236, 234, 196))
    broad_leaf(Cell(cv, CELLS['leaf_dark']), rng, c255(84, 92, 80), c255(42, 46, 42), rib=c255(110, 118, 96))
    broad_leaf(Cell(cv, CELLS['leaf_green']), rng, c255(84, 130, 60), c255(40, 80, 36), rib=c255(150, 180, 110),
               brown_edge=(c255(120, 96, 50), 1.25))
    broad_leaf(Cell(cv, CELLS['leaf_wilt']), rng, c255(150, 120, 70), c255(90, 66, 40), rib=c255(170, 150, 100),
               brown_edge=(c255(70, 50, 34), 0.95))
    leaf_clump(Cell(cv, CELLS['clump']), rng, 150, c255(150, 190, 60), c255(30, 52, 14), c255(200, 220, 90),
               c255(80, 60, 40))
    grass_strands(Cell(cv, CELLS['grass']), rng, 75, [c255(150, 104, 56), c255(120, 76, 46), c255(100, 72, 74),
                                                      c255(170, 132, 76), c255(96, 72, 44), c255(130, 96, 50)])
    stem_strip(Cell(cv, CELLS['stem_green']), c255(110, 140, 70), c255(50, 70, 30))
    stem_strip(Cell(cv, CELLS['stem_wood']), c255(120, 96, 70), c255(60, 46, 34))
    cv.save('leaves', strength=4.0, cutout=True)


# =================================================================== cactus skins (u = one rib, valley at 0 and 1)
def areole_row(cv, rows, felt, spine_base, spine_tip, count, length, width, centrals=None):
    for v in rows:
        cv.ellipse(0.5, v, 0.10, 0.018, felt, 0.8, n=10)
        radial_spines(cv, 0.5, v, count, length, width, spine_base, spine_tip, curve=0.1, h=1.0, lmin=0.5)
        if centrals:
            radial_spines(cv, 0.5, v, 2, centrals, width * 1.2, spine_base, spine_tip, spread=(-2.2, -0.9),
                          rot=0.0, curve=0.05, h=1.2)


def tex_bush10_skin():
    """bush10 (small saguaro): one rounded rib 256 x 512 (0.12 x 0.24 m): mid green, darker valleys, a paler crest,
    black areoles with short dark spines four per tile."""
    cv = Canvas(256, 512, 3, True, 7310)
    rib_base(cv, c255(40, 72, 34), c255(96, 150, 76), c255(150, 200, 124), crest_width=0.35, streaks=0.10,
             mottle=0.12)
    rows = [(k + 0.4) / 4 for k in range(4)]
    areole_row(cv, rows, c255(30, 34, 24), c255(20, 22, 16), c255(60, 56, 44), 7, 0.22, 0.02, centrals=0.16)
    cv.save('bush10_skin', strength=4.0)


def tex_bush10_spines():
    """bush10 spine rim (revision 2): fringe tile 256 x 512 (u = 0 on the crest -> 1 outward, v along 0.24 m of
    crest): two areoles per tile, each with three or four long black-brown spines curving outward, as the sprite's."""
    cv = Canvas(256, 512, 3, True, 7314)
    cv.a[:] = 0
    for v in (0.25, 0.75):
        for s in range(int(cv.rng.integers(3, 5))):
            a = cv.rng.normal(0, 0.5)
            L = cv.rng.uniform(0.55, 0.95)
            bend = cv.rng.normal(0, 0.25)
            pts = [(0.02, v)]
            x, y = 0.02, v
            for k in range(4):
                aa = a + bend * k / 3
                x += math.cos(aa) * L / 4; y += math.sin(aa) * L / 4 * 0.25
                pts.append((min(x, 0.98), y))
            cv.stroke(pts, 0.07, 0.015, c255(24, 22, 16), c255(70, 60, 44), 0.8, 1.0)
    cv.save('bush10_spines', strength=2.0, cutout=True)


def tex_bush11_skin():
    """bush11 (tall pale column): one shallow rib 256 x 512 (0.12 x 0.24 m): pale sea-green flanks with fine
    streaks, a light crest and dense cream areoles with short yellow-red spines (the long ones are fringe cards)."""
    cv = Canvas(256, 512, 3, True, 7311)
    rib_base(cv, c255(70, 110, 60), c255(116, 164, 98), c255(176, 210, 144), crest_width=0.4, streaks=0.12,
             mottle=0.15)
    rows = [(k + 0.5) / 6 for k in range(6)]
    areole_row(cv, rows, c255(200, 196, 150), c255(170, 120, 80), c255(230, 220, 170), 8, 0.2, 0.018)
    cv.save('bush11_skin', strength=4.0)


def tex_bush11_spines():
    """Long spine fringe strip for bush11's crests (256 x 512, u = 0 on the crest -> 1 outward, v along the crest):
    a row of cream spines with red-brown bases fanning out from six areoles per tile."""
    cv = Canvas(256, 512, 3, True, 7312)
    cv.a[:] = 0
    for k in range(6):
        v = (k + 0.5) / 6
        for s in range(4):
            a = cv.rng.normal(0, 0.45)
            L = cv.rng.uniform(0.6, 0.95)
            x1 = 0.02 + math.cos(a) * L; y1 = v + math.sin(a) * L * 0.25
            cv.stroke([(0.02, v), ((0.02 + x1) * 0.6, (v + y1) * 0.5), (x1, y1)], 0.03, 0.008, c255(226, 214, 170),
                      c255(170, 90, 90), 0.8, 1.0)
    cv.save('bush11_spines', strength=2.0, cutout=True)


def tex_bush13_skin():
    """bush13 (candelabra): one deep rib 256 x 512 (0.16 x 0.32 m): dark green flanks, near-black valleys, a pale
    yellow-green crest stripe with red-brown areoles and short spines, five per tile."""
    cv = Canvas(256, 512, 3, True, 7313)
    rib_base(cv, c255(10, 28, 8), c255(42, 92, 32), c255(140, 168, 84), crest_width=0.26, streaks=0.10, mottle=0.12)
    rows = [(k + 0.5) / 5 for k in range(5)]
    for v in rows:
        cv.ellipse(0.5, v, 0.07, 0.016, c255(120, 50, 40), 0.9, n=10)
        radial_spines(cv, 0.5, v, 6, 0.14, 0.018, c255(110, 50, 40), c255(200, 170, 140), curve=0.1, h=1.0, lmin=0.5)
    cv.save('bush13_skin', strength=4.0)


def lumpy_pad(cv, cell, rx, ry, dark, mid, light, seed):
    """One fleshy pad in a cell (revision 2, adapted from the MM6 pad painter): an obovate oval round (0.5, 0.52)
    with semi-axes rx, ry whose outline wobbles by a few per cent, lit from the upper left, lumpy (raised bumps in
    the height field, glossy pale tops, dark hollows) and with jittered areoles: small raised bumps with a dark centre."""
    rng = np.random.default_rng(seed)
    harm = [(k, rng.uniform(0.015, 0.04) / k ** 0.5, rng.uniform(0, 2 * math.pi)) for k in (2, 3, 5, 7)]

    def wobble(t):
        return 1 + sum(a * math.sin(k * t + ph) for k, a, ph in harm)
    cx, cy = 0.5, 0.52
    pts = []
    for k in range(64):
        t = 2 * math.pi * k / 64
        dy = math.sin(t)
        wx = rx * (1 + 0.12 * max(min(-dy, 1), -1))
        r = wobble(t)
        pts.append(mm6.cell_xy(cell, cx + math.cos(t) * wx * r, cy + dy * ry * r))
    x0, y0 = mm6.cell_xy(cell, 0, 0)
    sl = (slice(int(y0 * cv.H), int((y0 + 0.5) * cv.H)), slice(int(x0 * cv.W), int((x0 + 0.5) * cv.W)))
    before = cv.a[sl].copy()
    cv.poly(pts, mid, None)
    hh, ww = cv.a[sl].shape
    yy, xx = np.mgrid[0:hh, 0:ww].astype(np.float32)
    lx = ((xx + 0.5) / ww - cx) / rx; ly = ((yy + 0.5) / hh - cy) / ry
    r = np.sqrt(lx * lx + ly * ly)
    inside = (cv.a[sl] > before + 0.01).astype(np.float32)
    lumps = cv.noise(2.0, size=(hh, ww)); fine = cv.noise(0.8, size=(hh, ww))
    light_dir = np.clip(0.5 - 0.35 * lx - 0.45 * ly, 0, 1)                   # upper left lit
    shade = np.clip(light_dir * 0.8 + (lumps - 0.5) * 0.9 + (1 - np.clip(r, 0, 1)) * 0.25, 0, 1)
    col = mix(dark, mid, np.clip(shade * 1.6, 0, 1))
    col = mix(col, light, np.clip((shade - 0.5) * 2.2, 0, 1))
    col *= (0.9 + 0.2 * fine)[..., None]
    col = mix(col, dark, np.clip((r - 0.86) / 0.14, 0, 1) * 0.55)             # a soft dark rim, not a hard outline
    cv.col[sl] = np.where(inside[..., None] > 0, col, cv.col[sl])
    cv.hgt[sl] = np.where(inside > 0, np.sqrt(np.clip(1 - r * r, 0, 1)) * 0.5 + (lumps - 0.5) * 0.8, cv.hgt[sl])
    for i in range(45):
        ax, ay = rng.uniform(-0.9, 0.9), rng.uniform(-0.9, 0.9)
        if ax * ax + ay * ay > 0.75:
            continue
        gx, gy = mm6.cell_xy(cell, cx + ax * rx, cy + ay * ry)
        cv.ellipse(gx, gy, 0.010, 0.010, scale(mid, 1.25), 0.5, opacity=0.6, n=10, hmode='add')
        cv.ellipse(gx, gy, 0.0035, 0.0035, dark, 0.3, opacity=0.8, n=8, hmode='add')


def tex_bush16_pads():
    """bush16 prickly pear: four fleshy, lumpy pad cells (no fruit), dark to glossy green as the sprite's."""
    cv = Canvas(1024, 1024, 2, False, 7316)
    for cell, (rx, ry), gain in ((0, (0.33, 0.45), 1.0), (1, (0.36, 0.44), 0.9), (2, (0.30, 0.45), 1.1),
                                 (3, (0.35, 0.43), 0.95)):
        lumpy_pad(cv, cell, rx, ry, c255(14, 34, 10), scale(c255(62, 120, 40), gain), scale(c255(170, 216, 128), gain),
                  73160 + cell)
    cv.save('pads_bush16', strength=6.0, cutout=True)


# =================================================================== Joshua tree (bush12)
def tex_joshua():
    """bush12 rosette atlas (512²): cell 'burst' a full star of stiff spiky leaves (dark green centre, yellow-green
    to pale straw tips) for crossed rosette cards; 'half' an upward half-star for the rosette tops."""
    cv = Canvas(1024, 512, 2, False, 7320)
    cv.a[:] = 0
    rng = cv.rng
    for name, full in (('burst', True), ('half', False)):
        cell = Cell(cv, CELLS[name])
        cx, cy = 0.5, (0.5 if full else 0.98) * cell.aspect
        n = 220 if full else 120
        order = sorted(range(n), key=lambda k: rng.uniform())
        for k in order:
            a = rng.uniform(-math.pi, math.pi) if full else rng.uniform(-1.45, 1.45)
            L = rng.uniform(0.25, 0.47) if full else rng.uniform(0.45, 0.95) * 0.5
            depth = rng.uniform()                               # 0 back .. 1 front (painted later = on top)
            base = mix(c255(16, 28, 12), c255(46, 66, 30), depth).tolist()
            tipc = mix(c255(90, 110, 50), c255(196, 200, 136), depth * rng.uniform(0.6, 1.0)).tolist()
            x1 = cx + math.sin(a) * L; y1 = cy - math.cos(a) * L
            droop = 0.03 * abs(math.sin(a))
            cv.stroke([cell.p(cx, cy), cell.p((cx + x1) / 2, (cy + y1) / 2 + droop * 0.5), cell.p(x1, y1 + droop)],
                      cell.width(0.014), cell.width(0.003), cv.jitter(base, 0.08), cv.jitter(tipc, 0.08), 0.5, 0.9)
        if full:
            cv.ellipse(*cell.p(cx, cy), 0.02, 0.04, c255(14, 20, 10), 0.4)
    cv.save('joshua', strength=3.0, cutout=True)


def tex_joshbark():
    """bush12 trunk: pale grey-olive shaggy bark, 512² tile (0.5 x 1.0 m): overlapping downward-pointing dead-leaf
    scales with dark gaps, streaked along the stem."""
    cv = Canvas(512, 512, 2, True, 7321)
    cv.fill(c255(70, 70, 50), 0.0)
    rng = cv.rng
    for k in range(900):
        x, y = rng.uniform(0, 1), rng.uniform(0, 1)
        L = rng.uniform(0.05, 0.12); w = rng.uniform(0.012, 0.025)
        c = mix(c255(110, 110, 80), c255(190, 186, 150), rng.uniform()).tolist()
        cv.stroke([(x, y), (x + rng.normal(0, 0.006), y + L)], w, w * 0.25, cv.jitter(c, 0.08),
                  cv.jitter(scale(c, 0.75), 0.08), 0.8, 0.4)
    n = cv.noise(1.5, (0.4, 3.0))
    cv.col *= (0.8 + 0.4 * n)[..., None]
    cv.save('joshbark', strength=4.0)


# =================================================================== pots (512², u around, v up the profile)
def crackle(cv, density, rng_scale=1.0):
    """Voronoi-style crack network: returns a 0..1 crack mask (1 on the cracks) at canvas resolution."""
    rng = cv.rng
    pts = rng.uniform(0, 1, size=(int(density), 2))
    small = 256
    yy, xx = np.mgrid[0:small, 0:small].astype(np.float32) / small
    best = np.full((small, small), 9.0, np.float32); second = best.copy()
    for px, py in pts:
        dx = np.abs(xx - px); dx = np.minimum(dx, 1 - dx)
        dy = np.abs(yy - py); dy = np.minimum(dy, 1 - dy)
        d = np.sqrt(dx * dx + dy * dy)
        second = np.where(d < best, best, np.minimum(second, d)); best = np.minimum(best, d)
    edge = np.clip(1 - (second - best) * small / 1.2, 0, 1)
    from PIL import Image
    im = Image.fromarray((edge * 255).astype(np.uint8)).resize((cv.W, cv.H), Image.BILINEAR)
    return np.asarray(im, np.float32) / 255.0


def pot_texture(name, seed, base, dark, light, crack=None, patches=None, bands=(), diamonds=None, holes=0,
                soil=None, mottle=0.25, rings=0.0, veins=None):
    """A pot surface tile: v (image rows, top = rim) runs down the profile; u wraps round. base colour with mottle,
    optional crackle, lighter peeled patches, horizontal bands (v0, v1, colour), a diamond band, dark broken holes,
    and the top rows (v < 0.06) left as the soil swatch."""
    cv = Canvas(512, 512, 2, True, seed)
    m1 = cv.noise(2.2); m2 = cv.noise(1.4, (1.0, 1.0))
    col = mix(dark, base, np.clip(m1 * 1.4 - 0.1, 0, 1))
    col = mix(col, light, np.clip((m2 - 0.62) * 3.0, 0, 1) * mottle * 2)
    speck = cv.noise(0.3)
    col *= (0.88 + 0.24 * speck)[..., None]
    cv.col[:] = col; cv.a[:] = 1; cv.hgt[:] = m1 * 0.15 + speck * 0.08
    x, y = cv.grid()
    if rings:
        r = 0.5 + 0.5 * np.sin(y * math.pi * 2 * 14)
        cv.col *= (1 - rings * r)[..., None]; cv.hgt -= r * 0.1
    if veins is not None:
        cr = crackle(cv, 40)
        n = cv.noise(1.8)
        v = np.clip(cr * 1.3 - 0.3, 0, 1) * np.clip(n * 2 - 0.2, 0, 1)
        cv.col[:] = mix(cv.col, veins, v * 0.9); cv.hgt -= v * 0.2
    if crack is not None:
        cr = crackle(cv, crack[1])
        cv.col[:] = mix(cv.col, crack[0], cr * 0.45); cv.hgt -= cr * 0.3
    if patches is not None:
        n = cv.noise(1.7)
        p = np.clip((n - patches[1]) * 10, 0, 1)
        cv.col[:] = mix(cv.col, patches[0], p); cv.hgt += p * 0.15
    for v0, v1, c in bands:
        b = ((y >= v0) & (y < v1)).astype(np.float32)
        cv.col[:] = mix(cv.col, c, b * 0.85); cv.hgt += b * 0.1
    if diamonds is not None:
        v0, v1, c, count = diamonds
        t = (y - v0) / (v1 - v0)
        inside = (t >= 0) & (t <= 1)
        phase = (x * count) % 1.0
        d = np.abs(phase - 0.5) * 2 + np.abs(t - 0.5) * 2
        dm = (inside & (d < 0.85) & (d > 0.45)).astype(np.float32)
        cv.col[:] = mix(cv.col, c, dm * 0.9)
    for k in range(holes):
        hx, hy = cv.rng.uniform(0, 1), cv.rng.uniform(0.45, 0.85)
        pts = []
        for j in range(10):
            a = 2 * math.pi * j / 10
            r = (0.05 if j % 2 == 0 else 0.022) * cv.rng.uniform(0.7, 1.3)
            pts.append((hx + math.cos(a) * r, hy + math.sin(a) * r * 1.4))
        cv.poly(pts, scale(dark, 0.25), -0.4, hmode='set')
    if soil is not None:
        s = (y < 0.06).astype(np.float32)
        n = cv.noise(0.8)
        cv.col[:] = mix(cv.col, np.asarray(soil, np.float32)[None, None] * (0.7 + 0.6 * n)[..., None], s)
    cv.save(name, strength=4.0)


def tex_pots():
    soil = c255(52, 38, 26)
    # plant01a glazed ochre amphora: cream rings and a yellow diamond band below the neck (v from the rim down)
    pot_texture('pot_gold', 7330, c255(196, 130, 52), c255(150, 84, 28), c255(236, 188, 90), mottle=0.35,
                bands=((0.345, 0.352, c255(230, 200, 130)), (0.42, 0.427, c255(230, 200, 130)),
                       (0.44, 0.447, c255(230, 200, 130)), (0.47, 0.475, c255(230, 200, 130))),
                diamonds=(0.355, 0.415, c255(232, 196, 80), 8), soil=soil)
    # plant01b worn olive-brass amphora with throwing rings, pale crackled patches and broken holes
    pot_texture('pot_brass', 7331, c255(156, 136, 70), c255(90, 78, 36), c255(200, 182, 110), rings=0.12,
                crack=(c255(50, 40, 20), 160), patches=(c255(190, 176, 116), 0.86), holes=3, soil=soil)
    # plant07b dark green bronze-patina amphora with flaking pale patches
    pot_texture('pot_patina', 7332, c255(56, 72, 52), c255(28, 36, 28), c255(96, 112, 80),
                crack=(c255(14, 16, 12), 140), patches=(c255(150, 150, 100), 0.66), soil=soil)
    # plant04b dark grey-olive stone amphora with ochre lichen mottle and broken holes
    pot_texture('pot_stone', 7333, c255(98, 94, 66), c255(44, 42, 32), c255(156, 140, 90), mottle=0.4,
                crack=(c255(24, 22, 18), 150), holes=4, soil=soil)
    # plant11a / plant02a terracotta: red-brown clay with a crackle network
    pot_texture('pot_clay', 7334, c255(118, 58, 40), c255(74, 34, 24), c255(150, 84, 62), mottle=0.3,
                crack=(c255(60, 26, 18), 220), soil=soil)
    # plant03b green-grey marble planter with dark veins
    pot_texture('pot_marble', 7335, c255(84, 92, 70), c255(40, 46, 34), c255(130, 136, 104), mottle=0.5,
                veins=c255(20, 22, 16), soil=soil)


TEXTURES = {'fronds': tex_fronds, 'leaves': tex_leaves, 'bush10_skin': tex_bush10_skin,
            'bush10_spines': tex_bush10_spines, 'bush11_skin': tex_bush11_skin, 'bush11_spines': tex_bush11_spines,
            'bush13_skin': tex_bush13_skin,
            'pads_bush16': tex_bush16_pads, 'joshua': tex_joshua, 'joshbark': tex_joshbark, 'pots': tex_pots}

if __name__ == '__main__':
    for name in (sys.argv[1:] or TEXTURES):
        TEXTURES[name]()
