#!/usr/bin/env python3
"""The sphinxes as signed distance fields (numpy), polygonised by surface nets into the high meshes.

Model space in map units (1 model metre = 100 units): x lateral (+x = the sphinx's own left = glTF/Blender +X),
f forward (the face's direction = glTF +Z = Blender -Y), z up. Origin = the middle of the door's threshold on the
breast face, at the ground. Everything is cut at z = -skirt (open bottom, the skirt sinks into the ground).

The body is a smooth union of ellipsoids, rounded boxes and capsules (haunches, folded hind legs, loaf-shaped torso,
shoulders, forelegs with paws and toes, a flat breast between the paws, a tail along the left flank); the door is a
framed opening cut into the breast. The head is the nemes headdress (front-, side- and top-view profiles intersected,
raised stripes, a plain forehead band with a uraeus), its two striped lappets and a window for the face; the face
itself is grafted in Blender (build_high.py), the `face_proxy` here is only for previews.

Usage: sphinx_sdf.py <north|south> [--cell 6] [--preview]   writes work/<id>/sdf.npz (+ previews)"""
import argparse
import json
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
WORK = HERE.parent / 'work'


# ---------------------------------------------------------------- primitives (vectorised over X, F, Z arrays)
def ellipsoid(X, F, Z, c, r):
    dx, df, dz = X - c[0], F - c[1], Z - c[2]
    k0 = np.sqrt((dx / r[0]) ** 2 + (df / r[1]) ** 2 + (dz / r[2]) ** 2)
    k1 = np.sqrt((dx / r[0] ** 2) ** 2 + (df / r[1] ** 2) ** 2 + (dz / r[2] ** 2) ** 2)
    return k0 * (k0 - 1.0) / np.maximum(k1, 1e-9)


def round_box(X, F, Z, c, h, r):
    qx = np.abs(X - c[0]) - h[0] + r
    qf = np.abs(F - c[1]) - h[1] + r
    qz = np.abs(Z - c[2]) - h[2] + r
    out = np.sqrt(np.maximum(qx, 0) ** 2 + np.maximum(qf, 0) ** 2 + np.maximum(qz, 0) ** 2)
    return out + np.minimum(np.maximum(np.maximum(qx, qf), qz), 0) - r


def capsule(X, F, Z, a, b, r1, r2=None):
    r2 = r1 if r2 is None else r2
    ba = np.subtract(b, a, dtype=float)
    px, pf, pz = X - a[0], F - a[1], Z - a[2]
    h = np.clip((px * ba[0] + pf * ba[1] + pz * ba[2]) / ba.dot(ba), 0, 1)
    return np.sqrt((px - ba[0] * h) ** 2 + (pf - ba[1] * h) ** 2 + (pz - ba[2] * h) ** 2) - (r1 + (r2 - r1) * h)


def smin(a, b, k):
    if k <= 0:
        return np.minimum(a, b)
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b + (a - b) * h - k * h * (1 - h)


def smax(a, b, k):
    return -smin(-a, -b, k)


def bands(t, period, gold=0.55, soft=0.12):
    """1 on the raised (gold) stripes, 0 on the sunk (dark) ones, soft edges."""
    ph = np.mod(t / period, 1.0)
    e = soft
    up = np.clip((ph - 0.0) / e, 0, 1) * np.clip((gold - ph) / e, 0, 1)
    return up * up * (3 - 2 * up)


def mirrored(X):
    return np.abs(X)


# ---------------------------------------------------------------- the head (shared by both sphinxes)
# Head-local frame: x lateral, g = f - head_f (0 at the face plane, the cheeks), z' = (z - head_z) (0 at the chin).
# Northern numbers: face 600 wide, chin to the nemes top 880, wings 1,380 wide.
HEAD = {
    'top': 880,
    # front-view half-width of the nemes (z' -> half-width)
    'w_z': [[-60, 640], [40, 690], [160, 680], [330, 560], [470, 445], [640, 425], [800, 400], [880, 380]],
    # side view: the front surface (g) and the back (g) as functions of z'
    'front_z': [[-60, -150], [150, -95], [400, -70], [540, -55], [600, -10], [740, -5], [810, -40], [880, -150]],
    'back_z': [[-60, -1150], [250, -1120], [600, -1000], [880, -820]],
    # top view: half-width limit as a function of g (the wings are flaps; behind them the cloth wraps the skull)
    'w_g': [[-1200, 330], [-950, 380], [-650, 470], [-380, 700], [0, 700]],
    'bottom': -60,             # the wings' lower edge
    'window': {'half': 300, 'z0': -120, 'z1': 590, 'g0': -330, 'r': 60},   # the face's opening
    'band': [585, 775],         # the plain forehead band (z')
    'stripe': {'period': 64, 'amp': 7, 'gold': 0.56},
    'uraeus': {'c': [0, 0, 760], 'r': [42, 40, 110]},
    'lappet': {'x': 400, 'half_x': 100, 'half_g': 90, 'z0': -720, 'z1': 120, 'g': -120, 'tilt': 0.08, 'r': 30},
    'skull': {'c': [0, -520, 380], 'r': [330, 520, 420]},
    'face_proxy': {'c': [0, -120, 330], 'r': [270, 230, 400]},
}


