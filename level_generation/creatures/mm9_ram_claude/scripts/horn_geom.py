"""Procedural ram horns fitted to the MM9 RAM.abc `ramhorn` piece (numpy only; imported by build_horns.py and
compose_horn.py).

MM9's horn is a 4-ring tube per side (21 vertices) rooted on top of the skull and curling up, out, back, down and
forward round the ear to a point (rigid on Xheadpiv). We keep its centreline (ring centres, plus the base pushed into
the skull) and its thickness profile, and sweep a smooth, finer tube along it:
- centreline: centripetal Catmull-Rom through the MM9 ring centres, resampled by arc length;
- frames: rotation-minimising (parallel transport), the reference axis turned to the outside of the curl;
- section: a rounded triangle (ram horns are flat on the outer face), radius from MM9's rings, tapering to the tip;
- growth ridges are not geometry: compose_horn.py paints them (colour + normal) from the same (s, theta) map.
UVs: the horn is unrolled (u along the length, v round the section) into two stacked strips of the 1K horn texture,
split at mid-length, so the texel density stays isotropic; both horns share the layout (mirror, deliberate overlap).
"""
import numpy as np

# MM9 ring centres of the RIGHT horn (creature's right = -X), bind pose, Blender world (Z up, faces -Y), from
# work/mm9_ram_pieces.npz (rings by graph distance from the skull boundary; tip = the last vertex)
RING_C = np.array([[-0.042, -0.494, 0.456], [-0.089, -0.444, 0.534], [-0.208, -0.375, 0.498],
                   [-0.268, -0.353, 0.320], [-0.204, -0.498, 0.221], [-0.139, -0.586, 0.248]])
RING_R = np.array([0.048, 0.075, 0.064, 0.053, 0.028, 0.0])
N_LEN = 36          # stations along the horn
N_AROUND = 12       # section vertices
BASE_SINK = 0.035   # the base continues this far into the skull (hidden), so no gap opens at the root


def catmull_rom(P, n, alpha=0.5):
    """Centripetal Catmull-Rom through P (end points mirrored), sampled densely, then resampled by arc length."""
    P = np.asarray(P, float)
    ext = np.vstack([2 * P[0] - P[1], P, 2 * P[-1] - P[-2]])
    dense = []
    for i in range(1, len(ext) - 2):
        p0, p1, p2, p3 = ext[i - 1:i + 3]
        t0 = 0.0
        t1 = t0 + np.linalg.norm(p1 - p0) ** alpha
        t2 = t1 + np.linalg.norm(p2 - p1) ** alpha
        t3 = t2 + np.linalg.norm(p3 - p2) ** alpha
        for t in np.linspace(t1, t2, 60, endpoint=False):
            a1 = (t1 - t) / (t1 - t0) * p0 + (t - t0) / (t1 - t0) * p1
            a2 = (t2 - t) / (t2 - t1) * p1 + (t - t1) / (t2 - t1) * p2
            a3 = (t3 - t) / (t3 - t2) * p2 + (t - t2) / (t3 - t2) * p3
            b1 = (t2 - t) / (t2 - t0) * a1 + (t - t0) / (t2 - t0) * a2
            b2 = (t3 - t) / (t3 - t1) * a2 + (t - t1) / (t3 - t1) * a3
            dense.append((t2 - t) / (t2 - t1) * b1 + (t - t1) / (t2 - t1) * b2)
    dense.append(P[-1])
    dense = np.array(dense)
    seg = np.linalg.norm(np.diff(dense, axis=0), axis=1)
    s = np.concatenate([[0], np.cumsum(seg)])
    # knot arc positions (where the dense curve passes the control points)
    knots = [0.0] + [s[60 * k] for k in range(1, len(P) - 1)] + [s[-1]]
    # denser sampling near the tip, where the curl is tight
    u = np.linspace(0, 1, n)
    u = 1 - (1 - u) ** 1.25
    target = u * s[-1]
    out = np.array([np.interp(target, s, dense[:, k]) for k in range(3)]).T
    return out, target, np.array(knots)


def centreline():
    base_dir = RING_C[0] - RING_C[1]
    base_dir /= np.linalg.norm(base_dir)
    base = RING_C[0] + base_dir * BASE_SINK
    pts = np.vstack([base, RING_C])
    radii = np.concatenate([[RING_R[0]], RING_R])
    C, s, knots = catmull_rom(pts, N_LEN)
    # radius along the arc: MM9 rings, the base kept full, a soft taper to a 4 mm tip
    r = np.interp(s, knots, radii)
    r = np.maximum(r, 0.004)
    r[0] = r[1] = max(r[1], 0.05)
    return C, s, r


