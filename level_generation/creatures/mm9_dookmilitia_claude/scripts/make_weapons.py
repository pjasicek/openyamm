#!/usr/bin/env python3
"""Short sword and dagger from MM9's own pieces (no Codex master: a weapon prompt is refused by the image filter, brief lesson; so the outlines are the MM9 vertices). Stations along the axis and the half widths are
MM9's: sword blade 48 cm, guard 15.6 cm, grip 13 cm, pommel; dagger blade 30 cm, guard 17.5 cm, grip 13 cm, pommel. Blade facets carry hard edges (their own vertices), hilts are round. Frame: t along the blade from the guard, a across the
blade's flat, b through it. Procedural PBR paint: pale steel, leather wrap, sword guard silver, dagger guard gold as HIGHWAYMANSS / HIGHWAYMANDAGGER. Writes work/weapons.npz and textures/dook_weapons_{basecolor,normal,orm}.png.
Run in the project folder."""
import numpy as np
from PIL import Image
from scipy import ndimage
W, H = 1024, 512
ROW = dict(sword=(0, 110), dagger=(110, 220), grip=(220, 300), silver=(300, 380), gold=(380, 450), pommel=(450, 512))
V, UV, F = [], [], []


def uvp(row, u, v):
    y0, y1 = ROW[row]
    return (u, 1 - (y0 + (y1 - y0) * v) / H)


def add(pts, uvs):
    b = len(V); V.extend(pts); UV.extend(uvs); return b


def quad(a, b, c, d): F.extend([(a, b, c), (a, c, d)])


def blade(st, row, dook_max):
    """st: (t, half width, half thickness). Four facets, each its own vertices: ridge a = 0 to the edges."""
    tmax = st[-1][0]
    for sa, sb in ((1, 1), (-1, 1), (-1, -1), (1, -1)):
        first = len(V)
        for t, hw, ht in st:
            u = t / tmax * 0.98 + 0.01
            v0 = 0.5; v1 = 0.5 + 0.48 * sa * hw / dook_max
            add([(t, 0, sb * ht), (t, sa * hw, 0)], [uvp(row, u, v0), uvp(row, u, v1)])
        for k in range(len(st) - 1):
            a, b_, c, d = first + 2 * k, first + 2 * k + 1, first + 2 * k + 3, first + 2 * k + 2
            if sa * sb > 0: quad(a, b_, c, d)
            else: quad(a, d, c, b_)


def lathe(rings, row, u0, u1, sides=10, flip=False):
    """rings: (t, ra, rb). A round section, ends closed by fans on the axis."""
    first = len(V); tlo, thi = rings[0][0], rings[-1][0]
    for t, ra, rb in rings:
        u = u0 + (u1 - u0) * (t - tlo) / (thi - tlo)
        for k in range(sides + 1):
            ang = 2 * np.pi * k / sides
            add([(t, ra * np.cos(ang), rb * np.sin(ang))], [uvp(row, u, k / sides)])
    n = sides + 1
    for r in range(len(rings) - 1):
        for k in range(sides):
            a, b_, c, d = first + r * n + k, first + r * n + k + 1, first + (r + 1) * n + k + 1, first + (r + 1) * n + k
            if flip: quad(a, b_, c, d)
            else: quad(a, d, c, b_)


def guardbar(tc, ht, ha, hb_mid, hb_end, row):
    """A bar along a, flared at the ends: rings along a. Section: rectangle-ish octagon in (t, b)."""
    first = len(V)
    stations = [-ha, -ha * 0.86, -ha * 0.6, -ha * 0.22, 0, ha * 0.22, ha * 0.6, ha * 0.86, ha]
    prof = [0.55, 1.0, 0.8, 0.8, 1.0, 0.8, 0.8, 1.0, 0.55]
    sides = 8
    for s, p in zip(stations, prof):
        u = 0.5 + 0.48 * s / ha
        thick = hb_end + (hb_mid - hb_end) * (1 - abs(s) / ha)
        for k in range(sides + 1):
            ang = 2 * np.pi * (k + 0.5) / sides
            add([(tc + ht * p * 1.25 * np.cos(ang), s, thick * p * 1.25 * np.sin(ang))], [uvp(row, u, k / sides)])
    n = sides + 1
    for r in range(len(stations) - 1):
        for k in range(sides):
            a, b_, c, d = first + r * n + k, first + r * n + k + 1, first + (r + 1) * n + k + 1, first + (r + 1) * n + k
            quad(a, b_, c, d)


def fan_close(first_ring, sides, tip, uv, flip):
    b = add([tip], [uv])
    for k in range(sides):
        a, c = first_ring + k, first_ring + k + 1
        F.append((b, a, c) if flip else (b, c, a))


def weapon(blade_st, hw, row_blade, row_guard, guard, grip, pommel):
    start = len(V); fs = len(F)
    blade(blade_st, row_blade, hw)
    guardbar(*guard, row_guard)
    first = len(V)
    lathe(grip, 'grip', 0.02, 0.98, flip=True)
    first2 = len(V)
    lathe(pommel, 'pommel', 0.02 if row_guard == 'silver' else 0.52, 0.48 if row_guard == 'silver' else 0.98, flip=True)
    fan_close(first2 + (len(pommel) - 1) * 11, 10, (pommel[-1][0] - 0.004, 0, 0), uvp('pommel', 0.25 if row_guard == 'silver' else 0.75, 0.5), False)
    return (start, len(V), fs, len(F))