def head_sdf(X, F, Z, head_f, head_z, s, with_face_proxy=False):
    """Nemes + lappets (and a face stand-in for previews) at scale s; returns (d_nemes, d_face_proxy)."""
    H = HEAD
    x = np.abs(X) / s
    g = (F - head_f) / s
    z = (Z - head_z) / s
    w = np.array(H['w_z'], float)
    fz = np.array(H['front_z'], float)
    bz = np.array(H['back_z'], float)
    wg = np.array(H['w_g'], float)
    st = H['stripe']
    sz = bands(z, st['period'], st['gold'])
    sx = bands(x + 0.5 * st['period'] * st['gold'], st['period'], st['gold'])
    plain = (z > H['band'][0]) & (z < H['band'][1])
    sz = np.where(plain, 0.0, sz)
    amp = st['amp'] * STRIPES
    d_side = x - np.interp(z, w[:, 0], w[:, 1]) - amp * sz
    d_front = g - np.interp(z, fz[:, 0], fz[:, 1]) - amp * np.where(plain, 0.6, sz)
    d_back = np.interp(z, bz[:, 0], bz[:, 1]) - g - amp * sz
    d_topw = x - np.interp(g, wg[:, 0], wg[:, 1]) - amp * sz
    d_top = z - H['top'] - amp * sx
    d_bot = H['bottom'] - z
    d = smax(d_side, d_front, 18)
    d = smax(d, d_back, 30)
    d = smax(d, d_topw, 40)
    d = smax(d, d_top, 26)
    d = smax(d, d_bot, 14)
    win = H['window']
    d_win = round_box(x, g, z, (0, win['g0'] + 400, 0.5 * (win['z0'] + win['z1'])),
                      (win['half'], 400, 0.5 * (win['z1'] - win['z0'])), win['r'])
    d = smax(d, -d_win, 16)
    u = H['uraeus']
    d = smin(d, ellipsoid(x, g, z, (0, np.interp(u['c'][2], fz[:, 0], fz[:, 1]) + 12, u['c'][2]), u['r']), 12)
    # lappets: striped bands falling in front of the shoulders, leaning forward a little at the bottom
    L = H['lappet']
    lz = np.clip(z, L['z0'], L['z1'])
    lg = L['g'] + L['tilt'] * (L['z1'] - lz)
    d_lap = round_box(x, g - lg, z, (L['x'], 0, 0.5 * (L['z0'] + L['z1'])),
                      (L['half_x'], L['half_g'], 0.5 * (L['z1'] - L['z0'])), L['r']) - amp * sz
    d = smin(d, d_lap, 20)
    d_face = None
    if with_face_proxy:
        fp = H['face_proxy']
        d_face = ellipsoid(x, g, z, fp['c'], fp['r'])
    return d * s, (None if d_face is None else d_face * s)


# ---------------------------------------------------------------- the bodies
def door_cut(X, F, Z, D):
    """The framed doorway: a raised Egyptian frame (jambs, lintel with a cornice) on the breast and the opening cut
    through frame and breast from the frame's front back to D['back'] (open at the back)."""
    hw, h = D['width'] / 2, D['height']
    j, fr = D['jamb'], D['front']
    frame = round_box(X, F, Z, (0, fr - 40, (h + D['lintel']) / 2 - 20),
                      (hw + j, 40, (h + D['lintel']) / 2 + 20), 6)
    cornice = round_box(X, F, Z, (0, fr - 40 + D['cornice_out'] / 2, h + D['lintel'] - D['cornice_h'] / 2 + 14),
                        (hw + j + D['cornice_out'], 40 + D['cornice_out'] / 2, D['cornice_h'] / 2), 8)
    opening = round_box(X, F, Z, (0, (fr + D['back']) / 2 + 30, h / 2 - 50),
                        (hw, (fr - D['back']) / 2 + 30, h / 2 + 50), 2)
    return smin(frame, cornice, 6), opening


