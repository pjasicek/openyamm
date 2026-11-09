#!/usr/bin/env python3
"""Cutlass from MM9's own stations (no Codex master, the brief's lesson on weapon prompts): the blade's outline with the notches on the spine, the bow in the blade's plane, grip, guard, two curled quillons with balls, blue stone. Frame: s along the blade, w across it, t through it (work/cut_frame.npz, MM9's vertices).
Procedural PBR as LIZORCCUTLASS: pale blue-white blade, gold hilt, orange-brown wrapped grip. Writes work/weapon.npz (v in the bind, placed at the solved grip, uv, f) and textures/cutlass_{basecolor,normal,orm}.png."""
import numpy as np, json
from PIL import Image
from scipy import ndimage
Fr = np.load('work/cut_frame.npz'); Q = Fr['Q']; c0, a, b, n = Fr['c'], Fr['a'], Fr['b'], Fr['n']
H = json.load(open('work/hand_poses.json')); G = np.array(H['G'])
W, Hh = 1024, 512
ROW = dict(blade=(0, 200), gold=(200, 320), grip=(320, 420), gem=(420, 512))
V, UV, F = [], [], []
def uvp(row, u, v): y0, y1 = ROW[row]; return (u, 1 - (y0 + (y1 - y0) * v) / Hh)
def add(p, uv): i = len(V); V.append(p); UV.append(uv); return i
def quad(a_, b_, c_, d_): F.extend([(a_, b_, c_), (a_, c_, d_)])
# blade bow out of its plane, from MM9's vertices
bl = Q[Q[:, 0] > -.05]; sb = np.arange(-.05, .6, .05); tb = np.array([bl[np.abs(bl[:, 0] - s) < .04, 2].mean() if (np.abs(bl[:, 0] - s) < .04).any() else np.nan for s in sb]); tb = np.interp(sb, sb[~np.isnan(tb)], tb[~np.isnan(tb)])
bow = lambda s: np.interp(s, sb, ndimage.gaussian_filter1d(tb, 1.0))
print('bow', np.round(tb, 3))
ST = np.array([(-.085, .022, -.012), (0, .012, -.03), (.1, .002, -.05), (.2, -.004, -.068), (.225, -.005, -.073), (.255, .002, -.075), (.29, .010, -.075), (.322, -.008, -.075), (.335, .012, -.073), (.355, .024, -.07), (.385, .004, -.068),
               (.40, .040, -.066), (.43, .050, -.06), (.48, .042, -.036), (.53, .056, .0), (.56, .068, .045), (.578, .078, .078)])
T0 = .0055
for sgn in (1, -1):
    start = len(V)
    for i, (s, ws, wb) in enumerate(ST):
        wid = ws - wb; u = (s + .09) / .67
        rows = ((wb, 0.), (wb + wid * .22, .55), (wb + wid * .62, 1.), (ws, .55))
        for j, (w, k) in enumerate(rows):
            add((s, w, bow(s) + sgn * T0 * k * min(1, wid / .05 + .15)), uvp('blade', u, [0.02, .3, .7, .98][j]))
    for i in range(len(ST) - 1):
        for j in range(3):
            A, B, C, D = start + 4 * i + j, start + 4 * i + j + 1, start + 4 * (i + 1) + j + 1, start + 4 * (i + 1) + j
            if sgn > 0: quad(A, D, C, B)
            else: quad(A, B, C, D)
n0 = len(ST)
sp = [(0, 3), (1, 3)]
for i in range(n0 - 1):     # the spine strip, both faces join
    A, B = 3 + 4 * i, 3 + 4 * (i + 1); C, D = n0 * 4 + B, n0 * 4 + A
    quad(A, B, C, D)
    A2, B2 = 4 * i, 4 * (i + 1); C2, D2 = n0 * 4 + B2, n0 * 4 + A2
    quad(A2, D2, C2, B2)