vs = weapon([(0.0, 0.038, 0.009), (0.35, 0.0372, 0.0088), (0.697, 0.036, 0.0084), (0.80, 0.019, 0.0052), (0.853, 0.0004, 0.0004)], 0.038, 'sword', 'silver',
            (-0.014, 0.017, 0.12, 0.018, 0.0125), [(-0.235, 0.0150, 0.0130), (-0.222, 0.0160, 0.0140), (-0.125, 0.0170, 0.0150), (-0.045, 0.0160, 0.0140), (-0.028, 0.0150, 0.0130)],
            [(-0.228, 0.0120, 0.0115), (-0.240, 0.0260, 0.0200), (-0.262, 0.0340, 0.0250), (-0.285, 0.0260, 0.0200), (-0.301, 0.0060, 0.0050)])
n1, m1 = len(V), len(F)
np.savez('work/weapons.npz', v=np.array(V), uv=np.array(UV), f=np.array(F), sword=np.array([0, n1, 0, m1]), dagger=np.array([n1, len(V), m1, len(F)]))
print('WEAPONS verts', len(V), 'tris sword', m1)
# ---------- paint
rng = np.random.RandomState(9)
def noise(sx, sy, amp=1.0):
    n = ndimage.gaussian_filter(rng.randn(H, W), (sy, sx)); return n / n.std() * amp
base = np.zeros((H, W, 3)); hgt = np.zeros((H, W)); rough = np.zeros((H, W)); metal = np.zeros((H, W))
yy, xx = np.mgrid[0:H, 0:W]
def rows(k): y0, y1 = ROW[k]; return (yy >= y0) & (yy < y1), (yy - y0) / (y1 - y0)
# blades: pale steel, a fuller along the middle, bright bevel at the edge, long scratches
for k in ('sword', 'dagger'):
    m, v = rows(k); a = np.abs(v - 0.5) / 0.48; u = xx / W
    full = np.exp(-(a / 0.3) ** 4) * (u < (0.74 if k == 'sword' else 0.6))
    edge = np.clip((a - 0.74) / 0.2, 0, 1)
    s = 0.74 + 0.05 * noise(60, 1.0) + 0.03 * noise(8, 3)
    s = s - 0.11 * full + 0.14 * edge
    s = np.clip(s - 0.25 * np.clip(noise(30, 18), 0, None) * 0.25, 0, 1)
    c = np.stack([s * 0.96, s * 0.97, s * 1.0], -1)
    base[m] = c[m]; hgt[m] = (-0.8 * full + 0.3 * np.clip(1 - a, 0, 1) + 0.02 * noise(30, 1))[m]
    rough[m] = (0.36 + 0.08 * noise(40, 2, 1) - 0.1 * edge)[m]; metal[m] = 0.8
# leather wrap
m, v = rows('grip')
grain = 0.5 + 0.5 * noise(70, 2.2) * 0.5                        # DOOKSWORD's grip is plain dark wood, a thin pale band at each end
ring = np.clip(1 - np.minimum(xx, W - xx) / 26.0, 0, 1)
l = 0.21 + 0.1 * grain + 0.02 * noise(2, 2)
c = np.stack([l * 1.0, l * 0.6, l * 0.3], -1) * (1 - ring[..., None]) + np.array([0.62, 0.5, 0.26]) * ring[..., None]
base[m] = c[m]; hgt[m] = (0.25 * grain + 0.8 * ring)[m]; rough[m] = 0.55; metal[m] = 0
# silver and gold guards, pommels
def metalrow(k, col, xr=None):
    m, v = rows(k)
    if xr: m = m & (xx >= xr[0]) & (xx < xr[1])
    band = 0.5 + 0.5 * np.cos(2 * np.pi * v * 2)
    eng = (np.abs(((xx / W - 0.5) * 18) % 1 - 0.5) < 0.06).astype(float)
    eng = ndimage.gaussian_filter(eng, 1.2)
    s = 0.82 + 0.1 * band - 0.28 * eng + 0.04 * noise(6, 6)
    c = np.stack([col[i] * s for i in range(3)], -1)
    base[m] = c[m]; hgt[m] = (0.5 * band - 0.5 * eng)[m]; rough[m] = 0.38; metal[m] = 0.85
metalrow('silver', (0.78, 0.66, 0.36)); metalrow('gold', (0.80, 0.62, 0.26)); metalrow('pommel', (0.78, 0.66, 0.36), (0, 512)); metalrow('pommel', (0.80, 0.62, 0.26), (512, 1024))  # DOOKSWORD: pale brass guard and pommel
Image.fromarray((np.clip(base, 0, 1) * 255).astype('u1')).save('textures/dook_weapons_basecolor.png')
hs = ndimage.gaussian_filter(hgt, 1.0)
dx = ndimage.sobel(hs, 1) * 0.5; dy = ndimage.sobel(hs, 0) * 0.5
n = np.stack([-dx, dy, np.ones_like(dx)], -1); n /= np.linalg.norm(n, axis=2, keepdims=True)
Image.fromarray(((n * 0.5 + 0.5) * 255).astype('u1')).save('textures/dook_weapons_normal.png')
Image.fromarray((np.stack([np.ones_like(rough), np.clip(rough, 0, 1), metal], -1) * 255).astype('u1')).save('textures/dook_weapons_orm.png')
print('PAINT done')
