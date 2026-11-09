#!/usr/bin/env python3
"""Low-poly rebuild of the Giant's Meshy mallet (pass 2, orchestrator 2026-11-04; RETOPOLOGY_PLAYBOOK "replace broken
small parts"). The installed mallet (3,506 triangles in 32 Meshy pieces: hex head shell, band and end plates, 8-ring
wrap, studs, pommel) breaks under any decimation, so it is rebuilt from measurements of itself, in bind space (glTF axes):
- head: the hexagonal prism of the shell (corner angles and radii from the dense-sampled mid section, ends at the shell's
  extent along the head axis); bands, plates, studs and the band spikes go to the baked maps;
- shaft: an N-sided lathe (default 8) round the fitted shaft axis whose profile is the old surface's maximum radius per
  2 mm, simplified by Douglas-Peucker (TOL); corners at CORNER x the old radius (flats a little inside, corners a little
  outside: the fist's pads keep their contact); it runs from 6 mm inside the head to the pommel tip, and a second short
  lathe makes the top knob;
- UVs: one strip per lathe part (split at SPLIT_T to fit), the head's six sides as one strip, the two caps; shelf-packed
  into the unit square with MARGIN px at RES;
- normals: smooth across edges under SHARP (0.8 rad: the lathe stays round, the hex head and its caps stay hard), split at sharper edges and at UV seams.
Writes work/mallet_new.npz (P, N, UV, I) and prints the triangle count. Inputs: work/mallet_geom.json,
work/mallet_samples.npz, work/shaft_profile.npy (mallet_analyse.py and the sampling step)."""
import json
import os
import numpy as np

SIDES = int(os.environ.get('SIDES', '8'))
TOL = float(os.environ.get('TOL', '0.002'))
CORNER = float(os.environ.get('CORNER', '1.03'))
SPLIT_T = float(os.environ.get('SPLIT_T', '0.29'))
RES, MARGIN = 1024, 8
SHARP = float(os.environ.get('SHARP', '0.8'))   # above the 8-sided lathe's 45 deg (round shaft), below the hex head's 60 deg
G = json.load(open('work/mallet_geom.json'))
c, ax = np.array(G['shaft_c']), np.array(G['shaft_ax'])
hc, hx, e1, e2 = (np.array(G[k]) for k in ('head_c', 'head_ax', 'head_e1', 'head_e2'))
d = np.load('work/mallet_samples.npz'); S, sp = d['S'], d['piece']
prof = np.load('work/shaft_profile.npy')        # t, r max, r p90 per 2 mm (shaft pieces only)

# shaft frame: two unit vectors perpendicular to the axis, the first towards the head's long axis
a1 = hx - (hx @ ax) * ax; a1 /= np.linalg.norm(a1); a2 = np.cross(ax, a1)


def dp(pts, tol):
    """Douglas-Peucker on a 2D polyline (keeps the end points)."""
    if len(pts) < 3:
        return pts
    a, b = pts[0], pts[-1]; ab = b - a; L = np.linalg.norm(ab)
    dist = np.abs(ab[0] * (pts[:, 1] - a[1]) - ab[1] * (pts[:, 0] - a[0])) / L if L > 0 else np.linalg.norm(pts - a, axis=1)
    k = int(np.argmax(dist))
    if dist[k] > tol:
        return np.vstack([dp(pts[:k + 1], tol)[:-1], dp(pts[k:], tol)])
    return np.vstack([a, b])


tris, uvs, isl = [], [], []        # triangles as 3x3 positions, 3x2 island-local uv (metres), island id
islands = []                        # per island: list of triangle indices


def add_island():
    islands.append([]); return len(islands) - 1


def tri(p, q, w, island):
    tris.append(np.array([p[0], q[0], w[0]])); uvs.append(np.array([p[1], q[1], w[1]])); isl.append(island)