def frames(C):
    T = np.gradient(C, axis=0)
    T /= np.linalg.norm(T, axis=1, keepdims=True)
    # reference: away from the curl's centre (centre of the MM9 rings 1-4)
    centre = RING_C[1:5].mean(0)
    n0 = (C[0] - centre)
    n0 -= T[0] * (n0 @ T[0])
    n0 /= np.linalg.norm(n0)
    N = [n0]
    for k in range(1, len(C)):
        v = N[-1] - T[k] * (N[-1] @ T[k])
        N.append(v / np.linalg.norm(v))
    N = np.array(N)
    # turn every frame so N points away from the curl centre (keeps the flat outer face outside all along)
    for k in range(len(C)):
        want = C[k] - centre
        want -= T[k] * (want @ T[k])
        if np.linalg.norm(want) < 1e-6:
            continue
        want /= np.linalg.norm(want)
        b = np.cross(T[k], N[k])
        ang = np.arctan2(want @ b, want @ N[k])
        N[k] = np.cos(ang) * N[k] + np.sin(ang) * b
    B = np.cross(T, N)
    return T, N, B


def section(theta):
    """Rounded triangle: flatter on the outer face (theta = 0 points outward)."""
    return 1.0 + 0.10 * np.cos(3 * (theta + np.pi / 3)) - 0.06 * np.cos(theta)


def build(side=-1):
    """Vertices (n_len * n_around, 3), quads (as triangle index triples), per-corner UVs, per-vertex (s, theta).
    side -1 = the creature's right horn (MM9 data), +1 = mirrored left horn."""
    C, s, r = centreline()
    T, N, B = frames(C)
    th = np.linspace(0, 2 * np.pi, N_AROUND, endpoint=False)
    shape = section(th)
    V = (C[:, None, :] + r[:, None, None] * shape[None, :, None]
         * (np.cos(th)[None, :, None] * N[:, None, :] + np.sin(th)[None, :, None] * B[:, None, :]))
    V = V.reshape(-1, 3)
    if side > 0:
        V = V * np.array([-1, 1, 1])
    # isotropic unroll: u = arc length, v = arc round the section, both times one density D; two strips (split at
    # mid-length) stacked in v, each trapezoid centred on its own row
    ring = V.reshape(len(C), N_AROUND, 3)
    edge = np.linalg.norm(np.roll(ring, -1, axis=1) - ring, axis=2)          # (n_len, n_around)
    arc = np.concatenate([np.zeros((len(C), 1)), np.cumsum(edge, axis=1)], axis=1)   # (n_len, n_around + 1)
    circ = arc[:, -1]
    L = s[-1]
    split = int(np.searchsorted(s, L / 2))
    w0, w1 = circ[:split + 1].max(), circ[split:].max()
    l0, l1 = s[split], L - s[split]
    D = min(0.96 / max(l0, l1), 0.94 / (w0 + w1))
    rows = [(0.02 + w0 * D / 2), (0.02 + w0 * D + 0.02 + w1 * D / 2)]
    tris, uvs = [], []

    def uv(i, jj, strip):
        u = 0.02 + (s[i] - (0.0 if strip == 0 else s[split])) * D
        v = rows[strip] + (arc[i, jj] - circ[i] / 2) * D
        return (u, v)

    for i in range(len(C) - 1):
        strip = 0 if i < split else 1
        for j in range(N_AROUND):
            a = i * N_AROUND + j
            b = i * N_AROUND + (j + 1) % N_AROUND
            c = (i + 1) * N_AROUND + (j + 1) % N_AROUND
            d = (i + 1) * N_AROUND + j
            ua, ub, uc, ud = uv(i, j, strip), uv(i, j + 1, strip), uv(i + 1, j + 1, strip), uv(i + 1, j, strip)
            if side > 0:   # mirrored: keep outward winding
                tris += [(a, c, b), (a, d, c)]
                uvs += [(ua, uc, ub), (ua, ud, uc)]
            else:
                tris += [(a, b, c), (a, c, d)]
                uvs += [(ua, ub, uc), (ua, uc, ud)]
    # tip cap: a short cone closing the 4 mm end ring
    tip = len(V)
    V = np.vstack([V, (C[-1] + T[-1] * r[-1] * 0.8) * (np.array([-1, 1, 1]) if side > 0 else 1)])
    i = len(C) - 1
    uvt = (0.02 + (s[i] - s[split]) * D + r[-1] * 0.8 * D, rows[1])
    for j in range(N_AROUND):
        a = i * N_AROUND + j
        b = i * N_AROUND + (j + 1) % N_AROUND
        ua, ub = uv(i, j, 1), uv(i, j + 1, 1)
        if side > 0:
            tris.append((a, tip, b)); uvs.append((ua, uvt, ub))
        else:
            tris.append((a, b, tip)); uvs.append((ua, ub, uvt))
    info = {'length': float(L), 'split_s': float(s[split]), 'r_max': float(r.max()), 'stations': len(C),
            'density_uv_per_m': float(D), 'rows': rows, 'strip_widths': [float(w0 * D), float(w1 * D)]}
    return V, np.array(tris), np.array(uvs), info


def texel_to_s_theta(u, v, info, s_split):
    """Inverse map for compose_horn.py: texel UV -> (arc length s, arc round the section relative to the row centre)."""
    D = info['density_uv_per_m']
    rows = info['rows']
    strip = (v > (rows[0] + info['strip_widths'][0] / 2 + 0.01)).astype(int)
    s = np.where(strip == 0, (u - 0.02) / D, s_split + (u - 0.02) / D)
    a = (v - np.where(strip == 0, rows[0], rows[1])) / D
    return s, a, strip