def north_body(X, F, Z, P):
    d = ellipsoid(X, F, Z, (0, -5250, 280), (820, 1060, 760))                     # rump
    d = smin(d, ellipsoid(mirrored(X), F, Z, (600, -4700, 400), (285, 950, 480)), 200)   # hind thighs
    d = smin(d, capsule(mirrored(X), F, Z, (650, -4350, 150), (690, -3350, 120), 150, 125), 160)  # hind paws
    d = smin(d, round_box(X, F, Z, (0, -3650, 520), (650, 1950, 560), 430), 260)     # torso
    d = smin(d, ellipsoid(X, F, Z, (0, -2050, 700), (800, 820, 800)), 300)           # shoulders / chest
    d = smin(d, ellipsoid(mirrored(X), F, Z, (500, -2100, 760), (340, 700, 600)), 200)
    # forelegs: upper arm down to the elbow, forearm lying flat to the paw, paw with four toes
    for sx in (-1, 1):
        cx = sx * 640
        leg = capsule(X, F, Z, (sx * 600, -2250, 700), (sx * 640, -1650, 290), 300, 250)
        leg = smin(leg, round_box(X, F, Z, (cx, -650, 205), (238, 1050, 205), 150), 160)
        leg = smin(leg, ellipsoid(X, F, Z, (cx, 250, 150), (250, 260, 165)), 90)
        for tx in (-170, -57, 57, 170):
            leg = smin(leg, ellipsoid(X, F, Z, (cx + tx, 425, 85), (66, 92, 88)), 30)
        d = smin(d, leg, 140)
    # breast: flat front between the paws, curving back up to the throat
    br = round_box(X, F, Z, (0, -560, 400), (384, 580, 400), 110)
    br = smin(br, ellipsoid(X, F, Z, (0, -780, 720), (400, 640, 560)), 260)
    d = smin(d, br, 200)
    d = smin(d, ellipsoid(X, F, Z, (0, -1350, 1450), (520, 520, 560)), 250)          # neck
    # tail along the left flank (+x), lying on the ground, the tip curling up
    tail = capsule(X, F, Z, (690, -5900, 520), (790, -5450, 140), 95, 90)
    tail = smin(tail, capsule(X, F, Z, (790, -5450, 140), (800, -3700, 88), 90, 80), 60)
    tail = smin(tail, capsule(X, F, Z, (800, -3700, 88), (780, -3250, 170), 80, 70), 40)
    d = smin(d, tail, 50)
    return d


def south_body(X, F, Z, P):
    """Buried to the shoulders: the upper breast with its door, shoulders, a hump of back and the domed haunch,
    built as a shorter body sunk into the sand (z 0 = the sand line at the door)."""
    sink = P['sink']
    Zs = Z + sink
    d = ellipsoid(X, F, Zs, (0, -2300, 300), (520, 520, 760))                        # haunch
    d = smin(d, round_box(X, F, Zs, (0, -1500, 420), (420, 1050, 560), 360), 260)     # back
    d = smin(d, ellipsoid(X, F, Zs, (0, -620, 500), (620, 520, 600)), 300)            # shoulders / chest
    d = smin(d, ellipsoid(mirrored(X), F, Zs, (400, -620, 480), (240, 420, 560)), 160)
    br = round_box(X, F, Zs, (0, -210, sink + 200), (300, 230, 360), 90)                 # breast, flat front
    br = smin(br, ellipsoid(X, F, Zs, (0, -300, sink + 450), (320, 300, 220)), 120)
    d = smin(d, br, 160)
    d = smin(d, ellipsoid(X, F, Zs, (0, -560, sink + 820), (330, 360, 400)), 200)     # neck
    return d


BODIES = {'north': north_body, 'south': south_body}

STRIPES = 1.0     # 0 for the low mesh's source (stripes only in the normal and colour maps)
CONFIG = json.loads((HERE / 'sphinx.json').read_text())