def lathe(stations, close_start, close_end, split=None):
    """stations: (t, r) along the axis. Rings of SIDES vertices; uv: u = arc round the ring at that radius (centred),
    v = profile arc length. Closing a ring end adds a fan to a centre point."""
    rings = []
    for t, r in stations:
        rc = r * CORNER
        rings.append([c + ax * t + rc * (np.cos(2 * np.pi * k / SIDES) * a1 + np.sin(2 * np.pi * k / SIDES) * a2) for k in range(SIDES + 1)])
    arc = np.concatenate([[0], np.cumsum(np.hypot(np.diff(stations[:, 0]), np.diff(stations[:, 1] * CORNER)))])
    island = add_island(); v0 = 0.0
    for i in range(len(stations) - 1):
        if split is not None and stations[i, 0] >= split and stations[i - 1, 0] < split and i > 0:
            island = add_island(); v0 = arc[i]
        for k in range(SIDES):
            def P(j, kk):
                w = 2 * np.pi * stations[j, 1] * CORNER
                return (rings[j][kk], np.array([(kk / SIDES - 0.5) * w, arc[j] - v0]))
            A, B, C, D = P(i, k), P(i, k + 1), P(i + 1, k + 1), P(i + 1, k)
            if stations[i, 1] > 1e-5:
                tri(A, B, C, island)
            if stations[i + 1, 1] > 1e-5:
                tri(A, C, D, island)
    for end, close in ((0, close_start), (len(stations) - 1, close_end)):
        if not close or stations[end, 1] < 1e-5:
            continue
        island = add_island(); t, r = stations[end]; rc = r * CORNER
        ctr = (c + ax * t, np.zeros(2))
        for k in range(SIDES):
            pa = (rings[end][k], rc * np.array([np.cos(2 * np.pi * k / SIDES), np.sin(2 * np.pi * k / SIDES)]))
            pb = (rings[end][k + 1], rc * np.array([np.cos(2 * np.pi * (k + 1) / SIDES), np.sin(2 * np.pi * (k + 1) / SIDES)]))
            tri(ctr, pb, pa, island) if end == 0 else tri(ctr, pa, pb, island)


# --- shaft lathe: from 6 mm inside the head's lower flat to the pommel tip -------------------------------------------
t_head_lo = float(((hc - c) @ ax)) + 0.1328          # head centre + hex inradius along the shaft
t_head_hi = float(((hc - c) @ ax)) - 0.1328
m = prof[:, 0] > t_head_lo - 0.006
pts = np.column_stack([prof[m, 0], prof[m, 1]])
pts = np.vstack([[pts[0, 0] - 0.002, pts[0, 1]], pts, [pts[-1, 0] + 0.002, 0.0]])
st = dp(pts, TOL)
print('shaft stations', len(st))
lathe(st, close_start=True, close_end=False, split=SPLIT_T)
# --- top knob: from 6 mm inside the head's upper flat to the tip ----------------------------------------------------
m = prof[:, 0] < t_head_hi + 0.006
pts = np.column_stack([prof[m, 0], prof[m, 1]])[::-1]
pts = np.vstack([pts, [pts[-1, 0] - 0.001, 0.0]])
st2 = dp(pts, TOL)
print('knob stations', len(st2))
lathe(st2[::-1], close_start=False, close_end=True)

# --- head: hexagonal prism ------------------------------------------------------------------------------------------
q = S[sp == 17] - hc; s = q @ hx; mid = np.abs(s) < 0.2
qq = q[mid] - np.outer(s[mid], hx); ang = np.arctan2(qq @ e2, qq @ e1); rr = np.linalg.norm(qq, axis=1)
bins = np.linspace(-np.pi, np.pi, 145); rb = np.array([rr[(ang >= bins[i]) & (ang < bins[i + 1])].max() for i in range(144)])
rb_s = np.array([rb[(i + np.arange(-2, 3)) % 144].max() for i in range(144)])
peaks = [i for i in range(144) if rb_s[i] == rb[i] and rb[i] >= rb[(i - 1) % 144] and rb[i] >= rb[(i + 1) % 144]]
peaks = sorted(peaks, key=lambda i: -rb[i])[:6]; peaks = sorted(peaks)
corners = []
for i in peaks:
    mm = (ang >= bins[i]) & (ang < bins[i + 1]); j = np.argmax(np.where(mm, rr, -1))
    corners.append(qq[j] / 1.0)
corners = np.array(corners)
print('hex corners: angles', np.round(np.degrees(np.arctan2(corners @ e2, corners @ e1)), 1), 'radii', np.round(np.linalg.norm(corners, axis=1), 4))
s0, s1 = float(s.min()), float(s.max())
ring0 = [hc + hx * s0 + p for p in corners]; ring1 = [hc + hx * s1 + p for p in corners]
side = add_island(); u = 0.0
for k in range(6):
    k2 = (k + 1) % 6; w = np.linalg.norm(corners[k2] - corners[k])
    A, B = (ring0[k], np.array([u, 0])), (ring0[k2], np.array([u + w, 0]))
    C, D = (ring1[k2], np.array([u + w, s1 - s0])), (ring1[k], np.array([u, s1 - s0]))
    tri(A, B, C, side); tri(A, C, D, side); u += w
for ring, sign in ((ring0, -1), (ring1, 1)):
    cap = add_island(); ctr2 = np.array([corners @ e1, corners @ e2]).T
    pts2 = [(ring[k], np.array([corners[k] @ e1, corners[k] @ e2]) * (1 if sign > 0 else -1) * np.array([1, 1])) for k in range(6)]
    for k in range(1, 5):
        a_, b_, c_ = pts2[0], pts2[k], pts2[k + 1]
        tri(a_, b_, c_, cap) if sign > 0 else tri(a_, c_, b_, cap)

T = np.array(tris); UVm = np.array(uvs); ISL = np.array(isl)
# winding is outward by construction: rings run counter-clockwise about their axis, stations along +axis
print('TRIANGLES', len(T), 'islands', len(islands))

