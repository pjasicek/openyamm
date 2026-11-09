"""Limb centrelines from exact mesh cross-sections (numpy, outside Blender; input from dump_mesh.py).
A limb is traced by marching from a seed along a direction: at each step the skin (piece 0) is cut by the plane
through the predicted point normal to the current direction, the section loop nearest the prediction is kept, its
area centroid is the centre, and the direction follows the last centres (smoothed).
Writes work/centrelines.json: per limb a list of {p: centre, area: m2, r: equivalent radius}.
Args: <npz> <out json>"""
import sys, json
import numpy as np

d = np.load(sys.argv[1]); co, tri, pv = d['co'], d['tri'], d['piece']
tri = tri[pv[tri].min(1) == 0]
V = co[tri]                                                     # (n, 3, 3)


def section(o, n):
    """segments of the plane (o, n) through the skin triangles: (m, 2, 3)"""
    s = (V - o) @ n                                             # (n, 3)
    pos = s > 0
    cut = pos.any(1) & ~pos.all(1)
    segs = []
    for t, sv in zip(V[cut], s[cut]):
        pts = []
        for i, j in ((0, 1), (1, 2), (2, 0)):
            if (sv[i] > 0) != (sv[j] > 0):
                a = sv[i] / (sv[i] - sv[j]); pts.append(t[i] + (t[j] - t[i]) * a)
        if len(pts) == 2:
            segs.append(pts)
    return np.array(segs)


def loops(segs, tol=1e-6):
    """chain segments into connected components (by shared endpoints)"""
    if len(segs) == 0:
        return []
    P = segs.reshape(-1, 3)
    key = np.round(P / 1e-5).astype(np.int64)
    _, inv = np.unique(key, axis=0, return_inverse=True)
    inv = inv.reshape(-1, 2)
    parent = list(range(inv.max() + 1))

    def f(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    for a, b in inv:
        ra, rb = f(a), f(b)
        if ra != rb:
            parent[ra] = rb
    comp = np.array([f(a) for a in inv[:, 0]])
    return [segs[comp == c] for c in np.unique(comp)]


def loop_stats(lp, o, n):
    """area centroid of a closed section (fan from its mean point, signed areas along n)"""
    m = lp.reshape(-1, 3).mean(0)
    a = lp[:, 0] - m; b = lp[:, 1] - m
    cr = np.cross(a, b) @ n                                      # 2 x signed area
    A = cr.sum() / 2
    if abs(A) < 1e-9:
        return m, 0.0
    c = m + ((a + b) / 3 * cr[:, None]).sum(0) / (2 * A)
    return c, abs(A)


def trace(seed, direction, length, step=0.025, smooth=4, R0=0.22):
    """contour centroid of the section segments within R of the prediction (length-weighted, tolerant of holes);
    R follows 1.7 x the last mean contour radius"""
    p = np.array(seed, float); dvec = np.array(direction, float); dvec /= np.linalg.norm(dvec)
    out = []; hist = []; R = R0
    t = 0.0
    while t <= length:
        segs = section(p, dvec)
        if len(segs):
            mid = segs.mean(1); L = np.linalg.norm(segs[:, 1] - segs[:, 0], axis=1)
            m = np.linalg.norm(mid - p, axis=1) < R
        if not len(segs) or m.sum() < 3:
            out.append({'p': [round(float(x), 5) for x in p], 'r': None, 'lost': True})
            p = p + dvec * step; t += step
            continue
        c = (mid[m] * L[m, None]).sum(0) / L[m].sum()
        for _ in range(2):                                       # re-centre once on the refined centre
            m = np.linalg.norm(mid - c, axis=1) < R
            c = (mid[m] * L[m, None]).sum(0) / L[m].sum()
        r = float((np.linalg.norm(mid[m] - c, axis=1) * L[m]).sum() / L[m].sum())
        R = max(0.08, min(0.3, 1.7 * r))
        out.append({'p': [round(float(x), 5) for x in c], 'r': round(r, 4), 'perim': round(float(L[m].sum()), 4)})
        hist.append(c)
        if len(hist) >= 3:
            h = np.array(hist[-smooth:])
            u = np.linalg.svd(h - h.mean(0))[2][0]
            if u @ dvec < 0:
                u = -u
            dvec = 0.6 * dvec + 0.4 * u; dvec /= np.linalg.norm(dvec)
        p = c + dvec * step; t += step
    return out


if __name__ == '__main__':
    SEEDS = json.load(open(sys.argv[3])) if len(sys.argv) > 3 else {}
    res = {}
    for name, s in SEEDS.items():
        res[name] = trace(s['seed'], s['dir'], s['len'], s.get('step', 0.025))
        for k, e in enumerate(res[name]):
            print(name, k, e['p'], e['r'], 'LOST' if e.get('lost') else '')
    json.dump(res, open(sys.argv[2], 'w'), indent=1)