def full_sdf(X, F, Z, P, face_proxy=False):
    d_body = BODIES[P['body']](X, F, Z, P)
    frame, opening = door_cut(X, F, Z, P['door'])
    d_body = smin(d_body, frame, 10)
    hp = P['head']
    d_head, d_face = head_sdf(X, F, Z, hp['f'], hp['z'], hp['scale'], face_proxy)
    d = np.minimum(d_body, d_head)
    if face_proxy:
        d = np.minimum(d, d_face)
    d = smax(d, -opening, 4)
    d = np.maximum(d, -P['skirt'] - Z)            # cut at the skirt's bottom (open there)
    return d, d_body, d_head


def grid_axes(P, cell):
    b = P['bounds']   # [[x0, x1], [f0, f1], [z0, z1]]
    xs = np.arange(b[0][0], b[0][1] + cell, cell, dtype=np.float32)
    fs = np.arange(b[1][0], b[1][1] + cell, cell, dtype=np.float32)
    zs = np.arange(-P['skirt'] - 2 * cell, b[2][1] + cell, cell, dtype=np.float32)
    return xs, fs, zs


def sample(P, cell, face_proxy=False):
    xs, fs, zs = grid_axes(P, cell)
    V = np.empty((len(xs), len(fs), len(zs)), np.float32)
    X, Z = np.meshgrid(xs, zs, indexing='ij')
    for j, f in enumerate(fs):
        V[:, j, :] = full_sdf(X, np.full_like(X, f), Z, P, face_proxy)[0]
    return xs, fs, zs, V


# ---------------------------------------------------------------- surface nets
CORNERS = np.array([[i, j, k] for k in (0, 1) for j in (0, 1) for i in (0, 1)])
EDGES = [(a, b) for a in range(8) for b in range(a + 1, 8) if np.abs(CORNERS[a] - CORNERS[b]).sum() == 1]


def surface_nets(V, origin, cell):
    nx, ny, nz = V.shape
    inside = V < 0
    any_in = np.zeros((nx - 1, ny - 1, nz - 1), bool)
    all_in = np.ones((nx - 1, ny - 1, nz - 1), bool)
    for c in CORNERS:
        s = inside[c[0]:nx - 1 + c[0], c[1]:ny - 1 + c[1], c[2]:nz - 1 + c[2]]
        any_in |= s
        all_in &= s
    active = any_in & ~all_in
    del any_in, all_in
    ci = np.argwhere(active).astype(np.int32)
    lin = np.ravel_multi_index(ci.T, active.shape)
    del active
    vals = np.stack([V[ci[:, 0] + c[0], ci[:, 1] + c[1], ci[:, 2] + c[2]] for c in CORNERS], 1)
    acc = np.zeros((len(ci), 3))
    cnt = np.zeros(len(ci))
    for a, b in EDGES:
        va, vb = vals[:, a], vals[:, b]
        m = (va < 0) != (vb < 0)
        t = va[m] / (va[m] - vb[m])
        acc[m] += CORNERS[a] + (CORNERS[b] - CORNERS[a]) * t[:, None]
        cnt[m] += 1
    verts = (ci + acc / cnt[:, None]) * cell + origin
    order = np.argsort(lin)
    lin_sorted = lin[order]
    shape = (nx - 1, ny - 1, nz - 1)

    def vid(i, j, k):
        q = np.ravel_multi_index((i, j, k), shape)
        pos = np.searchsorted(lin_sorted, q)
        return order[pos]

    quads = []
    for axis in range(3):
        # grid edges along `axis` between point p and p + e_axis with a sign change; the 4 cells around share it
        sl0 = [slice(1, n - 1) for n in V.shape]
        sl1 = list(sl0)
        sl0[axis] = slice(0, V.shape[axis] - 1)
        sl1[axis] = slice(1, V.shape[axis])
        a_in = inside[tuple(sl0)]
        b_in = inside[tuple(sl1)]
        change = a_in != b_in
        idx = np.argwhere(change).astype(np.int32)
        flip = a_in[change]
        idx += np.array([0 if ax == axis else 1 for ax in range(3)], np.int32)   # back to grid point indices
        u, v = [ax for ax in range(3) if ax != axis]
        cells = []
        for du, dv in ((0, 0), (1, 0), (1, 1), (0, 1)):
            c = idx.copy()
            c[:, u] -= 1 - du
            c[:, v] -= 1 - dv
            cells.append(vid(c[:, 0], c[:, 1], c[:, 2]))
        q = np.stack(cells, 1)
        # orientation: outward = from inside to outside along the axis
        q = np.where(((flip if axis != 1 else ~flip))[:, None], q, q[:, ::-1])
        quads.append(q)
    return verts.astype(np.float32), np.concatenate(quads).astype(np.int32)


