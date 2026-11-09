#!/usr/bin/env python3
"""Throwing axe from MM9's own PROJECTILES/AXE.abc (no Codex master: a weapon prompt can be refused by the image filter, brief lesson, so the outline is MM9's vertices): haft 43 cm, spike to 34 cm above the grip, one bit 15 cm wide, two etched panels with gems.
Frame: s along the haft from the grip (MM9's origin), b toward the edge, th through the blade. Procedural PBR paint after AXE.dtx: pale steel, dark etched panels, pink gems, red-brown wood.
Writes work/weapons.npz and textures/dwarf_weapons_{basecolor,normal,orm}.png. Run in the project folder."""
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
W, H = 1024, 512
BL = (0, 0, 620, 512)                # blade side: planar
V, UV, F = [], [], []


def px(x, y): return (x / W, 1 - y / H)


def add(pts, uvs):
    b = len(V); V.extend(pts); UV.extend(uvs); return b


def quad(a, b, c, d): F.extend([(a, b, c), (a, c, d)])


def lathe(rings, y0, y1, sides=8, flip=False):
    """rings: (s, r). Hard-free round part; u round, v along: one column per side, one row per ring."""
    first = len(V)
    n = len(rings)
    S0 = 640; S1 = 1024
    L = np.r_[0, np.cumsum(np.hypot(np.diff([q[0] for q in rings]), np.diff([q[1] for q in rings])))]; L = L / L[-1]
    for i, (s, r) in enumerate(rings):
        for k in range(sides + 1):
            a = 2 * np.pi * k / sides
            add([(s, r * np.cos(a), r * np.sin(a))], [px(S0 + (S1 - S0) * k / sides, y0 + (y1 - y0) * L[i])])
    for i in range(n - 1):
        for k in range(sides):
            a = first + i * (sides + 1) + k
            b = a + 1; c = a + sides + 2; d = a + sides + 1
            if flip: quad(a, d, c, b)
            else: quad(a, b, c, d)


# haft, pommel: MM9 stations
lathe([(-0.087, 0.0015), (-0.084, 0.010), (-0.075, 0.017), (-0.052, 0.0125)], 300, 340)      # pommel
lathe([(-0.052, 0.0125), (0.155, 0.0125)], 0, 120)                                           # haft
lathe([(0.155, 0.0125), (0.155, 0.021), (0.161, 0.0135), (0.175, 0.016), (0.288, 0.016), (0.289, 0.0185), (0.298, 0.0185), (0.298, 0.0085), (0.341, 0.0005)], 130, 290)   # collar, socket, spike
F_round = len(F)
# the bit: loops L0 root, L1 shoulder, L2 inner bevel, L3 edge; ends explicit (MM9's concave flanks)
EDGE = np.array([(.152, .112), (.176, .130), (.204, .144), (.232, .151), (.26, .154), (.288, .149), (.317, .142)])
tp = np.linspace(0, 1, len(EDGE))
T = np.linspace(0, 1, 11)
L3 = np.c_[np.interp(T, tp, EDGE[:, 0]), np.interp(T, tp, EDGE[:, 1])]
L1 = np.c_[0.176 + 0.112 * T, 0.066 + 0.008 * np.sin(T * np.pi) ** 2 * 0]
L0 = np.c_[0.180 + 0.103 * T, np.full_like(T, 0.016)]
Ld = np.array([(.169, .085), (.294, .095)])
L2 = L1 + (L3 - L1) * 0.45
e = np.abs(2 * T - 1) ** 4
L2 = L2 * (1 - e[:, None]) + np.where(T[:, None] < 0.5, Ld[0], Ld[1]) * e[:, None]
L25 = L1 + (L3 - L1) * 0.86
TH = (0.0085, 0.0048, 0.0028, 0.0014)
def side(sgn):
    rows = (L0, L1, L2, L25)
    first = len(V)
    for k, (L, th) in enumerate(zip(rows, TH)):
        for s_, b_ in L:
            u = 10 + (s_ - 0.14) / 0.19 * 600; v = 500 - (b_ - 0.0) / 0.16 * 490
            add([(s_, b_, sgn * th)], [px(u, v)])
    n = len(T)
    for r in range(3):
        for i in range(n - 1):
            a, b_, c, d = first + r * n + i, first + r * n + i + 1, first + (r + 1) * n + i + 1, first + (r + 1) * n + i
            if sgn > 0: quad(a, b_, c, d)
            else: quad(a, d, c, b_)
    # the bevel to the edge: its own vertices, hard
    first = len(V)
    for L, th in ((L25, 0.0014), (L3, 0.0)):
        for s_, b_ in L:
            u = 10 + (s_ - 0.14) / 0.19 * 600; v = 500 - (b_ - 0.0) / 0.16 * 490
            add([(s_, b_, sgn * th)], [px(u, v)])
    for i in range(n - 1):
        a, b_, c, d = first + i, first + i + 1, first + n + i + 1, first + n + i
        if sgn > 0: quad(a, b_, c, d)
        else: quad(a, d, c, b_)
side(1); side(-1)
# flanks of the bit: thickness closed along the top and bottom
for i0 in (0, len(T) - 1):
    first = len(V)
    prof = [L0[i0], L1[i0], L2[i0], L25[i0]]
    for sgn in (1, -1):
        for p, th in zip(prof, TH): add([(p[0], p[1], sgn * th)], [px(40, 480)])
    n = len(prof)
    for r in range(n - 1):
        a, b_ = first + r, first + r + 1; c, d = first + n + r + 1, first + n + r
        if i0 == 0: quad(a, b_, c, d)
        else: quad(a, d, c, b_)
