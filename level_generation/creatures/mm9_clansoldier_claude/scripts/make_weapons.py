#!/usr/bin/env python3
"""Sword and shield from MM9's own pieces (no Codex master for the sword: a weapon prompt is refused by the image filter, brief lesson; so the outline is MM9's vertices). Sword: blade 79 cm, guard 21 cm, grip 14 cm, disc pommel. Shield: MM9's coffin
outline 1.32 x 0.61 m, made symmetric, a shallow dome (MM9's is flat), rim faces of their own; the Codex faces map straight on. Handle bar and struts are a unit lathe placed by finish_clan.py. Frames: sword t along the blade from the guard, a across the flat, b through it; shield s along from the tip,
w across, d outward. Atlas 1536 x 1024 per tier: outer face left (682 x 1024), inner face (341 x 512), sword rows bottom right, grip row. Writes work/weapons.npz, textures/clan_weapons_{a,b,c}_{basecolor,normal,orm}.png. Run in the project folder, after the Codex shield faces are in references_shield/."""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
W_, H_ = 1536, 1024
OUT = (0, 0, 682, 1024); INN = (682, 0, 1023, 512)
ROW = dict(blade=(512, 640), grip=(640, 730), bar=(730, 790), gold=(790, 900), pommel=(900, 1024))
X0 = 682
V, UV, F = [], [], []
def uvp(row, u, v):
    y0, y1 = ROW[row]
    return ((X0 + (W_ - X0) * u) / W_, 1 - (y0 + (y1 - y0) * v) / H_)
def add(pts, uvs):
    b = len(V); V.extend(pts); UV.extend(uvs); return b
def quad(a, b, c, d): F.extend([(a, b, c), (a, c, d)])
def blade(st, hw_max):
    tmax = st[-1][0]
    for sa, sb in ((1, 1), (-1, 1), (-1, -1), (1, -1)):
        first = len(V)
        for t, hw, ht in st:
            u = t / tmax * 0.98 + 0.01
            add([(t, 0, sb * ht), (t, sa * hw, 0)], [uvp('blade', u, 0.5), uvp('blade', u, 0.5 + 0.48 * sa * hw / hw_max)])
        for k in range(len(st) - 1):
            a, b_, c, d = first + 2 * k, first + 2 * k + 1, first + 2 * k + 3, first + 2 * k + 2
            if sa * sb > 0: quad(a, b_, c, d)
            else: quad(a, d, c, b_)
def lathe(rings, row, u0, u1, sides=10, flip=False):
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
    return first
def guardbar(tc, ht, ha, hb_mid, hb_end):
    first = len(V)
    stations = [-ha, -ha * 0.86, -ha * 0.6, -ha * 0.22, 0, ha * 0.22, ha * 0.6, ha * 0.86, ha]
    prof = [0.55, 1.0, 0.8, 0.8, 1.0, 0.8, 0.8, 1.0, 0.55]; rise = [0.016, 0.016, 0.006, 0, 0, 0, 0.006, 0.016, 0.016]
    sides = 8
    for s, p, up in zip(stations, prof, rise):
        u = 0.5 + 0.48 * s / ha; thick = hb_end + (hb_mid - hb_end) * (1 - abs(s) / ha)
        for k in range(sides + 1):
            ang = 2 * np.pi * (k + 0.5) / sides
            add([(tc + up + ht * p * 1.25 * np.cos(ang), s, thick * p * 1.25 * np.sin(ang))], [uvp('gold', u, k / sides)])
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
# sword, stations MM9's
blade([(0.0, 0.0335, 0.0092), (0.35, 0.0365, 0.0080), (0.686, 0.0385, 0.0062), (0.792, 0.0004, 0.0004)], 0.0385)
guardbar(0.002, 0.012, 0.105, 0.016, 0.009)
lathe([(-0.158, 0.0125, 0.0115), (-0.145, 0.0145, 0.0130), (-0.09, 0.0160, 0.0145), (-0.035, 0.0145, 0.0130), (-0.004, 0.0125, 0.0115)], 'grip', 0.02, 0.98, flip=True)
f2 = lathe([(-0.15, 0.0120, 0.0115), (-0.163, 0.0270, 0.0125), (-0.185, 0.0300, 0.0150), (-0.205, 0.0240, 0.0125), (-0.216, 0.0100, 0.0060)], 'pommel', 0.02, 0.98, flip=True)
fan_close(f2 + 44, 10, (-0.2165, 0, 0), uvp('pommel', 0.5, 0.5), False)
n1, m1 = len(V), len(F)
# shield
fr = json.load(open('work/shield_frame.json')); st = fr['stations']; LEN = fr['length']
SS = np.array([0, 0.2, 0.409, 0.6, 0.8, 0.999, 1.14, 1.283, LEN]); HW = np.interp(SS, [st[0][0], st[1][0], st[2][0], st[3][0], LEN], [st[0][1], st[1][1], st[2][1], st[3][1], 0.012])
CC = np.array([-1, -0.72, -0.4, 0, 0.4, 0.72, 1.0]); TH = 0.022; BULGE = 0.03
def face_uv(box, s, w):
    x0, y0, x1, y1 = box; PX = (x1 - x0) / 1024
    return ((x0 + (512 + w * 1100) * PX) / W_, 1 - (y0 + (1536 - 45 - s * 1100) * (y1 - y0) / 1536) / H_)