# ---------------------------------------------------------------- previews (orthographic, from the grid)
def depth_view(V, axis, reverse):
    inside = V < 0
    if reverse:
        inside = np.flip(inside, axis)
    hit = inside.any(axis)
    first = np.argmax(inside, axis).astype(np.float32)
    first[~hit] = np.nan
    return first


def shade(depth, cell, scale=1.0):
    d = np.nan_to_num(depth, nan=np.nanmax(depth) + 50) * cell
    gy, gx = np.gradient(d)
    n = np.stack([-gx / cell, -gy / cell, np.ones_like(d)], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    light = np.array([-0.45, -0.55, 0.70])
    light /= np.linalg.norm(light)
    v = np.clip(n @ light, 0, 1) * 0.75 + 0.25
    img = np.where(np.isnan(depth), 0.12, v)
    return (np.clip(img, 0, 1) * 255).astype(np.uint8)


def previews(V, cell, out):
    # V axes (x, f, z). front: look along -f from +f -> image rows = z (top = high), cols = x (viewer's right = +x)
    fr = depth_view(V, 1, True)                          # (x, z)
    fr_img = shade(fr.T[::-1, :], cell)
    sd = depth_view(V, 0, False)                         # from -x side (the sphinx's right): (f, z)
    sd_img = shade(sd.T[::-1, ::-1], cell)               # cols: front to the left
    tp = depth_view(V, 2, True)                          # from above: (x, f)
    tp_img = shade(tp.T[::-1, :], cell)                  # rows: f high at top (front up)
    from PIL import Image
    for name, img in (('front', fr_img), ('side', sd_img), ('top', tp_img)):
        Image.fromarray(img).save(f'{out}_{name}.png')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('id')
    ap.add_argument('--cell', type=float, default=6.0)
    ap.add_argument('--preview', action='store_true')
    ap.add_argument('--proxy', action='store_true', help='face stand-in (previews only)')
    ap.add_argument('--no-mesh', action='store_true')
    ap.add_argument('--flat', action='store_true', help='no stripe relief (the low source): writes sdf_low.npz')
    a = ap.parse_args()
    global STRIPES
    P = CONFIG[a.id]
    if a.flat:
        STRIPES = 0.0
    work = WORK / a.id
    work.mkdir(parents=True, exist_ok=True)
    t = time.time()
    xs, fs, zs, V = sample(P, a.cell, a.proxy)
    print('SAMPLED', V.shape, '%.1fs' % (time.time() - t))
    edge = np.concatenate([V[0].ravel(), V[-1].ravel(), V[:, 0].ravel(), V[:, -1].ravel(), V[:, :, -1].ravel()])
    if (edge < 0).any():
        raise SystemExit('the model reaches the grid bounds: widen bounds in sphinx.json')
    if a.preview:
        previews(V, a.cell, str(work / 'sdf'))
    if a.no_mesh:
        return
    verts, quads = surface_nets(V, np.array([xs[0], fs[0], zs[0]]), a.cell)
    del V
    # labels per vertex: 0 body, 1 head (nemes, lappets), 2 door frame and opening
    X, F, Z = verts[:, 0].astype(np.float64), verts[:, 1].astype(np.float64), verts[:, 2].astype(np.float64)
    _, d_body, d_head = full_sdf(X, F, Z, P)
    frame, opening = door_cut(X, F, Z, P['door'])
    label = np.where(np.abs(d_head) < np.abs(d_body), 1, 0)
    label = np.where((np.minimum(np.abs(frame), np.abs(opening)) < 3 * a.cell) & (label == 0), 2, label)
    # the bottom cap (at -skirt) is dropped: quads whose vertices all lie on the cut
    cut = Z <= -P['skirt'] + 0.6 * a.cell
    keep = ~cut[quads].all(1)
    quads = quads[keep]
    np.savez_compressed(work / ('sdf_low.npz' if a.flat else 'sdf.npz'), verts=verts, quads=quads, label=label.astype(np.int8), cell=a.cell)
    print('MESH', len(verts), 'verts', len(quads), 'quads', '%.1fs' % (time.time() - t))


if __name__ == '__main__':
    main()