def tube(path, r0, r1, row, flat=.75, sides=5):
    path = np.array(path, float); seg = np.r_[0, np.cumsum(np.linalg.norm(np.diff(path, axis=0), axis=1))]
    fine = np.linspace(0, seg[-1], max(5, int(seg[-1] / .03)))
    P_ = np.c_[np.interp(fine, seg, path[:, 0]), np.interp(fine, seg, path[:, 1])]
    P_[:, 0] = ndimage.gaussian_filter1d(P_[:, 0], .8, mode='nearest'); P_[:, 1] = ndimage.gaussian_filter1d(P_[:, 1], .8, mode='nearest')
    first = len(V); N = len(P_)
    for i, p in enumerate(P_):
        d = P_[min(i + 1, N - 1)] - P_[max(i - 1, 0)]; d /= np.linalg.norm(d); nor = np.array([-d[1], d[0]])
        r = r0 + (r1 - r0) * i / (N - 1)
        for k in range(sides + 1):
            th = 2 * np.pi * k / sides
            q = p + nor * r * np.cos(th)
            add((q[0], q[1], bow(q[0]) + r * flat * np.sin(th)), uvp(row, i / (N - 1), k / sides))
    for i in range(N - 1):
        for k in range(sides):
            A, B, C, D = first + i * (sides + 1) + k, first + i * (sides + 1) + k + 1, first + (i + 1) * (sides + 1) + k + 1, first + (i + 1) * (sides + 1) + k
            quad(A, D, C, B)
    # end cap
    e = add((P_[-1][0], P_[-1][1], bow(P_[-1][0])), uvp(row, 1, .5))
    for k in range(sides): F.append((e, first + (N - 1) * (sides + 1) + k + 1, first + (N - 1) * (sides + 1) + k))
    return first
def lathe(rings, wc, row, sides=8, flip=False):
    first = len(V); s0, s1 = rings[0][0], rings[-1][0]
    for s, r, r2 in rings:
        for k in range(sides + 1):
            th = 2 * np.pi * k / sides
            add((s, wc + r * np.cos(th), bow(s) + r2 * np.sin(th)), uvp(row, (s - s0) / (s1 - s0), k / sides))
    for i in range(len(rings) - 1):
        for k in range(sides):
            A, B, C, D = first + i * (sides + 1) + k, first + i * (sides + 1) + k + 1, first + (i + 1) * (sides + 1) + k + 1, first + (i + 1) * (sides + 1) + k
            quad(A, D, C, B)
    return first
GW = .021
grip = lathe([(-.262, .014, .014), (-.25, .023, .022), (-.19, .025, .024), (-.135, .024, .023), (-.118, .016, .016)], GW, 'grip', sides=10)
pom = lathe([(-.262, .012, .012), (-.268, .023, .021), (-.283, .029, .026), (-.298, .021, .019), (-.31, .004, .004)], GW, 'gold', sides=10)
ball = lathe([(-.125, .009, .012), (-.118, .02, .016), (-.105, .03, .019), (-.09, .022, .015), (-.08, .006, .006)], .012, 'gold', sides=8)
ball2 = lathe([(-.12, .012, .01), (-.108, .056, .012), (-.098, .058, .012), (-.09, .02, .008)], .004, 'gold', sides=8)
tube([(-.098, .045), (-.098, .075), (-.08, .083), (-.045, .078), (-.03, .09), (-.045, .112), (-.06, .118)], .010, .007, 'gold')
b1 = lathe([(-.075, .001, .001), (-.067, .009, .009), (-.056, .012, .012), (-.045, .009, .009), (-.038, .001, .001)], .12, 'gold', sides=6)
tube([(-.098, -.045), (-.075, -.052), (-.05, -.056), (-.05, -.08), (-.07, -.098), (-.085, -.106)], .010, .007, 'gold')
b2 = lathe([(-.105, .001, .001), (-.098, .009, .009), (-.087, .012, .012), (-.076, .009, .009), (-.068, .001, .001)], -.11, 'gold', sides=6)
tube([(-.105, -.05), (-.14, -.07), (-.20, -.082), (-.25, -.062), (-.276, -.02), (-.288, .005)], .008, .011, 'gold')
# the stone on both faces of the guard
for sg in (1, -1):
    first = len(V); ce = np.array([-.098, .006, bow(-.098) + sg * .0145])
    i0 = add(tuple(ce + [0, 0, sg * .006]), uvp('gem', .5, .5)); M = 8
    for k in range(M + 1):
        th = 2 * np.pi * k / M; add((ce[0] + .012 * np.cos(th), ce[1] + .012 * np.sin(th), ce[2] - sg * .002), uvp('gem', .5 + .45 * np.cos(th), .5 + .45 * np.sin(th)))
    for k in range(M):
        F.append((i0, first + 1 + k, first + 2 + k) if sg > 0 else (i0, first + 2 + k, first + 1 + k))