def dome(s, c): return BULGE * (1 - c ** 2) * (1 - ((s - 0.75) / 0.9) ** 2)
for side, box in ((1, OUT), (-1, INN)):
    first = len(V)
    for s, h in zip(SS, HW):
        for c in CC:
            w = h * c
            add([(s, w, dome(s, c) + (0 if side > 0 else -TH))], [face_uv(box, s, -w * side if side > 0 else w)])
    n = len(CC)
    for r in range(len(SS) - 1):
        for k in range(n - 1):
            a, b_, c_, d = first + r * n + k, first + r * n + k + 1, first + (r + 1) * n + k + 1, first + (r + 1) * n + k
            if side > 0: quad(a, d, c_, b_)                 # L x W = n: the outer face looks along +n, the inner along -n
            else: quad(a, b_, c_, d)
# rim: its own vertices, on the outer face's edge band
loop = [(s, h, 1) for s, h in zip(SS, HW)] + [(s, -h, -1) for s, h in zip(SS[::-1], HW[::-1])]
first = len(V)
for s, w, c in loop:
    add([(s, w, dome(s, 1.0)), (s, w, dome(s, 1.0) - TH)], [face_uv(OUT, s, -w * 0.97), face_uv(OUT, s, -w * 0.97)])
nl = len(loop)
for k in range(nl - 1):
    a, b_ = first + 2 * k, first + 2 * k + 1; c, d = first + 2 * k + 2, first + 2 * k + 3
    if loop[k][:2] == loop[k + 1][:2]: continue
    quad(a, c, d, b_)
a, b_ = first + 2 * (nl - 1), first + 2 * (nl - 1) + 1
quad(a, first, first + 1, b_)
n2, m2 = len(V), len(F)
# handle bar: unit in (t, a, b) with t along the bar, r = 1.5 cm, two struts are the same lathe scaled in finish_clan.py
lathe([(-0.5, 0.012, 0.012), (-0.46, 0.0155, 0.0155), (0.46, 0.0155, 0.0155), (0.5, 0.012, 0.012)], 'bar', 0.02, 0.98, sides=8, flip=True)
n3, m3 = len(V), len(F)
np.savez('work/weapons.npz', v=np.array(V), uv=np.array(UV), f=np.array(F), sword=np.array([0, n1, 0, m1]), shield=np.array([n1, n2, m1, m2]), bar=np.array([n2, n3, m2, m3]))
print('WEAPONS verts', len(V), 'tris sword', m1, 'shield', m2 - m1, 'bar', m3 - m2)
# ---------- paint
rng = np.random.RandomState(9)
def noise(sx, sy, amp=1.0):
    n = ndimage.gaussian_filter(rng.randn(H_, W_), (sy, sx)); return n / n.std() * amp
yy, xx = np.mgrid[0:H_, 0:W_]
def rows(k):
    y0, y1 = ROW[k]; return (yy >= y0) & (yy < y1) & (xx >= X0), (yy - y0) / (y1 - y0)