# --- pack islands (shelf packer, binary search on the scale in px per metre) ----------------------------------------
boxes = []
for k in range(len(islands)):
    uv = UVm[ISL == k].reshape(-1, 2); boxes.append((uv.min(0), uv.max(0)))


def pack(scale):
    """skyline bottom-left packer, islands sorted by their longer side, each tried upright and turned 90 deg"""
    order = sorted(range(len(boxes)), key=lambda k: -max(boxes[k][1] - boxes[k][0]))
    sky = np.zeros(RES); place = {}
    for k in order:
        best = None
        for rot in (0, 1):
            w, h = (boxes[k][1] - boxes[k][0])[::-1 if rot else 1] * scale
            W, H = int(np.ceil(w)) + 2 * MARGIN, int(np.ceil(h)) + 2 * MARGIN
            if W > RES:
                continue
            for x in range(0, RES - W + 1, 4):
                y = sky[x:x + W].max()
                if y + H <= RES and (best is None or (y, x) < best[:2]):
                    best = (y, x, rot, W, H)
        if best is None:
            return None
        y, x, rot, W, H = best; sky[x:x + W] = y + H; place[k] = (x + MARGIN, y + MARGIN, rot)
    return place


lo, hi = 100.0, 5000.0
for _ in range(30):
    mid_ = (lo + hi) / 2
    lo, hi = (mid_, hi) if pack(mid_) else (lo, mid_)
scale = lo; place = pack(scale)
print('UV scale', round(scale, 1), 'px per metre')
UV = np.zeros_like(UVm)
for k in range(len(islands)):
    sel = ISL == k; ox, oy, rot = place[k]; loc = (UVm[sel] - boxes[k][0]) * scale
    if rot:
        loc = np.stack([loc[..., 1], (boxes[k][1] - boxes[k][0])[0] * scale - loc[..., 0]], -1)
    UV[sel] = (loc + np.array([ox, oy])) / RES

# --- vertices: split at sharp edges and UV seams --------------------------------------------------------------------
fn = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); fa = np.linalg.norm(fn, axis=1); fn /= fa[:, None]
pk = np.round(T.reshape(-1, 3), 6); _, pid = np.unique(pk, axis=0, return_inverse=True); pid = pid.reshape(-1, 3)
# corner groups: union corners of the same position in faces sharing an edge through it, when the edge is smooth
parent = np.arange(len(T) * 3)


def find(i):
    while parent[i] != i:
        parent[i] = parent[parent[i]]; i = parent[i]
    return i


edges = {}
for f in range(len(T)):
    for k in range(3):
        a, b = pid[f, k], pid[f, (k + 1) % 3]; edges.setdefault((min(a, b), max(a, b)), []).append((f, k, (k + 1) % 3))
for (a, b), lst in edges.items():
    if len(lst) != 2:
        continue
    (f, ka, kb), (g, la, lb) = lst
    if np.arccos(np.clip(fn[f] @ fn[g], -1, 1)) > SHARP:
        continue
    # corners of a and b in f and g
    for pos in (a, b):
        cf = f * 3 + [i for i in range(3) if pid[f, i] == pos][0]; cg = g * 3 + [i for i in range(3) if pid[g, i] == pos][0]
        ra, rb_ = find(cf), find(cg)
        if ra != rb_:
            parent[ra] = rb_
grp = np.array([find(i) for i in range(len(T) * 3)])
VN = np.zeros((len(T) * 3, 3))
acc = {}
for i in range(len(T) * 3):
    acc.setdefault(grp[i], np.zeros(3)); acc[grp[i]] += fn[i // 3] * fa[i // 3]
for i in range(len(T) * 3):
    v = acc[grp[i]]; VN[i] = v / np.linalg.norm(v)
key = np.hstack([pk, np.round(VN, 4), np.round(UV.reshape(-1, 2), 6)])
_, first, inv = np.unique(key, axis=0, return_index=True, return_inverse=True)
P = pk[first].astype(np.float32); N = VN[first].astype(np.float32); UVv = UV.reshape(-1, 2)[first].astype(np.float32)
I = inv.reshape(-1, 3).astype(np.uint32)
np.savez('work/mallet_new.npz', P=P, N=N, UV=UVv, I=I, island=ISL, scale=scale)
print('VERTICES', len(P), 'TRIANGLES', len(I), 'UV coverage', round(float(sum(
    abs((UV[i, 1] - UV[i, 0])[0] * (UV[i, 2] - UV[i, 0])[1] - (UV[i, 1] - UV[i, 0])[1] * (UV[i, 2] - UV[i, 0])[0]) / 2
    for i in range(len(UV)))), 3))
for k in range(len(islands)):
    print('island', k, 'size px', np.round((boxes[k][1] - boxes[k][0]) * scale).astype(int), 'at', place[k])