V_ = np.array(V); F_ = np.array(F); UV_ = np.array(UV)
# world: MM9's grip centre on our solved centre
Gm = c0 + a * -.19 + b * GW
Pw = c0 + np.outer(V_[:, 0], a) + np.outer(V_[:, 1], b) + np.outer(V_[:, 2], n) + (G - Gm)
fn = np.cross(Pw[F_[:, 1]] - Pw[F_[:, 0]], Pw[F_[:, 2]] - Pw[F_[:, 0]])
print('CUTLASS verts', len(V_), 'tris', len(F_), 'bbox', Pw.min(0).round(3), Pw.max(0).round(3), 'moved', (G - Gm).round(3))
np.savez('work/weapon.npz', v=Pw, uv=UV_, f=F_, local=V_, Gm=Gm)
rng = np.random.RandomState(4)
def noise(sx, sy, amp=1.):
    x = ndimage.gaussian_filter(rng.randn(Hh, W), (sy, sx)); return x / x.std() * amp
base = np.zeros((Hh, W, 3)); hgt = np.zeros((Hh, W)); rough = np.ones((Hh, W)) * .5; metal = np.zeros((Hh, W))
yy, xx = np.mgrid[0:Hh, 0:W]
def rows(k): y0, y1 = ROW[k]; return (yy >= y0) & (yy < y1), (yy - y0) / (y1 - y0)
m, v = rows('blade'); e = np.abs(v - .5) / .5
s = .80 + .04 * noise(60, 1.) + .02 * noise(10, 4) + .10 * (v < .32) - .09 * ((v > .55) & (v < .8))
c = np.stack([s * .93, s * .97, s * 1.0], -1); base[m] = c[m]; hgt[m] = (.02 * noise(30, 1))[m]; rough[m] = (.34 + .06 * noise(40, 2))[m]; metal[m] = .8
m, v = rows('gold'); band = .5 + .5 * np.cos(2 * np.pi * v * 2); eng = ndimage.gaussian_filter((np.abs(((xx / W) * 22) % 1 - .5) < .07).astype(float), 1.4)
s = .80 + .14 * band - .34 * eng + .06 * noise(6, 6)
c = np.stack([s * .98, s * .70, s * .27], -1); base[m] = c[m]; hgt[m] = (.5 * band - .6 * eng + .1 * noise(3, 3))[m]; rough[m] = .36; metal[m] = .85
m, v = rows('grip'); wr = (.5 + .5 * np.sin(2 * np.pi * (xx / 24. + v * 2.))) ** .6
l = .32 + .22 * wr + .04 * noise(2, 2)
c = np.stack([l * 1.0, l * .55, l * .22], -1); base[m] = c[m]; hgt[m] = (.8 * wr + .1 * noise(1.5, 1.5))[m]; rough[m] = .6
m, v = rows('gem'); rr = np.hypot((xx / W - .5) * 2 * (W / (ROW['gem'][1] - ROW['gem'][0])) * .5 * .1, v - .5)
c = np.stack([.10 + .25 * v, .18 + .3 * v, .75 + .2 * v], -1); base[m] = c[m]; rough[m] = .15; metal[m] = .3
Image.fromarray((np.clip(base, 0, 1) * 255).astype('u1')).save('textures/cutlass_basecolor.png')
hs = ndimage.gaussian_filter(hgt, 1.); dx = ndimage.sobel(hs, 1) * .5; dy = ndimage.sobel(hs, 0) * .5
nn = np.stack([-dx, dy, np.ones_like(dx)], -1); nn /= np.linalg.norm(nn, axis=2, keepdims=True)
Image.fromarray(((nn * .5 + .5) * 255).astype('u1')).resize((512, 256), Image.LANCZOS).save('textures/cutlass_normal.png')
Image.fromarray((np.stack([np.ones_like(rough), np.clip(rough, 0, 1), metal], -1) * 255).astype('u1')).resize((512, 256), Image.LANCZOS).save('textures/cutlass_orm.png')
print('PAINT done')
