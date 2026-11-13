#!/usr/bin/env python3
"""Stand-in for `oymap compare` (which did not exist during this run): stands at points on the original's floors,
looks up, down and in 16 level directions in both maps, and reports where distances and textures differ.
Usage: cmp.py [n points] [--sectors a,b,c]   (builds nothing: reads output/studio_cal/mm6_cd2/build/*.blv)"""
import sys, json, subprocess, math, random, collections
import numpy as np
R = '/home/pjasicek/github/OpenYAMM/'
D = R + 'output/studio_cal/mm6_cd2/'
O = R + 'openyamm-studio/build/oymap'


def load(path):
    return json.load(open(path))['map']


def tris(m, skip=()):
    V = np.array(m['vertices'], dtype=np.float64)
    A, B, C, T, FI = [], [], [], [], []
    for fi, f in enumerate(m['faces']):
        if f['is_portal'] or fi in skip:
            continue
        if f['attributes'] & 0x2000:  # invisible
            continue
        vs = f['vertices']
        for i in range(1, len(vs) - 1):
            A.append(V[vs[0]]); B.append(V[vs[i]]); C.append(V[vs[i + 1]]); T.append(f['texture'].lower()); FI.append(fi)
    return np.array(A), np.array(B), np.array(C), T, FI


def cast(A, B, C, orig, dirs):
    """Nearest hit distance and triangle for each ray (two-sided)."""
    e1 = B - A; e2 = C - A
    dist = np.full(len(orig), np.inf); idx = np.full(len(orig), -1)
    for s in range(0, len(orig), 256):
        o = orig[s:s + 256][:, None, :]; d = dirs[s:s + 256][:, None, :]
        p = np.cross(d, e2[None]); det = (e1[None] * p).sum(-1)
        ok = np.abs(det) > 1e-9
        inv = np.where(ok, 1.0 / np.where(ok, det, 1), 0)
        t = o - A[None]
        u = (t * p).sum(-1) * inv
        q = np.cross(t, e1[None])
        v = (d * q).sum(-1) * inv
        tt = (e2[None] * q).sum(-1) * inv
        hit = ok & (u >= -1e-6) & (v >= -1e-6) & (u + v <= 1 + 1e-6) & (tt > 1e-3)
        tt = np.where(hit, tt, np.inf)
        k = tt.argmin(1)
        dist[s:s + 256] = tt[np.arange(len(k)), k]; idx[s:s + 256] = np.where(np.isfinite(tt[np.arange(len(k)), k]), k, -1)
    return dist, idx


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 500
    only = None
    if '--sectors' in sys.argv:
        only = set(int(x) for x in sys.argv[sys.argv.index('--sectors') + 1].split(','))
    om = load(D + 'orig.json')
    subprocess.run([O, 'export', R + 'devdocs/map_studio/briefs/mm6_cd2/L4/build/calib_darkmoor.blv', '--out', D + 'rebuild.json'], check=True, capture_output=True)
    rm = load(D + 'rebuild.json')
    doors = json.load(open(D + 'doors.json'))
    oA, oB, oC, oT, oF = tris(om)
    rA, rB, rC, rT, rF = tris(rm)
    # sample points: area-weighted over the original's level-ish floor faces
    rnd = random.Random(7)
    V = om['vertices']
    cands = []
    for si, s in enumerate(om['sectors']):
        if only is not None and si not in only:
            continue
        for fi in s['floor_faces']:
            f = om['faces'][fi]
            p = [V[i] for i in f['vertices']]
            for i in range(1, len(p) - 1):
                a, b, c = np.array(p[0], float), np.array(p[i], float), np.array(p[i + 1], float)
                ar = np.linalg.norm(np.cross(b - a, c - a)) / 2
                if ar > 1:
                    cands.append((ar, a, b, c, si))
    # the caves are four fifths of the area: weight by the root of the area so the castle's rooms are looked at too
    w = [math.sqrt(c[0]) for c in cands]
    pts, sec = [], []
    for c in rnd.choices(cands, weights=w, k=n):
        u, v = rnd.random(), rnd.random()
        if u + v > 1:
            u, v = 1 - u, 1 - v
        p = c[1] + (c[2] - c[1]) * u + (c[3] - c[1]) * v
        pts.append(p + np.array([0, 0, 120.0])); sec.append(c[4])
    pts = np.array(pts)
    dirs = [(0, 0, 1), (0, 0, -1)] + [(math.cos(k * math.pi / 8), math.sin(k * math.pi / 8), 0) for k in range(16)]
    kinds = ['ceiling', 'floor'] + ['wall'] * 16
    tot = collections.Counter(); good = collections.Counter(); texgood = collections.Counter(); textot = collections.Counter()
    per = collections.defaultdict(lambda: [0, 0, collections.Counter()])
    shots = []
    for dv, kind in zip(dirs, kinds):
        dd = np.tile(np.array(dv, float), (len(pts), 1))
        d1, i1 = cast(oA, oB, oC, pts, dd)
        d2, i2 = cast(rA, rB, rC, pts, dd)
        for k in range(len(pts)):
            if not np.isfinite(d1[k]):
                continue
            tot[kind] += 1; per[sec[k]][1] += 1
            agree = np.isfinite(d2[k]) and abs(d1[k] - d2[k]) <= max(24.0, 0.08 * d1[k])
            if agree:
                good[kind] += 1; per[sec[k]][0] += 1
                textot[kind] += 1
                if oT[i1[k]] == rT[i2[k]]:
                    texgood[kind] += 1
                else:
                    per[sec[k]][2]['tex %s: %s for %s' % (kind, rT[i2[k]], oT[i1[k]])] += 1
            else:
                why = '%s %s' % (kind, 'missing' if not np.isfinite(d2[k]) else ('nearer' if d2[k] < d1[k] else 'farther'))
                per[sec[k]][2][why] += 1
                shots.append((abs(d1[k] - (d2[k] if np.isfinite(d2[k]) else 1e4)), sec[k], kind, pts[k].tolist(), dv, float(d1[k]), float(d2[k])))
    g = sum(good.values()); t = sum(tot.values())
    tg = sum(texgood.values()); tt = sum(textot.values())
    print('geometry %.1f %% (%d of %d rays agree): walls %.1f, ceilings %.1f, floors %.1f' % (
        100.0 * g / t, g, t, 100.0 * good['wall'] / max(1, tot['wall']), 100.0 * good['ceiling'] / max(1, tot['ceiling']),
        100.0 * good['floor'] / max(1, tot['floor'])))
    print('texture %.1f %% of agreeing rays: walls %.1f, ceilings %.1f, floors %.1f' % (
        100.0 * tg / max(1, tt), 100.0 * texgood['wall'] / max(1, textot['wall']),
        100.0 * texgood['ceiling'] / max(1, textot['ceiling']), 100.0 * texgood['floor'] / max(1, textot['floor'])))
    rows = sorted(((v[1] - v[0], k, v) for k, v in per.items()), reverse=True)
    print('worst sectors (rays that differ / rays, main reasons):')
    for miss, k, v in rows[:int(sys.argv[sys.argv.index('--worst') + 1]) if '--worst' in sys.argv else 14]:
        print('  S%-3d %3d / %3d  %s' % (k, miss, v[1], ', '.join('%s x%d' % (a, b) for a, b in v[2].most_common(4))))
    json.dump({'geometry': 100.0 * g / t, 'texture': 100.0 * tg / max(1, tt),
               'per_sector': {str(k): [v[0], v[1]] for k, v in per.items()},
               'worst_rays': [list(s) for s in sorted(shots, reverse=True)[:60]]}, open(D + 'cmp_last.json', 'w'))


if __name__ == '__main__':
    main()