np.savez('work/weapons.npz', v=np.array(V), uv=np.array(UV), f=np.array(F), axe=np.array([0, len(V), 0, len(F)]))
print('WEAPONS verts', len(V), 'tris', len(F))
# ---------- paint
rng = np.random.RandomState(9)
def noise(sx, sy, amp=1.0):
    n = ndimage.gaussian_filter(rng.randn(H, W), (sy, sx)); return n / n.std() * amp
base = np.zeros((H, W, 3)); hgt = np.zeros((H, W)); rough = np.full((H, W), 0.4); metal = np.full((H, W), 0.85)
steel = 0.52 + 0.04 * noise(40, 3) + 0.025 * noise(5, 5)
base[:] = np.stack([steel * 0.97, steel, steel * 1.03], -1)
# blade panels
mask = Image.new('L', (W, H), 0); glyph = Image.new('L', (W, H), 0); d = ImageDraw.Draw(mask); g = ImageDraw.Draw(glyph)
def bx(s0, b0, s1, b1):
    return (10 + (s0 - 0.14) / 0.19 * 600, 500 - b1 / 0.16 * 490, 10 + (s1 - 0.14) / 0.19 * 600, 500 - b0 / 0.16 * 490)
P = [bx(0.187, 0.040, 0.228, 0.135), bx(0.236, 0.040, 0.279, 0.135)]
for p in P:
    d.rounded_rectangle(p, 14, fill=255)
    x0, y0, x1, y1 = p
    for k in range(7):
        cx = x0 + (x1 - x0) * rng.uniform(0.12, 0.88); cy = y0 + (y1 - y0) * (0.16 + 0.11 * k) * 0.9 + 20
        r = rng.uniform(7, 15); t0 = rng.uniform(0, 360)
        g.arc((cx - r, cy - r, cx + r, cy + r), t0, t0 + rng.uniform(150, 270), fill=255, width=3)
        g.line((cx, cy, cx + rng.uniform(-22, 22), cy + rng.uniform(-14, 14)), fill=255, width=3)
pm = np.asarray(mask, float) / 255; pmb = ndimage.gaussian_filter(pm, 1.5); gm = ndimage.gaussian_filter(np.asarray(glyph, float) / 255, 0.7)
dark = 0.20 + 0.03 * noise(3, 3)
for c, k in enumerate((1.0, 1.0, 1.05)):
    base[..., c] = base[..., c] * (1 - pmb) + (dark * k) * pmb
    base[..., c] = base[..., c] * (1 - gm * pm) + 0.6 * gm * pm
hgt += -1.0 * pmb + 0.6 * gm * pm + 0.02 * noise(20, 2)
rough = rough * (1 - pmb) + 0.62 * pmb
yy, xx = np.mgrid[0:H, 0:W]
for p in P:                                                  # gem at the panel's root
    x0, y0, x1, y1 = p
    gx, gy = x0 + 40 * (0 + 1) * 0 + (x1 - x0) * 0.5, y1 - 34
    r = np.hypot(xx - gx, yy - gy); m = np.clip(14 - r, 0, 1)
    hi = np.clip(1 - r / 13, 0, 1)
    for c, k in enumerate((0.85, 0.16, 0.75)):
        base[..., c] = base[..., c] * (1 - m) + (k * (0.55 + 0.6 * hi)) * m
    hgt += 1.2 * np.sqrt(np.clip(1 - (r / 14) ** 2, 0, 1))
    rough = rough * (1 - m) + 0.2 * m; metal = metal * (1 - m)
# haft: red-brown wood
m = (yy < 124) & (xx >= 630)
grain = 0.5 + 0.5 * noise(1.2, 30); l = 0.13 + 0.12 * grain
base[m] = np.stack([l * 1.0, l * 0.5, l * 0.27], -1)[m]; hgt[m] = (0.5 * grain)[m]; rough[m] = 0.66; metal[m] = 0
# socket: dark bands, pale marks (rows 130-290)
m = (yy >= 126) & (yy < 296) & (xx >= 630)
v = (yy - 130) / 160.0                                      # along the socket: collar 0..0.12, panels 0.14..0.84, ring, spike
band = ((v > 0.16) & (v < 0.36)) | ((v > 0.42) & (v < 0.62)) | ((v > 0.68) & (v < 0.80))
sb = ndimage.gaussian_filter(band.astype(float), 1.0)
marks = (np.abs(np.sin((xx - 640) / 384 * 2 * np.pi * 8)) > 0.9) & band
l2 = np.where(band, 0.16, 0.52) + 0.025 * noise(3, 3)
l2 = np.where(marks, 0.55, l2)
base[m] = np.stack([l2, l2, l2 * 1.03], -1)[m]; hgt[m] = (-0.7 * sb + 0.3 * marks)[m]
Image.fromarray((np.clip(base, 0, 1) * 255).astype('u1')).save('textures/dwarf_weapons_basecolor.png')
gx = ndimage.sobel(ndimage.gaussian_filter(hgt, 1.0), axis=1) * 0.45; gy = ndimage.sobel(ndimage.gaussian_filter(hgt, 1.0), axis=0) * 0.45
n = np.dstack([-gx, gy, np.ones_like(gx)]); n /= np.linalg.norm(n, axis=2, keepdims=True)
Image.fromarray(((n * 0.5 + 0.5) * 255).astype('u1')).save('textures/dwarf_weapons_normal.png')
Image.fromarray((np.stack([np.ones_like(rough), np.clip(rough, 0, 1), np.clip(metal, 0, 1)], -1) * 255).astype('u1')).save('textures/dwarf_weapons_orm.png')