TIN = {'a': (0.92, 0.96, 1.0), 'b': (0.92, 0.96, 1.0), 'c': (0.62, 0.78, 0.74)}                  # BELDSWORD pale steel, BELDSWORDOLD verdigris
for t in 'abc':
    base = np.zeros((H_, W_, 3)); hgt = np.zeros((H_, W_)); rough = np.zeros((H_, W_)); metal = np.zeros((H_, W_))
    m, v = rows('blade'); a = np.abs(v - 0.5) / 0.48; u = (xx - X0) / (W_ - X0)
    full = np.exp(-(a / 0.3) ** 4) * (u < 0.8); edge = np.clip((a - 0.74) / 0.2, 0, 1)
    s = 0.72 + 0.05 * noise(60, 1.0) + 0.03 * noise(8, 3); s = s - 0.11 * full + 0.14 * edge
    s = np.clip(s - 0.06 * np.clip(noise(30, 18), 0, None), 0, 1)
    c = np.stack([s * k for k in TIN[t]], -1)
    base[m] = c[m]; hgt[m] = (-0.8 * full + 0.3 * np.clip(1 - a, 0, 1) + 0.02 * noise(30, 1))[m]
    rough[m] = (0.36 + 0.08 * noise(40, 2, 1) - 0.1 * edge)[m]; metal[m] = 0.8
    m, v = rows('grip'); wrap = (0.5 + 0.5 * np.sin(2 * np.pi * ((xx - X0) / 26.0 + v * 2.0))) ** 0.6
    l = 0.26 + 0.2 * wrap + 0.03 * noise(2, 2)
    base[m] = np.stack([l * 1.0, l * 0.52, l * 0.22], -1)[m]; hgt[m] = (0.8 * wrap + 0.1 * noise(1.5, 1.5))[m]; rough[m] = 0.62; metal[m] = 0
    m, v = rows('bar')                                              # the shield's handle and struts: dark worn iron
    l = 0.13 + 0.05 * noise(14, 3) + 0.02 * noise(2, 2)
    base[m] = np.stack([l * 1.0, l * 0.92, l * 0.86], -1)[m]; hgt[m] = (0.1 * noise(3, 3))[m]; rough[m] = 0.52; metal[m] = 0.7
    for k in ('gold', 'pommel'):
        m, v = rows(k); band = 0.5 + 0.5 * np.cos(2 * np.pi * v * 2)
        s = 0.8 + 0.1 * band + 0.05 * noise(6, 6)
        col = (0.86, 0.60, 0.20)
        c = np.stack([col[i] * s for i in range(3)], -1)
        base[m] = c[m]; hgt[m] = (0.5 * band + 0.05 * noise(3, 3))[m]; rough[m] = 0.36; metal[m] = 0.9
    for name, box, feather in (('outer', OUT, 1), ('inner', INN, 1)):
        p = Path(f'references_shield/{t}_{name}_clean.png')
        if not p.exists(): print('MISSING', p); continue
        im = Image.open(p).convert('RGBA'); al = np.asarray(im)[..., 3] > 128; ys, xs = np.nonzero(al)
        ol = np.asarray(Image.open('references_shield/outline.png').convert('RGBA'))[..., 3] > 128; oy, ox = np.nonzero(ol)
        sx = (xs.max() - xs.min()) / (ox.max() - ox.min()); sy = (ys.max() - ys.min()) / (oy.max() - oy.min())
        aff = (sx, 0, xs.min() - ox.min() * sx, 0, sy, ys.min() - oy.min() * sy)
        fit = im.transform(im.size, Image.AFFINE, aff, Image.BICUBIC)
        arr = np.asarray(fit, np.float32) / 255; rgb = arr[..., :3]; okm = arr[..., 3] > 0.9
        idx = ndimage.distance_transform_edt(~okm, return_distances=False, return_indices=True); rgb = rgb[idx[0], idx[1]]
        x0, y0, x1, y1 = box; rs = Image.fromarray((rgb * 255).astype('u1')).resize((x1 - x0, y1 - y0), Image.LANCZOS)
        reg = np.asarray(rs, np.float32) / 255
        base[y0:y1, x0:x1] = reg
        lum = reg @ np.array([.2126, .7152, .0722])
        hgt[y0:y1, x0:x1] = (lum - ndimage.gaussian_filter(lum, 8)) * 5
        sat = reg.max(2) - reg.min(2); steel = np.clip((0.09 - sat) / 0.05, 0, 1) * np.clip((lum - 0.18) / 0.15, 0, 1)
        rough[y0:y1, x0:x1] = 0.72 - 0.3 * steel; metal[y0:y1, x0:x1] = 0.75 * steel
    Image.fromarray((np.clip(base, 0, 1) * 255).astype('u1')).save(f'textures/clan_weapons_{t}_basecolor.png')
    hs = ndimage.gaussian_filter(hgt, 1.0); dx = ndimage.sobel(hs, 1) * 0.5; dy = ndimage.sobel(hs, 0) * 0.5
    n = np.stack([-dx, dy, np.ones_like(dx)], -1); n /= np.linalg.norm(n, axis=2, keepdims=True)
    Image.fromarray(((n * 0.5 + 0.5) * 255).astype('u1')).resize((768, 512), Image.LANCZOS).save(f'textures/clan_weapons_{t}_normal.png')
    Image.fromarray((np.stack([np.ones_like(rough), np.clip(rough, 0, 1), metal], -1) * 255).astype('u1')).resize((768, 512), Image.LANCZOS).save(f'textures/clan_weapons_{t}_orm.png')
print('PAINT done')
